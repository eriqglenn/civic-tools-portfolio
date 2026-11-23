"""Use the local Codex app-server as the engine, with only Ledger's scoped lookup callbacks."""
import base64
import functools
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import time

import ai_lookups as lookup
from ledger_ai import SYSTEM, VOICE_STYLE, evidence, text, voice_context, voice_query


def executable():
    root = Path(os.environ.get('LOCALAPPDATA','')) / 'OpenAI/Codex/bin'
    found = shutil.which('codex.exe')
    candidates = ([Path(found)] if found else []) + sorted(root.glob('*/codex.exe'), key=lambda p:p.stat().st_mtime, reverse=True)
    for path in candidates:
        if path.is_file() and path.resolve().is_relative_to(root.resolve()):
            return path.resolve()
    return None


@functools.lru_cache(maxsize=4)
def verify_binary(path, modified):
    shell = Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    script = """$s=Get-AuthenticodeSignature -LiteralPath $env:LEDGER_CODEX_BINARY
if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'O="OpenAI OpCo, LLC"') {exit 1}"""
    result = subprocess.run([str(shell),'-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode('ascii')],
        env={**os.environ,'LEDGER_CODEX_BINARY':str(path),'PSModulePath':str(shell.parent/'Modules')},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,timeout=40)
    if result.returncode:raise ValueError('Windows could not verify the OpenAI signature on the installed Codex engine.')


class Session:
    def __init__(self, folder, binary, token):
        private = Path(folder)
        child_home = private/'runtime'
        workspace = private/'empty'
        child_home.mkdir()
        workspace.mkdir()
        self.workspace = str(workspace)
        env = {k:v for k,v in os.environ.items() if k.upper() in {
            'SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH','PATHEXT',
            'COMSPEC','PROGRAMFILES','PROGRAMFILES(X86)','HTTPS_PROXY','HTTP_PROXY','NO_PROXY','ALLUSERSPROFILE'}}
        env.update(CODEX_HOME=str(child_home),ACCESS_TOKEN=token)
        options = {
            'model_provider':'ledger','model_providers.ledger.name':'Ledger ChatGPT plan',
            'model_providers.ledger.base_url':'https://api.openai.com/v1','model_providers.ledger.env_key':'ACCESS_TOKEN',
            'model_providers.ledger.wire_api':'responses','model_providers.ledger.requires_openai_auth':False,
            'model_providers.ledger.supports_websockets':False,'web_search':'disabled',
            'shell_environment_policy.inherit':'none','features.shell_tool':False,
            'features.multi_agent':False,'features.tool_search':False,'analytics.enabled':False,
        }
        args=[str(binary),'app-server','--listen','stdio://']
        for key,value in options.items():args.extend(['-c',key+'='+json.dumps(value)])
        self.proc=subprocess.Popen(args,cwd=workspace,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        self.deadline=time.monotonic()+130
        self.messages=queue.Queue(maxsize=256)
        self.stopped=threading.Event()
        self.reader=threading.Thread(target=self.read,daemon=True)
        self.reader.start()

    def read(self):
        while not self.stopped.is_set():
            line=self.proc.stdout.readline(2_000_001)
            try:message=json.loads(line) if line and len(line)<=2_000_000 else None
            except ValueError:message=None
            while not self.stopped.is_set():
                try:self.messages.put(message,timeout=.25);break
                except queue.Full:continue
            if message is None:return

    def close(self):
        self.stopped.set()
        if self.proc.poll() is None:self.proc.kill()
        self.proc.wait(timeout=10)
        self.reader.join(timeout=3)
        self.proc.stdin.close()
        self.proc.stdout.close()

    def send(self,message):
        self.proc.stdin.write(json.dumps(message,ensure_ascii=True).encode()+b'\n')
        self.proc.stdin.flush()

    def next(self):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise ValueError('Codex timed out. Please try a shorter question.')
        try:message=self.messages.get(timeout=remaining)
        except queue.Empty:raise ValueError('Codex timed out. Try again.') from None
        if message is None:raise ValueError('The local Codex engine stopped responding.')
        return message

    def request(self, ident, method, params):
        self.send({'id':ident,'method':method,'params':params})
        while True:
            msg=self.next()
            if msg.get('id')==ident and not msg.get('method'):
                if 'error' in msg:raise ValueError('Codex '+method+' failed: '+text(msg['error'].get('message'),240))
                return msg['result']
            if 'id' in msg and 'method' in msg:self.deny(msg)

    def deny(self,msg):
        self.send({'id':msg['id'],'error':{'code':-32601,'message':'Only Ledger lookups are available.'}})

    def run(self,model,instructions,context,tools,schema,dispatch):
        self.request(1,'initialize',{'clientInfo':{'name':'neighborhood_ledger_mls','title':'Neighborhood Ledger MLS','version':'13.8'},
            'capabilities':{'experimentalApi':True}})
        self.send({'method':'initialized'})
        th=self.request(2,'thread/start',{'model':model,'modelProvider':'ledger','allowProviderModelFallback':False,
            'ephemeral':True,'cwd':self.workspace,'sandbox':'read-only','approvalPolicy':'never',
            'environments':[],'runtimeWorkspaceRoots':[],'selectedCapabilityRoots':[],
            'baseInstructions':instructions,'dynamicTools':tools})['thread']['id']
        turn=self.request(3,'turn/start',{'threadId':th,'environments':[],'effort':'low','outputSchema':schema,
            'input':[{'type':'text','text':json.dumps(context,ensure_ascii=False)}]})['turn']['id']
        answer=''
        while True:
            msg=self.next()
            method=msg.get('method');p=msg.get('params',{})
            if 'id' in msg and method:
                if method!='item/tool/call' or p.get('threadId')!=th or p.get('turnId')!=turn:
                    self.deny(msg);continue
                value=dispatch(p)
                self.send({'id':msg['id'],'result':{'success':True,'contentItems':[{'type':'inputText','text':json.dumps(value)}]}})
            if p.get('threadId')!=th:continue
            if method=='item/completed' and p.get('turnId')==turn:
                item=p.get('item',{})
                if item.get('type')=='agentMessage':answer=item.get('text','')
            if method=='turn/completed' and p['turn']['id']==turn:
                ended=p['turn']
                if ended['status']!='completed':
                    reason=(ended.get('error') or {}).get('message','Please retry or use the standard Ledger engine.')
                    raise ValueError('Codex could not finish: '+text(reason,320))
                return answer


def run_turn(binary, token, model, instructions, context, tools, schema, dispatch):
    verify_binary(binary,binary.stat().st_mtime_ns)
    with tempfile.TemporaryDirectory(prefix='ledger-engine-') as tmp:
        session=Session(tmp,binary,token)
        try:return session.run(model,instructions,context,tools,schema,dispatch)
        finally:session.close()


def connection_test(assistant):
    binary=executable()
    if not binary:raise ValueError('The local Codex runtime is unavailable.')
    token,model=assistant.chatgpt.credentials()
    spec={'type':'object','additionalProperties':False,'properties':{'reply':{'type':'string','enum':['Connected']}},'required':['reply']}
    def no_tools(_):raise ValueError('The connection test has no lookup tools.')
    result=run_turn(binary,token,model,'Return Connected in the required format.',{'question':'Connection test'},[],spec,no_tools)
    if json.loads(result)!={'reply':'Connected'}:raise ValueError('Codex returned an unexpected test response.')
    return {'ok':True,'model':model,'message':'Connected to the local Codex engine using your ChatGPT plan. No neighborhood records were sent.'}


def ask(assistant,store,body,community):
    binary=executable()
    if not binary:raise ValueError('Install the OpenAI Codex desktop app or choose Standard in AI settings.')
    q=text(body.get('question'),1501)
    if not q or len(q)>1500:raise ValueError('Enter a question of up to 1,500 characters.')
    token,model=assistant.chatgpt.credentials()
    history=voice_context(body)
    supplied=voice_query(q,history)
    include=body.get('includeWork') is True
    package=evidence(store,supplied,include)
    refs=lookup.authorized_cases(store,include)
    context={'community':community,'question':q,'asOf':lookup.stamp(),**history,'evidence':package['sources'],'allowedCaseNumbers':refs}
    results=[];seen={}
    allow=body.get('allowLookups') is True
    definitions={f['name']:f for f in lookup.FUNCTIONS} if allow else {}
    tools=[{'type':'namespace','name':'ledger','description':'Read-only neighborhood lookups.',
        'tools':[{'type':'function','name':name,'description':f['description'],'inputSchema':f['parameters'],'deferLoading':False}
                 for name,f in definitions.items()]}] if allow else []
    ids=[s['id'] for s in package['sources']]
    schema=lookup.lookup_schema(ids+['L'+str(i) for i in (1,2,3)]+['L%dN%d'%(i,j) for i in (1,2,3) for j in range(1,13)])
    def dispatch(p):
        name=p.get('tool');args=p.get('arguments')
        if p.get('namespace')!='ledger' or name not in definitions:raise ValueError('Codex requested an unavailable tool.')
        key=json.dumps([name,args],sort_keys=True)
        if key in seen:return seen[key]
        if len(results)>=3:raise ValueError('Ask about up to three lookups at a time.')
        result=lookup.execute(name,args,supplied,refs,getattr(store,'community_id',None))
        lookup.record_result(package,results,result);seen[key]=result
        return result
    instructions=SYSTEM.replace('You have no browsing or action tools.','Use only the supplied Ledger tools.')+'\n'+lookup.PLAN+"""
Only cite sourceId or id values from actual supplied results. Cite live news articles by their own sourceId.
If today's checks fail, explain why. For a requested follow-up, populate follow_ups with a draft and its source_ids.
If a follow-up refers to a prior case, check that case again when live lookup is allowed. Never send or save drafts.
When asked a general conversational question, reply naturally in next_steps; use findings for sourced neighborhood facts."""
    if history:instructions+=VOICE_STYLE
    warning=''
    try:
        raw=run_turn(binary,token,model,instructions,context,tools,schema,dispatch)
        lookup.filter_fresh_sources(package,results)
        answer,drafts=lookup.parse_answer(raw,[s['id'] for s in package['sources']])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as e:
        if not results:raise ValueError(str(e) if isinstance(e,ValueError) else 'The local Codex engine could not complete this question.') from None
        lookup.filter_fresh_sources(package,results)
        warning='The lookup finished, but Codex could not prepare a verified summary.'
        answer={'findings':[],'next_steps':[],'missing_information':[warning]};drafts=[]
    return {**answer,**package,'lookups':results,'followUps':lookup.prepare_drafts(package,drafts),'warning':warning,
            'model':'Codex · '+model,'question':q,'generatedAt':lookup.stamp(),'usage':{}}


