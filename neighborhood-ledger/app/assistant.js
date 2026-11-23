// On-demand AI only. No automatic model calls or cross-neighborhood conversation memory.
viewNames.assistant='Neighborhood assistant';
const aiNav=document.createElement('button');aiNav.dataset.view='assistant';aiNav.innerHTML=uiIcon('documents')+'<span>Neighborhood assistant</span>';
$('.nav [data-view="dashboard"]').after(aiNav);aiNav.onclick=()=>showView('assistant');
const aiView=document.createElement('section');aiView.id='assistant';aiView.className='view';
aiView.innerHTML=`<div class="ai-layout"><header class="ai-heading"><div><h2>Neighborhood assistant</h2><p id="aiConnection" class="ai-note">Checking connection settings…</p></div><button class="btn" id="aiSetupToggle" aria-controls="aiSetup" aria-expanded="false">AI settings</button></header>
<div class="ai-conversation" id="aiConversation" role="region" aria-label="Assistant response" tabindex="0">
<section class="ai-setup" id="aiSetup" hidden><h3>Connect your assistant</h3><p>Use your ChatGPT plan for eligible requests. Sign in securely in your browser; there is no token to copy.</p>
<div class="ai-chatgpt"><div class="actions"><button type="button" class="btn ai-signin" id="aiChatSignIn" data-oai-siwc-button>Continue with ChatGPT</button><button class="btn ghost" id="aiChatCancel" hidden>Cancel sign-in</button><a id="aiChatReopen" target="_blank" rel="noopener noreferrer" hidden>Open sign-in again ↗</a></div><p id="aiChatStatus" class="ai-status" role="status"></p><div id="aiChatAccount" hidden><p id="aiAccountName"></p><div class="field"><label for="aiChatModel">ChatGPT model</label><select id="aiChatModel"></select></div><div class="actions"><button class="btn" id="aiChatUse">Use ChatGPT plan</button><button class="btn" id="aiChatModels">Refresh models</button><button class="btn ghost" id="aiChatOther">Use another account</button><button class="btn ghost" id="aiChatSignOut">Sign out</button></div><p><a href="https://chatgpt.com/settings/usage" target="_blank" rel="noopener">Manage usage ↗</a></p></div></div>
<details id="aiApiAlternative"><summary>Use an OpenAI API key instead</summary><p>API billing is separate. <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">Create an API key ↗</a> and check your project credits and usage limits.</p><form id="aiSetupForm"><div class="field"><label for="aiKey">OpenAI API key</label><input id="aiKey" type="password" autocomplete="off" spellcheck="false" placeholder="Paste your key here — never in chat" maxlength="512"><small>Encrypted for your Windows account. Never included in workspace exports.</small></div><details><summary>Model settings</summary><div class="field"><label for="aiModel">OpenAI model</label><input id="aiModel" value="gpt-4.1-mini" maxlength="100"><small>The model must support Responses and structured outputs.</small></div></details><div class="actions"><button type="submit" class="btn" id="aiSaveConnection">Save and use API connection</button><button type="button" class="btn ghost" id="aiDisconnect">Remove saved key</button></div></form></details><div class="field" id="aiEngineField" hidden><label for="aiEngine">Assistant engine</label><select id="aiEngine"><option value="standard">Standard Ledger</option><option value="codex">Codex with Ledger tools</option></select></div><div class="actions ai-test-row"><button type="button" class="btn primary" id="aiTest">Test connection</button></div><p id="aiSetupStatus" class="ai-status" role="status"></p></section>

<div class="ai-empty" id="aiEmpty"><h3>What would you like to work on?</h3><p>Ask about ${esc(community.name)}.</p><div class="ai-prompts">${[['Current news','Find current news for this neighborhood.'],['Check a 311 case','Check 311 case [case number] and draft a follow-up.'],['Saved updates','Summarize the saved neighborhood updates.'],['Follow up concerns','What needs follow-up in the saved concerns?'],['Meeting briefing','Draft a neighborhood meeting briefing.']].map(([label,q])=>`<button type="button" data-ai-prompt="${esc(q)}">${esc(label)}</button>`).join('')}</div></div>
<div id="aiWorking" class="ai-working" hidden><p class="ai-question" id="aiSentQuestion"></p><p>Checking your question…</p></div>
<article class="ai-answer" id="aiAnswer" hidden aria-live="polite"></article></div>
<form id="aiAskForm" class="ai-composer"><label for="aiQuestion" class="screen-reader">Message your neighborhood assistant</label><div class="ai-input-row"><textarea id="aiQuestion" rows="2" maxlength="1500" required placeholder="Ask about your neighborhood…"></textarea><button class="btn" id="aiVoice" type="button" aria-pressed="false">Chat</button><button class="btn primary" id="aiAsk" type="submit">Send ↑</button></div>
<div class="ai-composer-tools"><details id="aiOptions" class="ai-options"><summary>Sources & options</summary><div class="ai-options-panel"><p class="ai-plan" id="aiPlan" hidden>Using ChatGPT plan · <a href="https://chatgpt.com/settings/usage" target="_blank" rel="noopener">Manage usage ↗</a></p><div class="field"><label for="aiScope">Records to use</label><select id="aiScope"><option value="public">Public updates only</option><option value="work">Public updates + saved concerns and follow-ups</option></select></div><label class="ai-lookup-option"><input type="checkbox" id="aiAllowLookups" checked> Search live news, 311 and property sources when needed</label><p class="ai-note" id="aiSharing">Your question and up to 18 selected public records are sent to OpenAI when you ask. Current-news requests search live sources for this neighborhood.</p><p class="ai-note">Public searches go to news publishers or City/County sources; results go to OpenAI. Codex can use the last four turns in this session for follow-ups. Review answers and drafts before acting.</p><button type="button" class="btn" id="aiPreview">Preview records</button><div id="aiPreviewArea"></div></div></details><span id="aiScopeSummary" class="ai-scope-summary">Public records · Live lookups on</span><span class="ai-key-hint">Enter to send · Shift+Enter for a new line</span></div><p id="aiAskStatus" class="ai-status" role="status"></p></form></div>`;
$('.content').append(aiView);
const aiToday=document.createElement('div');aiToday.className='ai-intro';aiToday.innerHTML='<div><strong>A little help with your neighborhood work</strong><p>Ask the assistant to summarize records or suggest next steps.</p></div><button class="btn" id="aiTodayOpen">Ask your assistant →</button>';
$('#dashboard .community-picker').after(aiToday);$('#aiTodayOpen').onclick=()=>showView('assistant');
const aiSettingsLink=document.createElement('div');aiSettingsLink.className='card ai-settings-link pad';aiSettingsLink.innerHTML='<h3>Neighborhood assistant</h3><p>Connect your ChatGPT plan or an OpenAI API account for questions about your saved records.</p><button class="btn" id="aiSettingsOpen">Open AI settings</button>';
$('#data .pagehead').after(aiSettingsLink);$('#aiSettingsOpen').onclick=()=>{showView('assistant');setAISetup(true)};
let aiSettings=null,aiAnswer=null,aiPending=false,aiPreviewSequence=0;
function aiMessage(id,value,error=false){const el=$('#'+id);el.textContent=value;el.dataset.error=String(error)}
let aiSignInTimer=null,aiWelcomeShown=false;
const aiWelcome=document.createElement('dialog');aiWelcome.className='ai-welcome';aiWelcome.innerHTML='<h2>You’re using your ChatGPT plan</h2><p>Eligible AI requests in Ledger use your ChatGPT plan. You can review usage and adjust limits in ChatGPT settings.</p><div class="actions"><a href="https://chatgpt.com/settings/usage" target="_blank" rel="noopener">Manage usage ↗</a><button class="btn primary" id="aiWelcomeDone">Got it</button></div>';document.body.append(aiWelcome);
$('#aiWelcomeDone').onclick=async()=>{try{await officeApi('/api/ai/chatgpt/welcome',{});aiWelcome.close()}catch(e){aiMessage('aiSetupStatus',e.message,true)}};
aiWelcome.addEventListener('cancel',e=>{e.preventDefault();$('#aiWelcomeDone').click()});
async function aiLoad(keepOpen=false){try{aiSettings=await officeApi('/api/ai/settings');const c=aiSettings.chatgpt||{},active=aiSettings.authMode==='chatgpt';$('#voiceRemove').hidden=!aiSettings.liveVoiceConfigured;$('#aiEngineField').hidden=!active;$('#aiEngine').value=aiSettings.engine||'standard';$('#aiModel').value=aiSettings.apiModel||aiSettings.model;$('#aiConnection').textContent=aiSettings.configured?(active?(aiSettings.engine==='codex'?'Codex · ChatGPT plan · ':'ChatGPT plan · '):'OpenAI API · ')+aiSettings.model:'Connect your assistant to get started';$('#aiAsk').disabled=aiPending||!aiSettings.configured;$('#aiTest').disabled=!aiSettings.configured;$('#aiDisconnect').disabled=!aiSettings.apiKeyConfigured;$('#aiChatAccount').hidden=!c.connected;$('#aiAccountName').textContent=c.account?'Signed in as '+c.account:'';$('#aiChatModel').innerHTML=(c.models||[]).map(m=>'<option value="'+esc(m.slug)+'">'+esc(m.name)+'</option>').join('');$('#aiChatModel').value=c.model||'';$('#aiChatUse').hidden=active;$('#aiChatUse').disabled=!c.ready;$('#aiChatSignIn').hidden=false;$('#aiChatSignIn').disabled=c.phase==='waiting';$('#aiChatCancel').hidden=c.phase!=='waiting';$('#aiChatReopen').hidden=c.phase!=='waiting';$('#aiPlan').hidden=!active||!c.connected;aiMessage('aiChatStatus',c.message||'',c.phase==='error');if(c.phase!=='waiting'){clearTimeout(aiSignInTimer);aiSignInTimer=null;$('#aiChatReopen').removeAttribute('href')}else{clearTimeout(aiSignInTimer);aiSignInTimer=setTimeout(()=>aiLoad(true),2000)}if(c.welcomeNeeded&&!aiWelcomeShown&&!$('#aiSetup').hidden){aiWelcomeShown=true;aiWelcome.showModal()}}catch(e){aiMessage('aiSetupStatus',e.message,true);$('#aiConnection').textContent='Connection unavailable. Open AI settings.'}}
async function aiChatAction(action,body={}){aiMessage('aiSetupStatus','');try{const result=await officeApi('/api/ai/chatgpt/'+action,body);if(result.authorizationUrl){$('#aiChatReopen').href=result.authorizationUrl;$('#aiChatReopen').hidden=false}await aiLoad(true);return result}catch(e){aiMessage('aiChatStatus',e.message,true)}}
async function aiBeginSignIn(newAccount=false){$('#aiChatSignIn').disabled=true;$('#aiChatOther').disabled=true;aiMessage('aiChatStatus','Opening secure ChatGPT sign-in…');try{await aiChatAction('start',{newAccount})}finally{$('#aiChatSignIn').disabled=aiSettings?.chatgpt?.phase==='waiting';$('#aiChatOther').disabled=false}}
$('#aiChatSignIn').onclick=()=>aiBeginSignIn();$('#aiChatOther').onclick=()=>aiBeginSignIn(true);$('#aiChatCancel').onclick=()=>aiChatAction('cancel');$('#aiChatSignOut').onclick=()=>aiChatAction('signout');$('#aiChatModels').onclick=()=>aiChatAction('models');$('#aiChatModel').onchange=()=>aiChatAction('model',{model:$('#aiChatModel').value});$('#aiChatUse').onclick=async()=>{try{await officeApi('/api/ai/mode',{mode:'chatgpt'});await aiLoad(true)}catch(e){aiMessage('aiChatStatus',e.message,true)}};

