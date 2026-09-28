/* Flutter phone-screen mocks for Ralfiz Academy lessons.

   The renderer (FM) is copied from the standalone course app
   academy/content/sources/ralfiz-flutter-academy.html, unchanged except:
   - mountAll() finds the Academy's placeholders, <div class="mock-slot" data-mock="N">,
     and keeps their static fallback panel if a mock fails to render;
   - the "Predict the output" widget is not included (the converter turns it into HTML).

   The lesson page puts the lesson's mocks in <script type="application/json" id="lessonMocks">
   and this file mounts them into every .deep article: FlutterMocks.mountAll(root, mocks). */
(function(){
'use strict';
const FM=(function(){
  const e=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function hex(h){h=String(h||'#6750A4').replace('#','');if(h.length===3)h=h.split('').map(x=>x+x).join('');const n=parseInt(h,16);return [n>>16&255,n>>8&255,n&255];}
  function toHex(r,g,b){return '#'+[r,g,b].map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');}
  function mix(a,b,t){const x=hex(a),y=hex(b);return toHex(x[0]+(y[0]-x[0])*t,x[1]+(y[1]-x[1])*t,x[2]+(y[2]-x[2])*t);}
  function scheme(seed,dark){
    seed=seed||'#6750A4';
    if(!dark)return{primary:mix(seed,'#000000',.08),onPrimary:'#ffffff',pc:mix(seed,'#ffffff',.78),onPc:mix(seed,'#000000',.62),surface:mix(seed,'#ffffff',.965),surfC:mix(seed,'#ffffff',.9),surfCH:mix(seed,'#ffffff',.86),onSurface:'#1c1b1f',onSurfV:'#49454f',outline:mix(seed,'#79747e',.75),outlineV:mix(seed,'#cac4d0',.85),sec:mix(seed,'#ffffff',.84),onSec:mix(seed,'#000000',.6),error:'#b3261e',inverse:'#313033',onInverse:'#f4eff4'};
    return{primary:mix(seed,'#ffffff',.45),onPrimary:mix(seed,'#000000',.65),pc:mix(seed,'#000000',.55),onPc:mix(seed,'#ffffff',.8),surface:mix(seed,'#141218',.9),surfC:mix(seed,'#211f26',.88),surfCH:mix(seed,'#2b2930',.86),onSurface:'#e6e1e5',onSurfV:'#cac4d0',outline:'#938f99',outlineV:'#49454f',sec:mix(seed,'#332d41',.75),onSec:mix(seed,'#ffffff',.85),error:'#f2b8b5',inverse:'#e6e1e5',onInverse:'#313033'};
  }
  const TS={displayLarge:[57,400,64],displayMedium:[45,400,52],displaySmall:[36,400,44],headlineLarge:[32,400,40],headlineMedium:[28,400,36],headlineSmall:[24,400,32],titleLarge:[22,400,28],titleMedium:[16,500,24],titleSmall:[14,500,20],bodyLarge:[16,400,24],bodyMedium:[14,400,20],bodySmall:[12,400,16],labelLarge:[14,500,20],labelMedium:[12,500,16],labelSmall:[11,500,16]};
  const MA={start:'flex-start',center:'center',end:'flex-end',spaceBetween:'space-between',spaceAround:'space-around',spaceEvenly:'space-evenly'};
  const CA={start:'flex-start',center:'center',end:'flex-end',stretch:'stretch',baseline:'baseline'};
  let C;
  const col=v=>{if(!v)return null;if(v[0]==='#'||v.startsWith('rgb'))return v;return C[v]||v;};
  const ic=(name,size,color)=>`<span class="fm-ic" style="font-size:${size||24}px;${color?'color:'+col(color)+';':''}">${e(name)}</span>`;
  const pad=p=>p==null?'':Array.isArray(p)?p.map(x=>x+'px').join(' '):p+'px';
  function kids(n){return n.c||(n.child!=null?[n.child]:[]);}
  function r(n,ctx){
    if(n==null)return '';
    if(typeof n==='string'||typeof n==='number')return `<span class="fm-t" style="font-size:14px;line-height:20px">${e(n)}</span>`;
    const w=n.w,K=kids(n);
    switch(w){
      case 'Text':case 'text':{const s=TS[n.style||'bodyMedium']||TS.bodyMedium;return `<span class="fm-t" style="font-size:${s[0]}px;font-weight:${n.weight==='bold'?700:s[1]};line-height:${s[2]}px;${n.color?'color:'+col(n.color)+';':''}${n.align?'text-align:'+n.align+';display:block;':''}${n.italic?'font-style:italic;':''}${n.maxLines===1?'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;':''}">${e(n.t)}</span>`;}
      case 'Column':case 'Row':{const dir=w==='Row'?'row':'column';return `<div class="fm-flex" style="flex-direction:${dir};justify-content:${MA[n.main]||'flex-start'};align-items:${CA[n.cross]||'center'};${n.spacing?'gap:'+n.spacing+'px;':''}${n.fill?'flex:1;':''}${w==='Column'&&n.min!==true?'':''}">${K.map(k=>r(k,{dir})).join('')}</div>`;}
      case 'Wrap':return `<div class="fm-flex" style="flex-wrap:wrap;gap:${n.runSpacing||n.spacing||8}px ${n.spacing||8}px">${K.map(k=>r(k,{dir:'row'})).join('')}</div>`;
      case 'Expanded':case 'Flexible':return `<div style="flex:${n.flex||1} 1 0;min-width:0;min-height:0;display:flex;flex-direction:column">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Spacer':return `<div style="flex:${n.flex||1}"></div>`;
      case 'SizedBox':return `<div style="${n.width!=null?'width:'+n.width+'px;flex:none;':''}${n.height!=null?'height:'+n.height+'px;flex:none;':''}${n.expand?'width:100%;':''}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Padding':return `<div style="padding:${pad(n.p!=null?n.p:16)}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Center':return `<div class="fm-flex" style="justify-content:center;align-items:center;flex-direction:column;${n.fill!==false?'flex:1;width:100%;':''}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Align':return `<div class="fm-flex" style="width:100%;flex-direction:column;align-items:${({topLeft:'flex-start',centerLeft:'flex-start',bottomLeft:'flex-start',topRight:'flex-end',centerRight:'flex-end',bottomRight:'flex-end'})[n.align]||'center'}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Container':{const bg=n.gradient?`background:linear-gradient(${n.gradient.dir||'135deg'},${n.gradient.colors.map(col).join(',')});`:n.color?'background:'+col(n.color)+';':'';return `<div class="fm-box" style="${bg}${n.width!=null?'width:'+n.width+'px;flex:none;':''}${n.height!=null?'height:'+n.height+'px;':''}${n.p!=null?'padding:'+pad(n.p)+';':''}${n.m!=null?'margin:'+pad(n.m)+';':''}${n.radius!=null?'border-radius:'+(n.radius==='circle'?'50%':n.radius+'px')+';':''}${n.border?'border:'+(n.border.width||1)+'px solid '+col(n.border.color||'outlineV')+';':''}${n.shadow?'box-shadow:0 2px 6px rgba(0,0,0,.18);':''}${n.align==='center'?'display:flex;align-items:center;justify-content:center;':''}">${K.map(k=>r(k,ctx)).join('')}</div>`;}
      case 'Card':return `<div class="fm-card ${n.variant==='outlined'?'out':n.variant==='filled'?'fill':''}" style="${n.m!=null?'margin:'+pad(n.m)+';':''}">${n.p!=null?`<div style="padding:${pad(n.p)}">`:''}${K.map(k=>r(k,ctx)).join('')}${n.p!=null?'</div>':''}</div>`;
      case 'ListTile':{const lead=typeof n.leading==='string'?ic(n.leading,24,'onSurfV'):r(n.leading);const tr=typeof n.trailing==='string'?(/^[a-z_0-9]+$/.test(n.trailing)?ic(n.trailing,24,'onSurfV'):`<span class="fm-t" style="font-size:12px;color:${C.onSurfV}">${e(n.trailing)}</span>`):r(n.trailing);
        return `<div class="fm-lt ${n.selected?'sel':''}">${n.leading?`<div class="fm-lt-l">${lead}</div>`:''}<div class="fm-lt-m"><span class="fm-t" style="font-size:16px;line-height:24px">${e(n.title)}</span>${n.subtitle?`<span class="fm-t" style="font-size:14px;line-height:20px;color:${C.onSurfV}">${e(n.subtitle)}</span>`:''}</div>${n.trailing?`<div class="fm-lt-r">${tr}</div>`:''}</div>`;}
      case 'ListView':return `<div class="fm-list" style="${n.p!=null?'padding:'+pad(n.p)+';':''}${n.horizontal?'flex-direction:row;overflow:hidden;':''}${n.spacing?'gap:'+n.spacing+'px;':''}">${K.map((k,i)=>r(k,ctx)+(n.sep&&i<K.length-1?'<div class="fm-div"></div>':'')).join('')}</div>`;
      case 'GridView':return `<div class="fm-grid" style="grid-template-columns:repeat(${n.cols||2},1fr);gap:${n.spacing!=null?n.spacing:8}px;${n.p!=null?'padding:'+pad(n.p)+';':''}">${K.map(k=>`<div style="${n.ratio?'aspect-ratio:'+n.ratio+';':''}display:flex;flex-direction:column;min-width:0">${r(k,ctx)}</div>`).join('')}</div>`;
      case 'Icon':return ic(n.i,n.size,n.color||'onSurfV');
      case 'IconButton':return `<span class="fm-ib ${n.variant||''}">${ic(n.i,24,n.variant==='filled'?'onPrimary':n.color||'onSurfV')}</span>`;
      case 'ElevatedButton':case 'FilledButton':case 'OutlinedButton':case 'TextButton':case 'FilledTonalButton':{const cls={ElevatedButton:'el',FilledButton:'fi',OutlinedButton:'ou',TextButton:'tx',FilledTonalButton:'to'}[w];return `<span class="fm-btn ${cls} ${n.disabled?'dis':''} ${n.expand?'exp':''}">${n.icon?ic(n.icon,18):''}${e(n.t)}</span>`;}
      case 'FloatingActionButton':return `<span class="fm-fab ${n.t?'ext':''}">${ic(n.i||'add',24,'onPc')}${n.t?`<span>${e(n.t)}</span>`:''}</span>`;
      case 'TextField':return `<div class="fm-tf ${n.variant==='filled'?'filled':''} ${n.error?'err':''} ${n.focused?'foc':''}">${n.label?`<span class="fm-tf-l ${n.value||n.focused?'up':''}">${e(n.label)}</span>`:''}<div class="fm-tf-in">${n.icon?ic(n.icon,22,'onSurfV'):''}<span class="fm-tf-v ${n.value?'':'hint'}">${n.value?(n.obscure?'••••••••':e(n.value)):e(n.hint||'')}</span>${n.suffix?ic(n.suffix,22,'onSurfV'):''}</div>${n.error?`<span class="fm-tf-h err">${e(n.error)}</span>`:n.helper?`<span class="fm-tf-h">${e(n.helper)}</span>`:''}</div>`;
      case 'Checkbox':return `<label class="fm-row"><span class="fm-cb ${n.v?'on':''}">${n.v?ic('check',16,'onPrimary'):''}</span>${n.label?`<span class="fm-t" style="font-size:14px">${e(n.label)}</span>`:''}</label>`;
      case 'Radio':return `<label class="fm-row"><span class="fm-rd ${n.v?'on':''}"></span>${n.label?`<span class="fm-t" style="font-size:14px">${e(n.label)}</span>`:''}</label>`;
      case 'Switch':return `<label class="fm-row" style="justify-content:space-between;width:100%">${n.label?`<span class="fm-t" style="font-size:16px">${e(n.label)}</span>`:''}<span class="fm-sw ${n.v?'on':''}"><i></i></span></label>`;
      case 'Slider':return `<div class="fm-sl"><i style="width:${(n.v||0)*100}%"></i><b style="left:${(n.v||0)*100}%"></b></div>`;
      case 'Chip':return `<span class="fm-chip ${n.selected?'sel':''}">${n.selected?ic('check',18):n.icon?ic(n.icon,18):''}${e(n.t)}</span>`;
      case 'Badge':return `<span class="fm-badge-w">${r(n.child)}<span class="fm-badge">${e(n.t||'')}</span></span>`;
      case 'CircleAvatar':return `<span class="fm-av" style="width:${(n.r||20)*2}px;height:${(n.r||20)*2}px;font-size:${(n.r||20)*.8}px;${n.color?'background:'+col(n.color)+';':''}">${n.i?ic(n.i,(n.r||20)*1.1,'onPc'):e(n.t||'')}</span>`;
      case 'Image':return `<div class="fm-img" style="height:${n.height||160}px;${n.width?'width:'+n.width+'px;flex:none;':''}border-radius:${n.radius||0}px;background:linear-gradient(135deg,${col(n.c1||'pc')},${col(n.c2||'sec')})">${ic(n.i||'image',Math.min(48,(n.height||160)/3),'onPc')}${n.label?`<span>${e(n.label)}</span>`:''}</div>`;
      case 'Divider':return '<div class="fm-div"></div>';
      case 'Stack':return `<div class="fm-stack" style="${n.height?'height:'+n.height+'px;':''}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Positioned':return `<div style="position:absolute;${['top','left','right','bottom'].filter(s=>n[s]!=null).map(s=>s+':'+n[s]+'px').join(';')}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'CircularProgressIndicator':return `<span class="fm-cpi"></span>`;
      case 'LinearProgressIndicator':return `<div class="fm-lpi"><i style="width:${(n.v==null?.4:n.v)*100}%"></i></div>`;
      case 'SegmentedButton':return `<div class="fm-seg">${(n.items||[]).map((t,i)=>`<span class="${i===(n.sel||0)?'on':''}">${i===(n.sel||0)?ic('check',16):''}${e(t)}</span>`).join('')}</div>`;
      case 'TabBar':return `<div class="fm-tabs">${(n.tabs||[]).map((t,i)=>`<span class="${i===(n.sel||0)?'on':''}">${e(t)}</span>`).join('')}</div>`;
      case 'Placeholder':return `<div class="fm-ph" style="height:${n.height||100}px"></div>`;
      case 'Opacity':return `<div style="opacity:${n.v==null?.5:n.v}">${K.map(k=>r(k,ctx)).join('')}</div>`;
      case 'Hero':case 'GestureDetector':case 'InkWell':case 'SafeArea':case 'Builder':return K.map(k=>r(k,ctx)).join('');
      case 'Code':return `<pre class="fm-code">${e(n.t)}</pre>`;
      default:return `<div class="fm-unk">${e(w||'?')}</div>`;
    }
  }
  function screen(s){
    const sc=(s&&(s.w==='Scaffold'||(!s.w&&(s.appBar||s.body||s.nav||s.fab))))?s:{w:'Scaffold',body:s};
    const ab=sc.appBar;
    const bar=ab?`<div class="fm-ab ${ab.large?'lg':''}" style="${ab.color?'background:'+col(ab.color)+';':''}">${ab.leading?`<span class="fm-ib">${ic(ab.leading,24,ab.fg||'onSurface')}</span>`:''}<span class="fm-ab-t" style="${ab.center?'text-align:center;':''}${ab.fg?'color:'+col(ab.fg)+';':''}">${e(ab.title||'')}</span>${(ab.actions||[]).map(a=>`<span class="fm-ib">${ic(a,24,ab.fg||'onSurfV')}</span>`).join('')}</div>${ab.bottom?r(ab.bottom):''}`:'';
    const nav=sc.nav?`<div class="fm-nav">${sc.nav.items.map((it,i)=>`<span class="${i===(sc.nav.sel||0)?'on':''}"><b>${ic(it.i,24)}</b><small>${e(it.t)}</small></span>`).join('')}</div>`:'';
    const fab=sc.fab?`<div class="fm-fab-w ${sc.nav?'nav':''} ${sc.fabCenter?'c':''}">${r(Object.assign({w:'FloatingActionButton'},sc.fab))}</div>`:'';
    const snack=sc.snackBar?`<div class="fm-snack ${sc.nav?'nav':''}"><span>${e(sc.snackBar.t)}</span>${sc.snackBar.action?`<b>${e(sc.snackBar.action)}</b>`:''}</div>`:'';
    const dlg=sc.dialog?`<div class="fm-scrim"><div class="fm-dlg">${sc.dialog.icon?`<div style="text-align:center">${ic(sc.dialog.icon,24,'primary')}</div>`:''}<div class="fm-dlg-t">${e(sc.dialog.title||'')}</div><div class="fm-dlg-c">${typeof sc.dialog.content==='string'?e(sc.dialog.content):r(sc.dialog.content)}</div><div class="fm-dlg-a">${(sc.dialog.actions||[]).map(a=>`<span>${e(a)}</span>`).join('')}</div></div></div>`:'';
    const sheet=sc.sheet?`<div class="fm-scrim"><div class="fm-sheet"><i></i>${r(sc.sheet)}</div></div>`:'';
    const drawer=sc.drawer?`<div class="fm-scrim"><div class="fm-drawer">${r(sc.drawer)}</div></div>`:'';
    return `<div class="fm-status"><span>9:41</span><span>${ic('signal_cellular_alt',14)}${ic('wifi',14)}${ic('battery_full',14)}</span></div>${bar}<div class="fm-body" style="${sc.bg?'background:'+col(sc.bg)+';':''}">${r(sc.body)}</div>${nav}${fab}${snack}${dlg}${sheet}${drawer}`;
  }
  function vars(){return Object.entries(C).map(([k,v])=>`--fm-${k}:${v}`).join(';');}
  function render(m){
    C=scheme(m.seed||'#6750A4',!!m.dark);
    return `<div class="fm-phone ${m.dark?'dk':''}" style="${vars()}"><div class="fm-scr">${screen(m.screen)}</div></div>`;
  }
  function mount(el,mock,idx){
    const frames=mock.frames||[{label:'',screen:mock.screen}];let cur=0;
    el.innerHTML=`<figure class="fm-demo"><div class="fm-demo-h"><div><span class="fm-demo-k">Screen ${idx+1}</span><strong>${e(mock.title||'')}</strong></div>${frames.length>1?`<div class="fm-fr-w"><button class="btn sm fm-play" aria-label="Play through the states">▶ Play</button><div class="fm-frames" role="tablist">${frames.map((f,i)=>`<button role="tab" data-i="${i}" aria-selected="${i===0}">${e(f.label||('State '+(i+1)))}</button>`).join('')}</div></div>`:''}</div>
      <div class="fm-demo-b"><div class="fm-stage"></div>${mock.code?`<div class="fm-codecol"><div class="fm-code-h"><span>${e(mock.file||'main.dart')}</span><button class="btn sm fm-copy">Copy</button></div><pre class="code fm-src"><code>${e(mock.code)}</code></pre></div>`:''}</div>
      ${mock.caption?`<figcaption>${e(mock.caption)}</figcaption>`:''}</figure>`;
    const stage=el.querySelector('.fm-stage');
    const RM=(()=>{try{return matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(x){return false;}})();
    const show=(i,anim)=>{cur=i;stage.innerHTML=render(Object.assign({},mock,{screen:frames[i].screen,dark:frames[i].dark!=null?frames[i].dark:mock.dark}));el.querySelectorAll('.fm-frames button').forEach(b=>b.setAttribute('aria-selected',String(+b.dataset.i===i)));
      if(anim&&!RM){const sc=stage.querySelector('.fm-scr');if(sc&&sc.animate)sc.animate([{opacity:.15,transform:'scale(.985)'},{opacity:1,transform:'none'}],{duration:380,easing:'ease-out'});}};
    let timer=null;const pb=el.querySelector('.fm-play');
    const stop=()=>{clearTimeout(timer);timer=null;if(pb){pb.textContent='▶ Play';pb.setAttribute('aria-label','Play through the states');}};
    const step=()=>{if(cur>=frames.length-1){stop();return;}show(cur+1,true);timer=setTimeout(step,1900);};
    if(pb)pb.onclick=()=>{if(timer){stop();return;}if(cur>=frames.length-1)show(0,true);pb.textContent='❚❚ Pause';pb.setAttribute('aria-label','Pause');timer=setTimeout(step,1300);};
    el.querySelectorAll('.fm-frames button').forEach(b=>b.onclick=()=>{stop();show(+b.dataset.i,true);});
    const cp=el.querySelector('.fm-copy');
    if(cp)cp.onclick=()=>{const pre=el.querySelector('.fm-src');try{navigator.clipboard.writeText(mock.code).then(()=>{cp.textContent='Copied';setTimeout(()=>cp.textContent='Copy',1500);},()=>sel(pre));}catch(x){sel(pre);}};
    function sel(pre){const r=document.createRange();r.selectNodeContents(pre);const s=getSelection();s.removeAllRanges();s.addRange(r);cp.textContent='Selected: press Ctrl+C';}
    show(0);
  }
  function mountAll(root,mocks){
    if(!mocks||!mocks.length)return;
    const slots=[...root.querySelectorAll('.mock-slot[data-mock]')];
    const used=new Set();
    // Academy: the slot holds the no-JavaScript panel; put it back if a mock fails to render.
    slots.forEach(s=>{const i=+s.dataset.mock;if(mocks[i]){const keep=s.innerHTML;try{mount(s,mocks[i],i);used.add(i);}catch(x){s.innerHTML=keep;if(window.console)console.error(x);}}});
    const rest=mocks.map((m,i)=>i).filter(i=>!used.has(i));
    if(rest.length){const box=document.createElement('section');box.className='fm-more';box.innerHTML='<h3>Screen examples</h3>';rest.forEach(i=>{const d=document.createElement('div');box.appendChild(d);mount(d,mocks[i],i);});root.appendChild(box);}
  }
  return {render,mount,mountAll};
})();
window.FlutterMocks=FM;
function boot(){
  const data=document.getElementById('lessonMocks');
  if(!data)return;
  let mocks;
  try{mocks=JSON.parse(data.textContent);}catch(x){return;}
  document.querySelectorAll('.deep').forEach(root=>FM.mountAll(root,mocks));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
