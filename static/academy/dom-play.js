/* Live JavaScript / DOM playgrounds for Ralfiz Academy lessons.

   The renderer (JSP) is copied unchanged from the standalone course app
   academy/content/sources/ralfiz-dom-academy.html. Each playground's HTML, CSS
   and JavaScript run in an iframe sandboxed without allow-same-origin, so the
   code has an opaque origin and cannot reach this page, its cookies or the
   student's session; the frame talks back only through postMessage.

   The lesson page puts the lesson's playgrounds in
   <script type="application/json" id="lessonPlays"> and this file mounts them
   into the <div class="play-slot" data-play="N"> placeholders of every .deep
   article, which hold a static code panel for readers without JavaScript. */
(function(){
'use strict';
const JSP=(()=>{
const e=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const sp=(c,t)=>`<span class="h-${c}">${e(t)}</span>`;

/* ---------- syntax highlighting ---------- */
const KW=new Set('break case catch class const continue debugger default delete do else export extends finally for function if import in instanceof let new return super switch this throw try typeof var void while with yield async await of static get set from as'.split(' '));
const LIT=new Set('true false null undefined NaN Infinity'.split(' '));
function hlJS(s){
  let o='',i=0,prev='';const n=s.length;
  while(i<n){
    const c=s[i];let m;
    if(c==='/'&&s[i+1]==='/'){let j=s.indexOf('\n',i);if(j<0)j=n;o+=sp('c',s.slice(i,j));i=j;continue;}
    if(c==='/'&&s[i+1]==='*'){let j=s.indexOf('*/',i+2);j=j<0?n:j+2;o+=sp('c',s.slice(i,j));i=j;continue;}
    if(c==='"'||c==="'"){let j=i+1;while(j<n&&s[j]!==c&&s[j]!=='\n'){if(s[j]==='\\')j++;j++;}j=Math.min(j+1,n);o+=sp('s',s.slice(i,j));i=j;prev='v';continue;}
    if(c==='`'){let j=i+1,seg='`';
      while(j<n&&s[j]!=='`'){
        if(s[j]==='\\'){seg+=s.slice(j,j+2);j+=2;continue;}
        if(s[j]==='$'&&s[j+1]==='{'){o+=sp('s',seg);seg='';let d=1,k=j+2;while(k<n){if(s[k]==='{')d++;else if(s[k]==='}'){d--;if(!d)break;}k++;}
          o+=sp('p','${')+hlJS(s.slice(j+2,k))+(k<n?sp('p','}'):'');j=k+1;continue;}
        seg+=s[j];j++;}
      if(j<n)seg+='`';o+=sp('s',seg);i=j+1;prev='v';continue;}
    const r=s.slice(i,i+400);
    if(c==='/'&&prev!=='v'){m=r.match(/^\/(?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n[])+\/[dgimsuyv]*/);if(m){o+=sp('r',m[0]);i+=m[0].length;prev='v';continue;}}
    if((m=r.match(/^(?:0[xXbBoO][\da-fA-F_]+n?|\d[\d_]*(?:\.\d*)?(?:[eE][+-]?\d+)?n?|\.\d+(?:[eE][+-]?\d+)?)/))){o+=sp('n',m[0]);i+=m[0].length;prev='v';continue;}
    if((m=r.match(/^#?[A-Za-z_$][\w$]*/))){const w=m[0];let cls='';const after=s.slice(i+w.length,i+w.length+40);
      if(s[i-1]==='.'){cls=/^\s*\(/.test(after)?'f':'pr';}
      else if(KW.has(w))cls='k';else if(LIT.has(w))cls='l';else if(/^\s*\(/.test(after)||/^\s*=\s*(?:async\s*)?(?:\([^()]*\)|[\w$]+)\s*=>/.test(after))cls='f';else if(/^[A-Z]/.test(w))cls='t';
      o+=cls?sp(cls,w):e(w);i+=w.length;prev=(cls==='k'&&w!=='this'&&w!=='super')?'k':'v';continue;}
    if(/\s/.test(c)){o+=c;i++;continue;}
    o+=e(c);prev=(c===')'||c===']')?'v':'o';i++;
  }
  return o;
}
function hlCSS(s){
  const re=/(\/\*[\s\S]*?\*\/)|("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(@[\w-]+)|(--?[A-Za-z][\w-]*|[A-Za-z][\w-]*)(?=\s*:[^{};]*[;}])|(#[\da-fA-F]{3,8}\b)|(-?(?:\d+\.?\d*|\.\d+)(?:%|[a-zA-Z]+)?)|([{}])|(![a-z]+)/g;
  let o='',last=0,m;
  while((m=re.exec(s))){o+=e(s.slice(last,m.index));const t=m[0];
    o+=m[1]?sp('c',t):m[2]?sp('s',t):m[3]?sp('k',t):m[4]?sp('pr',t):m[5]?sp('n',t):m[6]?sp('n',t):m[7]?sp('p',t):sp('k',t);last=re.lastIndex;}
  return o+e(s.slice(last));
}
function hlHTML(s){
  const re=/(<!--[\s\S]*?-->)|(<!doctype[^>]*>)|<(\/?)([A-Za-z][\w-]*)((?:\s+[^\s=>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>/gi;
  let o='',last=0,m;
  while((m=re.exec(s))){
    o+=e(s.slice(last,m.index));
    if(m[1]||m[2]){o+=sp('c',m[0]);last=re.lastIndex;continue;}
    const attrs=(m[5]||'').replace(/(\s+)([^\s=>\/]+)(?:(\s*=\s*)("[^"]*"|'[^']*'|[^\s>]+))?/g,(x,ws,name,eq,val)=>'\u0001'+ws+'\u0002'+name+'\u0003'+(eq?eq+'\u0004'+val+'\u0005':''));
    const at=e(attrs).replace(/\u0001([\s\S]*?)\u0002([\s\S]*?)\u0003/g,'$1<span class="h-a">$2</span>').replace(/\u0004([\s\S]*?)\u0005/g,'<span class="h-s">$1</span>');
    o+=`<span class="h-p">&lt;${m[3]}</span><span class="h-tag">${e(m[4])}</span>${at}<span class="h-p">${m[6]}&gt;</span>`;
    last=re.lastIndex;
    const tag=m[4].toLowerCase();
    if(!m[3]&&(tag==='script'||tag==='style')){
      const close=s.toLowerCase().indexOf('</'+tag,last);const end=close<0?s.length:close;
      o+=tag==='script'?hlJS(s.slice(last,end)):hlCSS(s.slice(last,end));last=end;re.lastIndex=end;}
  }
  return o+e(s.slice(last));
}
function hlJSON(s){return s.replace(/("(?:\\.|[^"\\])*")(\s*:)?|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(true|false|null)\b|([^"\d\-tfn]+|.)/g,(x,str,colon,num,lit,other)=>str?(colon?sp('pr',str)+e(colon):sp('s',str)):num?sp('n',num):lit?sp('l',lit):e(x));}
function hlBash(s){return s.split('\n').map(l=>/^\s*#/.test(l)?sp('c',l):l.replace(/^(\s*)(\$ )?(\S+)(.*)$/,(x,a,p,cmd,rest)=>e(a)+(p?sp('c',p):'')+sp('f',cmd)+e(rest).replace(/(\s)(--?[\w-]+)/g,'$1<span class="h-k">$2</span>'))).join('\n');}
function hl(src,lang){lang=(lang||'js').toLowerCase();
  return lang==='html'||lang==='xml'||lang==='svg'?hlHTML(src):lang==='css'?hlCSS(src):lang==='json'?hlJSON(src):lang==='bash'||lang==='sh'||lang==='shell'?hlBash(src):lang==='text'||lang==='txt'?e(src):hlJS(src);}
function guess(src){const t=src.trimStart();if(/^(<!doctype|<[a-z])/i.test(t))return 'html';if(/^[{\[]/.test(t)&&/^\s*[{\[][\s\S]*[}\]]\s*$/.test(src)&&!/[;=]|=>|function/.test(src))return 'json';if(/^(\$ |npm |npx |node |git |cd |mkdir )/m.test(t)&&!/[;{}]\s*$/m.test(t))return 'bash';if(/^[.#:@*a-z][^{;=()]*\{[\s\S]*:[\s\S]*;/i.test(t)&&!/=>|function|const |let /.test(src))return 'css';return 'js';}
function hlAll(root){root.querySelectorAll('pre.code:not([data-hl])').forEach(p=>{const c=p.querySelector('code')||p;const src=c.textContent;const lang=p.dataset.lang||guess(src);c.innerHTML=hl(src,lang);p.dataset.hl=lang;p.classList.add('jp-hlpre');});}

/* ---------- Node-style inspect (serialised into the sandbox, so it must be self-contained) ---------- */
function INSPECT(){
  const BREAK=80,COMPACT=3,MAXARR=100,MAXSTR=10000;
  const idRe=/^[A-Za-z_$][\w$]*$/;
  const q=s=>{let quote="'";if(s.includes("'")){if(!s.includes('"'))quote='"';else if(!s.includes('`')&&!s.includes('${'))quote='`';}
    const esc=s.replace(/[\\\n\t\r\b\f\v\0]/g,c=>({'\\':'\\\\','\n':'\\n','\t':'\\t','\r':'\\r','\b':'\\b','\f':'\\f','\v':'\\v','\0':'\\0'})[c]);
    return quote+(quote==="'"?esc.replace(/'/g,"\\'"):esc)+quote;};
  const isEl=v=>typeof Node!=='undefined'&&v instanceof Node;
  const elShort=n=>{if(n.nodeType===1){let s=n.tagName.toLowerCase();if(n.id)s+='#'+n.id;const cl=typeof n.className==='string'?n.className.trim():'';if(cl)s+='.'+cl.split(/\s+/).join('.');return s;}if(n.nodeType===3)return '#text';if(n.nodeType===9)return '#document';if(n.nodeType===8)return '#comment';if(n.nodeType===11)return '#document-fragment';return n.nodeName;};
  const elLong=n=>{if(n.nodeType===1){const oh=n.outerHTML;if(oh.length<=120)return oh;const open=oh.slice(0,oh.indexOf('>')+1);return open+'…</'+n.tagName.toLowerCase()+'>';}if(n.nodeType===3)return '#text '+JSON.stringify(n.textContent.length>60?n.textContent.slice(0,60)+'…':n.textContent);if(n.nodeType===9)return '#document';return elShort(n);};
  function ctorName(v){let p=v;while(p){const d=Object.getOwnPropertyDescriptor(p,'constructor');if(d&&typeof d.value==='function'&&d.value.name)return d.value.name;p=Object.getPrototypeOf(p);}return null;}
  function fnBase(v){const src=Function.prototype.toString.call(v);if(/^class[\s{]/.test(src)){const sup=Object.getPrototypeOf(v);return '[class '+(v.name||'(anonymous)')+(sup&&sup!==Function.prototype&&sup.name?' extends '+sup.name:'')+']';}
    let t='Function';const cn=v.constructor&&v.constructor.name;if(cn==='AsyncFunction'||cn==='GeneratorFunction'||cn==='AsyncGeneratorFunction')t=cn;return v.name?'['+t+': '+v.name+']':'['+t+' (anonymous)]';}
  function fmtKey(k){if(typeof k==='symbol')return '['+k.toString()+']';return idRe.test(k)?k:q(k);}
  function groupArrayElements(ctx,output,value){
    let totalLength=0,maxLength=0,i=0;let outputLength=output.length;if(ctx.extra)outputLength--;
    const sep=2,dataLen=new Array(outputLength);
    for(;i<outputLength;i++){const len=output[i].length;dataLen[i]=len;totalLength+=len+sep;if(maxLength<len)maxLength=len;}
    const actualMax=maxLength+sep;
    if(actualMax*3+ctx.indentationLvl<BREAK&&(totalLength/actualMax>5||maxLength<=6)){
      const averageBias=Math.sqrt(actualMax-totalLength/output.length);const biasedMax=Math.max(actualMax-3-averageBias,1);
      const columns=Math.min(Math.round(Math.sqrt(2.5*biasedMax*outputLength)/biasedMax),Math.floor((BREAK-ctx.indentationLvl)/actualMax),COMPACT*4,15);
      if(columns<=1)return output;
      const tmp=[],maxLineLength=[];
      for(let i=0;i<columns;i++){let lineLength=0;for(let j=i;j<output.length;j+=columns)if(dataLen[j]>lineLength)lineLength=dataLen[j];maxLineLength.push(lineLength+sep);}
      let padStart=true;if(value!==undefined){for(let i=0;i<output.length;i++){if(typeof value[i]!=='number'&&typeof value[i]!=='bigint'){padStart=false;break;}}}
      for(let i=0;i<outputLength;i+=columns){const max=Math.min(i+columns,outputLength);let str='',j=i;
        for(;j<max-1;j++){const s=output[j]+', ';str+=padStart?s.padStart(maxLineLength[j-i]):s.padEnd(maxLineLength[j-i]);}
        str+=padStart?output[j].padStart(maxLineLength[j-i]-sep):output[j];tmp.push(str);}
      if(ctx.extra)tmp.push(output[outputLength]);
      return tmp;}
    return output;
  }
  function reduce(ctx,output,base,braces,isArr,recurseTimes,value){
    const entries=output.length;
    if(isArr&&entries>6)output=groupArrayElements(ctx,output,value);
    if(ctx.currentDepth-recurseTimes<COMPACT&&entries===output.length){
      const start=output.length+ctx.indentationLvl+braces[0].length+base.length+10;
      let total=output.length+start;for(const o of output)total+=o.length;
      if(total<=BREAK&&(base===''||!base.includes('\n'))){const joined=output.join(', ');if(!joined.includes('\n'))return (base?base+' ':'')+braces[0]+' '+joined+' '+braces[1];}
    }
    const ind='\n'+' '.repeat(ctx.indentationLvl);
    return (base?base+' ':'')+braces[0]+ind+'  '+output.join(','+ind+'  ')+ind+braces[1];
  }
  function fmt(ctx,v,recurseTimes,typed){
    const t=typeof v;
    if(t==='string'){let s=v;let trunc='';if(s.length>MAXSTR){trunc='... '+(s.length-MAXSTR)+' more characters';s=s.slice(0,MAXSTR);}
      if(ctx.indentationLvl+s.length>16&&s.length>16&&s.includes('\n')&&recurseTimes>0&&false){}
      return q(s)+trunc;}
    if(t==='number')return Object.is(v,-0)?'-0':String(v);
    if(t==='bigint')return v+'n';
    if(t==='undefined'||t==='boolean'||v===null)return String(v);
    if(t==='symbol')return v.toString();
    if(ctx.seen.includes(v))return '[Circular *1]';
    return fmtRaw(ctx,v,recurseTimes,typed);
  }
  function fmtRaw(ctx,v,recurseTimes){
    const t=typeof v;
    if(t==='function'){const base=fnBase(v);const keys=Object.keys(v);if(!keys.length)return base;}
    if(isEl(v))return recurseTimes===0?elLong(v):elShort(v);
    const cn=ctorName(v);
    const proto=Object.getPrototypeOf(v);
    let braces,base='',isArr=false,keys,output=[],extraKeys=true,prefix='';
    const isNodeList=typeof NodeList!=='undefined'&&(v instanceof NodeList||v instanceof HTMLCollection);
    if(Array.isArray(v)||isNodeList){
      prefix=(cn!=='Array'&&cn)?(cn+'('+v.length+') '):'';if(!cn)prefix='[Array(' + v.length + '): null prototype] ';
      braces=[prefix+'[',']'];isArr=true;
      if(v.length===0&&(isNodeList||Object.keys(v).length===0))return braces[0]+']';
      if(recurseTimes>ctx.depth)return '[Array]';
    }else if(v instanceof Map){braces=[(cn||'Map')+'('+v.size+') {','}'];if(v.size===0&&!Object.keys(v).length)return braces[0]+'}';if(recurseTimes>ctx.depth)return '[Map]';}
    else if(v instanceof Set){braces=[(cn||'Set')+'('+v.size+') {','}'];if(v.size===0&&!Object.keys(v).length)return braces[0]+'}';if(recurseTimes>ctx.depth)return '[Set]';}
    else if(ArrayBuffer.isView(v)&&!(v instanceof DataView)){braces=[cn+'('+v.length+') [',']'];isArr=true;if(v.length===0)return braces[0]+']';}
    else if(t==='function'){base=fnBase(v);braces=['{','}'];}
    else if(v instanceof RegExp){base=String(v);if(!Object.keys(v).length)return base;braces=['{','}'];}
    else if(v instanceof Date){base=isNaN(v)?'Invalid Date':v.toISOString();if(!Object.keys(v).length)return base;braces=['{','}'];}
    else if(v instanceof Error){const nm=v.name||'Error';let s=nm+(v.message?': '+v.message:'');if(cn&&cn!==nm&&!s.startsWith(cn))s=cn+' ['+nm+']'+(v.message?': '+v.message:'');
      const st=typeof v.stack==='string'&&v.stack.includes('\n    at ')?v.stack.split('\n').filter(l=>/^\s+at /.test(l)).slice(0,0):[];
      base=recurseTimes>0?'['+s+']':s;const ks=Object.keys(v).filter(k=>k!=='stack'&&k!=='message');
      if(v.cause!==undefined&&!ks.includes('cause'))ks.push('cause');
      if(!ks.length)return base;braces=['{','}'];keys=ks;extraKeys=false;}
    else if(typeof Promise!=='undefined'&&v instanceof Promise){return 'Promise { <unknown> }';}
    else if(v instanceof WeakMap)return 'WeakMap { <items unknown> }';
    else if(v instanceof WeakSet)return 'WeakSet { <items unknown> }';
    else if(v instanceof Number||v instanceof String||v instanceof Boolean){return '['+(v instanceof Number?'Number':v instanceof String?'String':'Boolean')+': '+fmt(ctx,v.valueOf(),recurseTimes)+']';}
    else{
      if(proto===null)braces=['[Object: null prototype] {','}'];
      else if(cn&&cn!=='Object')braces=[cn+' {','}'];
      else braces=['{','}'];
      if(v[Symbol.toStringTag]&&typeof v[Symbol.toStringTag]==='string'&&cn!==v[Symbol.toStringTag])braces[0]=(cn||'Object')+' ['+v[Symbol.toStringTag]+'] {';
    }
    if(!keys){keys=Object.keys(v);const syms=Object.getOwnPropertySymbols(v).filter(s=>Object.getOwnPropertyDescriptor(v,s).enumerable);keys=keys.concat(syms);if(isArr)keys=keys.filter(k=>typeof k==='symbol'||!/^(0|[1-9]\d*)$/.test(k));}
    if(recurseTimes>ctx.depth){return '['+(cn||'Object')+']';}
    recurseTimes++;
    ctx.seen.push(v);ctx.currentDepth=recurseTimes;
    ctx.extra=false;
    const saveLvl=ctx.indentationLvl;
    try{
      if(isArr){const len=v.length;const lim=Math.min(len,MAXARR);let holes=0;
        for(let i=0;i<lim;i++){
          if(!isNodeList&&!(i in v)){holes++;continue;}
          if(holes){output.push('<'+holes+' empty item'+(holes>1?'s':'')+'>');holes=0;}
          ctx.indentationLvl+=2;output.push(isNodeList?elShort(v[i]):fmt(ctx,v[i],recurseTimes));ctx.indentationLvl=saveLvl;}
        if(holes)output.push('<'+holes+' empty item'+(holes>1?'s':'')+'>');
        if(len>lim){output.push('... '+(len-lim)+' more item'+(len-lim>1?'s':''));ctx.extraFlag=true;}
      }else if(v instanceof Map){for(const [k,val] of v){ctx.indentationLvl+=2;output.push(fmt(ctx,k,recurseTimes)+' => '+fmt(ctx,val,recurseTimes));ctx.indentationLvl=saveLvl;}}
      else if(v instanceof Set){ctx.indentationLvl+=2;for(const x of v)output.push(fmt(ctx,x,recurseTimes));ctx.indentationLvl=saveLvl;}
      for(const k of keys){
        const d=Object.getOwnPropertyDescriptor(v,k)||{value:v[k]};let str;
        if(d.get||d.set)str=d.get&&d.set?'[Getter/Setter]':d.get?'[Getter]':'[Setter]';
        else{ctx.indentationLvl+=2;str=fmt(ctx,d.value,recurseTimes);ctx.indentationLvl=saveLvl;}
        output.push(fmtKey(k)+': '+str);
      }
    }finally{ctx.seen.pop();ctx.indentationLvl=saveLvl;}
    if(!output.length){ctx.extraFlag=false;return (base?base+' ':'')+braces[0]+braces[1];}
    const extraSave=ctx.extra;ctx.extra=!!ctx.extraFlag;ctx.extraFlag=false;
    const res=reduce(ctx,output,base,braces,isArr,recurseTimes,v);
    ctx.extra=extraSave;
    return res;
  }
  function inspect(v,depth){return fmt({seen:[],indentationLvl:0,currentDepth:0,depth:depth==null?2:depth},v,0);}
  function format(args){
    if(!args.length)return '';
    let out='',start=0;
    if(typeof args[0]==='string'&&args[0].includes('%')&&args.length>1){
      let a=1;const f=args[0];let last=0;
      for(let i=0;i<f.length-1;i++){
        if(f[i]!=='%')continue;const c=f[i+1];
        if(c==='%'){out+=f.slice(last,i)+'%';last=i+2;i++;continue;}
        if(a>=args.length)continue;
        let rep=null;const x=args[a];
        if(c==='s')rep=typeof x==='string'?x:typeof x==='bigint'?x+'n':(typeof x==='object'&&x!==null)?inspect(x,0):String(x);
        else if(c==='d'||c==='i'){rep=typeof x==='bigint'?x+'n':typeof x==='symbol'?'NaN':String(c==='i'?parseInt(x):Number(x));}
        else if(c==='f')rep=typeof x==='symbol'?'NaN':String(parseFloat(x));
        else if(c==='o'||c==='O'||c==='j')rep=c==='j'?JSON.stringify(x):inspect(x,c==='o'?4:2);
        else if(c==='c')rep='';
        if(rep!==null){out+=f.slice(last,i)+rep;last=i+2;a++;i++;}
      }
      out+=f.slice(last);start=a;
      for(let k=start;k<args.length;k++)out+=' '+(typeof args[k]==='string'?args[k]:inspect(args[k]));
      return out;
    }
    return args.map(x=>typeof x==='string'?x:inspect(x)).join(' ');
  }
  return {inspect,format};
}
const INS=INSPECT();

/* ---------- sandbox prelude (runs inside the iframe) ---------- */
function PRELUDE(RID,STORE,INSPECTSRC){
  const I=INSPECTSRC();
  const TOP=window.parent,POST=TOP.postMessage.bind(TOP);
  const P=m=>{m.__jsp=RID;try{POST(m,'*');}catch(_){}};
  let depth=0;const counts={},timers={};
  const out=(t,args)=>P({t,s:I.format(args),g:depth});
  const C=console;const orig={};['log','info','warn','error','debug','table','group','groupCollapsed','groupEnd','time','timeEnd','timeLog','count','countReset','assert','clear','dir','trace'].forEach(k=>orig[k]=C[k]);
  const call=(k,a)=>{try{orig[k]&&orig[k].apply(C,a);}catch(_){}};
  ['log','info','debug'].forEach(k=>C[k]=(...a)=>{out(k==='debug'?'log':k,a);call(k,a);});
  C.warn=(...a)=>{out('warn',a);call('warn',a);};
  C.error=(...a)=>{out('error',a);call('error',a);};
  C.dir=(x)=>{out('log',[x]);};
  C.trace=(...a)=>{out('log',['Trace:'+(a.length?' '+I.format(a):'')]);};
  C.group=C.groupCollapsed=(...a)=>{if(a.length)out('group',a);depth++;};
  C.groupEnd=()=>{depth=Math.max(0,depth-1);};
  C.clear=()=>{P({t:'clear'});};
  C.count=(l='default')=>{counts[l]=(counts[l]||0)+1;out('log',[l+': '+counts[l]]);};
  C.countReset=(l='default')=>{counts[l]=0;};
  C.time=(l='default')=>{timers[l]=performance.now();};
  const el=l=>{const ms=performance.now()-timers[l];return l+': '+(ms<1000?ms.toFixed(3)+'ms':(ms/1000).toFixed(3)+'s');};
  C.timeEnd=(l='default')=>{if(l in timers){out('log',[el(l)]);delete timers[l];}};
  C.timeLog=(l='default',...a)=>{if(l in timers)out('log',[el(l),...a]);};
  C.assert=(c,...a)=>{if(!c)out('error',['Assertion failed'+(a.length?': '+I.format(a):'')]);};
  C.table=(data,cols)=>{
    if(data===null||typeof data!=='object'){out('log',[data]);return;}
    const rows=[];const keys=[];let hasVal=false;
    const ent=data instanceof Map?[...data.entries()]:Object.entries(data);
    for(const [k,v] of ent){const r={i:String(k),c:{}};
      if(v!==null&&typeof v==='object'){for(const [ck,cv] of Object.entries(v)){if(!keys.includes(ck))keys.push(ck);r.c[ck]=I.inspect(cv,0);}}
      else{r.v=I.inspect(v,0);hasVal=true;}rows.push(r);}
    const head=(cols||keys);P({t:'table',head:['(index)',...head,...(hasVal?['Values']:[])],rows:rows.map(r=>[r.i,...head.map(h=>h in r.c?r.c[h]:''),...(hasVal?[r.v||'']:[])]),g:depth});
  };
  const errStr=x=>{if(x instanceof Error)return (x.name||'Error')+(x.message?': '+x.message:'');return I.inspect(x);};
  addEventListener('error',ev=>{if(ev.target&&ev.target!==window&&ev.target.tagName){P({t:'error',s:'Failed to load resource: '+(ev.target.src||ev.target.href||ev.target.tagName.toLowerCase()),g:0});return;}
    const m=ev.error!==undefined&&ev.error!==null?errStr(ev.error):String(ev.message||'Script error').replace(/^Uncaught /,'');P({t:'error',s:'Uncaught '+m,g:0,uncaught:1});},true);
  addEventListener('unhandledrejection',ev=>{P({t:'error',s:'Uncaught (in promise) '+errStr(ev.reason),g:0,uncaught:1});});
  /* storage shims: the sandbox has an opaque origin, so we keep storage per playground in the parent page */
  const mk=(name)=>{const data=Object.assign({},STORE[name]||{});
    const sync=()=>P({t:'store',k:name,v:data});
    const api={getItem:k=>Object.prototype.hasOwnProperty.call(data,String(k))?data[String(k)]:null,setItem:(k,v)=>{data[String(k)]=String(v);sync();},removeItem:k=>{delete data[String(k)];sync();},clear:()=>{for(const k of Object.keys(data))delete data[k];sync();},key:i=>Object.keys(data)[i]??null,get length(){return Object.keys(data).length;}};
    return new Proxy(api,{get(t,k){if(k in t)return t[k];if(typeof k==='string')return api.getItem(k)??undefined;return undefined;},set(t,k,v){api.setItem(k,v);return true;},deleteProperty(t,k){api.removeItem(k);return true;},ownKeys(){return Object.keys(data);},getOwnPropertyDescriptor(t,k){if(Object.prototype.hasOwnProperty.call(data,k))return {value:data[k],enumerable:true,configurable:true,writable:true};return undefined;},has(t,k){return k in t||Object.prototype.hasOwnProperty.call(data,k);}});};
  for(const n of ['localStorage','sessionStorage']){try{Object.defineProperty(window,n,{value:mk(n),configurable:true});}catch(_){}}
  try{const jar=Object.assign({},STORE.cookie||{});
    Object.defineProperty(document,'cookie',{configurable:true,get(){return Object.entries(jar).map(([k,v])=>k+'='+v).join('; ');},
      set(s){const parts=String(s).split(';');const [k,...rest]=parts[0].split('=');const name=k.trim();const val=rest.join('=').trim();
        const attrs=parts.slice(1).map(p=>p.trim().toLowerCase());const expired=attrs.some(a=>a==='max-age=0'||/^max-age=-/.test(a)||(a.startsWith('expires=')&&Date.parse(a.slice(8))<Date.now()));
        if(expired)delete jar[name];else jar[name]=val;P({t:'store',k:'cookie',v:jar});}});}catch(_){}
  /* keep the page inside the playground */
  addEventListener('click',ev=>{const a=ev.target.closest&&ev.target.closest('a[href]');if(!a||ev.defaultPrevented)return;const h=a.getAttribute('href');if(h.startsWith('#')||h.startsWith('javascript:'))return;ev.preventDefault();C.info('Link to '+h+' (navigation is disabled in the playground)');},false);
  addEventListener('submit',ev=>{if(!ev.defaultPrevented){ev.preventDefault();C.info('Form submitted: the playground stopped the page reload. Call event.preventDefault() in your submit handler.');}},false);
  const loc=()=>P({t:'loc',h:location.hash});addEventListener('hashchange',loc);addEventListener('popstate',loc);
  const ps=history.pushState.bind(history),rs=history.replaceState.bind(history);
  history.pushState=(s,t,u)=>{ps(s,t,u);loc();};history.replaceState=(s,t,u)=>{rs(s,t,u);loc();};
  addEventListener('message',ev=>{const d=ev.data;if(d&&d.__jspnav!==undefined){location.hash=d.__jspnav;}});
  addEventListener('load',()=>{P({t:'ready',h:location.hash});});
}

/* ---------- running code ---------- */
const handlers={};let seq=0;
if(typeof window!=='undefined')window.addEventListener('message',ev=>{const d=ev.data;if(d&&d.__jsp&&handlers[d.__jsp])handlers[d.__jsp](d,ev.source);});
const BASECSS='html{color-scheme:light}body{font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;margin:16px;color:#1f2328;background:#fff}';
function srcdoc(code,opt,rid,store){
  const safe=s=>String(s||'').replace(/<\/script/gi,'<\\/script');
  const pre='<script>('+PRELUDE.toString()+')('+JSON.stringify(rid)+','+safe(JSON.stringify(store||{}))+','+INSPECT.toString()+');<\/script>';
  const js=code.js&&code.js.trim()?'<script'+(opt.module?' type="module"':'')+'>\n'+safe(code.js)+'\n<\/script>':'';
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(opt.title||'Playground')+'</title>'+pre+'<style>'+BASECSS+'</style>'+(code.css?'<style>\n'+code.css.replace(/<\/style/gi,'<\\/style')+'\n</style>':'')+'</head><body>'+(code.html||'')+js+'</body></html>';
}
/* run(code,{module,visible,host,store,onMsg}) → {frame, rid, stop()} */
function run(code,opt){
  const rid='r'+(++seq)+'_'+Date.now().toString(36);
  const f=document.createElement('iframe');
  f.setAttribute('sandbox','allow-scripts allow-modals allow-forms allow-popups');
  f.setAttribute('title',opt.title||'Code preview');
  f.setAttribute('loading','eager');
  if(!opt.visible){f.style.cssText='position:absolute;width:1px;height:1px;border:0;opacity:0;pointer-events:none;left:-9999px';f.setAttribute('aria-hidden','true');f.tabIndex=-1;}
  handlers[rid]=(d,src)=>{if(src&&src!==f.contentWindow)return;opt.onMsg&&opt.onMsg(d);};
  f.srcdoc=srcdoc(code,opt,rid,opt.store);
  (opt.host||document.body).appendChild(f);
  return {frame:f,rid,stop(){delete handlers[rid];f.remove();}};
}

/* ---------- editor ---------- */
const ICON={
  play:'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>',
  reset:'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M12 5V2L7 6l5 4V7a5 5 0 1 1-5 5H5a7 7 0 1 0 7-7z"/></svg>',
  clear:'<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 2a8 8 0 0 1 6.32 12.9L7.1 5.68A7.96 7.96 0 0 1 12 4zM4 12c0-1.85.63-3.55 1.68-4.9L16.9 18.32A8 8 0 0 1 4 12z"/></svg>',
  lock:'<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"><path fill="currentColor" d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2zm-7-2a2 2 0 1 1 4 0v2h-4z"/></svg>',
  back:'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M15.4 7.4 14 6l-6 6 6 6 1.4-1.4L10.8 12z"/></svg>',
  fwd:'<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8.6 16.6 10 18l6-6-6-6-1.4 1.4 4.6 4.6z"/></svg>',
  reload:'<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M17.65 6.35A8 8 0 1 0 19.73 14h-2.08A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4z"/></svg>',
  phone:'<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M16 1H8a3 3 0 0 0-3 3v16a3 3 0 0 0 3 3h8a3 3 0 0 0 3-3V4a3 3 0 0 0-3-3zm1 19a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1zM10 18h4v1h-4z"/></svg>',
  desk:'<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M20 3H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h6v2H8v2h8v-2h-2v-2h6a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm0 13H4V5h16z"/></svg>',
  term:'<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zm0 2v10h16V7zm2 1.5 4 3.5-4 3.5-1-1.2 2.6-2.3L5 9.7zM11 15h6v1.5h-6z"/></svg>'
};
function editor(host,value,lang,onChange,onRun){
  host.innerHTML='<pre class="jp-hl" aria-hidden="true"><code></code></pre><textarea class="jp-ta" spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off" wrap="off" aria-label="'+(lang||'js').toUpperCase()+' code editor. Press Control+Enter to run, Escape then Tab to leave."></textarea>';
  const ta=host.querySelector('textarea'),code=host.querySelector('code');let lang0=lang,escMode=false;
  const paint=()=>{code.innerHTML=hl(ta.value,lang0)+'\n ';};
  ta.value=value;paint();
  ta.addEventListener('input',()=>{paint();onChange&&onChange(ta.value);});
  ta.addEventListener('keydown',ev=>{
    if((ev.ctrlKey||ev.metaKey)&&ev.key==='Enter'){ev.preventDefault();onRun&&onRun();return;}
    if(ev.key==='Escape'){escMode=true;return;}
    if(ev.key==='Tab'&&!escMode&&!ev.shiftKey){ev.preventDefault();document.execCommand?document.execCommand('insertText',false,'  '):ins('  ');return;}
    if(ev.key==='Enter'&&!ev.shiftKey){const s=ta.selectionStart;const line=ta.value.slice(0,s).split('\n').pop();let ind=(line.match(/^\s*/)||[''])[0];if(/[{[(]\s*$/.test(line))ind+='  ';if(ind){ev.preventDefault();if(!(document.execCommand&&document.execCommand('insertText',false,'\n'+ind)))ins('\n'+ind);}return;}
    escMode=false;});
  function ins(t){const s=ta.selectionStart,en=ta.selectionEnd;ta.value=ta.value.slice(0,s)+t+ta.value.slice(en);ta.selectionStart=ta.selectionEnd=s+t.length;paint();onChange&&onChange(ta.value);}
  return {get:()=>ta.value,set:(v,l)=>{if(l)lang0=l;ta.value=v;paint();},ta};
}

/* ---------- console view ---------- */
function consoleView(host){
  host.innerHTML='<div class="jp-ch"><span class="jp-ct">'+ICON.term+' Console</span><span class="jp-cnt"></span><span class="jp-sp"></span><button type="button" class="jp-ib jp-clear" title="Clear console" aria-label="Clear console">'+ICON.clear+'</button></div><div class="jp-lines" role="log" aria-live="polite"></div>';
  const lines=host.querySelector('.jp-lines'),cnt=host.querySelector('.jp-cnt');let n=0,errs=0;const all=[];
  const upd=()=>{cnt.innerHTML=(errs?'<b class="jp-errc">'+errs+' error'+(errs>1?'s':'')+'</b>':'');if(!n)lines.innerHTML='<div class="jp-empty">No output yet.</div>';};
  const api={
    clear(){lines.innerHTML='';n=0;errs=0;all.length=0;upd();},
    add(d){if(d.t==='clear'){api.clear();api.note('Console was cleared');return;}
      if(!n)lines.innerHTML='';n++;
      const div=document.createElement('div');div.className='jp-l jp-'+d.t;div.style.paddingLeft=(10+(d.g||0)*16)+'px';
      if(d.t==='table'){div.innerHTML='<div class="jp-tw"><table class="jp-tbl"><thead><tr>'+d.head.map(h=>'<th>'+e(h)+'</th>').join('')+'</tr></thead><tbody>'+d.rows.map(r=>'<tr>'+r.map(c=>'<td>'+e(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';all.push({t:'table',s:'[table]'});}
      else{const s=d.s===''?' ':d.s;div.textContent=s;all.push({t:d.t,s:d.s});}
      if(d.t==='error')errs++;
      lines.appendChild(div);lines.scrollTop=lines.scrollHeight;upd();},
    note(s){if(!n)lines.innerHTML='';n++;const div=document.createElement('div');div.className='jp-l jp-note';div.textContent=s;lines.appendChild(div);},
    text:()=>all.filter(x=>x.t!=='table').map(x=>x.s).join('\n'),all
  };
  host.querySelector('.jp-clear').onclick=()=>api.clear();
  upd();return api;
}

/* ---------- the playground widget ---------- */
const STORES={};
function mount(slot,it,key){
  const web=!!(it.html!==undefined||it.css!==undefined);
  const files=web?['html','css','js'].filter(k=>it[k]!==undefined):['js'];
  const cur={};files.forEach(k=>cur[k]=it[k]||'');
  let tab=it.tab&&files.includes(it.tab)?it.tab:(web?(files.includes('js')?'js':files[0]):'js');
  const store=STORES[key]=STORES[key]||{};
  const usesStore=/localStorage|sessionStorage|document\.cookie/.test(files.map(k=>it[k]).join('\n'));
  const H=it.height||(web?300:0);
  slot.innerHTML=`<figure class="jp ${web?'jp-web':'jp-con'}">
  <figcaption class="jp-head"><span class="jp-badge">${web?'Live page':'Live code'}</span><span class="jp-title">${e(it.title||'Try it')}</span><span class="jp-sp"></span>
    ${usesStore?`<button type="button" class="btn sm ghost jp-store" title="Forget saved storage for this example">Clear storage</button>`:''}
    <button type="button" class="btn sm ghost jp-reset" title="Put the original code back">${ICON.reset}<span>Reset</span></button>
    <button type="button" class="btn sm primary jp-run" title="Run (Ctrl+Enter)">${ICON.play}<span>Run</span></button></figcaption>
  ${web?`<div class="jp-win"><div class="jp-bar"><span class="jp-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="jp-nav" aria-hidden="true">${ICON.back}${ICON.fwd}</span><button type="button" class="jp-ib jp-reload" title="Reload page" aria-label="Reload page">${ICON.reload}</button>
    <div class="jp-url"><span class="jp-lock">${ICON.lock}</span><span class="jp-host">${e(it.url||'localhost:5173')}</span><span class="jp-hash"></span></div>
    <button type="button" class="jp-ib jp-dev" title="Toggle phone width" aria-label="Toggle phone width" aria-pressed="false">${ICON.phone}</button></div>
    <div class="jp-view" style="height:${H}px"></div></div>`:''}
  <div class="jp-code">${files.length>1||web?`<div class="jp-tabs" role="tablist">${files.map(k=>`<button type="button" role="tab" class="jp-tab" data-k="${k}" aria-selected="${k===tab}">${k==='js'?'JavaScript':k.toUpperCase()}</button>`).join('')}<span class="jp-sp"></span><span class="jp-hint">Edit, then Run</span></div>`:`<div class="jp-tabs"><span class="jp-tab jp-single" aria-selected="true">${it.module?'main.js (module)':'script.js'}</span><span class="jp-sp"></span><span class="jp-hint">Edit, then Run</span></div>`}
    <div class="jp-ed"></div></div>
  <div class="jp-con-host"></div>
  ${it.caption?`<p class="jp-cap">${e(it.caption)}</p>`:''}</figure>`;
  const fig=slot.firstElementChild,view=fig.querySelector('.jp-view');
  const con=consoleView(fig.querySelector('.jp-con-host'));
  const ed=editor(fig.querySelector('.jp-ed'),cur[tab],tab,v=>{cur[tab]=v;},()=>go());
  fig.querySelectorAll('.jp-tab[data-k]').forEach(b=>b.onclick=()=>{tab=b.dataset.k;fig.querySelectorAll('.jp-tab[data-k]').forEach(x=>x.setAttribute('aria-selected',x===b));ed.set(cur[tab],tab);});
  let runner=null;
  const hashEl=fig.querySelector('.jp-hash');
  function go(){
    if(runner)runner.stop();con.clear();
    if(hashEl)hashEl.textContent='';
    runner=run(cur,{module:!!it.module,visible:web,host:web?view:fig,title:it.title,store,
      onMsg(d){if(d.t==='store'){store[d.k]=d.v;return;}if(d.t==='loc'||d.t==='ready'){if(hashEl)hashEl.textContent=d.h||'';return;}con.add(d);}});
    fig.classList.add('jp-ran');
  }
  fig.querySelector('.jp-run').onclick=go;
  const rl=fig.querySelector('.jp-reload');if(rl)rl.onclick=go;
  fig.querySelector('.jp-reset').onclick=()=>{files.forEach(k=>cur[k]=it[k]||'');ed.set(cur[tab],tab);go();};
  const cs=fig.querySelector('.jp-store');if(cs)cs.onclick=()=>{for(const k of Object.keys(store))delete store[k];con.note('Saved storage cleared. Run again to start fresh.');};
  const dv=fig.querySelector('.jp-dev');if(dv)dv.onclick=()=>{const on=dv.getAttribute('aria-pressed')!=='true';dv.setAttribute('aria-pressed',on);fig.classList.toggle('jp-phone',on);dv.innerHTML=on?ICON.desk:ICON.phone;};
  const url=fig.querySelector('.jp-url');if(url)url.title='Address bar (the playground runs the page locally)';
  if(it.autorun!==false)go();else con.note('Press Run to see the output.');
  return {go,con,fig,cur};
}
function mountAll(root,items){
  root.querySelectorAll('.play-slot').forEach(s=>{const it=(items||[])[+s.dataset.i];if(!it){s.remove();return;}
    const key=(root.dataset.lid||'x')+':'+s.dataset.i;
    if('IntersectionObserver' in window&&it.autorun!==false){s.innerHTML='<div class="jp-wait" style="min-height:'+((it.height||120)+120)+'px"></div>';const io=new IntersectionObserver(en=>{if(en.some(x=>x.isIntersecting)){io.disconnect();mount(s,it,key);}},{rootMargin:'400px'});io.observe(s);}
    else mount(s,it,key);});
}

/* ---------- predict the output, with a Run button ---------- */
function mountPredict(el,items,lid){
  const done={};
  el.innerHTML=`<section class="console jp-pr" aria-label="Predict the output"><div class="console-head"><h3>Predict the output</h3><span style="font-size:13px;color:var(--muted)">${items.length} snippets · answer, then run the code to check</span></div><div class="fb-body" id="pr"></div></section>`;
  const box=el.querySelector('#pr');
  box.innerHTML=items.map((it,i)=>`<div class="pr-i" data-i="${i}"><p class="stem" style="margin:0 0 8px;font-weight:500">${e(it.q||'What does this log?')}</p><pre class="code jp-hlpre"><code>${hl(it.code,'js')}</code></pre><div class="opts">${it.o.map((o,j)=>`<button class="opt" data-j="${j}"><span class="k">${'ABCD'[j]}</span><span class="mono" style="white-space:pre-wrap">${e(o)}</span></button>`).join('')}</div><div class="why" hidden></div><div class="jp-prrun" hidden></div></div>`).join('');
  box.querySelectorAll('.pr-i').forEach(div=>{const it=items[+div.dataset.i];
    div.querySelectorAll('.opt').forEach(b=>b.onclick=()=>{const j=+b.dataset.j;
      div.querySelectorAll('.opt').forEach(o=>{o.disabled=true;const k=+o.dataset.j;if(k===it.a)o.classList.add('right');else if(k===j)o.classList.add('wrong');});
      const w=div.querySelector('.why');w.hidden=false;
      w.innerHTML=`<b class="${j===it.a?'ok':'no'}">${j===it.a?'Correct.':'Not quite.'}</b> ${e(it.w)} <span class="jp-prb"><button class="btn sm primary jp-prgo">${ICON.play}<span>Run it</span></button> <button class="btn sm ghost jp-again">Try again</button></span>`;
      w.querySelector('.jp-again').onclick=()=>{div.querySelectorAll('.opt').forEach(o=>{o.disabled=false;o.classList.remove('right','wrong');});w.hidden=true;div.querySelector('.jp-prrun').hidden=true;};
      w.querySelector('.jp-prgo').onclick=()=>{const h=div.querySelector('.jp-prrun');h.hidden=false;const c=consoleView(h);const r=run({js:it.code},{module:!!it.module,visible:false,host:h,onMsg:d=>{if(d.t!=='store'&&d.t!=='loc'&&d.t!=='ready')c.add(d);}});setTimeout(()=>r.stop(),8000);};
      done[div.dataset.i]=j===it.a;
      if(Object.values(done).filter(Boolean).length===items.length&&typeof S!=='undefined'){S.predict=S.predict||{};S.predict[lid]=true;typeof save==='function'&&save();}
    });});
}
return {mountAll,mount,mountPredict,hlAll,hl,run,inspect:INS.inspect,format:INS.format,consoleView,srcdoc};
})();
window.JSP=JSP;
function boot(){
  const data=document.getElementById('lessonPlays');
  if(!data)return;
  let plays;
  try{plays=JSON.parse(data.textContent);}catch(x){return;}
  const lid=(document.getElementById('lessonRoot')||{dataset:{}}).dataset.lesson||'x';
  document.querySelectorAll('.deep').forEach(root=>{
    JSP.hlAll(root);
    // Academy placeholders are data-play="N" (the source app used data-i).
    root.querySelectorAll('.play-slot[data-play]').forEach(s=>{
      const i=+s.dataset.play,it=plays[i];if(!it)return;
      const go=()=>{const keep=s.innerHTML;
        try{JSP.mount(s,it,lid+':'+i);}catch(x){s.innerHTML=keep;if(window.console)console.error(x);}};
      // As in the source app: start each frame only when it is about to scroll into view.
      if('IntersectionObserver' in window&&it.autorun!==false){
        const io=new IntersectionObserver(en=>{if(en.some(x=>x.isIntersecting)){io.disconnect();go();}},{rootMargin:'400px'});
        io.observe(s);
      }else go();
    });
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