function setAISetup(open){
    $('#aiSetup').hidden=!open;
    $('#aiSetupToggle').setAttribute('aria-expanded',String(open));
    if(open){$('#aiConversation').scrollTop=0;aiLoad(true)}
}
const aiPriorShow=showView;
showView=function(id){
    setAISetup(false);
    if(id!=='assistant' && id!=='dashboard')endVoice();
    aiPriorShow(id);document.body.classList.toggle('ai-screen',id==='assistant');
    if(id==='assistant'){window.scrollTo({top:0,behavior:'instant'});aiResize();aiLoad()}
};
$('#aiSetupToggle').onclick=()=>setAISetup($('#aiSetup').hidden);
$('#aiSetupForm').onsubmit=async e=>{e.preventDefault();const button=$('#aiSaveConnection');button.disabled=true;try{await officeApi('/api/ai/settings',{model:$('#aiModel').value,apiKey:$('#aiKey').value});$('#aiKey').value='';await aiLoad();aiMessage('aiSetupStatus','Connection saved. Choose Test connection to check your key and model.')}catch(error){aiMessage('aiSetupStatus',error.message,true)}finally{button.disabled=false}};
let codexTurns=[];
let codexTurnScope='';
$('#aiEngine').onchange=async()=>{
    const select=$('#aiEngine');select.disabled=true;
    try{await officeApi('/api/ai/engine',{engine:select.value});codexTurns=[];await aiLoad(true);aiMessage('aiSetupStatus','Assistant engine saved.')}
    catch(e){select.value=aiSettings.engine||'standard';aiMessage('aiSetupStatus',e.message,true)}
    finally{select.disabled=false}
};
$('#aiTest').onclick=async()=>{const b=$('#aiTest');b.disabled=true;aiMessage('aiSetupStatus','Testing OpenAI with a short message. No neighborhood records are sent.');try{const d=await officeApi('/api/ai/test',{});aiMessage('aiSetupStatus',d.message)}catch(e){aiMessage('aiSetupStatus',e.message,true)}finally{b.disabled=false}};
$('#aiDisconnect').onclick=async()=>{try{await officeApi('/api/ai/settings',{clearKey:true,model:$('#aiModel').value});$('#aiKey').value='';await aiLoad();aiMessage('aiSetupStatus','Saved key removed. Your neighborhood records are unchanged.')}catch(e){aiMessage('aiSetupStatus',e.message,true)}};
$$('[data-ai-prompt]').forEach(b=>b.onclick=()=>{$('#aiQuestion').value=b.dataset.aiPrompt;if(b.dataset.aiPrompt.includes('concerns')){$('#aiScope').value='work';$('#aiScope').dispatchEvent(new Event('change'))}aiResizeInput();$('#aiQuestion').focus()});
$('#aiScope').onchange=()=>{aiUpdateScope();aiPreviewSequence++;$('#aiPreviewArea').innerHTML='';$('#aiSharing').textContent=$('#aiScope').value==='work'?'Your question and selected records, including concern locations and free-text notes, will be sent to OpenAI. Dedicated contact fields are excluded; notes may still contain personal information. Preview records before asking.':'Your question and up to 18 selected public records are sent to OpenAI when you ask. Ask for current news to search live sources for the selected neighborhood. Saved articles are used for questions about saved records.'};
$('#aiQuestion').oninput=()=>{aiResizeInput();aiPreviewSequence++;$('#aiPreviewArea').innerHTML=''};
function aiDate(value){const date=new Date(/^\d{4}-\d{2}-\d{2}$/.test(value)?value+'T12:00:00':value);return Number.isNaN(date.getTime())?value:(value.length===10?date.toLocaleDateString():date.toLocaleString())}
function aiEvidenceHTML(d,prefix){return `<details class="ai-evidence" ${prefix==='preview'?'open':''}><summary>${d.sources.length} record${d.sources.length===1?'':'s'} ${prefix==='answer'?'used for this answer':'selected'}${d.subset?' from '+d.availableCount+' available':''}</summary>${d.sources.map(s=>`<div class="ai-source" id="${prefix}-${esc(s.id)}"><b>${esc(s.id)} · ${esc(s.title)}</b><p>${esc(s.kind)}${s.date?' · Record date: '+esc(aiDate(s.date)):''}${s.lastCheckedAt?' · Last retrieved: '+esc(aiDate(s.lastCheckedAt)):''}</p><p>${esc(s.text)}</p>${s.relatedCoverage?.length?`<details><summary>Related coverage (${s.relatedCoverage.length})</summary>${s.relatedCoverage.map(r=>`<p><a href="${esc(safeUrl(r.url))}" target="_blank" rel="noopener">${esc(r.title)} ↗</a></p>`).join('')}</details>`:''}${s.url?`<a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">Open source ↗</a>`:`<button class="btn small" data-ai-view="${esc(s.view)}">Open saved records →</button>`}</div>`).join('')||'<p>No records are available for this scope.</p>'}<p class="ai-note">Saved records retain their original dates. Live lookups show their check time and outcome. Neither is a complete neighborhood inventory.</p></details>`}
function aiWireEvidence(root){$$('[data-ai-view]',root).forEach(b=>b.onclick=()=>showView(b.dataset.aiView))}
$('#aiPreview').onclick=async()=>{const seq=++aiPreviewSequence;try{await saveState('');await saveChain;if(saveFailed)throw Error('Save your pending changes before previewing records.');const d=await officeApi('/api/ai/preview',{question:$('#aiQuestion').value,includeWork:$('#aiScope').value==='work'});if(seq!==aiPreviewSequence||communitySwitching)return;$('#aiPreviewArea').innerHTML=aiEvidenceHTML(d,'preview');aiWireEvidence($('#aiPreviewArea'))}catch(e){aiMessage('aiAskStatus',e.message,true)}};
$('#aiAskForm').onsubmit=async e=>{e.preventDefault();if(aiPending||!aiSettings?.configured)return;const question=$('#aiQuestion').value.trim();if(!question)return;const includeWork=$('#aiScope').value==='work',allowLookups=$('#aiAllowLookups').checked;aiPending=true;$('#aiAsk').disabled=true;$('#aiOptions').open=false;$('#aiEmpty').hidden=true;$('#aiAnswer').hidden=true;$('#aiWorking').hidden=false;$('#aiSentQuestion').textContent=question;$('#aiQuestion').value='';aiResizeInput();$('#aiConversation').scrollTop=0;aiMessage('aiAskStatus',allowLookups?'Checking sources and preparing your answer…':'Reading selected records…');try{await saveState('');await saveChain;if(saveFailed)throw Error('Save your pending changes before asking the assistant.');const useCodex=aiSettings.engine==='codex';
        const scope=JSON.stringify([community.id,includeWork,allowLookups,aiSettings.model,aiSettings.chatgpt?.account]);
        if(scope!==codexTurnScope){codexTurns=[];codexTurnScope=scope}
        const d=await officeApi('/api/ai/ask',{question,includeWork,allowLookups,...(useCodex?{voiceTurns:codexTurns.slice(-4)}:{})});
        if(communitySwitching)return;
        if(useCodex){codexTurns.push({question,answer:spokenAnswer(d)});codexTurns=codexTurns.slice(-4)}
        aiAnswer=d;$('#aiPreviewArea').innerHTML='';aiRenderAnswer(d);aiMessage('aiAskStatus',d.warning||'Answer ready above.',!!d.warning)}catch(error){if(!$('#aiQuestion').value){$('#aiQuestion').value=question;aiResizeInput()}$('#aiWorking').hidden=true;if(aiAnswer)aiRenderAnswer(aiAnswer);else $('#aiEmpty').hidden=false;aiMessage('aiAskStatus',error.message,true)}finally{aiPending=false;$('#aiWorking').hidden=true;$('#aiAsk').disabled=!aiSettings?.configured}};
