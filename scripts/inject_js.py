path = r'c:\Users\sahil kavishka\Downloads\Code-Wave\Code-Wave\src\web\index.html'

js_block = r"""
<script>
let currentResult=null,graphData={nodes:[],links:[]},canvasNodes=[],canvasLinks=[];
let activeTypes=new Set(['Location','Character','Relic','Faction','Era']);
let queryActiveIds=new Set(),focusMode=false,draggedNode=null,isPanning=false;
let startPan={x:0,y:0},zoomLevel=1.0,panOffset={x:0,y:0};
let hoveredNode=null,selectedNode=null,rafId=null;

(function(){
  const sc=document.getElementById('star-canvas'),sx=sc.getContext('2d');
  function resize(){sc.width=window.innerWidth;sc.height=window.innerHeight;}
  resize();window.addEventListener('resize',resize);
  const stars=Array.from({length:180},()=>({x:Math.random(),y:Math.random(),r:Math.random()*1.3+0.2,a:Math.random(),da:(Math.random()-0.5)*0.004}));
  function draw(){
    sx.clearRect(0,0,sc.width,sc.height);
    stars.forEach(s=>{
      s.a=Math.max(0.05,Math.min(0.9,s.a+s.da));
      if(s.a<=0.05||s.a>=0.9)s.da*=-1;
      sx.beginPath();sx.arc(s.x*sc.width,s.y*sc.height,s.r,0,Math.PI*2);
      sx.fillStyle='rgba(245,207,123,'+s.a+')';sx.fill();
    });requestAnimationFrame(draw);
  }
  draw();
})();

document.getElementById('btn-sidebar-toggle').addEventListener('click',()=>document.getElementById('sidebar').classList.toggle('collapsed'));
document.querySelectorAll('.nav-tab').forEach(tab=>{
  tab.addEventListener('click',()=>{
    document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
    tab.classList.add('active');
    const target=tab.getAttribute('data-tab');
    document.getElementById(target).classList.add('active');
    if(target==='tab-canvas')setTimeout(()=>{resizeCanvas();if(!rafId)rafId=requestAnimationFrame(drawGraph);},60);
  });
});
document.querySelectorAll('.chip-btn').forEach(btn=>btn.addEventListener('click',()=>{queryInput.value=btn.getAttribute('data-q');executeResearch();}));

function showToast(msg,icon){
  const icons={check:'OK',copy:'Copied',dl:'Downloaded',clear:'Cleared',star:'Star',warn:'Warn'};
  document.getElementById('toast-icon').textContent=icons[icon||'check']||'OK';
  document.getElementById('toast-text').textContent=msg;
  const el=document.getElementById('app-toast');
  el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);
}

const loadingOverlay=document.getElementById('loading-overlay');
let loadingTimer=null;
function startLoading(){
  loadingOverlay.classList.add('show');
  document.getElementById('verify-strip').classList.remove('show');
  ['ls-1','ls-2','ls-3','ls-4','ls-5'].forEach(id=>document.getElementById(id).classList.remove('visible'));
  let i=0;const steps=['ls-1','ls-2','ls-3','ls-4','ls-5'];
  function next(){if(i<steps.length){document.getElementById(steps[i++]).classList.add('visible');loadingTimer=setTimeout(next,700+Math.random()*350);}}
  next();
}
function stopLoading(){clearTimeout(loadingTimer);loadingOverlay.classList.remove('show');}

const queryInput=document.getElementById('query-input');
const btnResearch=document.getElementById('btn-research'),btnSpinner=document.getElementById('btn-spinner'),btnLabel=document.getElementById('btn-label');
const answerBox=document.getElementById('answer-box'),figureCard=document.getElementById('figure-card'),figureThumb=document.getElementById('figure-thumb'),figureLabel=document.getElementById('figure-label');
const timelineList=document.getElementById('timeline-list'),evidenceGrid=document.getElementById('evidence-grid'),tripletsSection=document.getElementById('triplets-section'),tripletsGrid=document.getElementById('triplets-grid');
const canvas=document.getElementById('kg-canvas'),ctx=canvas.getContext('2d'),kgTooltip=document.getElementById('kg-tooltip'),kgSel=document.getElementById('kg-sel');

btnResearch.addEventListener('click',executeResearch);
queryInput.addEventListener('keydown',e=>{if(e.key==='Enter')executeResearch();});
async function executeResearch(){
  const query=queryInput.value.trim();if(!query)return;
  btnResearch.disabled=true;btnSpinner.style.display='inline-block';btnLabel.textContent='RESEARCHING...';
  document.getElementById('conflict-box').classList.remove('show');
  figureCard.style.display='none';tripletsSection.style.display='none';
  answerBox.className='';answerBox.innerHTML='';
  startLoading();
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
  document.querySelector('[data-tab="tab-synthesis"]').classList.add('active');
  document.getElementById('tab-synthesis').classList.add('active');
  try{
    const res=await fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:query,max_hops:3,no_cache:false})});
    if(!res.ok)throw new Error('HTTP '+res.status);
    const data=await res.json();
    currentResult=data;saveHistory(data);renderWorkspace(data);
  }catch(err){
    stopLoading();
    answerBox.innerHTML='<div style="color:#f43f5e;padding:20px;text-align:center">Investigation failed: '+err.message+'</div>';
  }finally{
    btnResearch.disabled=false;btnSpinner.style.display='none';btnLabel.textContent='RESEARCH';
  }
}

function renderMarkdown(text){
  let t=text.replace(/![\s\S]*?\)/g,'').trim()
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>');
  t=t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>');
  t=t.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');
  t=t.split(/\n{2,}/).map(p=>/^<(h[23]|ul|ol|blockquote)/.test(p.trim())?p:'<p>'+p.replace(/\n/g,'<br>')+'</p>').join('');
  return t;
}

function renderWorkspace(data){
  stopLoading();
  answerBox.className='answer-text';answerBox.innerHTML=renderMarkdown(data.answer);
  const strip=document.getElementById('verify-strip');strip.classList.add('show');
  const score=(data.grounding_score*100).toFixed(1);
  document.getElementById('stat-conf').textContent=score+'%';
  document.getElementById('stat-facts').textContent=data.verified_facts_count||'--';
  const badge=document.getElementById('badge-status');badge.textContent=data.grounding_status;
  const isRef=data.grounding_status.includes('REFUSAL'),isPar=data.grounding_status.includes('PARTIAL');
  badge.className='grounding-badge '+(isRef?'refusal':isPar?'partial':'verified');
  const bar=document.getElementById('conf-bar');bar.style.width='0%';
  requestAnimationFrame(()=>{
    bar.style.width=score+'%';
    bar.style.background=score>=90?'linear-gradient(90deg,#8c5d18,#e6a73c,#f5cf7b)':score>=70?'linear-gradient(90deg,#b45309,#fb923c)':'linear-gradient(90deg,#9f1239,#f43f5e)';
  });
  const cb=document.getElementById('conflict-box');
  if(data.contradictions&&data.contradictions.length>0){
    const c=data.contradictions[0];
    document.getElementById('conflict-body').innerHTML='<strong>Topic:</strong> '+esc(c.topic||'--')+'<br><strong>Authoritative:</strong> '+esc(c.tier1_authority||'Codex Vaeloria')+'<br><strong>Resolution:</strong> '+esc(c.archival_resolution||'--');
    cb.classList.add('show');
  }else{cb.classList.remove('show');}
  if(data.rich_media&&data.rich_media.image_url){figureCard.style.display='flex';figureThumb.src=data.rich_media.image_url;figureLabel.textContent=data.rich_media.title||'Archive Plate';}else{figureCard.style.display='none';}
  document.getElementById('m-hops').textContent=data.hops.length+' Hop'+(data.hops.length!==1?'s':'');
  document.getElementById('m-sources').textContent=data.citations.length+' Source'+(data.citations.length!==1?'s':'');
  document.getElementById('m-triples').textContent=(data.kg_triplets||[]).length+' Triples';
  const triplets=data.kg_triplets||[];
  if(triplets.length>0){tripletsSection.style.display='block';tripletsGrid.innerHTML=triplets.slice(0,18).map(t=>'<div class="triplet-chip"><span class="tc-sub">'+esc(t.subject)+'</span><span class="tc-rel">'+esc(t.predicate)+'</span><span class="tc-obj">'+esc(t.object)+'</span></div>').join('');}else{tripletsSection.style.display='none';}
  const cntT=document.getElementById('cnt-traversal');cntT.textContent=data.hops.length;cntT.classList.toggle('show',data.hops.length>0);
  document.getElementById('traversal-pill').textContent=data.hops.length+' Hop'+(data.hops.length!==1?'s':'');
  timelineList.innerHTML='';
  if(data.hops.length===0){timelineList.innerHTML='<div class="history-empty">Single-hop query. No iterative traversal required.</div>';}
  else{data.hops.forEach(h=>{const node=document.createElement('div');node.className='timeline-node';node.setAttribute('data-hop',h.hop);node.innerHTML='<div class="timeline-card"><div class="timeline-hop-label"><span>Hop '+h.hop+'</span><span class="timeline-tag">EVALUATED</span></div><div class="timeline-query">'+esc(h.query)+'</div>'+(h.thought?'<div class="timeline-thought">'+esc(h.thought)+'</div>':'')+'</div>';timelineList.appendChild(node);});}
  const cits=data.pinpointed_citations||[],fall=data.citations||[],total=cits.length||fall.length;
  const cntE=document.getElementById('cnt-evidence');cntE.textContent=total;cntE.classList.toggle('show',total>0);
  document.getElementById('evidence-count-pill').textContent=total+' Citation'+(total!==1?'s':'');
  evidenceGrid.innerHTML='';
  (cits.length>0?cits:fall.map(c=>({source:c}))).forEach(p=>{
    const type=srcType(p.source),div=document.createElement('div');
    div.className='evidence-card '+type;
    div.innerHTML='<div class="evidence-src"><span class="evidence-src-name">'+esc(p.source)+'</span><span class="ev-type-tag '+type+'">'+type.toUpperCase()+'</span></div>'+(p.quote?'<div class="evidence-quote">'+esc(p.quote)+'</div>':'');
    evidenceGrid.appendChild(div);
  });
  queryActiveIds.clear();(data.kg_triplets||[]).forEach(t=>{queryActiveIds.add(t.subject);queryActiveIds.add(t.object);});
  rebuildDisplayGraph();
}

function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function srcType(s){s=(s||'').toLowerCase();if(s.includes('codex'))return 'codex';if(s.includes('chronicle'))return 'chronicle';if(s.includes('wiki')||s.includes('.md'))return 'wiki';if(s.includes('ephemera')||s.includes('.txt'))return 'ephemera';if(/\.(png|jpg|jpeg)/.test(s))return 'image';return 'chronicle';}

function saveHistory(item){
  let h=JSON.parse(localStorage.getItem('ashen_history')||'[]');
  h=h.filter(x=>x.question!==item.question);
  h.unshift({question:item.question,score:(item.grounding_score*100).toFixed(0),hops:item.hops.length,timestamp:new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),data:item});
  if(h.length>25)h.pop();localStorage.setItem('ashen_history',JSON.stringify(h));renderHistory();
}
function renderHistory(){
  const hl=document.getElementById('history-list'),h=JSON.parse(localStorage.getItem('ashen_history')||'[]');
  if(h.length===0){hl.innerHTML='<div class="history-empty">No investigations yet. Run a query to begin.</div>';return;}
  hl.innerHTML='';
  h.forEach((item,idx)=>{
    const el=document.createElement('div');el.className='history-item';
    el.innerHTML='<div class="history-item-q">'+esc(item.question)+'</div><div class="history-item-meta"><span>#'+(idx+1)+' - '+(item.hops||0)+' hops</span><span>'+item.timestamp+'</span></div><span class="history-item-score">'+(item.score||'--')+'% grounded</span>';
    el.addEventListener('click',()=>{document.querySelectorAll('.history-item').forEach(i=>i.classList.remove('active'));el.classList.add('active');queryInput.value=item.question;currentResult=item.data;renderWorkspace(item.data);});
    hl.appendChild(el);
  });
}
document.getElementById('btn-clear-history').addEventListener('click',()=>{localStorage.removeItem('ashen_history');renderHistory();showToast('History cleared.','clear');});
document.getElementById('btn-copy').addEventListener('click',()=>{if(!currentResult)return;navigator.clipboard.writeText(currentResult.answer).then(()=>showToast('Copied!','copy')).catch(()=>showToast('Copy failed.','warn'));});
document.getElementById('btn-print').addEventListener('click',()=>window.print());
document.getElementById('btn-dossier').addEventListener('click',()=>{
  if(!currentResult)return;const r=currentResult;
  const md=['# Ashen Era Archive Dossier','Query: '+r.question,'Score: '+(r.grounding_score*100).toFixed(1)+'%','Date: '+new Date().toISOString(),'','## Synthesis','',r.answer,'','## Traversal'];
  r.hops.forEach(h=>md.push('Hop '+h.hop+': '+h.query+(h.thought?' -- '+h.thought:'')));
  md.push('','## Citations');
  (r.pinpointed_citations||r.citations||[]).forEach((p,i)=>md.push((i+1)+'. '+(typeof p==='string'?p:p.source+(p.quote?' -- '+p.quote:''))));
  const blob=new Blob([md.join('\n')],{type:'text/markdown'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ashen_dossier_'+Date.now()+'.md';a.click();
  showToast('Dossier downloaded!','dl');
});
figureThumb.addEventListener('click',()=>{document.getElementById('modal-img').src=figureThumb.src;document.getElementById('modal-lightbox').classList.add('active');});
document.getElementById('modal-lightbox').addEventListener('click',e=>{if(e.target===e.currentTarget)e.currentTarget.classList.remove('active');});
document.getElementById('btn-modal-close').addEventListener('click',()=>document.getElementById('modal-lightbox').classList.remove('active'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.getElementById('modal-lightbox').classList.remove('active');});

function nodeColor(type){return{Location:'#38bdf8',Character:'#e6a73c',Relic:'#c084fc',Faction:'#34d399',Era:'#60a5fa'}[type]||'#f5cf7b';}
function nodeRadius(type){return{Location:15,Character:13,Relic:11,Faction:12,Era:10}[type]||10;}
async function loadFullGraph(){
  try{
    const res=await fetch('/api/graph');if(!res.ok)throw new Error('failed');
    graphData=await res.json();
    document.getElementById('t-kg').textContent='KG: '+graphData.stats.total_nodes+' Nodes';
    document.getElementById('canvas-status').textContent=graphData.stats.total_nodes+' nodes - '+graphData.stats.total_edges+' edges';
    const tc={};graphData.nodes.forEach(n=>{tc[n.type]=(tc[n.type]||0)+1;});
    document.querySelectorAll('.kg-type-cnt').forEach(el=>{el.textContent=tc[el.dataset.type]||0;});
    rebuildDisplayGraph();
  }catch(e){document.getElementById('canvas-status').textContent='Graph unavailable';}
}
function rebuildDisplayGraph(){
  if(!graphData.nodes||!graphData.nodes.length)return;
  let nodes=graphData.nodes.filter(n=>activeTypes.has(n.type)),links=graphData.links;
  if(focusMode&&queryActiveIds.size>0){const f=nodes.filter(n=>queryActiveIds.has(n.id));if(f.length>0){nodes=f;links=links.filter(l=>queryActiveIds.has(l.source)&&queryActiveIds.has(l.target));}}
  buildCanvasGraph(nodes.slice(0,50),links.slice(0,65));
}
function buildCanvasGraph(nodes,links){
  resizeCanvas();const cx=canvas.width/2,cy=canvas.height/2;
  canvasNodes=nodes.map((n,i)=>{
    const angle=(i/nodes.length)*Math.PI*2,r=Math.min(cx,cy)*0.58;
    return{id:n.id,label:n.label,type:n.type,x:cx+Math.cos(angle)*r+(Math.random()-.5)*60,y:cy+Math.sin(angle)*r+(Math.random()-.5)*60,vx:0,vy:0,radius:nodeRadius(n.type),color:nodeColor(n.type),isActive:queryActiveIds.has(n.id)};
  });
  const nm=new Map(canvasNodes.map(n=>[n.id,n]));
  canvasLinks=links.filter(l=>nm.has(l.source)&&nm.has(l.target)).map(l=>({source:nm.get(l.source),target:nm.get(l.target),relation:l.relation}));
}
function resizeCanvas(){const rect=canvas.parentElement.getBoundingClientRect(),w=Math.floor(rect.width),h=Math.floor(rect.height);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}}
function simulate(){
  for(let i=0;i<canvasNodes.length;i++){for(let j=i+1;j<canvasNodes.length;j++){const a=canvasNodes[i],b=canvasNodes[j],dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;if(d<160){const f=(160-d)/d*0.06;a.vx-=dx*f;a.vy-=dy*f;b.vx+=dx*f;b.vy+=dy*f;}}}
  canvasLinks.forEach(l=>{const dx=l.target.x-l.source.x,dy=l.target.y-l.source.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-110)*0.0025;l.source.vx+=dx*f;l.source.vy+=dy*f;l.target.vx-=dx*f;l.target.vy-=dy*f;});
  const cx=(canvas.width/2-panOffset.x)/zoomLevel,cy=(canvas.height/2-panOffset.y)/zoomLevel;
  canvasNodes.forEach(n=>{if(n!==draggedNode){n.vx+=(cx-n.x)*0.002;n.vy+=(cy-n.y)*0.002;n.x+=n.vx;n.y+=n.vy;n.vx*=0.83;n.vy*=0.83;}});
}
function drawGraph(){
  resizeCanvas();ctx.clearRect(0,0,canvas.width,canvas.height);ctx.save();ctx.translate(panOffset.x,panOffset.y);ctx.scale(zoomLevel,zoomLevel);simulate();
  canvasLinks.forEach(l=>{const active=l.source.isActive&&l.target.isActive;ctx.beginPath();ctx.moveTo(l.source.x,l.source.y);ctx.lineTo(l.target.x,l.target.y);ctx.strokeStyle=active?'rgba(245,207,123,.55)':'rgba(230,167,60,.16)';ctx.lineWidth=active?1.8:1.0;ctx.stroke();if(canvasLinks.length<=35&&l.relation){ctx.fillStyle='rgba(56,189,248,.65)';ctx.font='9px monospace';ctx.textAlign='center';ctx.fillText(l.relation,(l.source.x+l.target.x)/2,(l.source.y+l.target.y)/2);}});
  canvasNodes.forEach(n=>{const isSel=selectedNode&&selectedNode.id===n.id,isHov=hoveredNode&&hoveredNode.id===n.id,scale=isSel?1.3:isHov?1.15:1.0,r=n.radius*scale;ctx.beginPath();ctx.arc(n.x,n.y,r+(n.isActive?9:5),0,Math.PI*2);ctx.fillStyle=n.color+(n.isActive?'59':'26');ctx.fill();ctx.beginPath();ctx.arc(n.x,n.y,r,0,Math.PI*2);ctx.fillStyle=n.color;ctx.fill();ctx.strokeStyle=isSel?'#fff':n.isActive?'rgba(255,255,255,.8)':'rgba(255,255,255,.3)';ctx.lineWidth=isSel?2.5:1.5;ctx.stroke();ctx.fillStyle=(isHov||isSel)?'#fff':'rgba(241,245,249,.8)';ctx.font=(isSel?'bold ':'')+' 11px sans-serif';ctx.textAlign='center';const lbl=n.label.length>16?n.label.slice(0,16)+'...':n.label;ctx.fillText(lbl,n.x,n.y+r+14);});
  ctx.restore();rafId=requestAnimationFrame(drawGraph);
}
function canvasPos(e){const rect=canvas.getBoundingClientRect();return{x:(e.clientX-rect.left-panOffset.x)/zoomLevel,y:(e.clientY-rect.top-panOffset.y)/zoomLevel};}
function findNode(x,y){return canvasNodes.find(n=>{const dx=n.x-x,dy=n.y-y;return Math.sqrt(dx*dx+dy*dy)<=n.radius+8;});}
canvas.addEventListener('mousedown',e=>{const pos=canvasPos(e);draggedNode=findNode(pos.x,pos.y);if(!draggedNode){isPanning=true;startPan={x:e.clientX-panOffset.x,y:e.clientY-panOffset.y};}});
window.addEventListener('mousemove',e=>{if(draggedNode){const pos=canvasPos(e);draggedNode.x=pos.x;draggedNode.y=pos.y;draggedNode.vx=0;draggedNode.vy=0;}else if(isPanning){panOffset.x=e.clientX-startPan.x;panOffset.y=e.clientY-startPan.y;}else{const rect=canvas.getBoundingClientRect();if(e.clientX>=rect.left&&e.clientX<=rect.right&&e.clientY>=rect.top&&e.clientY<=rect.bottom){const pos=canvasPos(e);hoveredNode=findNode(pos.x,pos.y);if(hoveredNode){kgTooltip.style.display='block';kgTooltip.style.left=(e.clientX-rect.left+14)+'px';kgTooltip.style.top=(e.clientY-rect.top-10)+'px';document.getElementById('tt-name').textContent=hoveredNode.label;document.getElementById('tt-type').textContent=hoveredNode.type;canvas.style.cursor='pointer';}else{kgTooltip.style.display='none';canvas.style.cursor='grab';}}}});
window.addEventListener('mouseup',()=>{draggedNode=null;isPanning=false;});
canvas.addEventListener('click',e=>{const pos=canvasPos(e),node=findNode(pos.x,pos.y);if(node){selectedNode=selectedNode&&selectedNode.id===node.id?null:node;if(selectedNode){kgSel.classList.add('show');document.getElementById('sel-name').textContent=selectedNode.label;document.getElementById('sel-type').textContent='Type: '+selectedNode.type;const rels=canvasLinks.filter(l=>l.source.id===selectedNode.id||l.target.id===selectedNode.id).slice(0,6);document.getElementById('sel-rels').innerHTML=rels.length?rels.map(l=>'<div class="kg-rel-item"><span class="kg-rel-tag">'+l.relation+'</span>'+(l.source.id===selectedNode.id?l.target.label:l.source.label)+'</div>').join(''):'<span style="color:#4b5e76;font-size:11px">No visible edges</span>';}else{kgSel.classList.remove('show');}}});
canvas.addEventListener('wheel',e=>{e.preventDefault();zoomLevel=Math.max(0.35,Math.min(3.0,zoomLevel*(e.deltaY>0?0.88:1.14)));},{passive:false});
document.getElementById('btn-zoom-in').addEventListener('click',()=>zoomLevel=Math.min(3.0,zoomLevel*1.2));
document.getElementById('btn-zoom-out').addEventListener('click',()=>zoomLevel=Math.max(0.35,zoomLevel*0.82));
document.getElementById('btn-reset-view').addEventListener('click',()=>{zoomLevel=1.0;panOffset={x:0,y:0};rebuildDisplayGraph();});
document.getElementById('btn-focus-query').addEventListener('click',()=>{focusMode=!focusMode;document.getElementById('btn-focus-query').style.color=focusMode?'#e6a73c':'#f5cf7b';rebuildDisplayGraph();showToast(focusMode?'Focusing query nodes':'Full graph','star');});
document.querySelectorAll('.kg-type-filter').forEach(cb=>cb.addEventListener('change',()=>{if(cb.checked)activeTypes.add(cb.value);else activeTypes.delete(cb.value);rebuildDisplayGraph();}));

async function init(){
  renderHistory();
  try{
    const res=await fetch('/api/health');
    if(res.ok){
      const d=await res.json();
      document.getElementById('t-model').textContent=(d.active_model||'').split(':')[0]||'online';
      const chunks=(d.vector_chunks||0).toLocaleString();
      document.getElementById('t-chunks').textContent=chunks+' Chunks';
      document.getElementById('m-chunks').textContent=chunks+' Chunks';
    }
  }catch(e){document.getElementById('t-model').textContent='API Offline';}
  await loadFullGraph();
  rafId=requestAnimationFrame(drawGraph);
}
init();
</script>
"""

with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Insert before </body>
html = html.replace('</body>', js_block + '\n</body>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Done. File size:', len(html), 'bytes')
