// A full page transition keeps forms, maps, pending saves and scan results isolated.
const selectorPanel=document.createElement('section');
selectorPanel.className='card community-picker';
selectorPanel.innerHTML=`<div><label for="communitySelect">Select your Super Neighborhood</label><select id="communitySelect">${COMMUNITY_BOOT.communities.map(p=>`<option value="${esc(p.id)}" ${p.id===community.id?'selected':''}>${esc(p.name)} — SN ${esc(p.id)}</option>`).join('')}</select></div><p id="communitySwitchStatus" role="status"></p>`;
$('#dashboard .today-heading').after(selectorPanel);
const councilLinks=(community.councilDistricts||[]).map(d=>`<a class="source" href="https://www.houstontx.gov/council/${d.toLowerCase()}/" target="_blank" rel="noopener">District ${esc(d)} ↗</a>`).join(' · ');
sourceDetails.insertAdjacentHTML('beforeend',`<div id="councilSources"><p><b>Council districts serving ${esc(community.name)}</b><br>${councilLinks}</p><p>News checks include public newsletters, announcements and calendars from these districts. Source details show offices with no readable public archive or calendar. <a class="source" href="${esc(community.councilDistrictSource)}" target="_blank" rel="noopener">City district mapping (${esc(community.councilDistrictMapPeriod)}) ↗</a></p></div>`);
const communitySelect=$('#communitySelect');
communitySelect.onchange=async()=>{
 const next=communitySelect.value;if(next===community.id)return;
 communitySwitching=true;communitySelect.disabled=true;$('#communitySwitchStatus').textContent='Saving before switching…';
 try{
  await saveState('');await saveChain;
  if(saveFailed)throw Error('Switch paused because your changes could not be saved. Export your pending work before reloading.');
  const result=await officeApi('/api/community-selection',{id:next});
  location.assign(result.url);
 }catch(error){communitySwitching=false;communitySelect.value=community.id;communitySelect.disabled=false;$('#communitySwitchStatus').textContent=error.message}
};
// The official profile link replaces Fifth Ward's fixed demographic values elsewhere.
if(community.id!=='55'){
 const card=$$('#neighborhood .grid.two .card').find(c=>!c.contains($('#map')));
 if(card)card.innerHTML=`<div class="pad"><h3>${esc(community.name)}</h3><p>Super Neighborhood ${esc(community.id)} · Houston</p><p>The map uses the official City boundary. Select a plat or permit marker to open its record.</p><a class="source" href="${esc(community.url)}" target="_blank" rel="noopener">Official community page ↗</a></div>`;
 const directory=$$('#intelligence details').find(d=>d.querySelector('summary')?.textContent==='Community organizers and program directories');
 if(directory)directory.innerHTML=`<summary>Community information and program directories</summary><p><a class="source" href="${esc(community.url)}" target="_blank" rel="noopener">${esc(community.name)} — City community page ↗</a></p><p><a class="source" href="https://calendar.houstonlibrary.org/calendar/events" target="_blank" rel="noopener">Houston Public Library events — check the branch ↗</a></p><p>News includes recent matching stories and Houston-wide announcements. Local publication coverage varies.</p>`;
}
// Keep the URL explicit for reload, restore and multiple open browser tabs.
const communityUrl=new URL(location.href),refreshCommunity=communityUrl.searchParams.get('refresh')==='1';
communityUrl.searchParams.set('community',community.id);communityUrl.searchParams.delete('refresh');history.replaceState(null,'',communityUrl);
if(refreshCommunity)setTimeout(()=>startScan('all'),300);

