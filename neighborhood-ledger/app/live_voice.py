"""Local signaling for OpenAI GPT-Live. Media travels on the WebRTC connection."""
import base64
import json
import re
import threading
import urllib.error
import urllib.parse
import urllib.request

from ledger_ai import NoRedirect, protect

ENDPOINT = 'https://api.openai.com/v1/live/sessions'


def save_key(assistant, body):
    key = body.get('key')
    if body.get('remove') is not True and (not isinstance(key, str) or not re.fullmatch(r'sk-[^\s]{16,508}', key.strip())):
        raise ValueError('Enter an OpenAI project API key with GPT-Live access.')
    with assistant.lock:
        config = assistant.config()
        if body.get('remove') is True:
            config.pop('voiceKey', None)
        else:
            config['voiceKey'] = base64.b64encode(protect(key.strip().encode())).decode()
        assistant.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = assistant.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(config), encoding='utf-8')
        tmp.replace(assistant.path)
    return {'configured':bool(config.get('voiceKey'))}


def request(key, url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        'Authorization':'Bearer '+key, 'Content-Type':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
            data = response.read(256001)
            if len(data)>256000:raise ValueError('Unexpectedly large voice service response.')
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as error:
        if url.endswith('/hangup') and error.code in (404,410):return {}
        messages = {401:'OpenAI rejected the voice key. Replace it in Voice settings.',
                    403:'This project needs access to GPT-Live. Check its permissions and model access.',
                    404:'GPT-Live is unavailable for this API project.',
                    429:'OpenAI reported a rate or billing limit. Check the voice project’s billing and limits.'}
        raise ValueError(messages.get(error.code,'OpenAI could not connect live voice (HTTP '+str(error.code)+').')) from None
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError('Could not reach the OpenAI voice service. Check the network and try again.') from None


class LiveCalls:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = None

    def finish(self, session_id):
        with self.lock:
            if self.active and self.active[0] == session_id:
                self._hangup()
        return {'ok':True}

    def _hangup(self):
        session_id, key = self.active
        request(key, ENDPOINT+'/'+urllib.parse.quote(session_id,safe='')+'/hangup', {})
        self.active = None

    def shutdown(self):
        with self.lock:
            if self.active:
                try:self._hangup()
                except ValueError:pass

    def start(self, assistant, body, community):
        sdp = body.get('sdp')
        if not isinstance(sdp,str) or len(sdp)>65536 or not sdp.startswith('v=0') or 'm=audio ' not in sdp:
            raise ValueError('The microphone connection could not be negotiated. Reopen Chat.')
        cfg=assistant.config()
        if cfg.get('authMode')!='chatgpt' or cfg.get('engine')!='codex' or not assistant.chatgpt.status()['ready']:
            raise ValueError('Select your ChatGPT plan and Codex with Ledger tools in AI settings.')
        if not cfg.get('voiceKey'):raise ValueError('Add your OpenAI project key in Voice settings.')
        key=protect(base64.b64decode(cfg['voiceKey']),True).decode()
        prompt=('You are the live voice of Neighborhood Ledger for '+community+
            '. Talk naturally and briefly. For news, cases, property, local facts, saved records and drafts, always delegate to Ledger and wait for verified results. '
            'Ask the person to repeat ambiguous case numbers or addresses. Describe source limits. Never claim to have sent, filed or saved anything. '
            'The person can interrupt you. The End chat button closes the conversation.')
        config={'model':'gpt-live-1','instructions':prompt,'delegation':{'type':'client'},
                'client':{'data_channel':{'allowed_client_events':['session.commentary.append','session.close']}}}
        with self.lock:
            if self.active:self._hangup()
            result=request(key,ENDPOINT,{'session':config,'transport':{'type':'webrtc','sdp':sdp}})
            session_id=result.get('session',{}).get('id')
            if not isinstance(session_id,str) or not session_id:raise ValueError('OpenAI returned no voice session ID.')
            self.active=(session_id,key)
            answer=result.get('transport',{}).get('sdp')
            if not isinstance(answer,str) or not answer.startswith('v=0'):
                self._hangup()
                raise ValueError('OpenAI returned no usable audio connection.')
            return {'id':session_id,'sdp':answer}
