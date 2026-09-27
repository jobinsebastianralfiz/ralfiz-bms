/* Ralfiz Academy in-browser simulators.
 *
 * The engines and widgets below (Power Fx console, Flow builder, dataset
 * panel, DAX console, star schema builder, sorter) are copied unchanged from
 * the reference build ralfiz-academy-labs.html in the content package. They
 * are practice only and not graded, so solved challenges stay in this
 * browser's localStorage, as the integration guide allows.
 */
(function(){
'use strict';
var SIM_KEY='ralfizacademy.sims.v1';
var S={};
try{S=JSON.parse(localStorage.getItem(SIM_KEY)||'{}')||{};}catch(e){S={};}
function save(){try{localStorage.setItem(SIM_KEY,JSON.stringify(S));}catch(e){}}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));


/* ---------------- Power Fx console ---------------- */
const TICKETS=[
 {ID:1,Title:'Wi-Fi down in library',Priority:'High',Status:'Open',Days:2},
 {ID:2,Title:'Printer jam in lab 3',Priority:'Low',Status:'Closed',Days:1},
 {ID:3,Title:'Password reset for new student',Priority:'Medium',Status:'Open',Days:1},
 {ID:4,Title:'Projector not working in hall B',Priority:'High',Status:'In progress',Days:3},
 {ID:5,Title:"Laptop won't charge",Priority:'High',Status:'Open',Days:4},
 {ID:6,Title:'Email not syncing on phone',Priority:'Medium',Status:'Closed',Days:2}
];
const FX_TASKS=[
 {goal:'Count every ticket in the Tickets table.',exp:6,hint:'CountRows takes a table.',sol:'CountRows(Tickets)'},
 {goal:'Count only the tickets whose Status is "Open".',exp:3,hint:'Wrap Tickets in Filter(table, condition).',sol:'CountRows(Filter(Tickets, Status = "Open"))'},
 {goal:'Count the tickets that are Open AND High priority.',exp:2,hint:'Combine two conditions with && or And.',sol:'CountRows(Filter(Tickets, Status = "Open" && Priority = "High"))'},
 {goal:'Add up the Days column across all tickets.',exp:13,hint:'Sum(table, column) totals a column.',sol:'Sum(Tickets, Days)'},
 {goal:'Show "Urgent" if ThisItem is High priority, otherwise "Normal".',exp:'Urgent',hint:'If(condition, valueIfTrue, valueIfFalse). Use ThisItem.Priority.',sol:'If(ThisItem.Priority = "High", "Urgent", "Normal")'},
 {goal:'Show ThisItem’s title in capital letters.',exp:'WI-FI DOWN IN LIBRARY',hint:'Upper() converts text to capitals.',sol:'Upper(ThisItem.Title)'},
 {goal:'Find the Status of the ticket titled "Laptop won\'t charge".',exp:'Open',hint:'LookUp(table, condition, column) returns one value.',sol:'LookUp(Tickets, Title = "Laptop won\'t charge", Status)'}
];
class FxErr extends Error{}
const err=m=>new FxErr(m);
function tokenize(src){
  const t=[];let i=0;
  while(i<src.length){
    const c=src[i];
    if(/\s/.test(c)){i++;continue;}
    if(/[0-9]/.test(c)){let j=i;while(j<src.length&&/[0-9.]/.test(src[j]))j++;t.push({k:'num',v:parseFloat(src.slice(i,j))});i=j;continue;}
    if(c==='"'||c==='“'||c==='”'){let j=i+1,s='';for(;;){if(j>=src.length)throw err('A text value is missing its closing quote (").');const cj=src[j];if(cj==='"'||cj==='”'||cj==='“'){if(src[j+1]==='"'){s+='"';j+=2;continue;}break;}s+=cj;j++;}t.push({k:'str',v:s});i=j+1;continue;}
    if(c==="'"){const j=src.indexOf("'",i+1);if(j<0)throw err("A name in single quotes is missing its closing quote (').");t.push({k:'id',v:src.slice(i+1,j)});i=j+1;continue;}
    if(/[A-Za-z_]/.test(c)){let j=i;while(j<src.length&&/[A-Za-z0-9_]/.test(src[j]))j++;t.push({k:'id',v:src.slice(i,j)});i=j;continue;}
    const two=src.substr(i,2);
    if(['<>','<=','>=','&&','||'].includes(two)){t.push({k:'op',v:two});i+=2;continue;}
    if('&+-*/=<>!(),.;'.includes(c)){t.push({k:'op',v:c===';'?',':c});i++;continue;}
    throw err('Unexpected character "'+c+'".');
  }
  t.push({k:'eof',v:'end'});return t;
}
function parse(src){
  const t=tokenize(src);let p=0;
  const isOp=v=>t[p].k==='op'&&t[p].v===v;
  const isKw=v=>t[p].k==='id'&&t[p].v.toLowerCase()===v&&!(t[p+1].k==='op'&&t[p+1].v==='(');
  const expect=v=>{if(!isOp(v))throw err('Expected "'+v+'" but found "'+t[p].v+'".');p++;};
  function orE(){let l=andE();while(isOp('||')||isKw('or')){p++;l={t:'or',l,r:andE()};}return l;}
  function andE(){let l=cmp();while(isOp('&&')||isKw('and')){p++;l={t:'and',l,r:cmp()};}return l;}
  function cmp(){let l=cat();while(t[p].k==='op'&&['=','<>','<','>','<=','>='].includes(t[p].v)){const o=t[p++].v;l={t:'bin',o,l,r:cat()};}return l;}
  function cat(){let l=add();while(isOp('&')){p++;l={t:'bin',o:'&',l,r:add()};}return l;}
  function add(){let l=mul();while(isOp('+')||isOp('-')){const o=t[p++].v;l={t:'bin',o,l,r:mul()};}return l;}
  function mul(){let l=un();while(isOp('*')||isOp('/')){const o=t[p++].v;l={t:'bin',o,l,r:un()};}return l;}
  function un(){if(isOp('-')){p++;return{t:'neg',e:un()};}if(isOp('!')||isKw('not')){p++;return{t:'not',e:un()};}return post();}
  function post(){let e=prim();while(isOp('.')){p++;const n=t[p++];if(n.k!=='id')throw err('Expected a column name after the dot.');e={t:'dot',e,f:n.v};}return e;}
  function prim(){
    const k=t[p++];
    if(k.k==='num'||k.k==='str')return{t:'lit',v:k.v};
    if(k.k==='op'&&k.v==='('){const e=orE();expect(')');return e;}
    if(k.k==='id'){
      if(isOp('(')){p++;const args=[];if(!isOp(')')){args.push(orE());while(isOp(',')){p++;args.push(orE());}}expect(')');return{t:'call',n:k.v,args};}
      const lw=k.v.toLowerCase();
      if(lw==='true')return{t:'lit',v:true};if(lw==='false')return{t:'lit',v:false};
      return{t:'id',n:k.v};
    }
    if(k.k==='eof')throw err('The formula ends too early. Check for a missing value or closing bracket.');
    throw err('Unexpected "'+k.v+'".');
  }
  const e=orE();if(t[p].k!=='eof')throw err('Unexpected "'+t[p].v+'" after the end of the formula.');return e;
}
const num=v=>{if(v===null)return 0;if(typeof v==='boolean')return v?1:0;if(typeof v==='number')return v;const n=Number(v);if(v===''||isNaN(n))throw err('Expected a number but got "'+v+'".');return n;};
const str=v=>v===null?'':typeof v==='number'?String(+v.toFixed(10)):typeof v==='object'?(()=>{throw err('Expected text or a number, but got a '+(Array.isArray(v)?'table':'record')+'.');})():String(v);
const bool=v=>{if(typeof v==='boolean')return v;if(v===null)return false;if(typeof v==='number')return v!==0;if(typeof v==='string'){if(v.toLowerCase()==='true')return true;if(v.toLowerCase()==='false'||v==='')return false;}throw err('Expected true or false.');};
const eq=(a,b)=>{if(a===null||b===null)return a===b;if(typeof a==='number'||typeof b==='number'){return Math.abs(num(a)-num(b))<1e-9;}return String(a)===String(b);};
const tbl=v=>{if(!Array.isArray(v))throw err('Expected a table, such as Tickets.');return v;};
function findKey(obj,name){if(name in obj)return name;const k=Object.keys(obj).find(x=>x.toLowerCase()===name.toLowerCase());if(k)throw err('"'+name+'" isn’t recognised. Names are case-sensitive: did you mean '+k+'?');return undefined;}
function lookupId(n,sc){
  for(let i=sc.length-1;i>=0;i--){const o=sc[i];if(n in o)return o[n];}
  for(let i=sc.length-1;i>=0;i--){const o=sc[i];const k=Object.keys(o).find(x=>x.toLowerCase()===n.toLowerCase());if(k)throw err('"'+n+'" isn’t recognised. Names are case-sensitive: did you mean '+k+'?');}
  throw err('"'+n+'" isn’t recognised. Use Tickets, ThisItem, or a column name inside Filter, LookUp or Sum.');
}
function ev(n,sc){
  switch(n.t){
    case 'lit':return n.v;
    case 'id':return lookupId(n.n,sc);
    case 'dot':{const r=ev(n.e,sc);if(r===null)return null;if(typeof r!=='object'||Array.isArray(r))throw err('".'+n.f+'" can only follow a record, such as ThisItem.'+n.f+'.');const k=findKey(r,n.f);if(k===undefined)throw err('The record has no column named "'+n.f+'". Columns: '+Object.keys(r).join(', ')+'.');return r[k];}
    case 'neg':return -num(ev(n.e,sc));
    case 'not':return !bool(ev(n.e,sc));
    case 'and':return bool(ev(n.l,sc))&&bool(ev(n.r,sc));
    case 'or':return bool(ev(n.l,sc))||bool(ev(n.r,sc));
    case 'bin':{const a=ev(n.l,sc),b=ev(n.r,sc);switch(n.o){
      case '&':return str(a)+str(b);case '+':return num(a)+num(b);case '-':return num(a)-num(b);case '*':return num(a)*num(b);
      case '/':if(num(b)===0)throw err('Division by zero.');return num(a)/num(b);
      case '=':return eq(a,b);case '<>':return !eq(a,b);
      case '<':return num(a)<num(b);case '>':return num(a)>num(b);case '<=':return num(a)<=num(b);case '>=':return num(a)>=num(b);}}
    case 'call':return callFn(n,sc);
  }
}
const withRow=(sc,r)=>sc.concat([r]);
function agg(kind){return (a,sc)=>{let vals;const first=ev(a[0],sc);
  if(Array.isArray(first)){if(a.length<2)throw err(kind+'(table, column) needs a column or formula as the second argument.');vals=first.map(r=>num(ev(a[1],withRow(sc,r))));}
  else vals=[first,...a.slice(1).map(x=>ev(x,sc))].map(num);
  if(!vals.length)return 0;
  if(kind==='Sum')return vals.reduce((x,y)=>x+y,0);if(kind==='Average')return vals.reduce((x,y)=>x+y,0)/vals.length;if(kind==='Max')return Math.max(...vals);return Math.min(...vals);};}