// Council bylaws follow the same page-bound community as maps and saved work.
viewNames.bylaws='Bylaws';
const bylawsNav=document.createElement('button');bylawsNav.dataset.view='bylaws';
bylawsNav.innerHTML=uiIcon('documents')+'<span>Bylaws</span>';
$('.nav [data-view="neighborhood"]').after(bylawsNav);
bylawsNav.onclick=()=>showView('bylaws');
const bylawsView=document.createElement('section');bylawsView.id='bylaws';bylawsView.className='view';
bylawsView.innerHTML=`<div class="pagehead"><div><h2>Bylaws</h2><p>${esc(community.name)} · Super Neighborhood ${esc(community.id)}</p></div><button class="btn" id="bylawsRefresh">Refresh</button></div><div class="card" style="padding:24px"><div id="bylawsResult" role="status" aria-live="polite">Open this tab to check the City’s posted bylaws.</div><p style="margin-top:24px"><a class="source" href="${esc(community.url)}" target="_blank" rel="noopener">Official community page and council contact ↗</a></p></div>`;
$('.content').append(bylawsView);
let bylawsLoading=false,bylawsLoaded=false;
async function loadBylaws(){
 if(bylawsLoading)return;bylawsLoading=true;$('#bylawsRefresh').disabled=true;
 $('#bylawsResult').textContent='Checking the City’s bylaws for '+community.name+'…';
 try{
  const data=await officeApi('/api/bylaws');
  if(data.communityId!==community.id)throw Error('The response belongs to another community. Please retry.');
  $('#bylawsResult').innerHTML=`<p>${esc(data.message)}</p>${(data.documents||[]).map((d,i)=>d.status==='available'?`<p><a class="btn primary" href="${esc(safeUrl(d.url))}" target="_blank" rel="noopener">Open bylaws PDF${data.documents.length>1?' '+(i+1):''} ↗</a></p>`:`<p>Listed document could not be opened: ${esc(d.error||'Unavailable')}</p>`).join('')}${data.error?`<p>${esc(data.error)}</p>`:''}<p class="meta">Checked ${esc(friendlyDate(data.checkedAt,true))}</p>`;
  bylawsLoaded=['available','partial','not_posted'].includes(data.status);
 }catch(error){$('#bylawsResult').textContent='Could not load bylaws: '+error.message;bylawsLoaded=false}
 finally{bylawsLoading=false;$('#bylawsRefresh').disabled=false}
}
$('#bylawsRefresh').onclick=loadBylaws;
const beforeBylawsShow=showView;showView=function(id){beforeBylawsShow(id);if(id==='bylaws'&&!bylawsLoaded)loadBylaws()};