function aiRenderAnswer(d){const el=$('#aiAnswer');el.hidden=false;$('#aiEmpty').hidden=true;$('#aiWorking').hidden=true;el.innerHTML=`<div class="ai-question"><small>You</small><p>${esc(d.question)}</p></div><div class="ai-toolbar"><span class="ai-draft-tag">AI draft</span><small>${esc(d.model)} · ${esc(new Date(d.generatedAt).toLocaleString())}</small></div>${d.findings.map(f=>`<p>${esc(f.text)} ${f.source_ids.map(id=>`<button class="ai-citation" data-ai-cite="${esc(id)}" aria-label="Show source ${esc(id)}">${esc(id)}</button>`).join('')}</p>`).join('')||'<p>The available records do not support a factual answer to this question.</p>'}${d.next_steps.length?'<h3>Suggested next steps</h3><ol>'+d.next_steps.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>':''}${d.missing_information.length?'<h3>What still needs checking</h3><ul>'+d.missing_information.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ul>':''}${aiDraftHTML(d)}${aiLookupHTML(d)}<div class="actions"><button class="btn" id="aiDownload">Download answer</button>${d.next_steps.length&&!d.followUps?.length?'<button class="btn" id="aiFollowup">Create follow-up draft</button>':''}</div>${aiEvidenceHTML(d,'answer')}`;aiWireEvidence(el);$$('[data-ai-draft]',el).forEach(b=>b.onclick=()=>aiReviewDraft(d,Number(b.dataset.aiDraft)));$$('[data-ai-cite]',el).forEach(b=>b.onclick=()=>{const source=$('#answer-'+b.dataset.aiCite);source.closest('details').open=true;aiScrollTo(source)});$('#aiDownload').onclick=()=>download('Neighborhood-assistant-answer.txt',aiAnswerText(d));if($('#aiFollowup'))$('#aiFollowup').onclick=()=>{showView('office');editOffice();$('#ofTitle').value=d.question.slice(0,250);$('#ofNext').value=d.next_steps[0];$('#ofNotes').value='AI draft — check evidence before acting.\n\n'+aiAnswerText(d)};$('#aiConversation').scrollTo({top:0,behavior:'instant'})}
function aiAnswerText(d){return ['AI DRAFT · '+community.name,d.question,'Model: '+d.model,'Generated: '+d.generatedAt,'',...d.findings.map(f=>f.text+' ['+f.source_ids.join(', ')+']'),'','Suggested next steps:',...d.next_steps,'','Needs checking:',...d.missing_information,'','Lookup results:',...(d.lookups||[]).map(r=>r.tool+' · '+r.status+' · '+r.checkedAt+'\n'+r.message+'\n'+r.url),'','Follow-up drafts:',...(d.followUps||[]).map(r=>r.title+'\n'+r.next+'\n'+r.notes),'','Supporting records:',...d.sources.map(s=>s.id+' · '+s.title+' · '+(s.date||'Date not recorded')+'\n'+s.text+'\n'+s.url+(s.relatedCoverage||[]).map(r=>'\nRelated: '+r.title+'\n'+r.url).join(''))].join('\n')}