const FN={
  If:[2,(a,sc)=>{for(let i=0;i+1<a.length;i+=2){if(bool(ev(a[i],sc)))return ev(a[i+1],sc);}return a.length%2?ev(a[a.length-1],sc):null;}],
  Switch:[3,(a,sc)=>{const v=ev(a[0],sc);let i=1;for(;i+1<a.length;i+=2){if(eq(v,ev(a[i],sc)))return ev(a[i+1],sc);}return i<a.length?ev(a[i],sc):null;}],
  And:[1,(a,sc)=>a.every(x=>bool(ev(x,sc)))],Or:[1,(a,sc)=>a.some(x=>bool(ev(x,sc)))],Not:[1,(a,sc)=>!bool(ev(a[0],sc))],
  Filter:[2,(a,sc)=>tbl(ev(a[0],sc)).filter(r=>a.slice(1).every(c=>bool(ev(c,withRow(sc,r)))))],
  LookUp:[2,(a,sc)=>{const r=tbl(ev(a[0],sc)).find(r=>bool(ev(a[1],withRow(sc,r))));if(!r)return null;return a[2]?ev(a[2],withRow(sc,r)):r;}],
  CountIf:[2,(a,sc)=>tbl(ev(a[0],sc)).filter(r=>a.slice(1).every(c=>bool(ev(c,withRow(sc,r))))).length],
  Concat:[2,(a,sc)=>tbl(ev(a[0],sc)).map(r=>str(ev(a[1],withRow(sc,r)))).join(a[2]?str(ev(a[2],sc)):'')],
  Sum:[1,agg('Sum')],Average:[1,agg('Average')],Max:[1,agg('Max')],Min:[1,agg('Min')],
  CountRows:[1,(a,sc)=>tbl(ev(a[0],sc)).length],
  First:[1,(a,sc)=>tbl(ev(a[0],sc))[0]??null],Last:[1,(a,sc)=>{const t=tbl(ev(a[0],sc));return t[t.length-1]??null;}],
  Upper:[1,(a,sc)=>str(ev(a[0],sc)).toUpperCase()],Lower:[1,(a,sc)=>str(ev(a[0],sc)).toLowerCase()],
  Len:[1,(a,sc)=>str(ev(a[0],sc)).length],Trim:[1,(a,sc)=>str(ev(a[0],sc)).trim().replace(/\s+/g,' ')],
  Left:[2,(a,sc)=>str(ev(a[0],sc)).slice(0,num(ev(a[1],sc)))],Right:[2,(a,sc)=>{const s=str(ev(a[0],sc)),n=num(ev(a[1],sc));return n<=0?'':s.slice(-n);}],
  Concatenate:[1,(a,sc)=>a.map(x=>str(ev(x,sc))).join('')],
  StartsWith:[2,(a,sc)=>str(ev(a[0],sc)).toLowerCase().startsWith(str(ev(a[1],sc)).toLowerCase())],
  EndsWith:[2,(a,sc)=>str(ev(a[0],sc)).toLowerCase().endsWith(str(ev(a[1],sc)).toLowerCase())],
  Text:[1,(a,sc)=>str(ev(a[0],sc))],Value:[1,(a,sc)=>num(ev(a[0],sc))],
  Round:[2,(a,sc)=>{const f=Math.pow(10,num(ev(a[1],sc)));return Math.round(num(ev(a[0],sc))*f)/f;}],Abs:[1,(a,sc)=>Math.abs(num(ev(a[0],sc)))],
  IsBlank:[1,(a,sc)=>{const v=ev(a[0],sc);return v===null||v==='';}]
};
function callFn(n,sc){
  let f=FN[n.n];
  if(!f){const k=Object.keys(FN).find(x=>x.toLowerCase()===n.n.toLowerCase());
    if(k)throw err('Function names are case-sensitive: use '+k+'( ).');
    throw err('"'+n.n+'" isn’t available in this practice console. Try: '+Object.keys(FN).join(', ')+'.');}
  if(n.args.length<f[0])throw err(n.n+' needs at least '+f[0]+' argument'+(f[0]>1?'s':'')+'.');
  return f[1](n.args,sc);
}
function runFx(src){const ast=parse(src);return ev(ast,[{Tickets:TICKETS,ThisItem:TICKETS[0]}]);}
function fmtVal(v){
  if(v===null)return '<span style="color:var(--muted)">Blank</span>';
  if(typeof v==='boolean')return String(v);
  if(typeof v==='number')return String(+v.toFixed(6));
  if(typeof v==='string')return '"'+esc(v)+'"';
  if(Array.isArray(v)){if(!v.length)return 'Empty table (0 rows)';return tableHtml(v)+`<div style="font-family:var(--body);font-size:12px;color:var(--muted);margin-top:4px">${v.length} row${v.length>1?'s':''}</div>`;}
  return tableHtml([v]);
}
function tableHtml(rows){const cols=Object.keys(rows[0]);return `<table class="t"><thead><tr>${cols.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td class="${typeof r[c]==='number'?'nm':''}">${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function mountFx(el){
  let cur=0;const solved=(S.fxSolved=S.fxSolved||[]);
  el.innerHTML=`<section class="console" aria-label="Power Fx practice console">
   <div class="console-head"><h3>Power Fx console</h3><div class="chips" id="fxChips"></div></div>
   <div class="goal" id="fxGoal"></div>
   <div class="fxbar"><span class="lbl">fx</span><input id="fxIn" spellcheck="false" autocomplete="off" aria-label="Power Fx formula" placeholder="Type a formula, then press Enter"></div>
   <div class="fx-actions"><button class="btn primary sm" id="fxRun">Run formula</button><button class="btn sm" id="fxHint">Hint</button><button class="btn sm ghost" id="fxSol">Show answer</button></div>
   <div class="out" id="fxOut" aria-live="polite"><span class="lab">Result</span><span style="color:var(--muted)">Run a formula to see its result.</span></div>
   <div class="verdict" id="fxV"></div>
   <details class="data"><summary>Sample data: the Tickets table (ThisItem is row 1)</summary><div class="tw">${tableHtml(TICKETS)}</div></details>
  </section>`;
  const chips=el.querySelector('#fxChips'),goal=el.querySelector('#fxGoal'),inp=el.querySelector('#fxIn'),out=el.querySelector('#fxOut'),v=el.querySelector('#fxV');
  function drawChips(){chips.innerHTML=FX_TASKS.map((t,i)=>`<button class="chip ${solved[i]?'solved':''}" aria-pressed="${i===cur}" data-i="${i}" aria-label="Challenge ${i+1}${solved[i]?', solved':''}">${solved[i]?'✓':i+1}</button>`).join('');chips.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{cur=+b.dataset.i;show();});}
  function show(){drawChips();goal.textContent=`Challenge ${cur+1} of ${FX_TASKS.length}: ${FX_TASKS[cur].goal}`;inp.value='';v.textContent='';v.className='verdict';out.className='out';out.innerHTML='<span class="lab">Result</span><span style="color:var(--muted)">Run a formula to see its result.</span>';}
  function run(){
    const src=inp.value.trim();if(!src){inp.focus();return;}
    try{const r=runFx(src);out.className='out';out.innerHTML='<span class="lab">Result</span>'+fmtVal(r);
      const t=FX_TASKS[cur];const ok=!Array.isArray(r)&&(typeof r!=='object'||r===null)&&eq(r,t.exp)&&typeof r===typeof t.exp;
      if(ok){v.className='verdict ok';v.textContent=cur<FX_TASKS.length-1?'Correct. Pick the next challenge.':'Correct. You finished every challenge.';out.className='out ok';solved[cur]=true;save();drawChips();}
      else{v.className='verdict no';v.textContent='The formula ran, but the expected result is '+(typeof t.exp==='string'?'"'+t.exp+'"':t.exp)+'. Adjust it and run again.';}
    }catch(e){out.className='out err';out.innerHTML='<span class="lab">Error</span>'+esc(e instanceof FxErr?e.message:'Something in the formula couldn’t be read. Check brackets and quotes.');v.textContent='';v.className='verdict';}
  }
  el.querySelector('#fxRun').onclick=run;
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();run();}});
  el.querySelector('#fxHint').onclick=()=>{v.className='verdict';v.textContent='Hint: '+FX_TASKS[cur].hint;};
  el.querySelector('#fxSol').onclick=()=>{inp.value=FX_TASKS[cur].sol;v.className='verdict';v.textContent='Answer filled in. Run it, then try changing it.';inp.focus();};
  show();
}

/* ---------------- Flow builder ---------------- */
const TRIGGERS=[
 {id:'forms',c:'Microsoft Forms',n:'When a new response is submitted'},
 {id:'recur',c:'Schedule',n:'Recurrence'},
 {id:'dvrow',c:'Dataverse',n:'When a row is added, modified or deleted'},
 {id:'manual',c:'Manual',n:'Manually trigger a flow'},
 {id:'mail',c:'Office 365 Outlook',n:'When a new email arrives'},
 {id:'spitem',c:'SharePoint',n:'When an item is created'}
];
const ACTIONS=[
 {id:'formsget',c:'Microsoft Forms',n:'Get response details'},
 {id:'dvadd',c:'Dataverse',n:'Add a new row'},
 {id:'dvlist',c:'Dataverse',n:'List rows'},
 {id:'cond',c:'Control',n:'Condition'},
 {id:'each',c:'Control',n:'Apply to each'},
 {id:'appr',c:'Approvals',n:'Start and wait for an approval'},
 {id:'teams',c:'Microsoft Teams',n:'Post message in a chat or channel'},
 {id:'email',c:'Office 365 Outlook',n:'Send an email (V2)'},
 {id:'spcreate',c:'SharePoint',n:'Create item'}
];
const SCENARIOS=[
 {text:'When a student submits the “Report an IT problem” Microsoft Form, save it as a Ticket in Dataverse, then email the help desk.',trig:'forms',acts:['formsget','dvadd','email'],why:'The Forms trigger only gives a response ID, so “Get response details” must come first to read the answers.'},
 {text:'Every morning at 8:00, email the help desk manager the list of tickets from Dataverse.',trig:'recur',acts:['dvlist','email'],why:'A timetable means the Recurrence trigger. List rows fetches the tickets before the email is sent.'},
 {text:'When a new ticket row is added in Dataverse, check whether it is High priority. If it is, ask the manager to approve overtime, then post the result in Teams.',trig:'dvrow',acts:['cond','appr','teams'],why:'The Dataverse trigger fires on the new row. The Condition checks priority before the approval and the Teams post.'}
];
function mountFlow(el){
  let cur=0;const st=SCENARIOS.map(()=>({trig:'',acts:[]}));const solved=(S.flowSolved=S.flowSolved||[]);
  el.innerHTML=`<section class="console" aria-label="Flow builder practice">
   <div class="console-head"><h3>Flow Builder</h3><div class="chips" id="fbChips"></div></div>
   <div class="fb-body">
    <div class="fb-scn" id="fbScn"></div>
    <div><label class="fl" for="fbTrig">1. Choose the trigger</label><select id="fbTrig"></select></div>
    <div><span class="fl" style="font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600;display:block;margin-bottom:6px">2. Add actions in order</span><div class="palette" id="fbPal"></div></div>
    <div><span class="fl" style="font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600;display:block;margin-bottom:6px">Your flow</span><div class="canvas" id="fbCanvas"></div></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary sm" id="fbCheck">Check my flow</button><button class="btn sm" id="fbReset">Clear</button><button class="btn sm ghost" id="fbShow">Show answer</button></div>
    <div class="verdict" id="fbV" style="padding:0" aria-live="polite"></div>
   </div></section>`;
  const $=s=>el.querySelector(s);
  $('#fbTrig').innerHTML='<option value="">Select a trigger…</option>'+TRIGGERS.map(t=>`<option value="${t.id}">${esc(t.c)}: ${esc(t.n)}</option>`).join('');
  $('#fbPal').innerHTML=ACTIONS.map(a=>`<button class="pal" data-id="${a.id}"><small>${esc(a.c)}</small>+ ${esc(a.n)}</button>`).join('');
  function chips(){$('#fbChips').innerHTML=SCENARIOS.map((_,i)=>`<button class="chip ${solved[i]?'solved':''}" aria-pressed="${i===cur}" data-i="${i}" aria-label="Scenario ${i+1}${solved[i]?', solved':''}">${solved[i]?'✓':i+1}</button>`).join('');$('#fbChips').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{cur=+b.dataset.i;draw();$('#fbV').textContent='';});}
  function draw(){
    chips();const s=st[cur];$('#fbScn').textContent=`Scenario ${cur+1}: ${SCENARIOS[cur].text}`;$('#fbTrig').value=s.trig;
    const tr=TRIGGERS.find(t=>t.id===s.trig);
    let h=tr?`<div class="node trig"><span class="tag">Trigger</span><div class="body"><small>${esc(tr.c)}</small>${esc(tr.n)}</div></div>`:`<div class="empty">Choose a trigger to start the flow.</div>`;
    s.acts.forEach((id,i)=>{const a=ACTIONS.find(x=>x.id===id);h+=`<div class="conn"></div><div class="node"><span class="tag">Step ${i+1}</span><div class="body"><small>${esc(a.c)}</small>${esc(a.n)}</div><button class="x" data-i="${i}" aria-label="Remove ${esc(a.n)}">×</button></div>`;});
    if(tr&&!s.acts.length)h+=`<div class="conn"></div><div class="empty">Add actions from the list above.</div>`;
    $('#fbCanvas').innerHTML=h;
    $('#fbCanvas').querySelectorAll('.x').forEach(b=>b.onclick=()=>{s.acts.splice(+b.dataset.i,1);draw();});
  }
  $('#fbTrig').onchange=e=>{st[cur].trig=e.target.value;draw();};
  $('#fbPal').querySelectorAll('.pal').forEach(b=>b.onclick=()=>{if(st[cur].acts.length>=6)return;st[cur].acts.push(b.dataset.id);draw();});
  $('#fbReset').onclick=()=>{st[cur]={trig:'',acts:[]};$('#fbV').textContent='';draw();};
  $('#fbShow').onclick=()=>{const sc=SCENARIOS[cur];st[cur]={trig:sc.trig,acts:[...sc.acts]};draw();const v=$('#fbV');v.className='verdict';v.textContent=sc.why;};
  $('#fbCheck').onclick=()=>{
    const s=st[cur],sc=SCENARIOS[cur],v=$('#fbV');
    if(!s.trig){v.className='verdict no';v.textContent='Every flow needs exactly one trigger. Choose one first.';return;}
    if(s.trig!==sc.trig){v.className='verdict no';v.textContent='The trigger doesn’t match the event in the scenario. Ask: what starts this process?';return;}
    const ok=s.acts.length===sc.acts.length&&s.acts.every((a,i)=>a===sc.acts[i]);
    if(ok){v.className='verdict ok';v.textContent='Correct. '+sc.why;solved[cur]=true;save();chips();}
    else{const missing=sc.acts.filter(a=>!s.acts.includes(a)).length,extra=s.acts.filter(a=>!sc.acts.includes(a)).length;
      v.className='verdict no';v.textContent=missing?`Trigger is right. You’re missing ${missing} action${missing>1?'s':''}.`:extra?'Trigger is right, but some actions aren’t needed for this scenario.':'Right actions, wrong order. Think about which data each step needs first.';}
  };
  draw();
}


/* ================= Power BI add-on: dataset + simulators ================= */
const BI=(function(){
  function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
  const pad=n=>String(n).padStart(2,'0');
  function make(){
    const r=mulberry32(900),pick=a=>a[Math.floor(r()*a.length)],rows=[];
    for(let i=0;i<60;i++){
      const month=1+Math.floor(i/10),day=1+Math.floor(r()*27);
      const cat=1+Math.floor(r()*4),pr=pick(['Low','Medium','Medium','High']);
      const p=r();
      const status=month<=4?(p<.85?'Closed':p<.95?'In progress':'Open'):(p<.5?'Closed':p<.75?'In progress':'Open');
      let hours=null,closed='';
      if(status==='Closed'){
        hours=Math.round((pr==='High'?2+r()*14:pr==='Medium'?4+r()*30:8+r()*60)*10)/10;
        const d=new Date(Date.UTC(2026,month-1,day));d.setUTCHours(d.getUTCHours()+Math.ceil(hours)+Math.floor(r()*12));
        closed=d.toISOString().slice(0,10);
      }
      rows.push({TicketID:1001+i,CreatedDate:`2026-${pad(month)}-${pad(day)}`,ClosedDate:closed,CategoryID:cat,Priority:pr,Status:status,HoursToResolve:hours,Campus:pick(['North','South','City']),AssignedTo:pick(['Anu','Rahul','Meera','Joseph'])});
    }
    return rows;
  }
  const TICKETS=make();
  const CATEGORIES=[{CategoryID:1,Name:'Network',Team:'Infrastructure'},{CategoryID:2,Name:'Hardware',Team:'Infrastructure'},{CategoryID:3,Name:'Accounts',Team:'Identity'},{CategoryID:4,Name:'Software',Team:'Applications'}];
  function toCsv(rows){const cols=Object.keys(rows[0]);return [cols.join(',')].concat(rows.map(r=>cols.map(c=>{const v=r[c]===null?'':String(r[c]);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(','))).join('\n');}
  function dirtyCsv(){const d=TICKETS.map(r=>Object.assign({},r));d[4].Campus=d[4].Campus.toLowerCase();d[17].Campus=' '+d[17].Campus+' ';d[33].Campus=d[33].Campus.toLowerCase()+' ';d[48].Priority=d[48].Priority.toLowerCase();return toCsv(d);}

  /* ---------- Dataset copy panel ---------- */
  function copyText(text,btn,ta){
    const done=()=>{const o=btn.textContent;btn.textContent='Copied';setTimeout(()=>btn.textContent=o,1600);};
    const fallback=()=>{ta.focus();ta.select();btn.textContent='Selected: press Ctrl+C';};
    try{navigator.clipboard.writeText(text).then(done,fallback);}catch(e){fallback();}
  }
  function mountDataset(el){
    const files=[{name:'tickets.csv',text:dirtyCsv(),rows:TICKETS.length,note:'60 tickets from January to June 2026. A few Campus and Priority values are deliberately messy for the cleaning lab.'},
                 {name:'categories.csv',text:toCsv(CATEGORIES),rows:CATEGORIES.length,note:'4 categories and the support team for each.'}];
    el.innerHTML=`<section class="console" aria-label="Course dataset"><div class="console-head"><h3>Course dataset</h3><span style="font-size:13px;color:var(--muted)">Campus Help Desk tickets</span></div>
    <div class="fb-body"><p style="margin:0;font-size:14.5px">Copy each file, paste it into Notepad (or any text editor) and save it with the exact name shown, as UTF-8. Then load both into Power BI Desktop with <strong>Get data &gt; Text/CSV</strong>.</p>
    ${files.map((f,i)=>`<div class="dsf"><div class="dsf-h"><div><strong class="mono">${f.name}</strong><span>${f.rows} rows · ${esc(f.note)}</span></div><button class="btn sm primary" data-i="${i}">Copy ${f.name}</button></div><textarea id="ds-${i}" readonly rows="6" spellcheck="false" aria-label="${f.name} contents">${esc(f.text)}</textarea></div>`).join('')}
    </div></section>`;
    el.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>{const i=+b.dataset.i;copyText(files[i].text,b,el.querySelector('#ds-'+i));});
  }

  /* ---------- DAX engine ---------- */
  class DaxErr extends Error{}
  const E=m=>new DaxErr(m);
  const TABLES={Tickets:TICKETS,Categories:CATEGORIES};
  function tokenize(s){
    const t=[];let i=0;
    while(i<s.length){
      const c=s[i];
      if(/\s/.test(c)){i++;continue;}
      if(/[0-9]/.test(c)){let j=i;while(j<s.length&&/[0-9.]/.test(s[j]))j++;t.push({k:'num',v:parseFloat(s.slice(i,j))});i=j;continue;}
      if(c==='"'||c==='“'||c==='”'){let j=i+1,v='';for(;;){if(j>=s.length)throw E('A text value is missing its closing quote (").');const cj=s[j];if(cj==='"'||cj==='”'||cj==='“'){if(s[j+1]==='"'){v+='"';j+=2;continue;}break;}v+=cj;j++;}t.push({k:'str',v});i=j+1;continue;}
      if(c==="'"){const j=s.indexOf("'",i+1);if(j<0)throw E("A table name in single quotes is missing its closing quote.");t.push({k:'id',v:s.slice(i+1,j)});i=j+1;continue;}
      if(c==='['){const j=s.indexOf(']',i+1);if(j<0)throw E('A column name is missing its closing bracket ].');t.push({k:'col',v:s.slice(i+1,j)});i=j+1;continue;}
      if(/[A-Za-z_]/.test(c)){let j=i;while(j<s.length&&/[A-Za-z0-9_.]/.test(s[j]))j++;t.push({k:'id',v:s.slice(i,j)});i=j;continue;}
      const two=s.substr(i,2);
      if(['<>','<=','>=','&&','||','=='].includes(two)){t.push({k:'op',v:two==='=='?'=':two});i+=2;continue;}
      if('&+-*/=<>(),'.includes(c)){t.push({k:'op',v:c});i++;continue;}
      throw E('Unexpected character "'+c+'".');
    }
    t.push({k:'eof',v:'end'});return t;
  }
  function parse(src){
    const t=tokenize(src);let p=0;
    const isOp=v=>t[p].k==='op'&&t[p].v===v;
    const expect=v=>{if(!isOp(v))throw E('Expected "'+v+'" but found "'+t[p].v+'".');p++;};
    function orE(){let l=andE();while(isOp('||')){p++;l={t:'or',l,r:andE()};}return l;}
    function andE(){let l=cmp();while(isOp('&&')){p++;l={t:'and',l,r:cmp()};}return l;}
    function cmp(){let l=cat();while(t[p].k==='op'&&['=','<>','<','>','<=','>='].includes(t[p].v)){const o=t[p++].v;l={t:'bin',o,l,r:cat()};}return l;}
    function cat(){let l=add();while(isOp('&')){p++;l={t:'bin',o:'&',l,r:add()};}return l;}
    function add(){let l=mul();while(isOp('+')||isOp('-')){const o=t[p++].v;l={t:'bin',o,l,r:mul()};}return l;}
    function mul(){let l=un();while(isOp('*')||isOp('/')){const o=t[p++].v;l={t:'bin',o,l,r:un()};}return l;}
    function un(){if(isOp('-')){p++;return{t:'neg',e:un()};}return prim();}
    function prim(){
      const k=t[p++];
      if(k.k==='num'||k.k==='str')return{t:'lit',v:k.v};
      if(k.k==='op'&&k.v==='('){const e=orE();expect(')');return e;}
      if(k.k==='col')return{t:'colref',table:null,col:k.v};
      if(k.k==='id'){
        if(isOp('(')){p++;const args=[];if(!isOp(')')){args.push(orE());while(isOp(',')){p++;args.push(orE());}}expect(')');return{t:'call',n:k.v.toUpperCase(),raw:k.v,args};}
        if(t[p].k==='col'){const c=t[p++].v;return{t:'colref',table:k.v,col:c};}
        const up=k.v.toUpperCase();if(up==='TRUE')return{t:'lit',v:true};if(up==='FALSE')return{t:'lit',v:false};
        return{t:'tbl',name:k.v};
      }
      if(k.k==='eof')throw E('The formula ends too early. Check for a missing value or closing bracket.');
      throw E('Unexpected "'+k.v+'".');
    }
    const e=orE();if(t[p].k!=='eof')throw E('Unexpected "'+t[p].v+'" after the end of the formula.');return e;
  }
  const tname=n=>{const k=Object.keys(TABLES).find(x=>x.toLowerCase()===n.toLowerCase());if(!k)throw E('There is no table named "'+n+'". Tables: Tickets, Categories.');return k;};
  function checkCol(table,col){const r=TABLES[table][0];if(!(col in r)){const k=Object.keys(r).find(x=>x.toLowerCase()===col.toLowerCase());if(k)return k;throw E(table+' has no column ['+col+']. Columns: '+Object.keys(r).join(', ')+'.');}return col;}
  function resolveCol(n,ctx){
    if(n.table){const t=tname(n.table);return{table:t,col:checkCol(t,n.col)};}
    const inRow=Object.keys(ctx.row);for(const t of inRow){if(n.col in TABLES[t][0])return{table:t,col:n.col};}
    for(const t of Object.keys(TABLES)){if(n.col in TABLES[t][0])return{table:t,col:n.col};}
    throw E('Unknown column ['+n.col+']. Write it as Table[Column], for example Tickets[Priority].');
  }
  const num=v=>{if(v===null)return 0;if(typeof v==='boolean')return v?1:0;if(typeof v==='number')return v;const x=Number(v);if(v===''||isNaN(x))throw E('Cannot convert "'+v+'" to a number.');return x;};
  const str=v=>v===null?'':typeof v==='number'?String(+v.toFixed(10)):String(v);
  const bool=v=>v===null?false:typeof v==='boolean'?v:typeof v==='number'?v!==0:(()=>{throw E('Expected TRUE or FALSE, but got text "'+v+'".');})();
  function eq(a,b){if(a===null&&b===null)return true;if(a===null)return b===''||b===0||b===false;if(b===null)return a===''||a===0||a===false;if(typeof a==='number'||typeof b==='number')return Math.abs(num(a)-num(b))<1e-9;return String(a).toLowerCase()===String(b).toLowerCase();}
  function cmpv(a,b){if(typeof a==='string'&&typeof b==='string')return a.localeCompare(b);return num(a)-num(b);}
  function visible(table,ctx){
    let rows=TABLES[table].filter(r=>ctx.filters.every(f=>f.table!==table||f.pred(r)));
    if(table==='Tickets'&&ctx.filters.some(f=>f.table==='Categories')){const ids=new Set(visible('Categories',ctx).map(c=>c.CategoryID));rows=rows.filter(r=>ids.has(r.CategoryID));}
    return rows;
  }
  const withRow=(ctx,table,row)=>({filters:ctx.filters,row:Object.assign({},ctx.row,{[table]:row})});
  function tableOf(n,ctx){
    if(n.t==='tbl'){const t=tname(n.name);return{table:t,rows:visible(t,ctx)};}
    if(n.t==='call'&&n.n==='FILTER'){if(n.args.length<2)throw E('FILTER(table, condition) needs two arguments.');const src=tableOf(n.args[0],ctx);return{table:src.table,rows:src.rows.filter(r=>bool(ev(n.args[1],withRow(ctx,src.table,r))))};}
    if(n.t==='call'&&n.n==='ALL'){const a=n.args[0];if(!a)throw E('ALL needs a table or column.');if(a.t==='tbl'){const t=tname(a.name);return{table:t,rows:TABLES[t].slice()};}if(a.t==='colref'){const c=resolveCol(a,ctx);return{table:c.table,rows:TABLES[c.table].slice()};}throw E('ALL takes a table or a column.');}
    if(n.t==='call'&&n.n==='VALUES'){const a=n.args[0];if(a&&a.t==='tbl'){const t=tname(a.name);return{table:t,rows:visible(t,ctx)};}}
    throw E('This argument must be a table, such as Tickets or FILTER(Tickets, ...).');
  }
  function colsIn(n,out){if(!n||typeof n!=='object')return out;if(n.t==='colref')out.push(n);for(const k of ['l','r','e'])if(n[k])colsIn(n[k],out);if(n.args)n.args.forEach(a=>colsIn(a,out));return out;}
  function calculate(n,ctx){
    let filters=ctx.filters.slice();
    for(const [t,row] of Object.entries(ctx.row)){filters.push({table:t,key:'ct|'+t,pred:r=>r===row});}
    const outer={filters:ctx.filters,row:ctx.row};
    const add=[];
    for(const m of n.args.slice(1)){
      if(m.t==='call'&&m.n==='ALL'){const a=m.args[0];
        if(a&&a.t==='tbl'){const t=tname(a.name);filters=filters.filter(f=>!(f.table===t||(t==='Tickets'&&f.table==='Categories')));}
        else if(a&&a.t==='colref'){const c=resolveCol(a,outer);filters=filters.filter(f=>f.key!==c.table+'|'+c.col);}
        else throw E('ALL takes a table or a column.');
        continue;}
      if(m.t==='call'&&m.n==='KEEPFILTERS'){const inner=m.args[0];const cs=colsIn(inner,[]).map(c=>resolveCol(c,outer));const ts=[...new Set(cs.map(c=>c.table))];if(ts.length!==1)throw E('KEEPFILTERS needs a condition on one table.');add.push({table:ts[0],key:'kf|'+Math.random(),pred:r=>bool(ev(inner,{filters:[],row:{[ts[0]]:r}}))});continue;}
      if(m.t==='call'&&(m.n==='FILTER'||m.n==='VALUES')||m.t==='tbl'){const tb=tableOf(m,outer);const set=new Set(tb.rows);add.push({table:tb.table,key:'f|'+Math.random(),pred:r=>set.has(r)});continue;}
      const cs=colsIn(m,[]);
      if(!cs.length)throw E('Each CALCULATE filter must reference a column, like Tickets[Priority] = "High".');
      const rc=cs.map(c=>resolveCol(c,outer));const ts=[...new Set(rc.map(c=>c.table))];
      if(ts.length>1)throw E('A single CALCULATE filter can only use columns from one table. Split it into separate filters.');
      const keys=[...new Set(rc.map(c=>c.table+'|'+c.col))];
      filters=filters.filter(f=>!keys.includes(f.key));
      add.push({table:ts[0],key:keys.length===1?keys[0]:'b|'+Math.random(),pred:r=>bool(ev(m,{filters:[],row:{[ts[0]]:r}}))});
    }
    return ev(n.args[0],{filters:filters.concat(add),row:{}});
  }
  function aggCol(n,ctx,fn){const a=n.args[0];if(!a||a.t!=='colref')throw E(n.n+' takes one column, for example '+n.n+'(Tickets[HoursToResolve]).');const c=resolveCol(a,ctx);return fn(visible(c.table,ctx).map(r=>r[c.col]));}
  function iter(n,ctx,fn){if(n.args.length<2)throw E(n.n+'(table, expression) needs two arguments.');const tb=tableOf(n.args[0],ctx);return fn(tb.rows.map(r=>ev(n.args[1],withRow(ctx,tb.table,r))));}
  const nn=v=>v.filter(x=>x!==null&&x!=='');
  const sum=v=>{const a=nn(v);return a.length?a.reduce((x,y)=>x+num(y),0):null;};
  const avg=v=>{const a=nn(v);return a.length?a.reduce((x,y)=>x+num(y),0)/a.length:null;};
  const mx=v=>{const a=nn(v);return a.length?a.reduce((x,y)=>cmpv(x,y)>=0?x:y):null;};
  const mn=v=>{const a=nn(v);return a.length?a.reduce((x,y)=>cmpv(x,y)<=0?x:y):null;};
  function ev(n,ctx){
    switch(n.t){
      case 'lit':return n.v;
      case 'tbl':throw E('"'+n.name+'" is a table. Wrap it in a function such as COUNTROWS('+n.name+').');
      case 'colref':{const c=resolveCol(n,ctx);const row=ctx.row[c.table];
        if(row)return row[c.col]??null;
        if(c.table==='Categories'&&ctx.row.Tickets)throw E('Inside a Tickets row, reach Categories columns with RELATED(Categories['+c.col+']).');
        throw E(c.table+'['+c.col+'] needs a row context. Aggregate it (for example with SUM or DISTINCTCOUNT), or use it inside SUMX or FILTER.');}
      case 'neg':return n.e?(()=>{const v=ev(n.e,ctx);return v===null?null:-num(v);})():0;
      case 'and':return bool(ev(n.l,ctx))&&bool(ev(n.r,ctx));
      case 'or':return bool(ev(n.l,ctx))||bool(ev(n.r,ctx));
      case 'bin':{const a=ev(n.l,ctx),b=ev(n.r,ctx);switch(n.o){
        case '&':return str(a)+str(b);
        case '+':return a===null&&b===null?null:num(a)+num(b);
        case '-':return a===null&&b===null?null:num(a)-num(b);
        case '*':return a===null||b===null?null:num(a)*num(b);
        case '/':if(num(b)===0)throw E('Division by zero. Use DIVIDE(numerator, denominator) to return BLANK safely.');return a===null?null:num(a)/num(b);
        case '=':return eq(a,b);case '<>':return !eq(a,b);
        case '<':return cmpv(a??0,b??0)<0;case '>':return cmpv(a??0,b??0)>0;case '<=':return cmpv(a??0,b??0)<=0;case '>=':return cmpv(a??0,b??0)>=0;}}
      case 'call':return call(n,ctx);
    }
  }
  function call(n,ctx){
    const A=n.args,need=k=>{if(A.length<k)throw E(n.n+' needs at least '+k+' argument'+(k>1?'s':'')+'.');};
    switch(n.n){
      case 'COUNTROWS':need(1);return tableOf(A[0],ctx).rows.length||null;
      case 'SUM':return aggCol(n,ctx,sum);
      case 'AVERAGE':return aggCol(n,ctx,avg);
      case 'MIN':return aggCol(n,ctx,mn);
      case 'MAX':return aggCol(n,ctx,mx);
      case 'COUNT':return aggCol(n,ctx,v=>nn(v).length||null);
      case 'DISTINCTCOUNT':return aggCol(n,ctx,v=>new Set(v.map(x=>x===''?null:x)).size||null);
      case 'SUMX':return iter(n,ctx,sum);
      case 'AVERAGEX':return iter(n,ctx,avg);
      case 'MAXX':return iter(n,ctx,mx);
      case 'MINX':return iter(n,ctx,mn);
      case 'COUNTX':return iter(n,ctx,v=>nn(v).length||null);
      case 'DIVIDE':{need(2);const a=ev(A[0],ctx),b=ev(A[1],ctx);if(b===null||num(b)===0)return A[2]?ev(A[2],ctx):null;return a===null?null:num(a)/num(b);}
      case 'CALCULATE':need(1);return calculate(n,ctx);
      case 'RELATED':{need(1);const a=A[0];if(a.t!=='colref')throw E('RELATED takes a column, for example RELATED(Categories[Name]).');const c=resolveCol(a,ctx);if(c.table!=='Categories')throw E('RELATED follows the relationship to Categories, the “one” side.');const tr=ctx.row.Tickets;if(!tr)throw E('RELATED needs a row of Tickets, so use it inside FILTER(Tickets, ...) or SUMX(Tickets, ...).');const cr=CATEGORIES.find(x=>x.CategoryID===tr.CategoryID);return cr?cr[c.col]:null;}
      case 'IF':{need(2);return bool(ev(A[0],ctx))?ev(A[1],ctx):(A[2]?ev(A[2],ctx):null);}
      case 'AND':need(2);return bool(ev(A[0],ctx))&&bool(ev(A[1],ctx));
      case 'OR':need(2);return bool(ev(A[0],ctx))||bool(ev(A[1],ctx));
      case 'NOT':need(1);return !bool(ev(A[0],ctx));
      case 'BLANK':return null;
      case 'TRUE':return true;case 'FALSE':return false;
      case 'ISBLANK':need(1);{const v=ev(A[0],ctx);return v===null||v==='';}
      case 'ROUND':{need(2);const v=ev(A[0],ctx);if(v===null)return null;const f=Math.pow(10,num(ev(A[1],ctx)));return Math.round(num(v)*f)/f;}
      case 'ABS':need(1);{const v=ev(A[0],ctx);return v===null?null:Math.abs(num(v));}
      case 'FILTER':case 'ALL':case 'VALUES':throw E(n.n+' returns a table. Wrap it, for example COUNTROWS('+n.raw+'(...)).');
      default:throw E(n.raw+'( ) isn’t available in this practice console. Try COUNTROWS, SUM, AVERAGE, DISTINCTCOUNT, DIVIDE, CALCULATE, FILTER, ALL, SUMX, RELATED or IF.');
    }
  }
  function run(src,slicers){
    const filters=[];
    if(slicers.campus)filters.push({table:'Tickets',key:'Tickets|Campus',pred:r=>r.Campus===slicers.campus});
    if(slicers.cat)filters.push({table:'Categories',key:'Categories|Name',pred:r=>r.Name===slicers.cat});
    return ev(parse(src),{filters,row:{}});
  }
  function fmt(v){
    if(v===null||v===undefined)return '(Blank)';
    if(typeof v==='boolean')return v?'TRUE':'FALSE';
    if(typeof v==='number'){const r=Math.abs(v)<1&&v!==0?v.toLocaleString('en-US',{maximumFractionDigits:4}):v.toLocaleString('en-US',{maximumFractionDigits:2});return r;}
    return String(v);
  }
  const same=(a,b)=>(a===null&&b===null)||(typeof a==='number'&&typeof b==='number'&&Math.abs(a-b)<1e-6)||(a===b);

  const DAX_SETS={
    dax1:[
      {goal:'Count every ticket.',sol:'COUNTROWS(Tickets)',hint:'COUNTROWS takes a table and counts its rows.'},
      {goal:'Total hours spent resolving tickets.',sol:'SUM(Tickets[HoursToResolve])',hint:'SUM takes one column: SUM(Table[Column]). Blanks are ignored.'},
      {goal:'Average hours to resolve a ticket.',sol:'AVERAGE(Tickets[HoursToResolve])',hint:'AVERAGE ignores blank values, so open tickets don’t count.'},
      {goal:'How many different staff members have tickets assigned?',sol:'DISTINCTCOUNT(Tickets[AssignedTo])',hint:'DISTINCTCOUNT counts unique values in a column.'},
      {goal:'Hours over a 24-hour target, added up ticket by ticket.',sol:'SUMX(FILTER(Tickets, Tickets[HoursToResolve] > 24), Tickets[HoursToResolve] - 24)',hint:'SUMX(table, expression) calculates the expression for each row, then sums. Filter to tickets over 24 hours first.'},
      {goal:'Count tickets in the Hardware category, using RELATED inside FILTER.',sol:'COUNTROWS(FILTER(Tickets, RELATED(Categories[Name]) = "Hardware"))',hint:'Inside FILTER(Tickets, ...) each row is a ticket. RELATED(Categories[Name]) fetches its category name.'},
      {goal:'Average hours per closed ticket, using DIVIDE so an empty result can’t cause an error.',sol:'DIVIDE(SUM(Tickets[HoursToResolve]), COUNTROWS(FILTER(Tickets, Tickets[Status] = "Closed")))',hint:'DIVIDE(numerator, denominator) returns BLANK instead of an error when the denominator is 0 or blank.'}
    ],
    dax2:[
      {goal:'Count High priority tickets.',sol:'CALCULATE(COUNTROWS(Tickets), Tickets[Priority] = "High")',hint:'CALCULATE(expression, filter). The filter here is Tickets[Priority] = "High".'},
      {goal:'Count closed tickets in the Network category.',sol:'CALCULATE(COUNTROWS(Tickets), Tickets[Status] = "Closed", Categories[Name] = "Network")',hint:'Add two filters, separated by a comma. The Categories filter flows to Tickets through the relationship.'},
      {goal:'Share of tickets that are High priority (a decimal between 0 and 1).',sol:'DIVIDE(CALCULATE(COUNTROWS(Tickets), Tickets[Priority] = "High"), COUNTROWS(Tickets))',hint:'Divide the High count (CALCULATE) by the count of all tickets in the current context.'},
      {goal:'Tickets across all campuses, ignoring the Campus slicer.',sol:'CALCULATE(COUNTROWS(Tickets), ALL(Tickets[Campus]))',hint:'ALL(Tickets[Campus]) removes the filter on that one column. Try changing the Campus slicer: the result should not move.'},
      {goal:'The selected campus’s share of all tickets.',sol:'DIVIDE(COUNTROWS(Tickets), CALCULATE(COUNTROWS(Tickets), ALL(Tickets[Campus])))',hint:'Numerator: tickets in the current context. Denominator: the same count with the Campus filter removed.'},
      {goal:'Count North campus tickets, whatever the Campus slicer says.',sol:'CALCULATE(COUNTROWS(Tickets), Tickets[Campus] = "North")',hint:'A column filter in CALCULATE replaces any existing filter on that same column.'},
      {goal:'Count tickets that were closed in under 8 hours, using FILTER.',sol:'CALCULATE(COUNTROWS(Tickets), FILTER(Tickets, Tickets[Status] = "Closed" && Tickets[HoursToResolve] < 8))',hint:'Open tickets have a blank HoursToResolve, and DAX treats BLANK as 0 in a comparison. Check Status too.'},
      {goal:'Predict, then check: how many categories are visible when you filter Tickets to High priority?',sol:'CALCULATE(COUNTROWS(Categories), Tickets[Priority] = "High")',hint:'Write CALCULATE(COUNTROWS(Categories), ...) with a filter on Tickets.',note:'The answer is always 4. The relationship filters from Categories to Tickets only (single direction), so a filter on Tickets never reaches Categories.'}
    ]
  };
  const CAMPUSES=['North','South','City'];
  function mountDax(el,setId){
    const tasks=DAX_SETS[setId];let cur=0;
    const solved=(S.daxSolved=S.daxSolved||{})[setId]=(S.daxSolved[setId]||[]);
    const sl={campus:'',cat:''};
    el.innerHTML=`<section class="console dax" aria-label="DAX practice console">
     <div class="console-head"><h3>DAX console</h3><div class="chips" id="dxChips"></div></div>
     <div class="slicers"><span class="sl-lab">Slicers (filter context)</span>
       <label>Campus <select id="dxCampus"><option value="">All</option>${CAMPUSES.map(c=>`<option>${c}</option>`).join('')}</select></label>
       <label>Category <select id="dxCat"><option value="">All</option>${CATEGORIES.map(c=>`<option>${c.Name}</option>`).join('')}</select></label></div>
     <div class="goal" id="dxGoal"></div>
     <div class="fxbar"><span class="lbl">Measure =</span><input id="dxIn" spellcheck="false" autocomplete="off" aria-label="DAX measure" placeholder="Type a DAX expression, then press Enter"></div>
     <div class="fx-actions"><button class="btn primary sm" id="dxRun">Run measure</button><button class="btn sm" id="dxHint">Hint</button><button class="btn sm ghost" id="dxSol">Show answer</button></div>
     <div class="cardvis" id="dxOut" aria-live="polite"><span class="cv-val">–</span><span class="cv-lab" id="dxCtx"></span></div>
     <div class="verdict" id="dxV"></div>
     <details class="data"><summary>Model: Categories (1) → Tickets (*) on CategoryID, single direction. Show the data</summary><div class="tw">${tbl(CATEGORIES)}</div><div class="tw">${tbl(TICKETS)}</div></details>
    </section>`;
    const $=s=>el.querySelector(s),inp=$('#dxIn'),v=$('#dxV'),out=$('#dxOut');
    function ctxLabel(){const parts=[];if(sl.campus)parts.push('Campus = '+sl.campus);if(sl.cat)parts.push('Category = '+sl.cat);return parts.length?'Filter context: '+parts.join(', '):'Filter context: no slicers applied';}
    function chips(){$('#dxChips').innerHTML=tasks.map((t,i)=>`<button class="chip ${solved[i]?'solved':''}" aria-pressed="${i===cur}" data-i="${i}" aria-label="Challenge ${i+1}${solved[i]?', solved':''}">${solved[i]?'✓':i+1}</button>`).join('');$('#dxChips').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{cur=+b.dataset.i;show();});}
    function show(){chips();$('#dxGoal').textContent=`Challenge ${cur+1} of ${tasks.length}: ${tasks[cur].goal}`;inp.value='';v.textContent='';v.className='verdict';out.className='cardvis';out.querySelector('.cv-val').textContent='–';$('#dxCtx').textContent=ctxLabel();}
    function exec(){
      const src=inp.value.trim();if(!src){inp.focus();return;}
      $('#dxCtx').textContent=ctxLabel();
      try{
        const r=run(src,sl);
        if(r!==null&&typeof r==='object')throw E('The expression returned a table. Wrap it in COUNTROWS or another aggregation.');
        out.className='cardvis';out.querySelector('.cv-val').textContent=fmt(r);
        const t=tasks[cur];
        const exp=run(t.sol,sl);
        if(!same(r,exp)){v.className='verdict no';v.textContent='The measure ran. The expected result in this filter context is '+fmt(exp)+'. Adjust it and run again.';return;}
        const ctxs=[{campus:'',cat:''}].concat(CAMPUSES.map(c=>({campus:c,cat:''})),CATEGORIES.map(c=>({campus:'',cat:c.Name})));
        const robust=ctxs.every(c=>{try{return same(run(src,c),run(t.sol,c));}catch(e){return false;}});
        if(!robust){v.className='verdict no';v.textContent='Right for this slicer selection, but wrong when the slicers change. Avoid typing fixed numbers: build the logic in DAX.';return;}
        out.className='cardvis ok';v.className='verdict ok';v.textContent='Correct in every filter context.'+(t.note?' '+t.note:'')+(cur<tasks.length-1?' Try changing the slicers, then pick the next challenge.':'');
        solved[cur]=true;save();chips();
      }catch(e){out.className='cardvis err';out.querySelector('.cv-val').textContent='Error';v.className='verdict no';v.textContent=e instanceof DaxErr?e.message:'Something in the expression couldn’t be read. Check brackets, commas and quotes.';}
    }
    $('#dxRun').onclick=exec;inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();exec();}});
    $('#dxCampus').onchange=e=>{sl.campus=e.target.value;$('#dxCtx').textContent=ctxLabel();if(inp.value.trim())exec();};
    $('#dxCat').onchange=e=>{sl.cat=e.target.value;$('#dxCtx').textContent=ctxLabel();if(inp.value.trim())exec();};
    $('#dxHint').onclick=()=>{v.className='verdict';v.textContent='Hint: '+tasks[cur].hint;};
    $('#dxSol').onclick=()=>{inp.value=tasks[cur].sol;v.className='verdict';v.textContent='Answer filled in. Run it, then change the slicers and run again.';inp.focus();};
    show();
  }
  function tbl(rows){const cols=Object.keys(rows[0]);return `<table class="t"><thead><tr>${cols.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td class="${typeof r[c]==='number'?'nm':''}">${r[c]===null?'':esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}

  /* ---------- Star schema builder ---------- */
  const SS_TABLES=[
    {n:'Sales',k:'fact',d:'One row per item sold: OrderDate, ShipDate, ProductKey, CustomerKey, StoreKey, Quantity, Amount.',w:'Sales records events with numbers you add up (Quantity, Amount) and many rows: a fact table.'},
    {n:'Product',k:'dim',d:'One row per product: ProductKey, Name, Category, Colour.',w:'Product describes things you filter and group by: a dimension.'},
    {n:'Customer',k:'dim',d:'One row per customer: CustomerKey, Name, City, Segment.',w:'Customer describes who bought: a dimension.'},
    {n:'Date',k:'dim',d:'One row per calendar day: Date, Month, Quarter, Year.',w:'A date table is a dimension used to slice facts by time.'},
    {n:'Store',k:'dim',d:'One row per store: StoreKey, Name, Region.',w:'Store describes where the sale happened: a dimension.'},
    {n:'Returns',k:'fact',d:'One row per returned item: ReturnDate, ProductKey, Quantity, RefundAmount.',w:'Returns records events with amounts: a second fact table.'}
  ];
  const SS_RELS=[
    {from:'Product[ProductKey]',to:'Sales[ProductKey]',card:'1:*',dir:'Single',act:'Active',w:'Each product appears once in Product and many times in Sales.'},
    {from:'Customer[CustomerKey]',to:'Sales[CustomerKey]',card:'1:*',dir:'Single',act:'Active',w:'One customer, many sales. Single direction keeps filters flowing from dimension to fact.'},
    {from:'Date[Date]',to:'Sales[OrderDate]',card:'1:*',dir:'Single',act:'Active',w:'The main date relationship is active, so slicing by Date filters sales by order date.'},
    {from:'Date[Date]',to:'Sales[ShipDate]',card:'1:*',dir:'Single',act:'Inactive',w:'Only one relationship between two tables can be active. Date is a role-playing dimension here; use USERELATIONSHIP in a measure to use ShipDate.'},
    {from:'Store[StoreKey]',to:'Sales[StoreKey]',card:'1:*',dir:'Single',act:'Active',w:'One store, many sales.'},
    {from:'Product[ProductKey]',to:'Returns[ProductKey]',card:'1:*',dir:'Single',act:'Active',w:'Product filters both fact tables, so one slicer works for sales and returns.'}
  ];
  function mountStar(el){
    const st={k:{},r:SS_RELS.map(()=>({card:'',dir:'',act:''}))};let checked=false;
    el.innerHTML=`<section class="console" aria-label="Star schema builder"><div class="console-head"><h3>Star schema builder</h3><span style="font-size:13px;color:var(--muted)">A retail sales model</span></div>
     <div class="fb-body">
      <div><span class="fl2">1. Classify each table</span><div class="ss-tables" id="ssT"></div></div>
      <div><span class="fl2">2. Set up each relationship</span><div class="ss-rels" id="ssR"></div></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary sm" id="ssCheck">Check my model</button><button class="btn sm" id="ssReset">Clear</button></div>
      <div class="verdict" id="ssV" style="padding:0" aria-live="polite"></div>
     </div></section>`;
    const $=s=>el.querySelector(s);
    function mark(ok){return checked?`<span class="mk ${ok?'ok':'no'}" aria-label="${ok?'Correct':'Incorrect'}">${ok?'✓':'✗'}</span>`:'';}
    function draw(){
      $('#ssT').innerHTML=SS_TABLES.map((t,i)=>`<div class="ss-t ${st.k[i]||''}"><div><strong>${t.n}</strong>${mark(st.k[i]===t.k)}<small>${t.d}</small>${checked&&st.k[i]!==t.k?`<small class="ssw">${t.w}</small>`:''}</div><div class="seg" role="group" aria-label="${t.n} type"><button data-i="${i}" data-k="fact" aria-pressed="${st.k[i]==='fact'}">Fact</button><button data-i="${i}" data-k="dim" aria-pressed="${st.k[i]==='dim'}">Dimension</button></div></div>`).join('');
      $('#ssR').innerHTML=SS_RELS.map((r,i)=>{const s=st.r[i],ok=s.card===r.card&&s.dir===r.dir&&s.act===r.act;return `<div class="ss-r"><div class="ss-path"><span class="mono">${r.from}</span><span aria-hidden="true">→</span><span class="mono">${r.to}</span>${mark(ok)}</div>
        <div class="ss-sel"><select data-i="${i}" data-f="card" aria-label="Cardinality"><option value="">Cardinality…</option>${[['1:*','One-to-many (1:*)'],['1:1','One-to-one (1:1)'],['*:*','Many-to-many (*:*)']].map(o=>`<option value="${o[0]}" ${s.card===o[0]?'selected':''}>${o[1]}</option>`).join('')}</select>
        <select data-i="${i}" data-f="dir" aria-label="Cross-filter direction"><option value="">Direction…</option>${['Single','Both'].map(o=>`<option ${s.dir===o?'selected':''}>${o}</option>`).join('')}</select>
        <select data-i="${i}" data-f="act" aria-label="Active or inactive"><option value="">Status…</option>${['Active','Inactive'].map(o=>`<option ${s.act===o?'selected':''}>${o}</option>`).join('')}</select></div>
        ${checked&&!ok?`<small class="ssw">${r.w}</small>`:''}</div>`;}).join('');
      $('#ssT').querySelectorAll('.seg button').forEach(b=>b.onclick=()=>{st.k[b.dataset.i]=b.dataset.k;draw();});
      $('#ssR').querySelectorAll('select').forEach(sel=>sel.onchange=()=>{st.r[sel.dataset.i][sel.dataset.f]=sel.value;});
    }
    $('#ssCheck').onclick=()=>{checked=true;draw();
      const tOk=SS_TABLES.filter((t,i)=>st.k[i]===t.k).length,rOk=SS_RELS.filter((r,i)=>{const s=st.r[i];return s.card===r.card&&s.dir===r.dir&&s.act===r.act;}).length;
      const v=$('#ssV'),all=tOk===SS_TABLES.length&&rOk===SS_RELS.length;
      v.className='verdict '+(all?'ok':'no');
      v.textContent=all?'Correct. Two fact tables share four dimensions: a star schema. Single-direction one-to-many relationships are the default you should aim for.':`${tOk} of ${SS_TABLES.length} tables and ${rOk} of ${SS_RELS.length} relationships are right. Read the notes under each ✗ and try again.`;
      if(all){S.starSolved=true;save();}};
    $('#ssReset').onclick=()=>{st.k={};st.r=SS_RELS.map(()=>({card:'',dir:'',act:''}));checked=false;$('#ssV').textContent='';draw();};
    draw();
  }
  return {mountDataset,mountDax,mountStar,run,parse,DAX_SETS,TICKETS,CATEGORIES,dirtyCsv};
})();