// HPW geometry is fetched separately from saved plats and permits.
const hpwPanel=document.createElement('div');
hpwPanel.className='pad';
hpwPanel.innerHTML='<div class="actions"><label><input type="checkbox" id="hpwShow" checked> HPW projects</label><label><input type="checkbox" id="hpwDesign"> Include design projects</label><button class="btn small" id="hpwRefresh">Refresh HPW</button></div><p class="meta" id="hpwStatus" role="status"></p><details><summary>HPW source details</summary><p>Roads, water, wastewater and drainage projects intersecting this neighborhood. Orange shows construction; purple dashed lines show design. Stages and dates are reported by HPW. This covers the published capital-project layers.</p><div id="hpwChecks"></div></details>';
$('#map').after(hpwPanel);
let hpwData=null,hpwLayer=null,hpwBusy=false;
function openHPWDetails(feature){
 const p=feature.properties;
 $('#hpwDetailTitle').textContent=p.PROJECT_DESCRIPTION||'HPW project';
 $('#hpwDetailSubtitle').textContent=(p.CIP_NUMBER||'Project number not supplied')+' · '+p.ledgerCategory;
 const fields=[
  ['Project number',p.CIP_NUMBER],['Reported status',p.PROJECT_STAGE],
  ['Project type',p.PROJECT_TYPE||p.ledgerCategory],['Department',p.PROJECT_DEPARTMENT],
  ['Reported start',p.START_DATE],['Reported end',p.END_DATE],
  ['Design project manager',p.DESIGN_PROJECT_MGR],['Construction project manager',p.CONSTRUCTION_PROJECT_MGR],
  ['Council district',p.COUNCIL_DISTRICT],['Project record updated',p.GIS_MOD_DATE],
  ['Source layer updated',friendlyDate(p.ledgerSourceUpdated,true)],
  ['Retrieved',friendlyDate(hpwData.checkedAt,true)]
 ];
 $('#hpwDetailBody').innerHTML='<div class="detailsection"><span class="tag development">Houston Public Works</span><p>'+esc(p.PROJECT_SCOPE||'Project scope has not been supplied by HPW.')+'</p><p>Mapped project intersects '+esc(community.name)+'.</p></div><div class="formgrid">'+fields.map(([label,value])=>'<div class="field"><label>'+esc(label)+'</label><div class="generated" style="min-height:auto">'+esc(value||'Not supplied')+'</div></div>').join('')+'</div>';
 $('#hpwDetailSource').href=p.ledgerSource+'/query?where=OBJECTID%3D'+encodeURIComponent(p.OBJECTID)+'&outFields=*&returnGeometry=false&f=html';
 map.closePopup();
 openModal('hpwDetailModal');
}
function drawHPW(){
 if(hpwLayer){map?.removeLayer(hpwLayer);hpwLayer=null}
 if(!map||!hpwData)return;
 const rows=hpwData.features.filter(f=>$('#hpwDesign').checked||f.properties.PROJECT_STAGE==='Construction');
 if($('#hpwShow').checked){
  if(!map.getPane('hpwProjects'))map.createPane('hpwProjects').style.zIndex=410;
  hpwLayer=L.geoJSON(rows,{
   pane:'hpwProjects',
   style:f=>({color:f.properties.PROJECT_STAGE==='Construction'?'#c45512':'#7553a6',weight:5,opacity:.9,fillOpacity:.12,dashArray:f.properties.PROJECT_STAGE==='Design'?'7 5':null}),
   onEachFeature:(f,layer)=>{
    const p=f.properties;
    layer.bindTooltip(esc(p.PROJECT_DESCRIPTION||p.CIP_NUMBER||'HPW project')+'<br>Click for project details');
    layer.on('click',()=>openHPWDetails(f));
    layer.on('add',()=>{
     const element=layer.getElement?.();
     if(!element)return;
     element.setAttribute('tabindex','0');element.setAttribute('role','button');
     element.setAttribute('aria-label',(p.PROJECT_DESCRIPTION||p.CIP_NUMBER||'HPW project')+' — open project details');
     element.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();openHPWDetails(f)}};
    });
   }
  }).addTo(map);
 }
 const count=new Set(rows.map(f=>f.properties.CIP_NUMBER||f.properties.ledgerCategory+':'+f.properties.OBJECTID)).size;
 const failures=hpwData.checks.filter(c=>c.status!=='ok');
 $('#hpwStatus').textContent=(failures.length===5?'HPW projects unavailable.':count+' HPW project'+(count===1?'':'s')+' '+($('#hpwDesign').checked?'in construction or design':'reported in construction')+'.')+(failures.length&&failures.length<5?' Some sources are unavailable.':'')+' Checked '+friendlyDate(hpwData.checkedAt,true)+'.';
}
async function loadHPW(){
 if(hpwBusy)return;
 hpwBusy=true;$('#hpwRefresh').disabled=true;
 hpwData=null;if(hpwLayer){map?.removeLayer(hpwLayer);hpwLayer=null}
 $('#hpwStatus').textContent='Checking Houston Public Works projects…';$('#hpwChecks').textContent='';
 try{
  const data=await officeApi('/api/hpw-projects');
  if(data.communityId!==community.id||communitySwitching)return;
  hpwData=data;
  $('#hpwChecks').innerHTML=data.checks.map(c=>'<p>'+esc(c.name)+' · '+esc(c.status==='ok'?c.count+' mapped features':c.message)+'</p>').join('');
  drawHPW();
 }catch(error){$('#hpwStatus').textContent='HPW projects unavailable. '+error.message}
 finally{hpwBusy=false;$('#hpwRefresh').disabled=false}
}
$('#hpwShow').onchange=$('#hpwDesign').onchange=drawHPW;
$('#hpwRefresh').onclick=loadHPW;
const hpwPriorShow=showView;
showView=function(id){hpwPriorShow(id);if(id==='neighborhood'&&(!hpwData||Date.now()-Date.parse(hpwData.checkedAt)>300000))loadHPW()};