function aiLookupHTML(d){return (d.lookups||[]).length?`<details class="ai-lookups" ${d.warning||!d.findings?.length?'open':''}><summary>Live source checks (${d.lookups.length})</summary>`+d.lookups.map(r=>{const labels={found:'Record found',not_found:'No exact match',ambiguous:'Needs clarification',partial:'Partial results',unavailable:'Source unavailable',needs_information:'More information needed'};return `<div class="ai-lookup-result"><b>${esc(r.tool==='search_current_news'?'Current news · '+r.communityName:r.caseNumber?'311 case '+r.caseNumber:r.tool==='lookup_deed_address'?'Address / deed index':'Subdivision / deed index')}</b><span class="ai-draft-tag">${esc(labels[r.status]||r.status)}</span><p>${esc(r.message||'')}</p>${r.articles?aiNewsResults(r):''}${r.record?`<p>${esc(r.record.serviceType)} · ${esc(r.record.address)}<br>City status: <b>${esc(r.record.cityStatus)}</b></p>`:''}<small>Checked ${esc(aiDate(r.checkedAt))}</small>${r.url?` · <a href="${esc(safeUrl(r.url))}" target="_blank" rel="noopener">Official source ↗</a>`:''}</div>`}).join('')+'</details>':''}
function aiDraftHTML(d){return (d.followUps||[]).map((r,index)=>`<section class="ai-followup-draft"><div class="eyebrow">FOLLOW-UP DRAFT · NOT SAVED OR SENT</div><h3>${esc(r.title)}</h3>${r.caseNo?`<p>311 reference: ${esc(r.caseNo)}</p>`:''}<p><b>Suggested next action</b><br>${esc(r.next)}</p><p>${esc(r.notes)}</p><button class="btn primary" data-ai-draft="${index}">Review follow-up draft</button></section>`).join('')}
function aiReviewDraft(answer,index){const draft=answer.followUps[index];if(!draft)return;showView('office');editOffice();$('#ofStatus').value='Draft';$('#ofTitle').value=draft.title;$('#ofNext').value=draft.next;$('#ofAgency').value=draft.agency||'';$('#ofCase').value=draft.caseNo||'';$('#ofSource').value=draft.sourceUrl||'';$('#ofNotes').value='AI DRAFT — review before saving or sending.\n'+draft.notes+'\n\n'+aiAnswerText(answer);$('#ofUpdate').value='Reviewed AI follow-up draft';}