function mountSorter(el,s,lid){
  const pick={};let checked=false;
  el.innerHTML=`<section class="console" aria-label="${esc(s.title)}"><div class="console-head"><h3>${esc(s.title)}</h3><span style="font-size:13px;color:var(--muted)">${s.items.length} scenarios</span></div>
  <div class="fb-body"><p style="margin:0">${esc(s.intro||'Choose the best option for each scenario.')}</p><ol class="sort-list" id="sl"></ol>
  <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary sm" id="sChk">Check answers</button><button class="btn sm" id="sRst">Clear</button></div><div class="verdict" id="sV" style="padding:0" aria-live="polite"></div></div></section>`;
  const draw=()=>{el.querySelector('#sl').innerHTML=s.items.map((it,i)=>{const ok=pick[i]===it.a;return `<li class="sort-i ${checked?(ok?'ok':'no'):''}"><p>${esc(it.t)}</p><select id="so-${lid}-${i}" data-i="${i}" aria-label="Answer for scenario ${i+1}"><option value="">Choose…</option>${s.options.map((o,j)=>`<option value="${j}" ${pick[i]===j?'selected':''}>${esc(o)}</option>`).join('')}</select>${checked?`<small>${ok?'✓ Correct. ':'✗ Best answer: '+esc(s.options[it.a])+'. '}${esc(it.w)}</small>`:''}</li>`;}).join('');
    el.querySelectorAll('#sl select').forEach(x=>x.onchange=()=>{pick[+x.dataset.i]=x.value===''?undefined:+x.value;});};
  el.querySelector('#sChk').onclick=()=>{checked=true;draw();const n=s.items.filter((it,i)=>pick[i]===it.a).length,v=el.querySelector('#sV');v.className='verdict '+(n===s.items.length?'ok':'no');v.textContent=n===s.items.length?'All correct.':`${n} of ${s.items.length} correct. Read the notes, then try the others again.`;if(n===s.items.length){S.sorters=S.sorters||{};S.sorters[lid]=true;save();}};
  el.querySelector('#sRst').onclick=()=>{for(const k in pick)delete pick[k];checked=false;el.querySelector('#sV').textContent='';draw();};
  draw();
}

function mount(el,widget,sorter,lessonId){
  if(!el)return;
  if(widget==='powerfx')mountFx(el);
  else if(widget==='flow')mountFlow(el);
  else if(widget==='dataset')BI.mountDataset(el);
  else if(widget==='star')BI.mountStar(el);
  else if(widget==='dax1'||widget==='dax2')BI.mountDax(el,widget);
  else if(widget==='sorter'&&sorter)mountSorter(el,sorter,lessonId);
}
window.AcademySims={mount:mount,runFx:runFx,BI:BI,FX_TASKS:FX_TASKS};
})();