function aiNewsResults(r){return `<div class="ai-news-results">${r.articles.map(a=>`<p><a href="${esc(safeUrl(a.url))}" target="_blank" rel="noopener"><b>${esc(a.title)}</b> ↗</a><br><small>Published ${esc(a.publishedAt.slice(0,10))} · ${esc(a.source)} · ${esc(a.scope)}</small></p>`).join('')||'<p>No current stories could be verified.</p>'}</div><details><summary>Sources checked (${r.checks.length})</summary>${r.checks.map(c=>`<p><a href="${esc(safeUrl(c.url))}" target="_blank" rel="noopener">${esc(c.name)}</a> · ${esc(c.status)} · ${c.count} items${c.warnings.length?'<br>'+esc(c.warnings.join(' ')):''}</p>`).join('')}</details>`}

function aiResize(){const content=$('.content'),top=$('.topbar').getBoundingClientRect().height+parseFloat(getComputedStyle(content).paddingTop);aiView.style.setProperty('--ai-top',top+'px')}
function aiResizeInput(){const box=$('#aiQuestion');box.style.height='auto';box.style.height=Math.min(112,Math.max(64,box.scrollHeight))+'px'}
function aiScrollTo(el){const pane=$('#aiConversation');pane.scrollTo({top:pane.scrollTop+el.getBoundingClientRect().top-pane.getBoundingClientRect().top-16,behavior:'smooth'})}
function aiUpdateScope(){$('#aiScopeSummary').textContent=($('#aiScope').value==='work'?'Includes saved concerns':'Public records')+' · Live lookups '+($('#aiAllowLookups').checked?'on':'off')}
$('#aiAllowLookups').onchange=aiUpdateScope;
$('#aiQuestion').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();if(!$('#aiAsk').disabled)$('#aiAskForm').requestSubmit()}});
document.addEventListener('click',e=>{if(!$('#aiOptions').contains(e.target))$('#aiOptions').open=false});
$('#aiOptions').addEventListener('keydown',e=>{if(e.key==='Escape'){$('#aiOptions').open=false;$('#aiOptions>summary').focus()}});
window.addEventListener('resize',aiResize);new ResizeObserver(aiResize).observe($('.topbar'));

function spokenAnswer(answer){
    const facts=answer.findings.map(f=>f.text);
    const sections=[answer.warning,...facts.slice(0,2)];
    if(!facts.length && answer.lookups?.length)sections.push(answer.lookups[0].message);
    sections.push(answer.missing_information[0],answer.next_steps[0]);
    if(answer.followUps?.length)sections.push('Your follow-up draft is ready to review in Ledger.');
    return sections.filter(Boolean).join(' ').slice(0,3900) || 'I need more detail. What would you like me to check?';
}

const voiceSetup=document.createElement('details');
voiceSetup.id='voiceSetup';
voiceSetup.innerHTML=`<summary>Voice settings</summary>
<p>Live voice uses your OpenAI API project. Ledger lookups use your connected ChatGPT plan.</p>
<a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">Get a project API key ↗</a>
<form id="voiceKeyForm"><label for="voiceKey">OpenAI project key</label><input id="voiceKey" type="password" required maxlength="512" autocomplete="off"><div class="actions"><button class="btn" type="submit">Save voice key</button><button type="button" class="btn ghost" id="voiceRemove" hidden>Remove key</button></div></form>
<label for="voiceMic">Microphone</label><select id="voiceMic"><option value="">Windows default</option></select>
<div class="voice-level" id="voiceDevices" hidden><label for="voiceMeter">Input level</label><meter id="voiceMeter" min="0" max="100" value="0"></meter></div>
<p id="voiceState" role="status"></p>`;
$('#aiSetupStatus').before(voiceSetup);
const liveOutput=document.createElement('audio');
liveOutput.id='liveOutput';liveOutput.autoplay=true;liveOutput.hidden=true;document.body.append(liveOutput);
const todayVoice=document.createElement('button');
todayVoice.className='btn';todayVoice.textContent='Chat';
const todayAsk=$('#aiTodayOpen'), todayActions=document.createElement('div');
todayActions.className='actions';todayAsk.replaceWith(todayActions);todayActions.append(todayVoice,todayAsk);
let currentVoice=null;
const voiceButtons=[todayVoice,$('#aiVoice')];
const voiceNotices=voiceButtons.map(button=>{
    const notice=document.createElement('div');
    notice.className='voice-notice';notice.hidden=true;
    notice.innerHTML='<span role="status"></span> <button type="button" class="btn small">AI settings</button> <button type="button" class="btn small">Play audio</button>';
    const [settings,play]=notice.querySelectorAll('button');
    settings.onclick=()=>{showView('assistant');setAISetup(true);voiceSetup.open=true;voiceSetup.scrollIntoView({block:'nearest'})};
    play.onclick=()=>liveOutput.play().then(()=>voiceNotice('')).catch(()=>voiceNotice('Audio playback is blocked.','play'));
    button.parentElement.after(notice);
    return notice;
});
function voiceNotice(message,action=''){
    for(const notice of voiceNotices){
        notice.hidden=!message;notice.firstElementChild.textContent=message;
        const [settings,play]=notice.querySelectorAll('button');
        settings.hidden=action!=='settings';play.hidden=action!=='play';
    }
}
function syncVoiceButtons(){
    for(const button of voiceButtons){
        button.textContent=currentVoice?'End chat':'Chat';
        button.setAttribute('aria-pressed',String(Boolean(currentVoice)));
    }
}
const voiceText=message=>{$('#voiceState').textContent=message};
async function listMicrophones(){
    const devices=await navigator.mediaDevices?.enumerateDevices()||[];
    const mic=$('#voiceMic'),preferred=localStorage.getItem('ledgerLiveMic')||'';
    mic.replaceChildren(new Option('Windows default',''));
    for(const d of devices.filter(d=>d.kind==='audioinput' && d.deviceId && d.deviceId!=='default'))mic.add(new Option(d.label||'Microphone '+mic.options.length,d.deviceId));
    mic.value=[...mic.options].some(o=>o.value===preferred)?preferred:'';
}
voiceSetup.ontoggle=()=>{
    if(voiceSetup.open){$('#voiceRemove').hidden=!aiSettings?.liveVoiceConfigured;listMicrophones().catch(()=>{})}
};
function releaseVoice(session){
    if(!session || session.closed)return;
    session.closed=true;
    clearTimeout(session.timeout);clearTimeout(session.endTimer);clearInterval(session.meterTimer);
    session.stream?.getTracks().forEach(t=>t.stop());
    session.context?.close().catch(()=>{});
    if(session.events?.readyState==='open'){
        try{session.events.send(JSON.stringify({type:'session.close'}))}catch{}
    }
    session.pc?.close();
    if(session.id)officeApi('/api/ai/voice/end',{id:session.id}).catch(()=>{});
    const audio=$('#liveOutput');audio.pause();audio.srcObject=null;audio.hidden=true;
    $('#voiceDevices').hidden=true;$('#voiceMeter').value=0;
    session.parts=[];session.turns=[];
}
function endVoice(){
    releaseVoice(currentVoice);currentVoice=null;
    syncVoiceButtons();voiceNotice('');voiceText('');
}
function failVoice(session,message){
    if(currentVoice!==session || session.closed)return;
    releaseVoice(session);currentVoice=null;
    syncVoiceButtons();voiceText(message);voiceNotice(message,'settings');
}
function appendLive(session,content,id=null){
    if(currentVoice===session && session.events.readyState==='open'){
        session.events.send(JSON.stringify({type:'session.commentary.append',event_id:crypto.randomUUID(),delegation_id:id,content}));
    }
}
function inputParts(session,event){
    if(typeof event.delta!=='string' || !event.delta)return;
    clearTimeout(session.endTimer);
    if(Number(event.start_ms)-session.lastInputEnd>1600)session.phrase='';
    session.phrase=((session.phrase||'')+event.delta).slice(-1500);
    session.lastInputEnd=Number(event.end_ms)||Number(event.start_ms)||0;
    if(/^(end chat|end conversation|goodbye ledger)[.!?]?$/i.test(session.phrase.trim())){
        session.endTimer=setTimeout(()=>{if(currentVoice===session)endVoice()},900);
    }
    session.parts.push({t:Number(event.start_ms)||0,text:event.delta});
    if(session.parts.length>500)session.parts.shift();
}
async function delegateVoice(session,event){
    const id=event.delegation?.id;
    if(!id || event.delegation.target!=='client' || session.seen.has(id))return;
    session.seen.add(id);
    // Transcript fragments and the delegation arrive on separate event streams.
    await new Promise(resolve=>setTimeout(resolve,350));
    if(currentVoice!==session || session.closed)return;
    const cutoff=Number.isFinite(event.offset_ms)?event.offset_ms:Infinity;
    const parts=session.parts.filter(p=>p.t<=cutoff);
    session.parts=session.parts.filter(p=>p.t>cutoff);
    const question=parts.sort((a,b)=>a.t-b.t).map(p=>p.text).join('').trim().slice(-1500);
    if(!question){appendLive(session,'Ask the caller to repeat the question so Ledger can check it.',id);return}
    session.work=session.work.then(async()=>{
        if(currentVoice!==session || session.closed)return;
        voiceText('Codex is checking Ledger…');
        try{
            const answer=await officeApi('/api/ai/ask',{question,includeWork:session.includeWork,allowLookups:session.allowLookups,voiceTurns:session.turns.slice(-4)});
            if(currentVoice!==session || session.closed || communitySwitching)return;
            aiAnswer=answer;aiRenderAnswer(answer);
            const reply=spokenAnswer(answer);
            session.turns.push({question,answer:reply});session.turns=session.turns.slice(-4);
            appendLive(session,reply,id);
        }catch(error){appendLive(session,'Tell the caller Ledger could not complete this lookup. '+error.message,id)}
        if(currentVoice===session)voiceText('Live voice connected');
    });
}
function voiceEvent(session,data){
    if(currentVoice!==session || session.closed)return;
    let event;try{event=JSON.parse(data)}catch{return}
    switch(event.type){
        case 'session.started':
            clearTimeout(session.timeout);voiceText('Live voice connected');if(!session.playBlocked)voiceNotice('');
            appendLive(session,'Greet the caller briefly and ask how you can help with '+community.name+'.');break;
        case 'session.input_transcript.delta':inputParts(session,event);break;
        case 'session.delegation.created':delegateVoice(session,event).catch(()=>failVoice(session,'The voice lookup was interrupted.'));break;
        case 'session.closed':failVoice(session,'Conversation ended.');break;
        case 'error':failVoice(session,'OpenAI reported a voice error. '+String(event.error?.message||'Try connecting again.').slice(0,240));break;
    }
}
async function setMicrophone(session,id){
    const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,...(id?{deviceId:{exact:id}}:{})}});
    if(currentVoice!==session || session.closed){stream.getTracks().forEach(t=>t.stop());return}
    const track=stream.getAudioTracks()[0],old=session.stream;
    try{
        if(session.sender)await session.sender.replaceTrack(track);
        else session.sender=session.pc.addTrack(track,stream);
        if(currentVoice!==session || session.closed){stream.getTracks().forEach(t=>t.stop());return}
        session.stream=stream;old?.getTracks().forEach(t=>t.stop());
        track.onended=()=>{if(session.stream===stream)failVoice(session,'The microphone disconnected. Select an available microphone and reconnect.')};
        session.source?.disconnect();
        session.source=session.context.createMediaStreamSource(stream);
        session.source.connect(session.analyser);
    }catch(error){stream.getTracks().forEach(t=>t.stop());throw error}
}
async function gatherIce(pc){
    if(pc.iceGatheringState==='complete')return;
    await new Promise((resolve,reject)=>{
        const done=()=>{if(pc.iceGatheringState==='complete'){cleanup();resolve()}};
        const cleanup=()=>{clearTimeout(timer);pc.removeEventListener('icegatheringstatechange',done)};
        const timer=setTimeout(()=>{cleanup();reject(Error('Network negotiation timed out. Reopen Chat.'))},10000);
        pc.addEventListener('icegatheringstatechange',done);done();
    });
}
async function startLive(){
    if(currentVoice)return;
    const session={parts:[],turns:[],seen:new Set(),work:Promise.resolve(),includeWork:$('#aiScope').value==='work',allowLookups:$('#aiAllowLookups').checked};
    currentVoice=session;syncVoiceButtons();setAISetup(false);voiceNotice('Connecting…');
    try{
        const settings=await officeApi('/api/ai/settings');
        if(currentVoice!==session)return;
        aiSettings=settings;
        if(!settings.liveVoiceConfigured)throw Error('Add your voice key in AI settings to start a chat.');
        if(aiSettings?.engine!=='codex' || !aiSettings?.configured)throw Error('Connect ChatGPT and choose Codex with Ledger tools in AI settings.');
        voiceText('Connecting microphone…');
        if(!navigator.mediaDevices?.getUserMedia)throw Error('Microphone access is unavailable. Open the Ledger desktop app.');
        session.pc=new RTCPeerConnection();
        session.context=new AudioContext();session.analyser=session.context.createAnalyser();session.analyser.fftSize=256;
        session.context.resume().catch(()=>{});
        const preferred=localStorage.getItem('ledgerLiveMic')||'';
        try{await setMicrophone(session,preferred)}catch(error){
            if(!preferred || !['NotFoundError','OverconstrainedError'].includes(error.name))throw error;
            await setMicrophone(session,'');
        }
        if(currentVoice!==session || session.closed)return;
        await listMicrophones().catch(()=>{});
        if(currentVoice!==session || session.closed)return;
        $('#voiceDevices').hidden=false;
        const buffer=new Uint8Array(256);
        session.meterTimer=setInterval(()=>{session.analyser.getByteTimeDomainData(buffer);$('#voiceMeter').value=Math.min(100,Math.max(...buffer.map(v=>Math.abs(v-128)))*2)},120);
        session.pc.ontrack=e=>{
            if(session.closed)return;
            const audio=$('#liveOutput');audio.srcObject=e.streams[0]||new MediaStream([e.track]);
            audio.play().catch(()=>{if(currentVoice===session){session.playBlocked=true;voiceNotice('Select Play audio to hear Ledger.','play')}});
        };
        session.pc.onconnectionstatechange=()=>{if(session.pc.connectionState==='failed')failVoice(session,'Voice disconnected. Check your network and reconnect.')};
        const events=session.events=session.pc.createDataChannel('oai-events');
        events.onmessage=e=>voiceEvent(session,e.data);
        events.onclose=()=>failVoice(session,'Voice connection closed.');
        voiceText('Connecting to OpenAI live voice…');
        await session.pc.setLocalDescription(await session.pc.createOffer());
        await gatherIce(session.pc);
        await saveState('');await saveChain;
        if(currentVoice!==session || session.closed)return;
        if(saveFailed)throw Error('Save pending Ledger changes before connecting.');
        const result=await officeApi('/api/ai/voice/start',{sdp:session.pc.localDescription.sdp});
        if(currentVoice!==session || session.closed){await officeApi('/api/ai/voice/end',{id:result.id});return}
        session.id=result.id;
        session.timeout=setTimeout(()=>failVoice(session,'OpenAI did not start the audio connection. Check your network and retry.'),20000);
        await session.pc.setRemoteDescription({type:'answer',sdp:result.sdp});
    }catch(error){
        const msg=error.name==='NotAllowedError'?'Allow microphone access in the Ledger window and Windows microphone settings, then reconnect.':error.message;
        failVoice(session,msg);
    }
}
$('#voiceKeyForm').onsubmit=async e=>{
    e.preventDefault();const key=$('#voiceKey'),button=e.submitter;button.disabled=true;
    try{await officeApi('/api/ai/voice/key',{key:key.value});key.value='';await aiLoad(true);$('#voiceRemove').hidden=false;voiceNotice('');voiceText('Voice key saved. Select Chat to start.')}
    catch(error){voiceText(error.message)}finally{button.disabled=false}
};
$('#voiceRemove').onclick=async()=>{
    try{await officeApi('/api/ai/voice/key',{remove:true});await aiLoad(true);$('#voiceKey').value='';$('#voiceRemove').hidden=true;voiceText('Voice key removed.')}
    catch(error){voiceText(error.message)}
};
$('#voiceMic').onchange=async e=>{
    const session=currentVoice,mic=e.currentTarget,choice=mic.value;mic.disabled=true;
    try{if(session)await setMicrophone(session,choice);localStorage.setItem('ledgerLiveMic',choice)}
    catch{mic.value=localStorage.getItem('ledgerLiveMic')||'';voiceText('Could not switch microphones. Check the selected device.')}
    finally{mic.disabled=false}
};
for(const button of voiceButtons)button.onclick=()=>currentVoice?endVoice():startLive();
syncVoiceButtons();
window.addEventListener('pagehide',endVoice);
