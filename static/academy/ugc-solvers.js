/*! Ralfiz Academy: UGC NET CS interactive solvers (32 widgets).
 * Ported from the standalone UGC NET course app. Contract with the lesson page:
 *   <div class="solver-slot" data-solver="N">fallback</div>   (N = index into the list below)
 *   <script type="application/json" id="lessonSolvers">["truthtable","kmap"]</script>
 * Every slot is mounted on load. Only global: window.UGCSolvers.
 */
(function(){
'use strict';
const NS_ROOT={NETSOLVE:{}};
/* ================= ANIM core (from the course app; mountAll removed) ================= */
const ANIM=(function(){
  const REG={};
  const RM=()=>{try{return matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){return false;}};
  const h=(tag,attrs,html)=>{const n=document.createElement(tag);if(attrs)for(const k in attrs){if(k==='class')n.className=attrs[k];else if(k==='style')n.setAttribute('style',attrs[k]);else n.setAttribute(k,attrs[k]);}if(html!=null)n.innerHTML=html;return n;};
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  /* FLIP: animate layout changes. measure(nodes) -> apply change -> play(nodes) */
  function flip(nodes,change,ms){
    ms=RM()?0:(ms||450);
    const first=new Map();nodes.forEach(n=>first.set(n,n.getBoundingClientRect()));
    change();
    nodes.forEach(n=>{const a=first.get(n),b=n.getBoundingClientRect();if(!a)return;
      const dx=a.left-b.left,dy=a.top-b.top,sx=b.width?a.width/b.width:1,sy=b.height?a.height/b.height:1;
      if(!ms||(Math.abs(dx)<.5&&Math.abs(dy)<.5&&Math.abs(sx-1)<.01&&Math.abs(sy-1)<.01))return;
      n.animate([{transformOrigin:'top left',transform:`translate(${dx}px,${dy}px) scale(${sx},${sy})`},{transformOrigin:'top left',transform:'none'}],{duration:ms,easing:'cubic-bezier(.2,.8,.2,1)'});});
  }
  function register(id,def){REG[id]=def;}
  /* Mount one explainer into el */
  function mount(el,id){
    const def=REG[id];if(!def){el.innerHTML='';return;}
    const fig=h('figure',{class:'ax','data-ax':id});
    fig.innerHTML=`<div class="ax-h"><div><span class="ax-k">${def.steps===false?'Try it':'Animation'}</span><strong>${esc(def.title)}</strong></div>${def.steps===false?'':'<span class="ax-count"></span>'}</div><div class="ax-stage"></div><div class="ax-foot"></div>`;
    el.innerHTML='';el.appendChild(fig);
    const stage=fig.querySelector('.ax-stage'),foot=fig.querySelector('.ax-foot');
    const api=def.build(stage,{h,esc,flip,RM,foot});
    if(def.steps===false||!api||!api.steps){if(def.caption){const c=h('p',{class:'ax-cap'},esc(def.caption));fig.appendChild(c);}return;}
    /* stepper */
    const n=api.steps.length;let i=0,timer=null,playing=false;
    foot.innerHTML=`<p class="ax-cap" aria-live="polite"></p><div class="ax-ctl"><button class="btn sm ax-rs" aria-label="Restart">↺</button><button class="btn sm ax-pv" aria-label="Previous step">◀</button><button class="btn sm primary ax-pl" aria-label="Play">▶ Play</button><button class="btn sm ax-nx" aria-label="Next step">▶|</button><div class="ax-dots">${api.steps.map((s,k)=>`<button class="ax-dot" data-k="${k}" aria-label="Step ${k+1}"></button>`).join('')}</div></div>`;
    const cap=foot.querySelector('.ax-cap'),cnt=fig.querySelector('.ax-count'),pl=foot.querySelector('.ax-pl');
    function show(k){i=Math.max(0,Math.min(n-1,k));api.show(i);cap.innerHTML=api.steps[i];cnt.textContent=`Step ${i+1} of ${n}`;foot.querySelectorAll('.ax-dot').forEach((d,j)=>d.classList.toggle('on',j<=i));}
    function stop(){playing=false;clearTimeout(timer);pl.textContent='▶ Play';pl.setAttribute('aria-label','Play');}
    function tick(){if(!playing)return;if(i>=n-1){stop();return;}show(i+1);timer=setTimeout(tick,api.delay?api.delay(i):2600);}
    pl.onclick=()=>{if(playing){stop();return;}if(i>=n-1)show(0);playing=true;pl.textContent='❚❚ Pause';pl.setAttribute('aria-label','Pause');timer=setTimeout(tick,api.delay?api.delay(i):1400);};
    foot.querySelector('.ax-nx').onclick=()=>{stop();show(i+1);};
    foot.querySelector('.ax-pv').onclick=()=>{stop();show(i-1);};
    foot.querySelector('.ax-rs').onclick=()=>{stop();show(0);};
    foot.querySelectorAll('.ax-dot').forEach(d=>d.onclick=()=>{stop();show(+d.dataset.k);});
    show(0);
    /* stop timers when removed */
    const mo=new MutationObserver(()=>{if(!document.body.contains(fig)){stop();mo.disconnect();}});mo.observe(document.body,{childList:true,subtree:true});
  }
    return {register,mount,REG,flip,h,esc};
})();

/* ================= Solvers ================= */
/* ================= UGC NET solvers: group cn (subnet, crc, slidewin, tcpcong) =================
   Pure algorithms live on NETSOLVE.subnet / NETSOLVE.crc / NETSOLVE.slidewin / NETSOLVE.tcpcong
   so they can be tested in Node (global.window = {}). Everything is wrapped in an IIFE so no
   global names are declared (several net-*.js files are concatenated into one script). */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;
const P2=n=>Math.pow(2,n);

/* ======================================================================
   SUBNET core (IPv4 addressing, VLSM, summarisation)
   ====================================================================== */
const SN={};
SN.ipStr=v=>[Math.floor(v/16777216)%256,Math.floor(v/65536)%256,Math.floor(v/256)%256,v%256].join('.');
SN.bits=v=>(v>>>0).toString(2).padStart(32,'0');
SN.maskOf=p=>p<=0?0:(0xFFFFFFFF-(P2(32-p)-1));
SN.parseIP=function(s){
  s=String(s==null?'':s).trim();
  if(!s)return {err:'Enter an IPv4 address, e.g. 192.168.10.77.'};
  const m=s.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if(!m)return {err:`"${s}" is not an IPv4 address: write four numbers 0–255 separated by dots.`};
  let v=0;for(let i=1;i<=4;i++){const o=+m[i];if(o>255)return {err:`Octet ${o} in "${s}" is above 255.`};v=v*256+o;}
  return {v};
};
SN.parsePrefix=function(s){
  s=String(s==null?'':s).trim().replace(/^\//,'');
  if(!s)return {err:'Enter a prefix length (e.g. /26) or a subnet mask (e.g. 255.255.255.192).'};
  if(/^\d{1,2}$/.test(s)){const p=+s;if(p>32)return {err:`Prefix /${p} is too long: the maximum is /32.`};return {p};}
  const r=SN.parseIP(s);if(r.err)return {err:`"${s}" is neither a prefix length (0–32) nor a dotted subnet mask.`};
  const inv=0xFFFFFFFF-r.v;
  if(inv&&(((inv+1)&inv)>>>0)!==0&&inv!==0xFFFFFFFF)return {err:`${s} is not a valid subnet mask: its 1-bits must be contiguous from the left (binary ${SN.bits(r.v).replace(/(.{8})(?!$)/g,'$1.')}).`};
  let p=0;for(let i=31;i>=0;i--){if(Math.floor(r.v/P2(i))%2)p++;else break;}
  return {p};
};
SN.parseCIDR=function(s){
  s=String(s==null?'':s).trim();
  const m=s.match(/^([\d.]+)\s*(?:\/\s*|\s+)([\d.]+)$/);
  if(!m){const ip=SN.parseIP(s);if(ip.err)return ip;return {err:`"${s}" needs a prefix, e.g. ${s}/24.`};}
  const ip=SN.parseIP(m[1]);if(ip.err)return ip;const pr=SN.parsePrefix(m[2]);if(pr.err)return pr;
  return {v:ip.v,p:pr.p};
};
SN.cls=function(v){
  const o=Math.floor(v/16777216);
  if(o<128)return {c:'A',def:8,range:'0–127'};
  if(o<192)return {c:'B',def:16,range:'128–191'};
  if(o<224)return {c:'C',def:24,range:'192–223'};
  if(o<240)return {c:'D',def:null,range:'224–239',use:'multicast'};
  return {c:'E',def:null,range:'240–255',use:'reserved (experimental)'};
};
const SPECIAL=[['10.0.0.0',8,'private','Private (RFC 1918)'],['172.16.0.0',12,'private','Private (RFC 1918)'],['192.168.0.0',16,'private','Private (RFC 1918)'],
  ['127.0.0.0',8,'special','Loopback'],['169.254.0.0',16,'special','Link-local (APIPA)'],['100.64.0.0',10,'special','Shared address space (carrier-grade NAT)'],
  ['0.0.0.0',8,'special','"This network" (source only)'],['255.255.255.255',32,'special','Limited broadcast'],['224.0.0.0',4,'special','Multicast (class D)'],['240.0.0.0',4,'special','Reserved (class E)']];
SN.scope=function(v){
  for(const [a,p,k,lab] of SPECIAL){const n=SN.parseIP(a).v,sz=P2(32-p);if(v>=n&&v<n+sz)return {kind:k,label:lab,block:a+'/'+p};}
  return {kind:'public',label:'Public (globally routable)'};
};
SN.info=function(v,p,opt){
  opt=opt||{};
  const total=P2(32-p),mask=SN.maskOf(p),wild=total-1,net=Math.floor(v/total)*total,bc=net+total-1;
  let usable,first,last;
  if(p<=30){usable=total-2;first=net+1;last=bc-1;}
  else if(p===31){usable=2;first=net;last=bc;}
  else {usable=1;first=net;last=net;}
  const c=SN.cls(v),sc=SN.scope(v);
  const r={v,p,mask,wild,net,bc,total,usable,first,last,cls:c,scope:sc,role:p>=31?'host':(v===net?'network':v===bc?'broadcast':'host')};
  /* the "interesting" octet: the octet where the prefix boundary falls */
  const oi=p>=32?3:Math.floor(p/8);r.octet=oi;
  if(oi<4){const mo=Math.floor(mask/P2(24-8*oi))%256;r.octMask=mo;r.octBlock=256-mo;r.octVal=Math.floor(v/P2(24-8*oi))%256;r.octNet=Math.floor(r.octVal/r.octBlock)*r.octBlock;}
  if(c.def!=null){
    const cn=Math.floor(v/P2(32-c.def))*P2(32-c.def);r.classNet=cn;
    if(p>=c.def){const s=p-c.def;r.borrowed=s;r.subnets=opt.noZero?Math.max(0,P2(s)-2):P2(s);r.subnetIdx=Math.floor((net-cn)/total);
      r.zeroOrOnes=s>0&&(r.subnetIdx===0||r.subnetIdx===P2(s)-1);}
    else {r.supernetOf=P2(c.def-p);}
  }
  return r;
};
SN.rangeToCIDR=function(start,end){ /* [start,end) -> minimal aligned blocks */
  const out=[];let a=start;
  while(a<end){let k=32;while(k>0){const sz=P2(33-k);if(a%sz===0&&a+sz<=end)k--;else break;}out.push({net:a,p:k});a+=P2(32-k);}
  return out;
};
SN.hostsToBlock=function(h){let b=0;while(P2(b)<h+2)b++;if(b<2)b=2;return b;};
SN.vlsm=function(baseStr,reqs){
  const base=SN.parseCIDR(baseStr);if(base.err)return base;
  if(base.p>30)return {err:`A /${base.p} block is too small to split into subnets.`};
  if(!reqs.length)return {err:'Add at least one subnet with its number of hosts.'};
  for(const q of reqs){if(!(Number.isInteger(q.hosts)&&q.hosts>=1))return {err:`Hosts for "${q.name||'?'}" must be a whole number ≥ 1.`};}
  const size=P2(32-base.p),net=Math.floor(base.v/size)*size,end=net+size;
  const order=reqs.map((q,i)=>({name:q.name||('Subnet '+(i+1)),hosts:q.hosts,i})).sort((a,b)=>b.hosts-a.hosts||a.i-b.i);
  let cur=net;const rows=[];
  for(const q of order){
    const hb=SN.hostsToBlock(q.hosts),bs=P2(hb),pr=32-hb;
    const at=Math.ceil(cur/bs)*bs;
    const row={name:q.name,hosts:q.hosts,i:q.i,hb,bs,p:pr,usable:bs-2,waste:bs-2-q.hosts};
    if(at+bs>end){row.fail=true;rows.push(row);continue;}
    Object.assign(row,{net:at,bc:at+bs-1,first:at+1,last:at+bs-2,gap:at-cur});cur=at+bs;rows.push(row);
  }
  const used=rows.filter(r=>!r.fail).reduce((s,r)=>s+r.bs,0),need=rows.reduce((s,r)=>s+r.hosts,0);
  return {net,p:base.p,size,end,rows,used,need,free:SN.rangeToCIDR(cur,end),freeAddr:end-cur,warnHost:base.v!==net,ok:rows.every(r=>!r.fail)};
};
SN.parseList=function(text){
  const parts=String(text==null?'':text).split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
  if(parts.length<1)return {err:'Enter at least one network, e.g. 200.1.0.0/24.'};
  if(parts.length>64)return {err:'At most 64 networks, please.'};
  const L=[];for(const s of parts){const r=SN.parseCIDR(s);if(r.err)return {err:r.err};const sz=P2(32-r.p);L.push({net:Math.floor(r.v/sz)*sz,p:r.p,given:r.v,src:s});}
  return {L};
};
SN.summarise=function(text){
  const pl=SN.parseList(text);if(pl.err)return pl;const L=pl.L;
  const lo=Math.min(...L.map(n=>n.net)),hi=Math.max(...L.map(n=>n.net+P2(32-n.p)-1));
  const x=(lo^hi)>>>0;const p=Math.clz32(x);
  const size=P2(32-p),sumNet=Math.floor(lo/size)*size;
  const iv=L.map(n=>[n.net,n.net+P2(32-n.p)]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  const merged=[];let overlap=false;
  for(const [a,b] of iv){const m=merged[merged.length-1];if(m&&a<m[1]){overlap=true;m[1]=Math.max(m[1],b);}else if(m&&a===m[1])m[1]=Math.max(m[1],b);else merged.push([a,b]);}
  const union=merged.reduce((s,[a,b])=>s+b-a,0);
  const agg=[];merged.forEach(([a,b])=>agg.push(...SN.rangeToCIDR(a,b)));
  /* classic supernetting rules for equal-size blocks */
  let rules=null;
  if(L.length>1&&L.every(n=>n.p===L[0].p)){
    const sz=P2(32-L[0].p),s=L.map(n=>n.net).sort((a,b)=>a-b),n=s.length;
    const contig=s.every((v,i)=>i===0||v===s[i-1]+sz),pow=(n&(n-1))===0,aligned=s[0]%(n*sz)===0;
    rules={n,sz,contig,pow,aligned,ok:contig&&pow&&aligned&&!overlap,first:s[0],newP:L[0].p-Math.round(Math.log2(n))};
  }
  return {L,lo,hi,p,sumNet,size,union,exact:union===size,extra:size-union,merged,agg,overlap,rules,hostBits:L.some(n=>n.given!==n.net)};
};
NETSOLVE.subnet=SN;

/* ======================================================================
   CRC core (mod-2 long division) + Hamming code
   ====================================================================== */
const CR={};
const xorS=(a,b)=>{let s='';for(let i=0;i<a.length;i++)s+=a[i]===b[i]?'0':'1';return s;};
CR.parseBits=function(s,what){
  s=String(s==null?'':s).replace(/[\s_]/g,'');
  if(!s)return {err:`Enter the ${what} as 0s and 1s.`};
  if(!/^[01]+$/.test(s))return {err:`The ${what} may contain only 0 and 1 (found "${s.replace(/[01]/g,'')[0]}").`};
  if(s.length>64)return {err:`The ${what} is too long (at most 64 bits, please).`};
  return {b:s};
};
CR.parsePoly=function(s){
  s=String(s==null?'':s).trim();
  if(!s)return {err:'Enter a generator: bits (10011) or a polynomial (x^4 + x + 1).'};
  let b;
  if(/x/i.test(s)){
    const t=s.replace(/\s+/g,'').replace(/\*\*/g,'^').toLowerCase().split('+').filter(Boolean);const deg=new Set();
    for(const term of t){let m;
      if(term==='1')deg.add(0);else if(term==='x')deg.add(1);
      else if((m=term.match(/^x\^?(\d+)$/)))deg.add(+m[1]);
      else return {err:`Cannot read the term "${term}". Write terms like x^4, x, 1 joined by +.`};}
    const mx=Math.max(...deg);if(mx>32)return {err:'Generator degree above 32 is not supported.'};
    b='';for(let i=mx;i>=0;i--)b+=deg.has(i)?'1':'0';
  } else {const r=CR.parseBits(s,'generator');if(r.err)return r;b=r.b.replace(/^0+/,'');}
  if(b.length<2)return {err:'The generator needs degree ≥ 1 (at least two bits, starting with 1).'};
  return {b};
};
CR.polyStr=function(b){const n=b.length-1,t=[];for(let i=0;i<=n;i++)if(b[i]==='1'){const d=n-i;t.push(d===0?'1':d===1?'x':'x^'+d);}return t.join(' + ');};
CR.divide=function(dividend,gen){
  const r=gen.length-1,steps=[];let q='';
  if(dividend.length<gen.length)return {q:'0',rem:dividend.padStart(r,'0'),steps};
  let cur=dividend.slice(0,r+1);
  for(let i=0;i+r<dividend.length;i++){
    const qb=cur[0],sub=qb==='1'?gen:'0'.repeat(r+1),res=xorS(cur,sub),down=i+r+1<dividend.length?dividend[i+r+1]:null;
    steps.push({i,win:cur,q:qb,sub,res,down});q+=qb;cur=res.slice(1)+(down==null?'':down);
  }
  return {q,rem:cur,steps};
};
CR.encode=function(data,gen){
  const r=gen.length-1,dividend=data+'0'.repeat(r),d=CR.divide(dividend,gen);
  return {r,dividend,q:d.q,rem:d.rem,steps:d.steps,frame:data+d.rem};
};
CR.check=function(frame,gen,pattern){
  const pat=pattern?pattern:'0'.repeat(frame.length);
  const rx=xorS(frame,pat),d=CR.divide(rx,gen),zero=/^0*$/.test(d.rem),err=/1/.test(pat);
  return {rx,pat,rem:d.rem,q:d.q,steps:d.steps,ok:zero,err,undetected:zero&&err,nbits:(pat.match(/1/g)||[]).length};
};
/* Hamming code: parity bits at positions 1,2,4,8,...; order 'left' = position 1 is the leftmost
   written bit (Tanenbaum), 'right' = position 1 is the rightmost written bit (Forouzan / d7..p1). */
CR.hammingR=function(m){let r=0;while(P2(r)<m+r+1)r++;return r;};
const isP2=x=>(x&(x-1))===0;
CR.idxOf=(pos,n,order)=>order==='right'?n-pos:pos-1;
CR.hamming=function(data,opt){
  opt=opt||{};const par=opt.parity||'even',order=opt.order||'left';
  const m=data.length,r=CR.hammingR(m),n=m+r;
  const dpos=[];for(let j=1;j<=n;j++)if(!isP2(j))dpos.push(j);
  const bit={};const src={};
  const dat=order==='right'?[...data].reverse():[...data];
  dpos.forEach((j,k)=>{bit[j]=dat[k];src[j]=order==='right'?m-1-k:k;});
  const checks=[];
  for(let k=0;k<r;k++){const p=P2(k);const cov=[];for(let j=1;j<=n;j++)if(j&p)cov.push(j);
    const ones=cov.filter(j=>j!==p&&bit[j]==='1').length;const v=par==='even'?ones%2:1-ones%2;bit[p]=String(v);checks.push({p,cov,ones,bit:String(v)});}
  const code=Array.from({length:n},(_,i)=>{const pos=order==='right'?n-i:i+1;return bit[pos];}).join('');
  const cells=Array.from({length:n},(_,i)=>{const pos=order==='right'?n-i:i+1;return {pos,type:isP2(pos)?'p':'d',bit:bit[pos],src:src[pos]};});
  return {m,r,n,code,cells,checks,parity:par,order};
};
CR.hamCheck=function(recv,opt){
  opt=opt||{};const par=opt.parity||'even',order=opt.order||'left';
  const n=recv.length;let r=0;while(P2(r)<=n)r++;const m=n-r;
  if(m<1)return {err:`A ${n}-bit word has no room for data bits (${r} of them would be parity bits).`};
  const bit=j=>recv[CR.idxOf(j,n,order)];
  const checks=[];let syn=0;
  for(let k=0;k<r;k++){const p=P2(k);const cov=[];for(let j=1;j<=n;j++)if(j&p)cov.push(j);
    const ones=cov.filter(j=>bit(j)==='1').length;const bad=par==='even'?ones%2===1:ones%2===0;if(bad)syn+=p;checks.push({p,cov,ones,bad});}
  let corrected=recv,pos=0,multi=false;
  if(syn){if(syn>n)multi=true;else{pos=syn;const i=CR.idxOf(syn,n,order);corrected=recv.slice(0,i)+(recv[i]==='1'?'0':'1')+recv.slice(i+1);}}
  const dpos=[];for(let j=1;j<=n;j++)if(!isP2(j))dpos.push(j);
  const cb=j=>corrected[CR.idxOf(j,n,order)];
  let data=dpos.map(cb).join('');if(order==='right')data=[...data].reverse().join('');
  return {n,m,r,checks,syn,pos,multi,corrected,data};
};
CR.distance=(a,b)=>{let d=0;for(let i=0;i<a.length;i++)if(a[i]!==b[i])d++;return d;};
NETSOLVE.crc=CR;

/* ======================================================================
   SLIDEWIN core: efficiency formulas + a discrete timeline simulation
   ====================================================================== */
const SW={};
SW.log2c=x=>{let k=0;while(P2(k)<x)k++;return k;};
SW.calc=function(o){
  /* o: B (bit/s), L (bits), Tp (s), W, k (seq bits or null), ack (bits), cyc: 'full' (Tt+2Tp) | 'rtt' (2Tp) */
  const Tt=o.L/o.B,Ta=(o.ack||0)/o.B,Tp=o.Tp,a=Tp/Tt;
  const cycle=o.cyc==='rtt'?2*Tp:Tt+Ta+2*Tp;
  const sw=Math.min(1,Tt/cycle),win=W=>Math.min(1,W*Tt/cycle);
  const Wraw=cycle/Tt,Wopt=Math.max(1,Math.ceil(Wraw-1e-9));
  const r={Tt,Ta,Tp,a,cycle,Wraw,Wopt,sw:{eta:sw,thr:sw*o.B},W:o.W,
    gbn:{eta:win(o.W),thr:win(o.W)*o.B,bits:SW.log2c(o.W+1),bitsOpt:SW.log2c(Wopt+1)},
    sr:{eta:win(o.W),thr:win(o.W)*o.B,bits:SW.log2c(2*o.W),bitsOpt:SW.log2c(2*Wopt)},
    bdp:o.B*2*Tp};
  if(o.k!=null){r.k=o.k;r.maxGBN=P2(o.k)-1;r.maxSR=P2(o.k-1);r.gbn.fits=o.W<=r.maxGBN;r.sr.fits=o.W<=r.maxSR;
    r.gbn.etaK=win(Math.min(o.W,r.maxGBN));r.sr.etaK=win(Math.min(o.W,r.maxSR));}
  return r;
};
SW.seqBits=(proto,W)=>proto==='sw'?1:proto==='gbn'?SW.log2c(W+1):SW.log2c(2*W);
/* Time unit = one frame transmission time. ACKs take no transmission time. */
SW.sim=function(o){
  const proto=o.proto,N=o.N,W=proto==='sw'?1:o.W,P=o.P,To=o.To||(2*P+1);
  const k=SW.seqBits(proto,W),mod=P2(k);
  const frames=[],acks=[],timeouts=[],rxlog=[],deliver=[];
  let base=0,next=0,busy=0,gTimer=null;const acked=[],sTimer={},resendQ=[],sent=[];
  let expected=0,rb=0;const buf=new Set();
  let lostF=false,lostA=false,t=0,end=null;
  const sendAck=(n,t0,forF)=>{const lost=!lostA&&o.loseAck===forF;if(lost)lostA=true;acks.push({n,lab:n%mod,t0,arr:t0+P,lost,forF});};
  for(t=0;t<=400;t++){
    /* 1. frames arriving at the receiver */
    for(const f of frames)if(!f.lost&&f.arr===t){
      if(proto==='sr'){
        if(f.f>=rb&&f.f<rb+W){if(buf.has(f.f)||f.f<rb){f.rx='dup';}else{buf.add(f.f);f.rx=f.f===rb?'accept':'buffer';}
          sendAck(f.f,t,f.f);while(buf.has(rb)){buf.delete(rb);deliver.push({f:rb,t});rb++;}}
        else if(f.f<rb){f.rx='dup';sendAck(f.f,t,f.f);}
        else f.rx='discard';
      } else {
        if(f.f===expected){f.rx='accept';deliver.push({f:f.f,t});expected++;sendAck(expected,t,f.f);}
        else if(f.f<expected){f.rx='dup';sendAck(expected,t,f.f);}
        else f.rx='discard';
      }
    }
    /* 2. ACKs arriving at the sender */
    for(const a of acks)if(!a.lost&&a.arr===t){
      if(proto==='sr'){if(!acked[a.n]){acked[a.n]=true;delete sTimer[a.n];a.eff='new';}else a.eff='dup';while(acked[base])base++;}
      else{if(a.n>base){base=a.n;a.eff='new';if(next<base)next=base;gTimer=base<next?t+To:null;}else a.eff='dup';}
    }
    if(base>=N){end=t;break;}
    /* 3. timeouts */
    if(proto==='sr'){for(const f of Object.keys(sTimer).map(Number).sort((x,y)=>x-y))if(sTimer[f]===t){delete sTimer[f];timeouts.push({t,f});resendQ.push(f);}}
    else if(gTimer!=null&&gTimer===t){timeouts.push({t,f:base,from:base,to:next-1});gTimer=null;next=base;}
    /* 4. transmit one frame if the link is free */
    if(busy<=t){
      let f=null;
      if(proto==='sr'){if(resendQ.length)f=resendQ.shift();else if(next<base+W&&next<N)f=next++;}
      else if(next<base+W&&next<N)f=next++;
      if(f!=null){const re=sent[f]===true;sent[f]=true;const lost=!lostF&&o.lose===f;if(lost)lostF=true;
        frames.push({f,lab:f%mod,t0:t,t1:t+1,arr:t+1+P,lost,re});busy=t+1;
        if(proto==='sr')sTimer[f]=t+1+To;else if(gTimer==null)gTimer=t+1+To;}
    }
  }
  const tx=frames.length;
  return {proto,N,W,P,To,k,mod,frames,acks,timeouts,deliver,end,tx,re:tx-N,util:end?N/end:0,done:end!=null};
};
NETSOLVE.slidewin=SW;

/* ======================================================================
   TCPCONG core: cwnd per transmission round
   ====================================================================== */
const TC={};
TC.parseEvents=function(text,rounds){
  const ev={};const s=String(text==null?'':text).trim();if(!s)return {ev};
  for(const part of s.split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean)){
    const m=part.match(/^(?:r(?:ound)?\s*)?(\d+)\s*[:=\s-]\s*(.+)$/i);
    if(!m)return {err:`Cannot read "${part}". Write events like 8:3dup or 14:timeout.`};
    const r=+m[1],t=m[2].trim().toLowerCase().replace(/[\s-]/g,'');
    let type=null;if(/^(to|t|timeout|rto|time)$/.test(t))type='timeout';else if(/^(3dup|3|dup|d|3dupack|3dupacks|tripledup|tda|fastretransmit)$/.test(t))type='3dup';
    if(!type)return {err:`Unknown event "${m[2].trim()}" at round ${r}: use timeout or 3dup.`};
    if(r<1||(rounds&&r>rounds))return {err:`Event round ${r} is outside 1–${rounds}.`};
    if(ev[r])return {err:`Round ${r} has two events.`};
    ev[r]=type;
  }
  return {ev};
};
TC.run=function(o){
  /* o: ssthresh, cwnd0, rounds, ev {round:type}, variant 'tahoe'|'reno', cap (slow start capped at ssthresh),
        plus3 (Reno: cwnd = ssthresh + 3 after 3 dup ACKs), rwnd (null = unlimited) */
  const rows=[];let cw=o.cwnd0||1,th=o.ssthresh;
  for(let r=1;r<=o.rounds;r++){
    const phase=cw<th?'SS':'CA',send=o.rwnd?Math.min(cw,o.rwnd):cw;
    const row={r,cwnd:cw,ssthresh:th,phase,send};const e=o.ev[r];
    if(e){
      const nt=Math.max(Math.floor(cw/2),2);row.ev=e;row.newTh=nt;
      if(e==='timeout'||o.variant==='tahoe'){row.rule=e==='timeout'?'timeout':'tahoe3';cw=1;}
      else {row.rule='reno3';cw=nt+(o.plus3?3:0);}
      th=nt;
    } else if(phase==='SS'){const d=cw*2;if(o.cap&&d>th){cw=th;row.rule='sscap';}else {cw=d;row.rule='ss';}}
    else {cw=cw+1;row.rule='ca';}
    row.nextCwnd=cw;row.nextTh=th;rows.push(row);
  }
  const sent=rows.reduce((s,x)=>s+x.send,0);
  return {rows,sent,finalCwnd:cw,finalTh:th,maxCwnd:Math.max(...rows.map(x=>x.cwnd))};
};
NETSOLVE.tcpcong=TC;

/* ======================================================================
   UI (browser only)
   ====================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let UID=0;
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=a=>a[Math.floor(Math.random()*a.length)];
function debounce(fn,ms){let t;return (...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
const fmtN=(x,d)=>{d=d==null?4:d;if(!isFinite(x))return '∞';const a=Math.abs(x);if(a!==0&&(a>=1e9||a<1e-4))return x.toExponential(3).replace(/\.?0+e/,'e').replace('e+','e');return String(+x.toFixed(d));};
const fmtT=s=>{const a=Math.abs(s);if(a===0)return '0 s';if(a>=1)return fmtN(s)+' s';if(a>=1e-3)return fmtN(s*1e3)+' ms';if(a>=1e-6)return fmtN(s*1e6)+' µs';return fmtN(s*1e9)+' ns';};
const fmtR=b=>b>=1e9?fmtN(b/1e9)+' Gbps':b>=1e6?fmtN(b/1e6)+' Mbps':b>=1e3?fmtN(b/1e3)+' kbps':fmtN(b)+' bps';
const pct=x=>fmtN(x*100,2)+'%';
const num=s=>{s=String(s==null?'':s).trim().replace(/\s+/g,'').replace(/[×xX*]10\^?/,'e').replace(/^10\^/,'1e');if(!s)return NaN;return /^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s)?Number(s):NaN;};
const chip=(k,v,cls,sub)=>`<div class="netcn-chip ${cls||''}"><span>${k}</span><b>${v}</b>${sub?`<small>${sub}</small>`:''}</div>`;
/* generic step-through control: frames 0..n-1, render(i) sets the whole state for step i (idempotent) */
function stepper(host,n,render,start){
  let i=0,timer=null;
  host.innerHTML=`<div class="netcn-stp"><span class="netcn-sl">Step through</span><button type="button" class="btn sm" data-a="rs" aria-label="Back to the first step">↺</button><button type="button" class="btn sm" data-a="pv">◀ Prev</button><button type="button" class="btn sm primary" data-a="pl">▶ Play</button><button type="button" class="btn sm" data-a="nx">Next ▶</button><button type="button" class="btn sm" data-a="end">All</button><input type="range" min="0" max="${Math.max(0,n-1)}" value="0" aria-label="Jump to step"><span class="netcn-stpc" aria-live="polite"></span></div>`;
  const pl=host.querySelector('[data-a=pl]'),rg=host.querySelector('input'),ct=host.querySelector('.netcn-stpc');
  const stop=()=>{clearTimeout(timer);timer=null;pl.textContent='▶ Play';};
  const go=k=>{i=Math.max(0,Math.min(n-1,k));rg.value=i;ct.textContent=`Step ${i+1} of ${n}`;render(i);};
  const tick=()=>{if(!document.body.contains(host)){stop();return;}if(i>=n-1){stop();return;}go(i+1);timer=setTimeout(tick,1400);};
  host.querySelector('[data-a=rs]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-a=pv]').onclick=()=>{stop();go(i-1);};
  host.querySelector('[data-a=nx]').onclick=()=>{stop();go(i+1);};
  host.querySelector('[data-a=end]').onclick=()=>{stop();go(n-1);};
  pl.onclick=()=>{if(timer){stop();return;}if(i>=n-1)go(0);pl.textContent='❚❚ Pause';timer=setTimeout(tick,700);};
  rg.oninput=()=>{stop();go(+rg.value);};
  go(start==null?0:start);return {go,stop,get i(){return i;}};
}
function tabs(host,names,cur,onPick){
  host.innerHTML=names.map((nm,k)=>`<button type="button" aria-pressed="${k===cur}" data-k="${k}">${nm}</button>`).join('');
  host.querySelectorAll('button').forEach(b=>b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(+b.dataset.k);});
}
function seg(host,cur,onPick){
  host.querySelectorAll('button').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.v===cur));b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(b.dataset.v);};});
}
function showErr(root,msg){const e=root.querySelector('.netcn-err'),o=root.querySelector('.netcn-out');if(msg){e.hidden=false;e.textContent=msg;o&&o.classList.add('netcn-stale');}else{e.hidden=true;o&&o.classList.remove('netcn-stale');}}
const conv=items=>`<details class="netcn-conv" open><summary>Conventions used</summary><ul>${items.map(x=>`<li>${x}</li>`).join('')}</ul></details>`;

/* ---------------------------------------------------------------- subnet UI */
const ipS=SN.ipStr;
function bitsHTML(v,p,cls){
  const b=SN.bits(v);let s='';
  for(let i=0;i<32;i++){if(i&&i%8===0)s+='<i>.</i>';s+=`<span class="${i<p?'n':'h'}${cls&&cls(i)?' '+cls(i):''}">${b[i]}</span>`;}
  return `<span class="subnet-bits">${s}</span>`;
}
ANIM.register('subnet',{title:'IPv4 subnetting, VLSM and supernetting',steps:false,
 caption:'Enter an address with a prefix or mask, split a block with VLSM, or summarise a list of networks. The binary view colours network bits and host bits differently (key above the table).',
 build(stage){
  stage.style.padding='0';stage.classList.add('netcn-stage');
  const st={mode:0,ip:'192.168.10.77',pfx:'/26',noZero:false,
    base:'192.168.1.0/24',reqs:[['Sales',100],['HR',50],['Lab',25],['Office',10],['WAN link',2]],
    list:'200.1.0.0/24, 200.1.1.0/24, 200.1.2.0/24, 200.1.3.0/24'};
  stage.innerHTML=`<div class="netcn subnet"><div class="netcn-tabs" role="group" aria-label="Solver mode"></div><div class="subnet-pane"></div></div>`;
  const root=stage.querySelector('.subnet'),pane=root.querySelector('.subnet-pane');
  tabs(root.querySelector('.netcn-tabs'),['Address / mask','VLSM','Summarise / supernet'],0,k=>{st.mode=k;draw();});
  function draw(){[addrPane,vlsmPane,sumPane][st.mode]();}

  /* ----- address / mask ----- */
  function addrPane(){
    pane.innerHTML=`<div class="netcn-in"><div class="netcn-ctl">
      <label>IP address<input type="text" data-k="ip" spellcheck="false" autocomplete="off" size="15"></label>
      <label>Prefix or subnet mask<input type="text" data-k="pfx" spellcheck="false" autocomplete="off" size="15"></label>
      <label class="chk"><input type="checkbox" data-k="nz"> <span>Old classful rule: all-0s and all-1s subnets unusable (2<sup>s</sup> − 2 subnets)</span></label></div>
      <div class="netcn-btns"><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
      <p class="netcn-err" role="alert" hidden></p></div>
     <div class="netcn-out"><div class="netcn-chips"></div><p class="netcn-note subnet-role"></p>
      <div class="netcn-h">Binary view</div><div class="netcn-scroll"><table class="netcn-tbl subnet-bt"></table></div>
      <div class="netcn-h">Working</div><div class="netcn-f subnet-work"></div>
      ${conv(['Usable hosts = 2<sup>h</sup> − 2 (network and broadcast addresses excluded), where h = 32 − prefix.','/31 is a point-to-point link with 2 usable addresses (RFC 3021); /32 is a single host.','Classes by first octet: A 0–127, B 128–191, C 192–223, D 224–239 (multicast), E 240–255.','Subnets are counted from 0; modern CIDR allows subnet-zero and the all-ones subnet (2<sup>s</sup> subnets). Tick the box for the old 2<sup>s</sup> − 2 rule.','Private ranges (RFC 1918): 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16.'])}</div>`;
    const $=s=>pane.querySelector(s);
    $('[data-k=ip]').value=st.ip;$('[data-k=pfx]').value=st.pfx;$('[data-k=nz]').checked=st.noZero;
    const run=()=>{
      const a=SN.parseIP(st.ip),m=SN.parsePrefix(st.pfx);
      if(a.err||m.err){showErr(pane,a.err||m.err);return;}showErr(pane,'');
      const r=SN.info(a.v,m.p,{noZero:st.noZero}),h=32-r.p;
      $('.netcn-chips').innerHTML=chip('Network address',ipS(r.net)+'/'+r.p,'main')+chip('Broadcast address',r.p>=31?'none':ipS(r.bc),'main')
        +chip('First host',ipS(r.first))+chip('Last host',ipS(r.last))+chip('Usable hosts',r.usable.toLocaleString('en'),'main',r.p<=30?`2^${h} − 2`:r.p===31?'RFC 3021 link':'single host')
        +chip('Total addresses',r.total.toLocaleString('en'),'',`2^${h}`)+chip('Subnet mask',ipS(r.mask))+chip('Wildcard',ipS(r.wild))
        +chip('Class',r.cls.c+(r.cls.use?' ('+r.cls.use+')':''),'',`first octet ${Math.floor(r.v/16777216)}: ${r.cls.range}`)
        +chip('Scope',r.scope.kind==='private'?'Private':r.scope.kind==='public'?'Public':'Special',r.scope.kind==='private'?'ok':'',r.scope.label);
      $('.subnet-role').innerHTML=r.p>=31?`With /${r.p} every address in the block is usable.`:r.role==='network'?`<b>${ipS(r.v)}</b> is the <b>network address</b> of this subnet, so it cannot be assigned to a host.`:r.role==='broadcast'?`<b>${ipS(r.v)}</b> is the <b>broadcast address</b> of this subnet, so it cannot be assigned to a host.`:`<b>${ipS(r.v)}</b> is a valid host address in ${ipS(r.net)}/${r.p}.`;
      const row=(k,sub,v)=>`<tr><th>${k}<small>${sub?sub+' · ':''}${ipS(v)}</small></th><td>${bitsHTML(v,r.p)}</td></tr>`;
      $('.subnet-bt').innerHTML=`<thead><tr><th></th><th><span class="subnet-key n">network bits: ${r.p}</span> <span class="subnet-key h">host bits: ${h}</span></th></tr></thead><tbody>
        ${row('IP address','',r.v)}${row('Subnet mask',`/${r.p}`,r.mask)}${row('Network','IP AND mask',r.net)}${row('Wildcard','NOT mask',r.wild)}${row('Broadcast','network OR wildcard',r.bc)}</tbody>`;
      const o=['1st','2nd','3rd','4th'];let w='';
      w+=`<p>Prefix /${r.p} → mask = ${r.p} ones followed by ${h} zeros = <b>${ipS(r.mask)}</b>.</p>`;
      if(r.octet<4&&r.p<32){w+=`<p>The prefix boundary falls in the <b>${o[r.octet]} octet</b> (mask octet ${r.octMask}). Block size = 256 − ${r.octMask} = <b>${r.octBlock}</b>.</p>`;
        w+=`<p>Network octet = ⌊${r.octVal} ÷ ${r.octBlock}⌋ × ${r.octBlock} = ${Math.floor(r.octVal/r.octBlock)} × ${r.octBlock} = <b>${r.octNet}</b>; the octets after it become 0 → network <b>${ipS(r.net)}</b>.</p>`;
        w+=`<p>Broadcast = network + 2<sup>${h}</sup> − 1 = <b>${ipS(r.bc)}</b> (${r.octet<3?'later octets become 255, ':''}${o[r.octet]} octet ${r.octNet} + ${r.octBlock} − 1 = ${r.octNet+r.octBlock-1}).</p>`;}
      w+=`<p>Host bits h = 32 − ${r.p} = ${h} → total 2<sup>${h}</sup> = ${r.total.toLocaleString('en')} addresses; usable ${r.p<=30?`2<sup>${h}</sup> − 2 = <b>${r.usable.toLocaleString('en')}</b>`:`<b>${r.usable}</b>`}.</p>`;
      if(r.cls.def!=null){
        if(r.borrowed!=null)w+=`<p>Class ${r.cls.c} default mask is /${r.cls.def}. Subnet bits borrowed s = ${r.p} − ${r.cls.def} = ${r.borrowed} → ${st.noZero?`2<sup>${r.borrowed}</sup> − 2`:`2<sup>${r.borrowed}</sup>`} = <b>${r.subnets}</b> subnet${r.subnets===1?'':'s'} of the classful network ${ipS(r.classNet)}/${r.cls.def}${r.borrowed?`; this is subnet <b>#${r.subnetIdx}</b> (counting from 0)`:''}.${st.noZero&&r.zeroOrOnes?' <b>Under the old rule this subnet (all-0s or all-1s) is not usable.</b>':''}</p>`;
        else w+=`<p>Class ${r.cls.c} default mask is /${r.cls.def}; /${r.p} is shorter, so this block is a <b>supernet</b> of ${r.supernetOf} class-${r.cls.c} networks.</p>`;
      } else w+=`<p>Class ${r.cls.c} addresses (${r.cls.use}) have no default mask and are not used for host subnetting.</p>`;
      $('.subnet-work').innerHTML=w;
    };
    const upd=debounce(run,200);
    $('[data-k=ip]').oninput=e=>{st.ip=e.target.value;upd();};
    $('[data-k=pfx]').oninput=e=>{st.pfx=e.target.value;upd();};
    $('[data-k=nz]').onchange=e=>{st.noZero=e.target.checked;run();};
    $('[data-b=rand]').onclick=()=>{const c=pick(['A','B','C','C','P']);const o1=c==='A'?pick([10,rnd(1,126)]):c==='B'?pick([172,rnd(128,191)]):c==='C'?pick([192,rnd(192,223)]):rnd(1,223);
      const o2=o1===172?rnd(16,31):o1===192?168:rnd(0,255);st.ip=[o1,o2,rnd(0,255),rnd(1,254)].join('.');
      const p=c==='A'?rnd(9,30):c==='B'?rnd(17,30):rnd(24,30);st.pfx=Math.random()<.5?'/'+p:ipS(SN.maskOf(p));
      $('[data-k=ip]').value=st.ip;$('[data-k=pfx]').value=st.pfx;run();};
    $('[data-b=def]').onclick=()=>{st.ip='192.168.10.77';st.pfx='/26';$('[data-k=ip]').value=st.ip;$('[data-k=pfx]').value=st.pfx;run();};
    run();
  }

  /* ----- VLSM ----- */
  function vlsmPane(){
    pane.innerHTML=`<div class="netcn-in"><div class="netcn-ctl">
      <label>Address block to split<input type="text" data-k="base" spellcheck="false" autocomplete="off" size="18"></label></div>
      <div class="netcn-h">Subnets and hosts needed</div>
      <div class="netcn-scroll"><table class="netcn-tbl netcn-edit subnet-req"><thead><tr><th>Name</th><th>Hosts</th><th></th></tr></thead><tbody></tbody></table></div>
      <div class="netcn-btns"><button type="button" class="btn sm" data-b="add">+ Add subnet</button><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
      <p class="netcn-err" role="alert" hidden></p></div>
     <div class="netcn-out"><div class="netcn-chips"></div><div class="subnet-warn"></div>
      <div class="subnet-st"></div><p class="netcn-note subnet-cap" aria-live="polite"></p>
      <div class="subnet-bar" aria-hidden="true"></div>
      <div class="netcn-scroll"><table class="netcn-tbl subnet-vt"></table></div>
      <div class="netcn-f subnet-free"></div>
      ${conv(['Largest requirement first (ties keep the input order); each subnet starts at the next free address, which is then already aligned.','Block for h hosts = the smallest power of 2 ≥ h + 2 (network + broadcast), minimum 4 (/30).','Prefix = 32 − log<sub>2</sub>(block size). Wasted = usable addresses − hosts needed.'])}</div>`;
    const $=s=>pane.querySelector(s),tb=$('.subnet-req tbody');
    $('[data-k=base]').value=st.base;
    const rowsHTML=()=>{tb.innerHTML=st.reqs.map((q,i)=>`<tr><td><input type="text" data-r="${i}" data-c="0" value="${E(q[0])}" size="10" aria-label="Name of subnet ${i+1}"></td><td><input type="text" inputmode="numeric" data-r="${i}" data-c="1" value="${E(q[1])}" size="6" aria-label="Hosts in subnet ${i+1}"></td><td><button type="button" class="netcn-x" data-del="${i}" aria-label="Remove subnet ${i+1}" ${st.reqs.length<2?'disabled':''}>×</button></td></tr>`).join('');
      tb.querySelectorAll('input').forEach(inp=>inp.oninput=e=>{const r=+e.target.dataset.r,c=+e.target.dataset.c;st.reqs[r][c]=e.target.value;upd();});
      tb.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{st.reqs.splice(+b.dataset.del,1);rowsHTML();run();});};
    let stp=null;
    const run=()=>{
      for(const q of st.reqs){if(!/^\s*\d+\s*$/.test(String(q[1]))){showErr(pane,`Hosts for "${q[0]||'?'}" must be a whole number.`);return;}}
      const res=SN.vlsm(st.base,st.reqs.map(q=>({name:String(q[0]).trim(),hosts:+q[1]})));
      if(res.err){showErr(pane,res.err);return;}showErr(pane,'');
      const R=res.rows,good=R.filter(r=>!r.fail);
      $('.netcn-chips').innerHTML=chip('Block',`${ipS(res.net)}/${res.p}`,'',`${res.size.toLocaleString('en')} addresses`)+chip('Subnets allocated',`${good.length} of ${R.length}`,res.ok?'main ok':'main bad')
        +chip('Addresses used',res.used.toLocaleString('en'),'',pct(res.used/res.size)+' of the block')+chip('Left free',res.freeAddr.toLocaleString('en'))+chip('Hosts needed',res.need.toLocaleString('en'),'',`efficiency ${pct(res.need/Math.max(1,res.used))}`);
      $('.subnet-warn').innerHTML=(res.warnHost?`<p class="netcn-verdict warn">The block address has host bits set; using its network address ${ipS(res.net)}/${res.p}.</p>`:'')+(res.ok?'':`<p class="netcn-verdict bad">Not enough space: ${R.filter(r=>r.fail).map(r=>E(r.name)+' ('+r.hosts+' hosts, needs /'+r.p+')').join(', ')} could not be placed.</p>`);
      $('.subnet-free').innerHTML=`<p><b>Free after allocation:</b> ${res.free.length?res.free.map(f=>ipS(f.net)+'/'+f.p).join(', '):'none, the block is fully used'}.</p>`;
      const render=k=>{ /* k = number of subnets allocated so far */
        $('.subnet-vt').innerHTML=`<thead><tr><th>#</th><th>Subnet</th><th>Hosts<small>needed</small></th><th>Block<small>2<sup>h</sup> ≥ hosts+2</small></th><th>Prefix</th><th>Network</th><th>Usable range</th><th>Broadcast</th><th>Mask</th><th>Wasted</th></tr></thead><tbody>${R.map((r,i)=>{
          const cls=i===k-1?' class="cur"':i>=k?' class="netcn-pend"':'';
          if(r.fail)return `<tr${cls}><td>${i+1}</td><th>${E(r.name)}</th><td>${r.hosts}</td><td>${r.bs}</td><td>/${r.p}</td><td colspan="5" class="netcn-badt">does not fit in the remaining space</td></tr>`;
          const sh=i<k;return `<tr${cls}><td>${i+1}</td><th>${E(r.name)}</th><td>${r.hosts}</td><td>2<sup>${r.hb}</sup> = ${r.bs}</td><td>/${r.p}</td><td>${sh?ipS(r.net):'…'}</td><td>${sh?ipS(r.first)+' – '+ipS(r.last):'…'}</td><td>${sh?ipS(r.bc):'…'}</td><td>${ipS(SN.maskOf(r.p))}</td><td>${r.waste}</td></tr>`;}).join('')}</tbody>`;
        let bar='';R.forEach((r,i)=>{if(r.fail||i>=k)return;const l=(r.net-res.net)/res.size*100,w=r.bs/res.size*100;bar+=`<div class="subnet-seg c${i%6}${i===k-1?' cur':''}" style="left:${l}%;width:${w}%" title="${E(r.name)}"><span>${w>7?E(r.name):''}</span></div>`;});
        $('.subnet-bar').innerHTML=`<div class="subnet-track">${bar}</div><div class="subnet-ends"><span>${ipS(res.net)}</span><span>${ipS(res.end-1)}</span></div>`;
        let cap;
        if(k===0)cap=`Sort the requirements, largest first: ${R.map(r=>E(r.name)+' '+r.hosts).join(', ')}. Allocation starts at <b>${ipS(res.net)}</b>.`;
        else{const r=R[k-1];cap=r.fail?`<b>${E(r.name)}</b> needs ${r.hosts} + 2 = ${r.hosts+2} → block ${r.bs} (/${r.p}), but not enough space is left in the block.`
          :`<b>${E(r.name)}</b> needs ${r.hosts} hosts: ${r.hosts} + 2 = ${r.hosts+2} ≤ 2<sup>${r.hb}</sup> = ${r.bs} → <b>/${r.p}</b>. Next free address ${ipS(r.net)} → subnet <b>${ipS(r.net)}/${r.p}</b>, hosts ${ipS(r.first)} – ${ipS(r.last)}, broadcast ${ipS(r.bc)}. Next free: ${ipS(r.bc+1)}.`;}
        $('.subnet-cap').innerHTML=cap;
      };
      stp=stepper($('.subnet-st'),R.length+1,render,R.length);
    };
    const upd=debounce(run,250);
    $('[data-k=base]').oninput=e=>{st.base=e.target.value;upd();};
    $('[data-b=add]').onclick=()=>{if(st.reqs.length>=16)return;st.reqs.push(['Subnet '+(st.reqs.length+1),10]);rowsHTML();run();};
    $('[data-b=def]').onclick=()=>{st.base='192.168.1.0/24';st.reqs=[['Sales',100],['HR',50],['Lab',25],['Office',10],['WAN link',2]];$('[data-k=base]').value=st.base;rowsHTML();run();};
    $('[data-b=rand]').onclick=()=>{const p=pick([22,23,24,24]);const size=P2(32-p);const net=SN.parseIP(pick(['192.168.0.0','172.16.0.0','10.10.0.0','200.10.0.0'])).v+rnd(0,15)*size;
      st.base=ipS(net)+'/'+p;const n=rnd(3,5);let left=size;st.reqs=[];const names=['Sales','HR','Lab','Office','Accounts','WAN 1','WAN 2','Guest'];
      for(let i=0;i<n;i++){const h=i===n-1&&Math.random()<.6?2:rnd(3,Math.max(4,Math.floor(left/3)));const b=P2(SN.hostsToBlock(h));if(b>left)break;left-=b;st.reqs.push([names[i],h]);}
      if(!st.reqs.length)st.reqs=[['Sales',20]];$('[data-k=base]').value=st.base;rowsHTML();run();};
    rowsHTML();run();
  }

  /* ----- summarise / supernet ----- */
  function sumPane(){
    pane.innerHTML=`<div class="netcn-in"><div class="netcn-ctl"><label class="netcn-wide">Networks (comma or one per line)<textarea data-k="list" rows="3" spellcheck="false"></textarea></label></div>
      <div class="netcn-btns"><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
      <p class="netcn-err" role="alert" hidden></p></div>
     <div class="netcn-out"><div class="netcn-chips"></div><div class="subnet-verd"></div>
      <div class="netcn-h">Common prefix in binary</div><div class="netcn-scroll"><table class="netcn-tbl subnet-bt subnet-st2"></table></div>
      <div class="netcn-f subnet-work"></div>
      ${conv(['Summary route = the longest prefix shared by every address in the list (lowest network address to highest broadcast address).','It is <b>exact</b> only if the networks fill the summary block with nothing extra; otherwise the route also covers addresses not in the list.','Supernetting rule (equal-size blocks): the count is a power of 2, the blocks are contiguous, and the first network is divisible by (count × block size).'])}</div>`;
    const $=s=>pane.querySelector(s);$('[data-k=list]').value=st.list;
    const run=()=>{
      const r=SN.summarise(st.list);if(r.err){showErr(pane,r.err);return;}showErr(pane,'');
      $('.netcn-chips').innerHTML=chip('Summary route',`${ipS(r.sumNet)}/${r.p}`,'main')+chip('Summary mask',ipS(SN.maskOf(r.p)))
        +chip('Exact?',r.exact?'Yes':'No',r.exact?'ok':'bad',r.exact?'covers only the listed networks':`${r.extra.toLocaleString('en')} extra addresses`)
        +chip('Addresses',`${r.union.toLocaleString('en')} listed`,'',`summary covers ${r.size.toLocaleString('en')}`);
      let v='';
      if(r.hostBits)v+=`<p class="netcn-verdict warn">Some entries had host bits set; their network addresses are used.</p>`;
      if(r.overlap)v+=`<p class="netcn-verdict warn">Some networks overlap; overlapping addresses are counted once.</p>`;
      if(r.rules){const q=r.rules,Y=(b,t)=>`<li class="${b?'ok':'bad'}">${b?'✓':'✗'} ${t}</li>`;
        v+=`<div class="netcn-verdict ${q.ok?'ok':'bad'}"><b>Supernetting rules for ${q.n} blocks of ${q.sz.toLocaleString('en')} addresses:</b><ul class="subnet-rules">${Y(q.pow,`count ${q.n} is a power of 2`)}${Y(q.contig,'the blocks are contiguous')}${Y(q.aligned,`first network ${ipS(q.first)} is divisible by ${q.n} × ${q.sz} = ${(q.n*q.sz).toLocaleString('en')}`)}</ul>${q.ok?`They combine into one supernet <b>${ipS(q.first)}/${q.newP}</b>.`:'They cannot be combined into a single supernet without covering extra addresses.'}</div>`;}
      $('.subnet-verd').innerHTML=v;
      const L=r.L.slice().sort((a,b)=>a.net-b.net);
      const row=(k,val,pp,extra)=>`<tr${extra||''}><th>${k}<small>${ipS(val)}/${pp}</small></th><td>${bitsHTML(val,r.p,i=>i<pp?'':'x')}</td></tr>`;
      $('.subnet-st2').innerHTML=`<thead><tr><th>Network</th><th><span class="subnet-key n">common bits: ${r.p}</span> <span class="subnet-key h">differ / host</span></th></tr></thead><tbody>${L.map((n,i)=>row('Network '+(i+1),n.net,n.p)).join('')}${L.length>1?row('Highest address',r.hi,32):''}${row('Summary',r.sumNet,r.p,' class="subnet-sum"')}</tbody>`;
      let w=`<p>Lowest network ${ipS(r.lo)}, highest address ${ipS(r.hi)}. They agree on the first <b>${r.p}</b> bits → summary <b>${ipS(r.sumNet)}/${r.p}</b> (2<sup>${32-r.p}</sup> = ${r.size.toLocaleString('en')} addresses).</p>`;
      w+=`<p>Listed networks hold ${r.union.toLocaleString('en')} addresses → ${r.exact?'the summary is <b>exact</b>.':`the summary adds <b>${r.extra.toLocaleString('en')}</b> addresses that are not in the list.`}</p>`;
      w+=`<p>Smallest exact set of CIDR blocks for the list: <b>${r.agg.map(a=>ipS(a.net)+'/'+a.p).join(', ')}</b>${r.agg.length===1?' (one route).':` (${r.agg.length} routes).`}</p>`;
      $('.subnet-work').innerHTML=w;
    };
    $('[data-k=list]').oninput=debounce(e=>{st.list=e.target.value;run();},250);
    $('[data-b=def]').onclick=()=>{st.list='200.1.0.0/24, 200.1.1.0/24, 200.1.2.0/24, 200.1.3.0/24';$('[data-k=list]').value=st.list;run();};
    $('[data-b=rand]').onclick=()=>{const p=pick([24,24,25,26,27]),sz=P2(32-p),n=pick([2,4,4,8]);const al=n*sz;
      let base=SN.parseIP(pick(['192.168.0.0','172.16.0.0','10.1.0.0','200.1.0.0'])).v+rnd(0,31)*al;if(Math.random()<.3)base+=sz;
      const L=[];for(let i=0;i<n;i++)L.push(ipS(base+i*sz)+'/'+p);if(Math.random()<.25&&L.length>2)L.pop();
      st.list=L.join(', ');$('[data-k=list]').value=st.list;run();};
    run();
  }
  draw();
 }});

/* ---------------------------------------------------------------- crc UI */
function divTable(dividend,gen,steps,upto,opts){
  /* long-division layout: one column per dividend bit; rows up to step `upto` (inclusive) */
  const n=dividend.length,r=gen.length-1,dataLen=opts.dataLen;
  const cells=(arr)=>arr.map(c=>c?`<td class="${c.c||''}">${c.b}</td>`:'<td></td>').join('');
  const blank=()=>Array(n).fill(null);
  let q=blank();steps.forEach((s,i)=>{if(i<=upto)q[i+r]={b:s.q,c:'q'+(s.q==='1'?' one':'')};});
  const rows=[];
  rows.push(`<tr class="crc-qr"><th>Quotient</th>${cells(q)}</tr>`);
  const dv=[...dividend].map((b,i)=>({b,c:i>=dataLen?'z':''}));
  rows.push(`<tr class="crc-dv"><th>${E(gen)} )</th>${cells(dv)}</tr>`);
  steps.forEach((s,i)=>{if(i>upto)return;const cur=i===upto?' cur':'';
    const sub=blank();[...s.sub].forEach((b,j)=>sub[i+j]={b,c:s.q==='1'?'g':'zero'});
    rows.push(`<tr class="crc-sub${cur}"><th>${s.q==='1'?'XOR':'XOR 0'}</th>${cells(sub)}</tr>`);
    const res=blank();[...s.res].forEach((b,j)=>{if(j>0)res[i+j]={b,c:''};});
    if(s.down!=null)res[i+r+1]={b:s.down,c:'dn'};
    const last=i===steps.length-1;
    rows.push(`<tr class="crc-res${cur}${last?' fin':''}"><th>${last?'Remainder':''}</th>${cells(res)}</tr>`);});
  return rows.join('');
}
ANIM.register('crc',{title:'CRC and Hamming code',steps:false,
 caption:'CRC: mod-2 long division with the full XOR trace and a receiver check. Hamming: place parity bits, then find and fix a single-bit error from the syndrome.',
 build(stage){
  stage.style.padding='0';stage.classList.add('netcn-stage');
  const st={mode:0,data:'1101011011',gen:'10011',pat:'',hd:'1011',par:'even',order:'right',recv:'1000101'};
  stage.innerHTML=`<div class="netcn crc"><div class="netcn-tabs" role="group" aria-label="Solver mode"></div><div class="crc-pane"></div></div>`;
  const root=stage.querySelector('.crc'),pane=root.querySelector('.crc-pane');
  tabs(root.querySelector('.netcn-tabs'),['CRC','Hamming code'],0,k=>{st.mode=k;draw();});
  function draw(){[crcPane,hamPane][st.mode]();}

  function crcPane(){
    pane.innerHTML=`<div class="netcn-in"><div class="netcn-ctl">
      <label>Data bits<input type="text" data-k="data" spellcheck="false" autocomplete="off" size="16"></label>
      <label>Generator (bits or polynomial)<input type="text" data-k="gen" spellcheck="false" autocomplete="off" size="14"></label>
      <label class="netcn-wide">Error pattern on the frame (optional; 1 = flip that bit)<input type="text" data-k="pat" spellcheck="false" autocomplete="off" placeholder="blank = no error"></label></div>
      <div class="netcn-btns"><button type="button" class="btn sm" data-b="flip">Flip one random bit</button><button type="button" class="btn sm" data-b="clr">No error</button><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
      <p class="netcn-err" role="alert" hidden></p></div>
     <div class="netcn-out"><div class="netcn-chips"></div>
      <div class="netcn-h">Sender: divide data + ${'r'} zeros by the generator (mod-2)</div>
      <div class="crc-st"></div><p class="netcn-note crc-cap" aria-live="polite"></p>
      <div class="netcn-scroll"><table class="crc-div crc-send"></table></div>
      <div class="netcn-f crc-work"></div>
      <div class="netcn-h">Receiver check</div><div class="crc-rx"></div>
      <details class="crc-rxd"><summary>Receiver division trace</summary><div class="netcn-scroll"><table class="crc-div crc-recv"></table></div></details>
      ${conv(['Generator of degree r (r + 1 bits): append r zeros to the data, divide by mod-2 (XOR, no borrows); the r-bit remainder is the CRC.','Transmitted frame = data followed by the CRC, i.e. T(x) = M(x)·x<sup>r</sup> + R(x).','At each step: if the leading bit is 1 the quotient bit is 1 and we XOR with the generator; if it is 0 the quotient bit is 0 and we XOR with zeros.','Receiver divides the whole received frame; remainder 0 → accept. An error pattern that is itself a multiple of the generator goes undetected.'])}</div>`;
    const $=s=>pane.querySelector(s);
    $('[data-k=data]').value=st.data;$('[data-k=gen]').value=st.gen;$('[data-k=pat]').value=st.pat;
    let res=null;
    const run=()=>{
      const d=CR.parseBits(st.data,'data'),g=CR.parsePoly(st.gen);
      if(d.err||g.err){showErr(pane,d.err||g.err);return;}
      const e=CR.encode(d.b,g.b),fl=e.frame.length;let pat=st.pat.replace(/[\s_]/g,'');
      if(pat){if(!/^[01]+$/.test(pat)){showErr(pane,'The error pattern may contain only 0 and 1.');return;}
        if(pat.length!==fl){showErr(pane,`The error pattern must have ${fl} bits, the length of the frame (it has ${pat.length}).`);return;}}
      showErr(pane,'');
      const k=CR.check(e.frame,g.b,pat||null);res={e,k,g:g.b,d:d.b};
      const fr=`<span class="crc-d">${d.b}</span><span class="crc-c">${e.rem}</span>`;
      $('.netcn-chips').innerHTML=chip('Generator',E(g.b),'',`${E(CR.polyStr(g.b))}, degree r = ${e.r}`)+chip('Dividend',`${d.b}<span class="crc-z">${'0'.repeat(e.r)}</span>`,'',`data + ${e.r} zeros`)
        +chip('Quotient',e.q)+chip('Remainder (CRC)',e.rem,'main')+chip('Transmitted frame',fr,'main',`${fl} bits`)
        +chip('Receiver',k.ok?(k.undetected?'Accepts (undetected error!)':'Accepts'):'Rejects',k.ok&&!k.undetected?'ok':'bad',`remainder ${k.rem}`);
      $('.netcn-h').innerHTML=`Sender: divide data + ${e.r} zeros by ${E(g.b)} (mod-2)`;
      $('.crc-work').innerHTML=`<p>r = degree of ${E(CR.polyStr(g.b))} = <b>${e.r}</b> → append ${e.r} zeros: ${d.b} → ${e.dividend}.</p><p>${e.dividend} ÷ ${g.b} (mod-2) → quotient ${e.q}, remainder <b>${e.rem}</b>.</p><p>Transmitted frame = data ‖ remainder = ${d.b} ‖ ${e.rem} = <b>${e.frame}</b>. Check: ${e.frame} ÷ ${g.b} leaves remainder 0.</p>`;
      const rx=k.err?[...k.rx].map((b,i)=>k.pat[i]==='1'?`<span class="crc-flip">${b}</span>`:b).join(''):k.rx;
      $('.crc-rx').innerHTML=`<div class="netcn-f"><p>Received = frame XOR error pattern = ${e.frame} ⊕ ${k.pat} = <b>${rx}</b>${k.err?` (${k.nbits} bit${k.nbits===1?'':'s'} flipped)`:''}.</p><p>Received ÷ ${g.b} → remainder <b>${k.rem}</b>.</p></div>
        <p class="netcn-verdict ${k.ok&&!k.undetected?'ok':'bad'}">${k.undetected?'Remainder is 0, so the receiver <b>accepts a corrupted frame</b>: the error pattern is a multiple of the generator, so CRC cannot see it.':k.ok?'Remainder is 0 → <b>no error detected</b>; the receiver accepts the frame and keeps the first '+d.b.length+' bits as data.':'Remainder is not 0 → <b>error detected</b>; the frame is discarded.'}</p>`;
      $('.crc-recv').innerHTML=divTable(k.rx,g.b,k.steps,k.steps.length-1,{dataLen:k.rx.length});
      stepper($('.crc-st'),e.steps.length,i=>{
        $('.crc-send').innerHTML=divTable(e.dividend,g.b,e.steps,i,{dataLen:d.b.length});
        const s=e.steps[i],last=i===e.steps.length-1;
        $('.crc-cap').innerHTML=`<b>Step ${i+1}:</b> the window is ${s.win}; its leading bit is ${s.q}, so the quotient bit is <b>${s.q}</b> and we XOR with ${s.q==='1'?'the generator '+g.b:'zeros '+s.sub} → ${s.res}. `+(last?`No bits left to bring down: the remainder is <b>${e.rem}</b>.`:`Drop the leading 0 and bring down the next bit (${s.down}) → ${s.res.slice(1)+s.down}.`);
      },e.steps.length-1);
    };
    const upd=debounce(run,220);
    ['data','gen','pat'].forEach(k=>$(`[data-k=${k}]`).oninput=ev=>{st[k]=ev.target.value;upd();});
    const setPat=p=>{st.pat=p;$('[data-k=pat]').value=p;run();};
    $('[data-b=flip]').onclick=()=>{if(!res)return;const n=res.e.frame.length,i=rnd(0,n-1);setPat('0'.repeat(i)+'1'+'0'.repeat(n-1-i));};
    $('[data-b=clr]').onclick=()=>setPat('');
    $('[data-b=def]').onclick=()=>{st.data='1101011011';st.gen='10011';$('[data-k=data]').value=st.data;$('[data-k=gen]').value=st.gen;setPat('');};
    $('[data-b=rand]').onclick=()=>{const g=pick(['1011','1101','10011','11001','x^3 + x + 1','x^4 + x + 1','100101','x^8 + x^2 + x + 1']);const n=rnd(6,12);let d='1';for(let i=1;i<n;i++)d+=rnd(0,1);
      st.data=d;st.gen=g;$('[data-k=data]').value=d;$('[data-k=gen]').value=g;const r=CR.parsePoly(g).b.length-1;
      if(Math.random()<.5){const L=n+r,i=rnd(0,L-1);setPat('0'.repeat(i)+'1'+'0'.repeat(L-1-i));}else setPat('');};
    run();
  }

  function hamPane(){
    pane.innerHTML=`<div class="netcn-in"><div class="netcn-ctl">
      <label>Data bits<input type="text" data-k="hd" spellcheck="false" autocomplete="off" size="14"></label>
      <label>Parity<select data-k="par"><option value="even">Even parity</option><option value="odd">Odd parity</option></select></label>
      <label>Bit positions<select data-k="order"><option value="right">Position 1 on the right (… d3 p2 p1)</option><option value="left">Position 1 on the left (p1 p2 d3 …)</option></select></label>
      <label class="netcn-wide">Received codeword to check<input type="text" data-k="recv" spellcheck="false" autocomplete="off"></label></div>
      <div class="netcn-btns"><button type="button" class="btn sm" data-b="flip">Sent codeword with one bit flipped</button><button type="button" class="btn sm" data-b="same">Sent codeword, no error</button><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
      <p class="netcn-err" role="alert" hidden></p></div>
     <div class="netcn-out"><div class="netcn-chips"></div>
      <div class="netcn-h">Sender: place data, then compute each parity bit</div>
      <div class="crc-hst"></div><p class="netcn-note crc-hcap" aria-live="polite"></p>
      <div class="netcn-scroll"><table class="netcn-tbl crc-pos"></table></div>
      <div class="netcn-f crc-hwork"></div>
      <div class="netcn-h">Receiver: syndrome and correction</div>
      <div class="netcn-scroll"><table class="netcn-tbl crc-chk"></table></div><div class="crc-hres"></div>
      ${conv(['Number of parity bits r: the smallest r with 2<sup>r</sup> ≥ m + r + 1 (m data bits).','Parity bits sit at positions 1, 2, 4, 8, …; parity bit p<sub>k</sub> checks every position whose binary number has the bit of value k set.','Data bits fill the other positions in order; with “position 1 on the right” the leftmost data bit goes to the highest position.','Syndrome = sum of the positions of the failing checks = position of a single-bit error (0 = no error). The code has minimum distance 3: it corrects 1 error or detects 2, not both.'])}</div>`;
    const $=s=>pane.querySelector(s);
    $('[data-k=hd]').value=st.hd;$('[data-k=par]').value=st.par;$('[data-k=order]').value=st.order;$('[data-k=recv]').value=st.recv;
    let H=null;
    const posHead=(n,order)=>Array.from({length:n},(_,i)=>order==='right'?n-i:i+1);
    const run=()=>{
      const d=CR.parseBits(st.hd,'data');if(d.err){showErr(pane,d.err);return;}
      if(d.b.length>26){showErr(pane,'At most 26 data bits, please.');return;}
      const opt={parity:st.par,order:st.order};H=CR.hamming(d.b,opt);
      const rv=st.recv.replace(/[\s_]/g,'');
      if(rv&&!/^[01]+$/.test(rv)){showErr(pane,'The received codeword may contain only 0 and 1.');return;}
      showErr(pane,'');
      const{m,r,n}=H;
      $('.netcn-chips').innerHTML=chip('Data bits m',m)+chip('Parity bits r',r,'',`2^${r} = ${P2(r)} ≥ ${m} + ${r} + 1 = ${m+r+1}`)+chip('Codeword length n',n)+chip('Codeword',H.cells.map(c=>`<span class="crc-${c.type==='p'?'c':'d'}">${c.bit}</span>`).join(''),'main',`${st.par} parity`);
      const pos=posHead(n,st.order);
      const render=k=>{ /* k=0: data placed; k=j: parity bits 1..j computed */
        const cur=k>0?H.checks[k-1]:null;
        const known=new Set(H.checks.slice(0,k).map(c=>c.p));
        const cov=cur?new Set(cur.cov):new Set();
        const cellsHTML=H.cells.map(c=>{const cl=[c.type==='p'?'p':'d'];if(cov.has(c.pos))cl.push('cov');if(cur&&c.pos===cur.p)cl.push('cur');
          const b=c.type==='p'&&!known.has(c.pos)?'?':c.bit;return `<td class="${cl.join(' ')}">${b}</td>`;}).join('');
        $('.crc-pos').innerHTML=`<tbody><tr><th>Position</th>${pos.map(p=>`<td class="crc-pn">${p}</td>`).join('')}</tr>
          <tr><th>Binary</th>${pos.map(p=>`<td class="crc-bn">${p.toString(2).padStart(r,'0')}</td>`).join('')}</tr>
          <tr><th>Bit</th>${H.cells.map(c=>`<td class="crc-role">${c.type==='p'?'p'+c.pos:'d'+c.pos}</td>`).join('')}</tr>
          <tr class="crc-val"><th>Value</th>${cellsHTML}</tr></tbody>`;
        $('.crc-hcap').innerHTML=!cur?`Put the ${m} data bits ${d.b} into the non-power-of-2 positions (${H.cells.filter(c=>c.type==='d').map(c=>c.pos).sort((a,b)=>a-b).join(', ')}); positions ${H.checks.map(c=>c.p).join(', ')} wait for parity.`
          :`<b>p${cur.p}</b> covers positions ${cur.cov.join(', ')} (binary has the ${cur.p}-bit set). Data bits there contain <b>${cur.ones}</b> one${cur.ones===1?'':'s'} → for ${st.par} parity p${cur.p} = <b>${cur.bit}</b>.`;
      };
      stepper($('.crc-hst'),r+1,render,r);
      $('.crc-hwork').innerHTML=H.checks.map(c=>`<p>p${c.p} = ${st.par==='odd'?'NOT(':''}${c.cov.filter(j=>j!==c.p).map(j=>'b'+j).join(' ⊕ ')}${st.par==='odd'?')':''} = ${st.par==='odd'?'NOT(':''}${c.cov.filter(j=>j!==c.p).map(j=>H.cells.find(x=>x.pos===j).bit).join(' ⊕ ')}${st.par==='odd'?')':''} = <b>${c.bit}</b></p>`).join('')+`<p>Codeword (written ${st.order==='right'?`position ${n} … 1`:`position 1 … ${n}`}) = <b>${H.code}</b></p>`;
      /* receiver */
      const word=rv||H.code;const q=CR.hamCheck(word,opt);
      if(q.err){$('.crc-chk').innerHTML='';$('.crc-hres').innerHTML=`<p class="netcn-verdict bad">${E(q.err)}</p>`;return;}
      const bitAt=j=>word[CR.idxOf(j,q.n,st.order)];
      $('.crc-chk').innerHTML=`<thead><tr><th>Check</th><th>Positions</th><th>Bits</th><th>1s</th><th>Result</th></tr></thead><tbody>${q.checks.map(c=>`<tr class="${c.bad?'crc-fail':''}"><th>c${c.p}</th><td>${c.cov.join(', ')}</td><td>${c.cov.map(bitAt).join('')}</td><td>${c.ones}</td><td>${c.bad?`✗ ${st.par==='even'?'odd':'even'} count → c${c.p} = 1`:'✓ → 0'}</td></tr>`).join('')}</tbody>`;
      const synB=q.checks.slice().reverse().map(c=>c.bad?1:0).join('');
      const wr=q.pos?[...q.corrected].map((b,i)=>i===CR.idxOf(q.pos,q.n,st.order)?`<span class="crc-flip">${b}</span>`:b).join(''):q.corrected;
      let v=`<div class="netcn-f"><p>Received ${E(word)} (${q.n} bits → ${q.r} checks, ${q.m} data bits${CR.hammingR(q.m)!==q.r?'; note: not a standard Hamming length':''}).</p><p>Syndrome = ${q.checks.slice().reverse().map(c=>'c'+c.p).join(' ')} = ${synB}<sub>2</sub> = <b>${q.syn}</b>${q.checks.filter(c=>c.bad).length>1?` = ${q.checks.filter(c=>c.bad).map(c=>c.p).join(' + ')}`:''}.</p></div>`;
      if(!q.syn)v+=`<p class="netcn-verdict ok">Syndrome 0 → <b>no single-bit error</b>. Data = <b>${q.data}</b>.</p>`;
      else if(q.multi)v+=`<p class="netcn-verdict bad">Syndrome ${q.syn} is larger than n = ${q.n}: <b>more than one bit is wrong</b>, so the error cannot be corrected.</p>`;
      else v+=`<p class="netcn-verdict warn">Error at <b>position ${q.pos}</b> (${q.pos&(q.pos-1)?'a data bit':'a parity bit'}). Flip it → corrected codeword <b>${wr}</b>, data = <b>${q.data}</b>.</p>`;
      if(word.length===H.n&&word!==H.code){const dd=CR.distance(word,H.code);v+=`<p class="netcn-mut">Compared with the sent codeword ${H.code}: Hamming distance ${dd}${dd>1?` → with ${dd} errors the syndrome ${q.corrected===H.code?'still recovers the word by luck':'points to the wrong bit (the code only corrects 1 error)'}`:''}.</p>`;}
      $('.crc-hres').innerHTML=v;
    };
    const upd=debounce(run,220);
    $('[data-k=hd]').oninput=e=>{st.hd=e.target.value;upd();};
    $('[data-k=recv]').oninput=e=>{st.recv=e.target.value;upd();};
    $('[data-k=par]').onchange=e=>{st.par=e.target.value;run();};
    $('[data-k=order]').onchange=e=>{st.order=e.target.value;run();};
    const setRecv=v=>{st.recv=v;$('[data-k=recv]').value=v;run();};
    const flip=()=>{if(!H)return;const i=rnd(0,H.n-1);setRecv(H.code.slice(0,i)+(H.code[i]==='1'?'0':'1')+H.code.slice(i+1));};
    $('[data-b=flip]').onclick=flip;
    $('[data-b=same]').onclick=()=>{if(H)setRecv(H.code);};
    $('[data-b=def]').onclick=()=>{st.hd='1011';st.par='even';st.order='right';$('[data-k=hd]').value=st.hd;$('[data-k=par]').value='even';$('[data-k=order]').value='right';setRecv('1000101');};
    $('[data-b=rand]').onclick=()=>{const n=rnd(4,11);let d='';for(let i=0;i<n;i++)d+=rnd(0,1);st.hd=d;st.par=pick(['even','even','odd']);$('[data-k=hd]').value=d;$('[data-k=par]').value=st.par;st.recv='';run();flip();};
    run();
  }
  draw();
 }});

/* ---------------------------------------------------------------- slidewin UI */
const PNAME={sw:'Stop-and-wait',gbn:'Go-Back-N',sr:'Selective Repeat'};
function timelineSVG(sim,T,width){
  const u=18,top=34,Sx=Math.max(78,Math.min(96,width*0.2)),Rx=Math.max(Sx+120,width-112),H=top+(sim.end+1)*u+12;
  const y=t=>top+t*u;const id='swc'+(++UID);
  let g='';
  /* time grid every 5 units */
  for(let t=0;t<=sim.end;t+=5)g+=`<line x1="${Sx}" x2="${Rx}" y1="${y(t)}" y2="${y(t)}" class="slidewin-grid"/><text x="${Sx+4}" y="${y(t)-2}" class="slidewin-tk">t=${t}</text>`;
  for(const f of sim.frames){
    const lab=`F${f.f}`+(sim.N>sim.mod?` (${f.lab})`:'');
    const cls=f.lost?'lost':f.re?'re':'new';
    if(f.lost){const k=.55,x=Sx+(Rx-Sx)*k;g+=`<polygon points="${Sx},${y(f.t0)} ${Sx},${y(f.t1)} ${x},${y(f.t1+sim.P*k)} ${x},${y(f.t0+sim.P*k)}" class="slidewin-fr ${cls}"/><text x="${x+4}" y="${y(f.t1+sim.P*k)}" class="slidewin-x">✗ lost</text>`;}
    else g+=`<polygon points="${Sx},${y(f.t0)} ${Sx},${y(f.t1)} ${Rx},${y(f.arr)} ${Rx},${y(f.t0+sim.P)}" class="slidewin-fr ${cls}"/>`;
    g+=`<text x="${Sx-6}" y="${y(f.t0+.5)+4}" text-anchor="end" class="slidewin-fl ${cls}">${lab}</text>`;
    if(!f.lost){const st={accept:'✓ accept',buffer:'buffer',discard:'✗ discard',dup:'dup'}[f.rx]||'';
      const ack=sim.acks.find(a=>a.t0===f.arr);
      g+=`<text x="${Rx+6}" y="${y(f.arr)+4}" class="slidewin-rl ${f.rx}">${st}${ack?`, ACK ${ack.n}${sim.N>sim.mod?` (${ack.lab})`:''}`:''}</text>`;}
  }
  for(const a of sim.acks){
    if(a.lost){const k=.55,x=Rx-(Rx-Sx)*k;g+=`<line x1="${Rx}" y1="${y(a.t0)}" x2="${x}" y2="${y(a.t0+sim.P*k)}" class="slidewin-ack lost"/><text x="${x-4}" y="${y(a.t0+sim.P*k)+4}" text-anchor="end" class="slidewin-x">ACK lost ✗</text>`;}
    else g+=`<line x1="${Rx}" y1="${y(a.t0)}" x2="${Sx+3}" y2="${y(a.arr)}" class="slidewin-ack${a.eff==='dup'?' dup':''}" marker-end="url(#${id}m)"/>`;
  }
  for(const o of sim.timeouts)g+=`<line x1="${Sx-10}" x2="${Sx}" y1="${y(o.t)}" y2="${y(o.t)}" class="slidewin-to"/><text x="4" y="${y(o.t)+4}" class="slidewin-tol">⏱ F${o.f}</text>`;
  const clipH=T==null?H:y(T)+.5;
  return `<svg class="slidewin-svg" width="${width}" height="${H}" viewBox="0 0 ${width} ${H}" role="img" aria-label="Timeline of frames and acknowledgements">
   <defs><marker id="${id}m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" class="slidewin-ah"/></marker><clipPath id="${id}c"><rect x="0" y="0" width="${width}" height="${clipH}"/></clipPath></defs>
   <text x="${Sx}" y="14" text-anchor="middle" class="slidewin-hd">Sender</text><text x="${Rx}" y="14" text-anchor="middle" class="slidewin-hd">Receiver</text>
   <line x1="${Sx}" x2="${Sx}" y1="${top-8}" y2="${H-4}" class="slidewin-ax"/><line x1="${Rx}" x2="${Rx}" y1="${top-8}" y2="${H-4}" class="slidewin-ax"/>
   <g clip-path="url(#${id}c)">${g}</g>${T!=null&&T<sim.end?`<line x1="0" x2="${width}" y1="${y(T)}" y2="${y(T)}" class="slidewin-now"/>`:''}</svg>`;
}
function simEvents(sim,t){
  const ev=[];
  for(const a of sim.acks)if(!a.lost&&a.arr===t)ev.push(`ACK ${a.n} reaches the sender${a.eff==='dup'?' (duplicate, ignored)':sim.proto==='sr'?` (frame ${a.n} acknowledged)`:` (frames up to ${a.n-1} acknowledged)`}`);
  for(const o of sim.timeouts)if(o.t===t)ev.push(sim.proto==='sr'?`timer of F${o.f} expires → resend only F${o.f}`:`timer of F${o.f} expires → go back and resend from F${o.f}${o.to>o.f?` to F${o.to}`:''}`);
  for(const f of sim.frames)if(!f.lost&&f.arr===t)ev.push(`F${f.f} arrives: ${{accept:'in order, delivered',buffer:'out of order, buffered',discard:'out of order, discarded (Go-Back-N receiver window = 1)',dup:'duplicate, discarded and re-acknowledged'}[f.rx]}`);
  for(const f of sim.frames)if(f.t0===t)ev.push(`sender transmits ${f.re?'<b>retransmission</b> of ':''}F${f.f}${f.lost?' (it will be lost)':''}`);
  return ev;
}
ANIM.register('slidewin',{title:'Flow control: stop-and-wait, Go-Back-N, Selective Repeat',steps:false,
 caption:'Enter the link, frame and window to get utilisation, throughput, the optimal window and sequence-number bits; then step a small timeline, optionally losing a frame or an ACK.',
 build(stage){
  stage.style.padding='0';stage.classList.add('netcn-stage');
  const st={B:'1',Bu:'1e6',L:'1000',Lu:'8',dm:'dist',dist:'2000',v:'2e8',tp:'10',rtt:'20',W:'3',k:'',ack:'0',cyc:'full',
    proto:'gbn',N:'8',TW:'4',P:'2',lose:'f2'};
  stage.innerHTML=`<div class="netcn slidewin"><div class="netcn-in"><div class="netcn-ctl">
     <label>Bandwidth<span class="netcn-pair"><input type="text" data-k="B" size="6"><select data-k="Bu"><option value="1">bps</option><option value="1e3">kbps</option><option value="1e6">Mbps</option><option value="1e9">Gbps</option></select></span></label>
     <label>Frame size<span class="netcn-pair"><input type="text" data-k="L" size="6"><select data-k="Lu"><option value="1">bits</option><option value="8">bytes</option></select></span></label>
     <label>Delay given as<select data-k="dm"><option value="dist">distance and signal speed</option><option value="tp">propagation delay Tp</option><option value="rtt">round-trip time RTT</option></select></label>
     <label data-g="dist">Distance (km)<input type="text" data-k="dist" size="7"></label>
     <label data-g="dist">Speed (m/s)<input type="text" data-k="v" size="7"></label>
     <label data-g="tp">Tp (ms)<input type="text" data-k="tp" size="7"></label>
     <label data-g="rtt">RTT (ms)<input type="text" data-k="rtt" size="7"></label>
     <label>Window W (frames)<input type="text" data-k="W" size="4"></label>
     <label>Sequence bits k (optional)<input type="text" data-k="k" size="4" placeholder="—"></label>
     <label>ACK size (bits)<input type="text" data-k="ack" size="5"></label>
     <label class="netcn-wide">Utilisation formula<select data-k="cyc"><option value="full">Tt + 2Tp: η = 1/(1+2a) (standard)</option><option value="rtt">RTT only: η = 1/(2a) (BDP form)</option></select></label></div>
     <div class="netcn-btns"><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
     <p class="netcn-err" role="alert" hidden></p></div>
   <div class="netcn-out"><div class="netcn-chips"></div>
     <div class="netcn-scroll"><table class="netcn-tbl slidewin-cmp"></table></div>
     <div class="netcn-h">Working</div><div class="netcn-f slidewin-work"></div>
     ${conv(['Tt = frame size ÷ bandwidth, Tp = distance ÷ speed (default 2 × 10<sup>8</sup> m/s), a = Tp ÷ Tt.','Stop-and-wait η = Tt ÷ (Tt + 2Tp) = 1/(1+2a); a window of W frames gives η = min(1, W/(1+2a)). Processing and queueing delays are ignored; the ACK time counts only if you enter an ACK size.','Throughput = η × bandwidth (no errors). Optimal window = ⌈1 + 2a⌉ frames (keeps the pipe full).','Sequence numbers with k bits: Go-Back-N sender window ≤ 2<sup>k</sup> − 1 (receiver window 1); Selective Repeat windows ≤ 2<sup>k−1</sup>. Stop-and-wait needs 1 bit.'])}
     <div class="netcn-h slidewin-tlh">Timeline: small example (time unit = one frame time Tt)</div>
     <div class="netcn-ctl slidewin-tc">
      <div class="netcn-segw"><span>Protocol</span><div class="seg" data-k="proto"><button type="button" data-v="sw">Stop-and-wait</button><button type="button" data-v="gbn">Go-Back-N</button><button type="button" data-v="sr">Selective Repeat</button></div></div>
      <label>Frames<select data-k="N">${[3,4,5,6,7,8,9,10,12].map(n=>`<option>${n}</option>`).join('')}</select></label>
      <label data-g="win">Window<select data-k="TW">${[2,3,4,5,6,7].map(n=>`<option>${n}</option>`).join('')}</select></label>
      <label>Tp (in Tt)<select data-k="P">${[1,2,3,4].map(n=>`<option>${n}</option>`).join('')}</select></label>
      <label>Lose<select data-k="lose"></select></label></div>
     <div class="netcn-chips slidewin-tchips"></div>
     <div class="slidewin-st"></div><p class="netcn-note slidewin-cap" aria-live="polite"></p>
     <div class="netcn-scroll slidewin-box"></div>
     <p class="netcn-mut slidewin-leg"><span class="slidewin-sw new"></span> new frame <span class="slidewin-sw re"></span> retransmission <span class="slidewin-sw lost"></span> lost · arrows are ACKs (Go-Back-N / stop-and-wait ACK n = “next frame expected is n”; Selective Repeat ACK n = “frame n received”) · (s) = sequence number when frames wrap.</p>
   </div></div>`;
  const root=stage.querySelector('.slidewin'),$=s=>root.querySelector(s);
  ['B','Bu','L','Lu','dm','dist','v','tp','rtt','W','k','ack','cyc','N','TW','P'].forEach(k=>{const el=$(`[data-k=${k}]`);el.value=st[k];});
  const vis=()=>{root.querySelectorAll('[data-g=dist],[data-g=tp],[data-g=rtt]').forEach(l=>l.hidden=l.dataset.g!==st.dm);$('[data-g=win]').hidden=st.proto==='sw';};
  function calc(){
    const B=num(st.B)*+st.Bu,L=num(st.L)*+st.Lu,W=num(st.W),ack=num(st.ack||'0');
    let Tp;if(st.dm==='dist'){const d=num(st.dist),v=num(st.v);if(!(d>=0))return {err:'Distance must be a number ≥ 0 (km).'};if(!(v>0))return {err:'Signal speed must be a positive number (m/s), e.g. 2e8.'};Tp=d*1e3/v;}
    else if(st.dm==='tp'){Tp=num(st.tp)/1e3;if(!(Tp>=0))return {err:'Tp must be a number ≥ 0 (ms).'};}
    else {Tp=num(st.rtt)/2e3;if(!(Tp>=0))return {err:'RTT must be a number ≥ 0 (ms).'};}
    if(!(B>0))return {err:'Bandwidth must be a positive number.'};
    if(!(L>0))return {err:'Frame size must be a positive number.'};
    if(!(Number.isInteger(W)&&W>=1&&W<=1e6))return {err:'Window W must be a whole number ≥ 1.'};
    if(!(ack>=0))return {err:'ACK size must be a number ≥ 0 (0 = ignore ACK transmission time).'};
    let k=null;if(String(st.k).trim()){k=num(st.k);if(!(Number.isInteger(k)&&k>=1&&k<=32))return {err:'Sequence bits k must be a whole number from 1 to 32 (or blank).'};}
    if(st.cyc==='rtt'&&Tp===0)return {err:'With the RTT form the propagation delay must be above 0.'};
    return {r:SW.calc({B,L,Tp,W,k,ack,cyc:st.cyc}),B,L};
  }
  function run(){
    vis();const c=calc();if(c.err){showErr(root,c.err);return;}showErr(root,'');
    const r=c.r,B=c.B,L=c.L,full=st.cyc==='full';
    const den=full?`1 + 2a${r.Ta?' + Ta/Tt':''}`:'2a';const denV=r.cycle/r.Tt;
    $('.netcn-chips').innerHTML=chip('Tt (transmission)',fmtT(r.Tt),'',`${fmtN(L)} bits ÷ ${fmtR(B)}`)+chip('Tp (propagation)',fmtT(r.Tp))+chip('a = Tp / Tt',fmtN(r.a))
      +chip('Stop-and-wait η',pct(r.sw.eta),'main',fmtR(r.sw.thr))+chip(`Window W = ${r.W} η`,pct(r.gbn.eta),'main',fmtR(r.gbn.thr)+' (GBN or SR)')
      +chip('Optimal window',`${r.Wopt} frames`,'main',`⌈${den}⌉ = ⌈${fmtN(denV)}⌉`)+chip('Bandwidth × RTT',fmtN(r.bdp)+' bits','',`${fmtN(r.bdp/L)} frames`);
    const kb=r.k!=null;
    const rowP=(nm,sw,rw,eta,thr,bits,maxW,fits,formula)=>`<tr><th>${nm}</th><td>${sw}</td><td>${rw}</td><td class="slidewin-fm">${formula}</td><td><b>${pct(eta)}</b></td><td>${fmtR(thr)}</td><td>${bits}</td>${kb?`<td class="${fits===false?'netcn-badt':''}">${maxW}${fits===false?' ✗':''}</td>`:''}</tr>`;
    const wf=`min(1, ${r.W}/${fmtN(denV)})`;
    $('.slidewin-cmp').innerHTML=`<thead><tr><th>Protocol</th><th>Sender<small>window</small></th><th>Receiver<small>window</small></th><th>η formula</th><th>η</th><th>Throughput</th><th>Seq bits<small>needed for W</small></th>${kb?`<th>Max window<small>with k = ${r.k}</small></th>`:''}</tr></thead><tbody>
      ${rowP('Stop-and-wait',1,1,r.sw.eta,r.sw.thr,1,1,true,`1/${fmtN(denV)}`)}
      ${rowP('Go-Back-N',r.W,1,r.gbn.eta,r.gbn.thr,`⌈log₂(${r.W}+1)⌉ = ${r.gbn.bits}`,kb?r.maxGBN:'',kb?r.gbn.fits:null,wf)}
      ${rowP('Selective Repeat',r.W,r.W,r.sr.eta,r.sr.thr,`⌈log₂(2·${r.W})⌉ = ${r.sr.bits}`,kb?r.maxSR:'',kb?r.sr.fits:null,wf)}</tbody>`;
    let w=`<p>Tt = L / B = ${fmtN(L)} / ${fmtN(B)} = <b>${fmtT(r.Tt)}</b></p>`;
    w+=st.dm==='dist'?`<p>Tp = d / v = ${fmtN(num(st.dist)*1e3)} m / ${fmtN(num(st.v))} m/s = <b>${fmtT(r.Tp)}</b></p>`:st.dm==='rtt'?`<p>Tp = RTT / 2 = <b>${fmtT(r.Tp)}</b></p>`:'';
    w+=`<p>a = Tp / Tt = ${fmtN(r.Tp)} / ${fmtN(r.Tt)} = <b>${fmtN(r.a)}</b></p>`;
    w+=full?`<p>Stop-and-wait: η = Tt / (Tt + ${r.Ta?'Ta + ':''}2Tp) = 1 / (${den}) = 1 / ${fmtN(denV)} = <b>${pct(r.sw.eta)}</b>${r.Ta?` (Ta = ${fmtT(r.Ta)})`:''}</p>`:`<p>Stop-and-wait: η = Tt / RTT = 1 / (2a) = 1 / ${fmtN(denV)} = <b>${pct(r.sw.eta)}</b>${r.sw.eta>=1?' (capped at 100%)':''}</p>`;
    w+=`<p>Window W = ${r.W}: η = min(1, W / ${fmtN(denV)}) = <b>${pct(r.gbn.eta)}</b>${r.gbn.eta>=1?' (the window covers the whole round trip)':''}; throughput = η × B = <b>${fmtR(r.gbn.thr)}</b></p>`;
    w+=`<p>Optimal window W<sub>opt</sub> = ⌈${den}⌉ = ⌈${fmtN(denV)}⌉ = <b>${r.Wopt}</b> → sequence bits: Go-Back-N ⌈log₂(${r.Wopt}+1)⌉ = <b>${r.gbn.bitsOpt}</b>, Selective Repeat ⌈log₂(2·${r.Wopt})⌉ = <b>${r.sr.bitsOpt}</b>.</p>`;
    if(kb)w+=`<p>With k = ${r.k} bits (sequence numbers 0–${P2(r.k)-1}): Go-Back-N window ≤ 2<sup>${r.k}</sup> − 1 = <b>${r.maxGBN}</b>, Selective Repeat window ≤ 2<sup>${r.k}−1</sup> = <b>${r.maxSR}</b>.${!r.gbn.fits||!r.sr.fits?` W = ${r.W} is too large${r.gbn.fits?' for Selective Repeat':''}; limited to that maximum, η would be GBN ${pct(r.gbn.etaK)}, SR ${pct(r.sr.etaK)}.`:''}</p>`;
    $('.slidewin-work').innerHTML=w;
  }
  function loseOpts(){
    const N=+st.N,sel=$('[data-k=lose]');let o='<option value="none">nothing</option>';
    for(let i=0;i<N;i++)o+=`<option value="f${i}">frame F${i}</option>`;for(let i=0;i<N;i++)o+=`<option value="a${i}">ACK for F${i}</option>`;
    sel.innerHTML=o;if(!/^[fa]\d+$/.test(st.lose)||+st.lose.slice(1)>=N)st.lose=st.lose==='none'?'none':'f'+Math.min(N-1,2);sel.value=st.lose;
  }
  let lastW=0,SIM=null,stp=null;
  function tl(){
    loseOpts();vis();
    const lose=st.lose[0]==='f'?+st.lose.slice(1):-1,loseAck=st.lose[0]==='a'?+st.lose.slice(1):-1;
    SIM=SW.sim({proto:st.proto,N:+st.N,W:+st.TW,P:+st.P,lose,loseAck});
    const s=SIM;
    $('.slidewin-tchips').innerHTML=chip('Total time',`${s.end} Tt`,'main')+chip('Frames sent',s.tx,'',`${s.N} new + ${s.re} retransmitted`)+chip('Utilisation of this run',pct(s.util),'',`${s.N}·Tt / ${s.end}·Tt`)
      +chip('Timeout',`${s.To} Tt`,'',`2·Tp + Tt, from end of sending`)+chip('Sequence numbers',`${s.k} bit${s.k>1?'s':''}`,'',`0–${s.mod-1}, window ${s.W}`);
    const times=[...new Set([0,...s.frames.map(f=>f.t0),...s.frames.filter(f=>!f.lost).map(f=>f.arr),...s.acks.filter(a=>!a.lost).map(a=>a.arr),...s.timeouts.map(o=>o.t),s.end])].sort((a,b)=>a-b);
    const box=$('.slidewin-box');
    const render=i=>{const T=times[i];lastW=Math.max(300,Math.min(560,box.clientWidth||520));box.innerHTML=timelineSVG(s,i===times.length-1?null:T,lastW);
      const ev=simEvents(s,T);$('.slidewin-cap').innerHTML=`<b>t = ${T}:</b> `+(i===times.length-1?`all ${s.N} frames are acknowledged at t = ${s.end}. ${s.re?`${s.re} retransmission${s.re>1?'s':''} (${PNAME[s.proto]}${s.proto==='gbn'?' resends every outstanding frame after a timeout':s.proto==='sr'?' resends only the missing frame':''}).`:'No retransmissions.'}`:(ev.join('; ')||'waiting')+'.');};
    stp=stepper($('.slidewin-st'),times.length,render,times.length-1);
  }
  const upd=debounce(run,220);
  ['B','L','dist','v','tp','rtt','W','k','ack'].forEach(k=>$(`[data-k=${k}]`).oninput=e=>{st[k]=e.target.value;upd();});
  ['Bu','Lu','dm','cyc'].forEach(k=>$(`[data-k=${k}]`).onchange=e=>{st[k]=e.target.value;run();});
  ['N','TW','P','lose'].forEach(k=>$(`[data-k=${k}]`).onchange=e=>{st[k]=e.target.value;tl();});
  seg($('[data-k=proto]'),st.proto,v=>{st.proto=v;tl();});
  $('[data-b=def]').onclick=()=>{Object.assign(st,{B:'1',Bu:'1e6',L:'1000',Lu:'8',dm:'dist',dist:'2000',v:'2e8',W:'3',k:'',ack:'0',cyc:'full'});['B','Bu','L','Lu','dm','dist','v','W','k','ack','cyc'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);run();};
  $('[data-b=rand]').onclick=()=>{const [b,bu]=pick([['1','1e6'],['10','1e6'],['100','1e6'],['1','1e9'],['64','1e3'],['50','1e3'],['4','1e6']]);
    Object.assign(st,{B:b,Bu:bu,L:String(pick([1000,1024,1500,512,2000])),Lu:pick(['1','8']),W:String(rnd(1,15)),k:Math.random()<.4?String(rnd(3,6)):'',ack:'0',cyc:'full'});
    st.dm=pick(['dist','tp','rtt']);st.dist=String(pick([1000,2000,3000,5000,36000]));st.v='2e8';st.tp=String(pick([5,10,20,25,270]));st.rtt=String(pick([10,20,40,80]));
    ['B','Bu','L','Lu','dm','dist','v','tp','rtt','W','k','ack','cyc'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);run();
    st.proto=pick(['sw','gbn','sr']);st.N=String(pick([5,6,8]));st.TW=String(rnd(3,5));st.P=String(rnd(1,3));st.lose=pick(['none','f'+rnd(1,3),'a'+rnd(0,2)]);
    ['N','TW','P'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);seg($('[data-k=proto]'),st.proto,v=>{st.proto=v;tl();});tl();};
  if(typeof ResizeObserver!=='undefined'){const ro=new ResizeObserver(()=>{const b=$('.slidewin-box');if(!b||!stp)return;const w=Math.max(300,Math.min(560,b.clientWidth||520));if(Math.abs(w-lastW)>8)stp.go(stp.i);});ro.observe($('.slidewin-box'));}
  run();tl();
 }});

/* ---------------------------------------------------------------- tcpcong UI */
function congChart(res,other,upto,width,th0){
  const H=250,ml=38,mr=12,mt=16,mb=34,R=res.rows,N=R.length;
  const ymax0=Math.max(th0,...R.map(r=>Math.max(r.cwnd,r.ssthresh)),...(other?other.rows.map(r=>r.cwnd):[]));
  const stepY=ymax0<=12?2:ymax0<=24?4:ymax0<=48?8:ymax0<=100?10:ymax0<=200?25:50,ymax=Math.ceil((ymax0+1)/stepY)*stepY;
  const x=r=>ml+(N===1?0.5:(r-1)/(N-1))*(width-ml-mr),y=v=>mt+(1-v/ymax)*(H-mt-mb);
  let g='';
  for(let v=0;v<=ymax;v+=stepY)g+=`<line x1="${ml}" x2="${width-mr}" y1="${y(v)}" y2="${y(v)}" class="tcpcong-grid"/><text x="${ml-6}" y="${y(v)+4}" text-anchor="end" class="tcpcong-tk">${v}</text>`;
  const xs=Math.max(1,Math.ceil(N/Math.max(4,Math.floor((width-ml-mr)/34))));
  for(let r=1;r<=N;r+=xs)g+=`<text x="${x(r)}" y="${H-mb+16}" text-anchor="middle" class="tcpcong-tk">${r}</text>`;
  g+=`<text x="${(ml+width-mr)/2}" y="${H-4}" text-anchor="middle" class="tcpcong-ax">transmission round</text><text x="12" y="${mt+(H-mt-mb)/2}" text-anchor="middle" transform="rotate(-90 12 ${mt+(H-mt-mb)/2})" class="tcpcong-ax">cwnd (MSS)</text>`;
  const vis=R.slice(0,upto+1);
  /* ssthresh as a dashed step line */
  let th='';vis.forEach((r,i)=>{const x0=x(r.r)-(i===0?0:(x(2)-x(1))/2),x1=x(r.r)+(i===vis.length-1?0:(x(2)-x(1))/2);th+=`${i?'L':'M'}${x0.toFixed(1)},${y(r.ssthresh).toFixed(1)}L${x1.toFixed(1)},${y(r.ssthresh).toFixed(1)}`;});
  g+=`<path d="${th}" class="tcpcong-th"/>`;
  if(other){const ov=other.rows.slice(0,upto+1);g+=`<polyline points="${ov.map(r=>`${x(r.r).toFixed(1)},${y(r.cwnd).toFixed(1)}`).join(' ')}" class="tcpcong-ghost"/>`;}
  g+=`<polyline points="${vis.map(r=>`${x(r.r).toFixed(1)},${y(r.cwnd).toFixed(1)}`).join(' ')}" class="tcpcong-line"/>`;
  vis.forEach((r,i)=>{g+=`<circle cx="${x(r.r)}" cy="${y(r.cwnd)}" r="${i===upto?5.5:3.6}" class="tcpcong-pt ${r.phase==='SS'?'ss':'ca'}${i===upto?' cur':''}"><title>round ${r.r}: cwnd ${r.cwnd}</title></circle>`;
    if(r.ev)g+=`<text x="${x(r.r)}" y="${y(r.cwnd)-9}" text-anchor="middle" class="tcpcong-ev">${r.ev==='timeout'?'TO':'3 dup'}</text>`;});
  return `<svg class="tcpcong-svg" width="${width}" height="${H}" viewBox="0 0 ${width} ${H}" role="img" aria-label="Congestion window per round">${g}</svg>`;
}
ANIM.register('tcpcong',{title:'TCP congestion window: Tahoe vs Reno',steps:false,
 caption:'Set the initial ssthresh and the rounds where a timeout or three duplicate ACKs happen. The chart and table give cwnd for every round; switch between Tahoe and Reno.',
 build(stage){
  stage.style.padding='0';stage.classList.add('netcn-stage');
  const st={variant:'reno',th:'8',cw0:'1',rounds:'20',ev:'8:3dup, 16:timeout',mss:'',rwnd:'',cap:'cap',r3:'half',cmp:true};
  stage.innerHTML=`<div class="netcn tcpcong"><div class="netcn-in"><div class="netcn-ctl">
     <div class="netcn-segw"><span>Variant</span><div class="seg" data-k="variant"><button type="button" data-v="tahoe">TCP Tahoe</button><button type="button" data-v="reno">TCP Reno</button></div></div>
     <label>Initial ssthresh (MSS)<input type="text" data-k="th" size="4"></label>
     <label>Initial cwnd (MSS)<input type="text" data-k="cw0" size="4"></label>
     <label>Rounds<input type="text" data-k="rounds" size="4"></label>
     <label class="netcn-wide">Loss events (round:type, type = timeout or 3dup)<input type="text" data-k="ev" spellcheck="false" autocomplete="off"></label>
     <label>MSS in bytes (optional)<input type="text" data-k="mss" size="6" placeholder="—"></label>
     <label>Receiver window (MSS, optional)<input type="text" data-k="rwnd" size="5" placeholder="none"></label>
     <label>Slow start near ssthresh<select data-k="cap"><option value="cap">cwnd = min(2·cwnd, ssthresh)</option><option value="over">doubles past ssthresh, then +1</option></select></label>
     <label>Reno after 3 dup ACKs<select data-k="r3"><option value="half">cwnd = new ssthresh</option><option value="plus3">cwnd = new ssthresh + 3 (Kurose)</option></select></label>
     <label class="chk"><input type="checkbox" data-k="cmp"> Show the other variant as a dashed line</label></div>
     <div class="netcn-btns"><button type="button" class="btn sm" data-b="rand">🎲 Random example</button><button type="button" class="btn sm" data-b="def">Default</button></div>
     <p class="netcn-err" role="alert" hidden></p></div>
   <div class="netcn-out"><div class="netcn-chips"></div>
     <div class="tcpcong-st"></div><p class="netcn-note tcpcong-cap" aria-live="polite"></p>
     <div class="netcn-scroll tcpcong-box"></div>
     <p class="netcn-mut tcpcong-leg"><span class="tcpcong-sw ss"></span> slow start <span class="tcpcong-sw ca"></span> congestion avoidance <span class="tcpcong-sw th"></span> ssthresh <span class="tcpcong-sw gh"></span> <span class="tcpcong-other"></span></p>
     <div class="netcn-scroll"><table class="netcn-tbl tcpcong-tbl"></table></div>
     ${conv(['cwnd is counted in MSS per transmission round (one RTT). Round 1 starts with the initial cwnd.','Slow start while cwnd &lt; ssthresh: cwnd doubles each round. Congestion avoidance while cwnd ≥ ssthresh: cwnd + 1 each round.','An event at round r happens while sending with that round’s cwnd; the new values apply from round r + 1.','Timeout (Tahoe and Reno) and 3 duplicate ACKs in Tahoe: ssthresh = max(⌊cwnd/2⌋, 2), cwnd = 1, back to slow start.','3 duplicate ACKs in Reno (fast retransmit + fast recovery): ssthresh = max(⌊cwnd/2⌋, 2), cwnd = ssthresh (or ssthresh + 3), then congestion avoidance.','Segments sent per round = min(cwnd, receiver window).'])}
   </div></div>`;
  const root=stage.querySelector('.tcpcong'),$=s=>root.querySelector(s);
  ['th','cw0','rounds','ev','mss','rwnd','cap','r3'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);$('[data-k=cmp]').checked=st.cmp;
  let stp=null,lastW=0;
  const pint=(s,lo,hi,name)=>{const v=num(s);return Number.isInteger(v)&&v>=lo&&v<=hi?{v}:{err:`${name} must be a whole number from ${lo} to ${hi}.`};};
  function run(){
    const th=pint(st.th,1,1e6,'Initial ssthresh'),cw=pint(st.cw0,1,1e6,'Initial cwnd'),rn=pint(st.rounds,1,60,'Rounds');
    const bad=[th,cw,rn].find(x=>x.err);if(bad){showErr(root,bad.err);return;}
    const ev=TC.parseEvents(st.ev,rn.v);if(ev.err){showErr(root,ev.err);return;}
    let rw=null;if(String(st.rwnd).trim()){const q=pint(st.rwnd,1,1e6,'Receiver window');if(q.err){showErr(root,q.err);return;}rw=q.v;}
    let mss=null;if(String(st.mss).trim()){const q=pint(st.mss,1,1e7,'MSS');if(q.err){showErr(root,q.err);return;}mss=q.v;}
    showErr(root,'');
    const base={ssthresh:th.v,cwnd0:cw.v,rounds:rn.v,ev:ev.ev,cap:st.cap==='cap',plus3:st.r3==='plus3',rwnd:rw};
    const res=TC.run(Object.assign({variant:st.variant},base)),oth=st.cmp?TC.run(Object.assign({},base,{variant:st.variant==='reno'?'tahoe':'reno'})):null;
    const V=st.variant==='reno'?'Reno':'Tahoe',OV=st.variant==='reno'?'Tahoe':'Reno';
    $('.tcpcong-other').textContent=st.cmp?`TCP ${OV} (for comparison)`:'';$('.tcpcong-sw.gh').hidden=!st.cmp;
    const R=res.rows,last=R[R.length-1],ss=R.filter(r=>r.phase==='SS').length;
    const B=v=>mss?` (${(v*mss).toLocaleString('en')} B)`:'';
    $('.netcn-chips').innerHTML=chip(`cwnd in round ${last.r}`,last.cwnd+' MSS','main',B(last.cwnd).trim())+chip('ssthresh in round '+last.r,last.ssthresh+' MSS')+chip('Next round',`cwnd ${res.finalCwnd}, ssthresh ${res.finalTh}`)
      +chip('Segments sent',res.sent.toLocaleString('en'),'main',mss?(res.sent*mss).toLocaleString('en')+' bytes':`rounds 1–${last.r}`)+chip('Largest cwnd',res.maxCwnd+' MSS')+chip('Rounds',`${ss} slow start, ${R.length-ss} CA`);
    const why=r=>{const t=r.newTh;switch(r.rule){
      case 'ss':return `slow start → ${r.nextCwnd}`;case 'sscap':return `2·${r.cwnd} = ${2*r.cwnd} > ${r.ssthresh} → capped ${r.nextCwnd}`;case 'ca':return `+1 → ${r.nextCwnd}`;
      case 'timeout':return `ssthresh = ⌊${r.cwnd}/2⌋${Math.floor(r.cwnd/2)<2?'→2':''} = ${t}, cwnd = 1`;case 'tahoe3':return `Tahoe: ssthresh = ${t}, cwnd = 1`;
      case 'reno3':return `Reno: ssthresh = ${t}, cwnd = ${r.nextCwnd}`;}return '';};
    const render=i=>{
      lastW=Math.max(320,Math.min(760,$('.tcpcong-box').clientWidth||600));
      $('.tcpcong-box').innerHTML=congChart(res,oth,i,lastW,th.v);
      $('.tcpcong-tbl').innerHTML=`<thead><tr><th>Round</th><th>Phase</th><th>cwnd</th><th>ssthresh</th>${rw?'<th>Sent<small>min(cwnd, rwnd)</small></th>':''}${mss?'<th>Bytes<small>sent</small></th>':''}<th>Event</th><th>Next round</th>${oth?`<th>${OV}<small>cwnd</small></th>`:''}</tr></thead><tbody>${R.map((r,k)=>`<tr class="${k===i?'cur':k>i?'netcn-pend':''}"><th>${r.r}</th><td>${r.phase==='SS'?'Slow start':'Cong. avoid.'}</td><td><b>${r.cwnd}</b></td><td>${r.ssthresh}</td>${rw?`<td>${r.send}</td>`:''}${mss?`<td>${(r.send*mss).toLocaleString('en')}</td>`:''}<td>${r.ev?`<span class="tcpcong-evt">${r.ev==='timeout'?'Timeout':'3 dup ACKs'}</span>`:''}</td><td class="tcpcong-why">${why(r)}</td>${oth?`<td>${oth.rows[k].cwnd}</td>`:''}</tr>`).join('')}</tbody>`;
      const r=R[i],t=r.newTh;let c=`<b>Round ${r.r}:</b> cwnd = ${r.cwnd}${B(r.cwnd)}, ssthresh = ${r.ssthresh}${rw&&r.send<r.cwnd?`, but the receiver window limits sending to ${r.send}`:''}. `;
      c+={ss:`Slow start (cwnd &lt; ssthresh): each ACK adds 1 MSS, so cwnd doubles to <b>${r.nextCwnd}</b>.`,
        sscap:`Doubling would give ${2*r.cwnd}, above ssthresh ${r.ssthresh}, so cwnd is capped at <b>${r.nextCwnd}</b> and congestion avoidance starts.`,
        ca:`Congestion avoidance (cwnd ≥ ssthresh): cwnd grows by 1 MSS per RTT to <b>${r.nextCwnd}</b>.`,
        timeout:`<b>Timeout</b>: ssthresh = max(⌊${r.cwnd}/2⌋, 2) = <b>${t}</b>, cwnd = <b>1</b>, slow start again.`,
        tahoe3:`<b>3 duplicate ACKs</b>: Tahoe treats them like a timeout: ssthresh = max(⌊${r.cwnd}/2⌋, 2) = <b>${t}</b>, cwnd = <b>1</b>.`,
        reno3:`<b>3 duplicate ACKs</b>: Reno does fast retransmit and fast recovery: ssthresh = max(⌊${r.cwnd}/2⌋, 2) = <b>${t}</b>, cwnd = ${st.r3==='plus3'?`${t} + 3 = `:''}<b>${r.nextCwnd}</b>, then congestion avoidance.`}[r.rule];
      $('.tcpcong-cap').innerHTML=c;
    };
    stp=stepper($('.tcpcong-st'),R.length,render,R.length-1);
  }
  const upd=debounce(run,250);
  ['th','cw0','rounds','ev','mss','rwnd'].forEach(k=>$(`[data-k=${k}]`).oninput=e=>{st[k]=e.target.value;upd();});
  ['cap','r3'].forEach(k=>$(`[data-k=${k}]`).onchange=e=>{st[k]=e.target.value;run();});
  $('[data-k=cmp]').onchange=e=>{st.cmp=e.target.checked;run();};
  seg($('[data-k=variant]'),st.variant,v=>{st.variant=v;run();});
  $('[data-b=def]').onclick=()=>{Object.assign(st,{th:'8',cw0:'1',rounds:'20',ev:'8:3dup, 16:timeout',mss:'',rwnd:'',cap:'cap',r3:'half'});['th','cw0','rounds','ev','mss','rwnd','cap','r3'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);run();};
  $('[data-b=rand]').onclick=()=>{const n=rnd(16,26),th=pick([8,12,16,20,32,64]);const e=[];let r=rnd(6,Math.min(12,n-6));e.push(r+':'+pick(['3dup','timeout']));if(Math.random()<.7){r+=rnd(5,8);if(r<n)e.push(r+':'+pick(['3dup','timeout']));}
    Object.assign(st,{th:String(th),cw0:'1',rounds:String(n),ev:e.join(', '),mss:Math.random()<.3?'1024':'',rwnd:Math.random()<.2?String(rnd(10,24)):''});['th','cw0','rounds','ev','mss','rwnd'].forEach(k=>$(`[data-k=${k}]`).value=st[k]);run();};
  if(typeof ResizeObserver!=='undefined'){const ro=new ResizeObserver(()=>{const b=$('.tcpcong-box');if(!stp)return;const w=Math.max(320,Math.min(760,b.clientWidth||600));if(Math.abs(w-lastW)>8)stp.go(stp.i);});ro.observe($('.tcpcong-box'));}
  run();
 }});

})();

/* ================= NET solvers · group "coa" =================
   cachemap (cache mapping + LRU/FIFO simulation), amat (cache levels, TLB, page-fault EAT),
   pipeline (space-time diagram, speedup), ieee754 (encode/decode), kmap (K-map + Quine–McCluskey).
   Pure algorithms are attached to window.NETSOLVE.<id> so they can be tested in Node. */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;

/* ====================================================================
   Shared pure helpers
   ==================================================================== */
const lg2=n=>{if(!(n>0)||!isFinite(n))return NaN;const e=Math.round(Math.log2(n));return 2**e===n?e:NaN;};
const isP2=n=>!isNaN(lg2(n));
function parseNum(s){
  if(typeof s==='number')return s;
  s=String(s==null?'':s).trim().replace(/\s+/g,'').replace(/,/g,'');
  if(!s)return NaN;
  let m;
  if((m=/^([+-]?\d+(?:\.\d+)?)\^([+-]?\d+)$/.exec(s)))return (+m[1])**(+m[2]);
  if((m=/^(.+)%$/.exec(s)))return parseNum(m[1])/100;
  if((m=/^([^/]+)\/([^/]+)$/.exec(s))){const a=parseNum(m[1]),b=parseNum(m[2]);return b?a/b:NaN;}
  if(/^[+-]?0x[0-9a-f]+$/i.test(s))return parseInt(s,16);
  if(/^0b[01]+$/i.test(s))return parseInt(s.slice(2),2);
  if(/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s))return Number(s);
  return NaN;
}
function parseList(s,decimalOnly){
  const toks=String(s||'').split(/[\s,;]+/).filter(Boolean),vals=[],bad=[];
  toks.forEach(t=>{let v=NaN;
    if(/^\d+$/.test(t))v=parseInt(t,10);
    else if(!decimalOnly&&/^0x[0-9a-f]+$/i.test(t))v=parseInt(t,16);
    else if(!decimalOnly&&/^0b[01]+$/i.test(t))v=parseInt(t.slice(2),2);
    if(Number.isSafeInteger(v))vals.push(v);else bad.push(t);});
  return {vals,bad};
}
function fmt(x,d){
  if(d==null)d=4;
  if(x===Infinity)return '∞';if(x===-Infinity)return '−∞';
  if(typeof x!=='number'||isNaN(x))return '—';
  if(x!==0&&Math.abs(x)<1e-4)return x.toExponential(3).replace(/\.?0+e/,'e');
  if(Math.abs(x)>=1e15)return x.toExponential(4).replace(/\.?0+e/,'e');
  const s=String(+x.toFixed(d));return s==='-0'?'0':s;
}
const popc=x=>{let c=0;while(x){x&=x-1;c++;}return c;};
function fmtBytes(b){for(const [u,v] of [['TB',2**40],['GB',2**30],['MB',2**20],['KB',1024]])if(b>=v&&b%v===0)return (b/v)+' '+u;return b+' B';}
function fmtBits(bits){let s=bits+' bits';if(bits%8===0){const B=bits/8;s+=' = '+B+' bytes';if(B>=1024&&B%1024===0)s+=' = '+fmtBytes(B);}return s;}

/* ====================================================================
   cachemap — geometry and simulation
   ==================================================================== */
const UNIT_BYTES={B:1,KB:2**10,MB:2**20,GB:2**30,TB:2**40};
function cmSizeBytes(v,u,wb){
  if(u in UNIT_BYTES)return v*UNIT_BYTES[u];
  if(u==='words')return v*wb;if(u==='K words')return v*1024*wb;if(u==='M words')return v*2**20*wb;
  return NaN;
}
/* o: {mmBytes | addrBits, cacheBytes, blockBytes, unitBytes, mapping:'direct'|'set'|'full', k, valid, dirty} (all sizes in bytes) */
function cmGeometry(o){
  const E=m=>({error:m});
  const unit=o.unitBytes==null?1:o.unitBytes;
  if(!(unit>0)||!isP2(unit))return E('Word size must be a power of 2 bytes (1, 2, 4, 8 …).');
  let mm=o.mmBytes;
  if(o.addrBits!=null){
    if(!Number.isInteger(o.addrBits)||o.addrBits<1||o.addrBits>64)return E('Address bits must be a whole number from 1 to 64.');
    mm=2**o.addrBits*unit;
  }
  const chk=[[mm,'Main memory size'],[o.cacheBytes,'Cache size'],[o.blockBytes,'Block size']];
  for(const [v,nm] of chk)if(!(v>0)||!isFinite(v))return E(nm+' must be a positive number.');
  if(!isP2(mm))return E('Main memory size must be a power of 2 (e.g. 64 KB, 4 GB).');
  if(!isP2(o.blockBytes))return E('Block size must be a power of 2.');
  if(o.blockBytes<unit)return E('A block must hold at least one addressable word.');
  if(o.cacheBytes<o.blockBytes)return E('The cache must hold at least one block.');
  if(o.cacheBytes>mm)return E('The cache cannot be larger than main memory.');
  const lines=o.cacheBytes/o.blockBytes;
  if(!Number.isInteger(lines))return E('Cache size must be a whole number of blocks.');
  const units=mm/unit;
  if(!Number.isInteger(units)||units<1)return E('Main memory must be at least one word.');
  const addrBits=lg2(units),blockUnits=o.blockBytes/unit,offsetBits=lg2(blockUnits);
  let ways,sets;
  if(o.mapping==='direct'){ways=1;sets=lines;}
  else if(o.mapping==='full'){ways=lines;sets=1;}
  else{
    const k=o.k;
    if(!Number.isInteger(k)||k<1)return E('k (lines per set) must be a positive whole number.');
    if(k>lines)return E(`k = ${k} is more than the ${lines} lines in the cache.`);
    if(lines%k)return E(`${lines} lines cannot be split evenly into sets of ${k}.`);
    ways=k;sets=lines/k;
  }
  if(!isP2(sets))return E(`The number of ${o.mapping==='direct'?'lines':'sets'} (${sets}) must be a power of 2, so that it maps to whole index bits.`);
  const indexBits=lg2(sets),tagBits=addrBits-indexBits-offsetBits;
  const extra=(o.valid?1:0)+(o.dirty?1:0);
  return {mapping:o.mapping,unitBytes:unit,mmBytes:mm,cacheBytes:o.cacheBytes,blockBytes:o.blockBytes,units,addrBits,blockUnits,offsetBits,
    lines,sets,ways,indexBits,tagBits,mmBlocks:mm/o.blockBytes,extra,perLine:tagBits+extra,tagMemBits:(tagBits+extra)*lines,
    blocksPerSet:(mm/o.blockBytes)/sets};
}
/* o: {sets, ways, blockUnits, kind:'block'|'addr', refs:[int], policy:'LRU'|'FIFO'} */
function cmSim(o){
  const state=new Map(),seen=new Set(),steps=[];let hits=0;
  o.refs.forEach((a,t)=>{
    const b=o.kind==='addr'?Math.floor(a/o.blockUnits):a,off=o.kind==='addr'?a%o.blockUnits:null;
    const set=b%o.sets,tag=Math.floor(b/o.sets);
    let ways=state.get(set);if(!ways){ways=Array(o.ways).fill(null);state.set(set,ways);}
    let w=ways.findIndex(x=>x&&x.b===b),ev=null;const hit=w>=0,cold=!seen.has(b);seen.add(b);
    if(hit){ways[w].last=t;hits++;}
    else{
      w=ways.indexOf(null);
      if(w<0){const key=o.policy==='FIFO'?'ins':'last';w=0;for(let i=1;i<ways.length;i++)if(ways[i][key]<ways[w][key])w=i;ev=ways[w].b;}
      ways[w]={b,tag,last:t,ins:t};
    }
    steps.push({t,a,b,off,set,tag,hit,way:w,ev,cold});
  });
  const n=steps.length;
  return {steps,hits,misses:n-hits,ratio:n?hits/n:0,cold:steps.filter(s=>!s.hit&&s.cold).length,state};
}
NETSOLVE.cachemap={geometry:cmGeometry,simulate:cmSim,sizeBytes:cmSizeBytes};

/* ====================================================================
   amat — cache levels, TLB, page fault
   ==================================================================== */
/* levels [{t,h}], tm, mode 'hier' (look-through: times add up) | 'simul' (look-aside: only the serving level's time) */
function amatLevels(levels,tm,mode){
  if(!levels.length)return {error:'Add at least one cache level.'};
  for(let i=0;i<levels.length;i++){const L=levels[i];
    if(!(L.t>=0)||!isFinite(L.t))return {error:`L${i+1}: access time must be a number ≥ 0.`};
    if(!(L.h>=0&&L.h<=1))return {error:`L${i+1}: hit ratio must be between 0 and 1 (e.g. 0.9 or 90%).`};}
  if(!(tm>=0)||!isFinite(tm))return {error:'Main memory access time must be a number ≥ 0.'};
  let miss=1,cum=0,T=0;const rows=[];
  levels.forEach((L,i)=>{cum+=L.t;const p=miss*L.h,time=mode==='hier'?cum:L.t;rows.push({where:'L'+(i+1),p,time,c:p*time});T+=p*time;miss*=1-L.h;});
  const time=mode==='hier'?cum+tm:tm;rows.push({where:'Main memory',p:miss,time,c:miss*time});T+=miss*time;
  return {T,rows,missAll:miss};
}
/* t = TLB time, m = memory time, h = TLB hit ratio, L = page-table levels, mode 'seq' | 'par' */
function tlbEAT(o){
  const {t,m,h}=o,L=o.L==null?1:o.L;
  if(!(t>=0)||!(m>=0))return {error:'Times must be numbers ≥ 0.'};
  if(!(h>=0&&h<=1))return {error:'TLB hit ratio must be between 0 and 1.'};
  if(!Number.isInteger(L)||L<1||L>6)return {error:'Page-table levels must be a whole number from 1 to 6.'};
  const hit=t+m,miss=(o.mode==='par'?0:t)+(L+1)*m;
  return {hit,miss,EAT:h*hit+(1-h)*miss,noTLB:(L+1)*m};
}
/* ma (ns), p, sClean, sDirty (ns), d = fraction of victims dirty, addMa (count the memory access after service) */
function pfEAT(o){
  const {ma,p}=o,d=o.d||0;
  if(!(ma>=0))return {error:'Memory access time must be a number ≥ 0.'};
  if(!(p>=0&&p<=1))return {error:'Page-fault rate p must be between 0 and 1 (e.g. 0.001, 1/1000 or 1e-6).'};
  if(!(o.sClean>=0))return {error:'Page-fault service time must be a number ≥ 0.'};
  if(!(d>=0&&d<=1))return {error:'Fraction of dirty victims must be between 0 and 1.'};
  if(d>0&&!(o.sDirty>=0))return {error:'Enter the service time when the victim page is dirty.'};
  const s=(1-d)*o.sClean+d*(d>0?o.sDirty:0),sEff=o.addMa?s+ma:s,EAT=(1-p)*ma+p*sEff;
  let pMax=null;if(o.target!=null&&!isNaN(o.target)){pMax=sEff>ma?(o.target-ma)/(sEff-ma):null;}
  return {s,sEff,EAT,pMax};
}
NETSOLVE.amat={levels:amatLevels,tlb:tlbEAT,pageFault:pfEAT};

/* ====================================================================
   pipeline — cycle-accurate in-order pipeline with stalls
   events: {type:'stall', i:instr(1-based), j:stage it waits to enter (2..k), c:cycles} | {type:'branch', i, c}
   ==================================================================== */
function pipeSim(o){
  const k=o.k,n=o.n;
  if(!Number.isInteger(k)||k<1||k>30)return {error:'Number of stages k must be a whole number from 1 to 30.'};
  if(!Number.isInteger(n)||n<1||n>100000)return {error:'Number of instructions n must be a whole number from 1 to 100000.'};
  let d=(o.delays||[]).slice();
  if(!d.length)return {error:'Enter the stage delay (one value if all stages are equal).'};
  if(d.length===1)d=Array(k).fill(d[0]);
  else if(d.length!==k)return {error:`Give one delay (all stages equal) or exactly ${k} delays; you gave ${d.length}.`};
  if(d.some(x=>!(x>0)||!isFinite(x)))return {error:'Stage delays must be positive numbers.'};
  const latch=o.latch||0;if(!(latch>=0))return {error:'Latch (buffer) delay must be a number ≥ 0.'};
  const stall=new Map(),br=new Map();
  for(const ev of o.events||[]){
    if(!Number.isInteger(ev.c)||ev.c<1)return {error:'Stall and branch cycles must be whole numbers ≥ 1.'};
    if(!Number.isInteger(ev.i)||ev.i<1||ev.i>n)return {error:`Instruction number must be from 1 to ${n}.`};
    if(ev.type==='stall'){
      if(!Number.isInteger(ev.j)||ev.j<2||ev.j>k)return {error:`A data stall waits before entering a stage from 2 to ${k}.`};
      const key=(ev.i-1)+','+(ev.j-1);stall.set(key,(stall.get(key)||0)+ev.c);
    }else{
      if(ev.i>=n)return {error:`Branch penalty on I${ev.i}: there is no instruction after it to delay.`};
      br.set(ev.i-1,(br.get(ev.i-1)||0)+ev.c);
    }
  }
  const S=[];
  for(let i=0;i<n;i++){
    const row=new Array(k);
    for(let j=0;j<k;j++){
      let v=j===0?(i===0?0:S[i-1][0]+1+(br.get(i-1)||0)):row[j-1]+1+(stall.get(i+','+j)||0);
      if(i>0)v=Math.max(v,j<k-1?S[i-1][j+1]:S[i-1][j]+1);
      row[j]=v;
    }
    S.push(row);
  }
  const cycles=S[n-1][k-1]+1,tau=Math.max(...d)+latch,Tp=cycles*tau;
  const tnp=(o.tnp!=null&&!isNaN(o.tnp))?o.tnp:d.reduce((a,b)=>a+b,0);
  if(!(tnp>0))return {error:'Non-pipelined time per instruction must be positive.'};
  const Sp=n*tnp/Tp;
  return {k,n,d,latch,tau,cycles,ideal:k+n-1,extra:cycles-(k+n-1),Tp,tnp,Tseq:n*tnp,speedup:Sp,Sinf:tnp/tau,
    eff:n/cycles,effSk:Sp/k,thr:n/Tp,start:S};
}
/* occupancy grid[j][c] = {i, held} for the space-time diagram */
function pipeOcc(r){
  const g=[];for(let j=0;j<r.k;j++)g.push(new Array(r.cycles).fill(null));
  r.start.forEach((row,i)=>row.forEach((s,j)=>{const e=j<r.k-1?row[j+1]-1:s;for(let c=s;c<=e;c++)g[j][c]={i,held:c>s};}));
  return g;
}
NETSOLVE.pipeline={simulate:pipeSim,occupancy:pipeOcc};

/* ====================================================================
   ieee754 — exact encode (BigInt) and decode
   ==================================================================== */
const FMT={single:{P:24,E:8,bias:127,W:32,name:'single'},double:{P:53,E:11,bias:1023,W:64,name:'double'}};
const bl=x=>x.toString(2).length;
const B=BigInt;
function parseDec(str){
  const s=String(str==null?'':str).trim().replace(/[_\s]/g,'').replace(/−/g,'-');
  if(!s)return {error:'Enter a decimal number, e.g. -13.625, 0.1 or 1e-40.'};
  let m;
  if((m=/^([+-]?)(inf|infinity|∞)$/i.exec(s)))return {special:'inf',neg:m[1]==='-'};
  if(/^[+-]?nan$/i.test(s))return {special:'nan',neg:s[0]==='-'};
  m=/^([+-]?)(\d*)(?:\.(\d*))?(?:e([+-]?\d+))?$/i.exec(s);
  if(!m||!((m[2]||'')+(m[3]||'')).length)return {error:`"${str}" is not a decimal number. Use digits, one point and an optional exponent (e.g. 6.02e23), or inf / nan.`};
  const ex=parseInt(m[4]||'0',10);
  if(Math.abs(ex)>10000)return {error:'Exponent is too large; keep it within ±10000.'};
  const fr=m[3]||'';let N=B((m[2]||'')+fr||'0'),D=10n**B(fr.length);
  if(ex>0)N*=10n**B(ex);else if(ex<0)D*=10n**B(-ex);
  return {neg:m[1]==='-',N,D};
}
function exactDec(M,q){ /* decimal string of M * 2^q (M >= 0 BigInt) */
  if(q>=0)return (M<<B(q)).toString();
  const k=-q,num=(M*5n**B(k)).toString().padStart(k+1,'0');
  let s=num.slice(0,num.length-k)+'.'+num.slice(num.length-k);
  return s.replace(/0+$/,'').replace(/\.$/,'');
}
function ratToSci(num,den,sig){
  sig=sig||6;if(num===0n)return '0';
  let neg=false;if(num<0n){neg=true;num=-num;}
  let e=num.toString().length-den.toString().length;
  const ge=x=>x>=0?num>=den*10n**B(x):num*10n**B(-x)>=den;
  if(!ge(e))e--;
  const s=sig-e;/* one extra digit for rounding */
  let q=s>=0?(num*10n**B(s))/den:num/(den*10n**B(-s));
  q=(q+5n)/10n;
  if(q.toString().length>sig){q/=10n;e++;}
  const ds=q.toString();let mnt=ds[0]+(ds.length>1?'.'+ds.slice(1):'');
  mnt=mnt.replace(/(\.\d*?)0+$/,'$1').replace(/\.$/,'');
  return (neg?'-':'')+mnt+(e!==0?'e'+e:'');
}
function ieeeEncode(str,fmtName,round){
  const F=FMT[fmtName||'single'];if(!F)return {error:'Unknown format.'};
  round=round==='trunc'?'trunc':'rne';
  const p=parseDec(str);if(p.error)return p;
  const fb=F.P-1,emin=1-F.bias,emax=F.bias,hidden=1n<<B(fb),sign=p.neg?1:0,allOnes=(1<<F.E)-1;
  const pack=(biased,frac,cls,extra)=>{
    const expBits=biased.toString(2).padStart(F.E,'0'),fracBits=frac.toString(2).padStart(fb,'0'),bits=sign+expBits+fracBits;
    return Object.assign({fmt:F.name,W:F.W,E:F.E,fb,bias:F.bias,sign,biased,frac,expBits,fracBits,bits,
      hex:B('0b'+bits).toString(16).toUpperCase().padStart(F.W/4,'0'),cls},extra||{});
  };
  if(p.special==='nan')return pack(allOnes,1n<<B(fb-1),'NaN',{special:true});
  if(p.special==='inf')return pack(allOnes,0n,sign?'−∞':'+∞',{special:true});
  const {N,D}=p;
  if(N===0n)return pack(0,0n,sign?'−0 (negative zero)':'+0 (zero)',{special:true,zero:true});
  let e=bl(N)-bl(D);
  const ge=x=>x>=0?N>=(D<<B(x)):(N<<B(-x))>=D;
  if(!ge(e))e--;
  const eTrue=e;let eu=Math.max(e,emin);
  const sh=fb-eu;let num=N,den=D;if(sh>=0)num=N<<B(sh);else den=D<<B(-sh);
  const M0=num/den,R=num%den;
  const hi=Math.max(eTrue,0),lo=Math.min(0,Math.max(eu,eTrue)-fb-3);
  const X=(N<<B(-lo))/D,more=((N<<B(-lo))%D)!==0n,allb=X.toString(2).padStart(hi-lo+1,'0');
  const kd=D.toString().length-1,nd=N.toString().padStart(kd+1,'0');
  const disp={eTrue,x:p,M0,intBin:allb.slice(0,hi+1),fracBin:allb.slice(hi+1),more,intPart:N/D,fracNum:N%D,D,emin,
    xSci:ratToSci(N,D,8),xAbs:kd?(nd.slice(0,nd.length-kd)+'.'+nd.slice(nd.length-kd)).replace(/0+$/,'').replace(/\.$/,''):nd};
  const G=(2n*R)/den,Rb=((4n*R)/den)%2n,St=(4n*R)%den!==0n;
  let up=false;
  if(round==='rne'){const c=2n*R;up=c>den||(c===den&&(M0&1n)===1n);}
  let M=up?M0+1n:M0,carry=false;
  if(M===(hidden<<1n)){M>>=1n;eu++;carry=true;}
  let overflow=false;
  if(eu>emax){overflow=true;
    if(round==='rne')return pack(allOnes,0n,(sign?'−∞':'+∞')+' (overflow)',Object.assign({},disp,{overflow,round,inexact:true,G,Rb,St,up,eu,M:0n,normal:false}));
    M=(hidden<<1n)-1n;eu=emax;}
  const normal=M>=hidden,biased=normal?eu+F.bias:0,frac=M&(hidden-1n);
  const q=eu-fb;/* stored = M * 2^q */
  const storedNum=q>=0?(M<<B(q))*D:M*D,storedDen=q>=0?D:D<<B(-q);
  const errNum=q>=0?(M<<B(q))*D-N:M*D-(N<<B(-q));
  const cls=M===0n?(sign?'−0 (underflow)':'+0 (underflow)'):normal?'normal':'denormal (subnormal)';
  return pack(biased,frac,cls,Object.assign({},disp,{eu,M,G,Rb,St,up,carry,inexact:R!==0n,round,overflow,x:p,normal,denormal:!normal&&M!==0n,
    underflow:M===0n,storedExact:(sign&&M!==0n?'-':'')+exactDec(M,q),storedNum,storedDen,errSci:(sign?'-':'')+ratToSci(errNum,storedDen,4),q}));
}
function ieeeDecode(str,fmtName){
  const F=FMT[fmtName||'single'];if(!F)return {error:'Unknown format.'};
  let s=String(str==null?'':str).trim().replace(/[\s_]/g,'');
  let bits;
  if(/^[01]+$/.test(s)&&s.length===F.W)bits=s;
  else{
    s=s.replace(/^0x/i,'');
    if(!/^[0-9a-f]+$/i.test(s))return {error:`Enter ${F.W/4} hex digits (0–9, A–F), e.g. ${F.W===32?'41480000':'4029000000000000'}. A ${F.W}-bit binary string also works.`};
    if(s.length!==F.W/4)return {error:`${F.name[0].toUpperCase()+F.name.slice(1)} precision needs exactly ${F.W/4} hex digits; you gave ${s.length}.`};
    bits=B('0x'+s).toString(2).padStart(F.W,'0');
  }
  const fb=F.P-1,sign=+bits[0],expBits=bits.slice(1,1+F.E),fracBits=bits.slice(1+F.E),E=parseInt(expBits,2),frac=B('0b'+fracBits),allOnes=(1<<F.E)-1;
  const hex=B('0b'+bits).toString(16).toUpperCase().padStart(F.W/4,'0');
  const base={fmt:F.name,W:F.W,E:F.E,fb,bias:F.bias,sign,biased:E,expBits,fracBits,frac,bits,hex};
  const sg=sign?'−':'+';
  if(E===allOnes){
    if(frac===0n)return Object.assign(base,{cls:sg+'∞',value:sign?'-Infinity':'Infinity',num:sign?-Infinity:Infinity});
    return Object.assign(base,{cls:(fracBits[0]==='1'?'quiet':'signalling')+' NaN',value:'NaN',num:NaN});
  }
  let M,q,cls,e;
  if(E===0){ if(frac===0n)return Object.assign(base,{cls:sg+'0',value:sign?'-0':'0',num:sign?-0:0,M:0n,q:0});
    M=frac;e=1-F.bias;q=e-fb;cls='denormal (subnormal)';}
  else{M=frac|(1n<<B(fb));e=E-F.bias;q=e-fb;cls='normal';}
  const value=(sign?'-':'')+exactDec(M,q);
  const dv=new DataView(new ArrayBuffer(8));
  if(F.W===32){dv.setUint32(0,parseInt(hex,16));}else{dv.setUint32(0,parseInt(hex.slice(0,8),16));dv.setUint32(4,parseInt(hex.slice(8),16));}
  const num=F.W===32?dv.getFloat32(0):dv.getFloat64(0);
  return Object.assign(base,{cls,M,q,e,value,num});
}
function ieeeBitsOfNumber(x,fmtName){ /* reference bits via DataView (used by the tests) */
  const dv=new DataView(new ArrayBuffer(8));
  if(fmtName==='double'){dv.setFloat64(0,x);return (dv.getUint32(0).toString(16).padStart(8,'0')+dv.getUint32(4).toString(16).padStart(8,'0')).toUpperCase();}
  dv.setFloat32(0,x);return dv.getUint32(0).toString(16).padStart(8,'0').toUpperCase();
}
NETSOLVE.ieee754={encode:ieeeEncode,decode:ieeeDecode,exactDec,parseDec,bitsOfNumber:ieeeBitsOfNumber};

/* ====================================================================
   kmap — Quine–McCluskey, exact minimum cover, SOP and POS
   ==================================================================== */
function patOf(v,m,n){let s='';for(let b=n-1;b>=0;b--)s+=(m>>b)&1?'-':((v>>b)&1?'1':'0');return s;}
function qm(n,ms,ds){
  const all=[...new Set([...ms,...ds])].sort((a,b)=>a-b);
  let col=all.map(v=>({v,m:0,terms:[v],used:false}));
  const cols=[],primes=[];
  while(col.length){
    cols.push(col);
    const next=[],seen=new Map();
    for(let a=0;a<col.length;a++)for(let b=a+1;b<col.length;b++){
      const A=col[a],Bb=col[b];if(A.m!==Bb.m)continue;
      const d=A.v^Bb.v;if(popc(d)!==1)continue;
      A.used=Bb.used=true;
      const v=A.v&~d,m=A.m|d,key=v+'/'+m;
      if(!seen.has(key)){const e={v,m,terms:[...A.terms,...Bb.terms].sort((x,y)=>x-y),used:false};seen.set(key,e);next.push(e);}
    }
    col.forEach(x=>{if(!x.used)primes.push(x);});
    col=next;
  }
  const mset=new Set(ms);
  const pis=primes.map(p=>({v:p.v,m:p.m,pat:patOf(p.v,p.m,n),terms:p.terms,covers:p.terms.filter(t=>mset.has(t)),lits:n-popc(p.m)}));
  pis.sort((a,b)=>b.terms.length-a.terms.length||a.terms[0]-b.terms[0]);
  pis.forEach((p,i)=>{p.id=i;p.covset=new Set(p.covers);});
  return {cols,pis};
}
function minCover(pis,ms,cap){
  cap=cap||40;
  const cand=pis.filter(p=>p.covers.length);
  let best=null,sols=[];const keys=new Set();
  (function rec(unc,chosen,nT,nL){
    if(best&&(nT>best[0]||(nT===best[0]&&nL>best[1])))return;
    if(!unc.length){
      if(!best||nT<best[0]||(nT===best[0]&&nL<best[1])){best=[nT,nL];sols=[];keys.clear();}
      const key=chosen.map(p=>p.id).sort((a,b)=>a-b).join(',');
      if(!keys.has(key)&&sols.length<cap){keys.add(key);sols.push(chosen.slice().sort((a,b)=>a.id-b.id));}
      return;
    }
    if(best&&nT+1>best[0])return;
    let pc=null;
    for(const mt of unc){const c=cand.filter(p=>p.covset.has(mt));if(!pc||c.length<pc.length)pc=c;}
    for(const p of pc){if(chosen.includes(p))continue;chosen.push(p);rec(unc.filter(x=>!p.covset.has(x)),chosen,nT+1,nL+p.lits);chosen.pop();}
  })(ms.slice(),[],0,0);
  return {sols,terms:best?best[0]:0,lits:best?best[1]:0};
}
function termSOP(p,names){const n=names.length;let s='';for(let b=0;b<n;b++){const c=p.pat[b];if(c==='1')s+=names[b];else if(c==='0')s+=names[b]+"'";}return s||'1';}
function termPOS(p,names){const n=names.length,l=[];for(let b=0;b<n;b++){const c=p.pat[b];if(c==='0')l.push(names[b]);else if(c==='1')l.push(names[b]+"'");}return l.length?(l.length>1?'('+l.join(' + ')+')':l[0]):'0';}
/* full solve: n vars, minterms, don't-cares, names */
function kmSolve(n,ms,ds,names){
  if(!Number.isInteger(n)||n<2||n>5)return {error:'Number of variables must be 2 to 5.'};
  const N=1<<n;
  const bad=[...ms,...ds].filter(x=>!(Number.isInteger(x)&&x>=0&&x<N));
  if(bad.length)return {error:`With ${n} variables the minterm numbers run from 0 to ${N-1}; ${bad.join(', ')} ${bad.length>1?'are':'is'} out of range.`};
  ms=[...new Set(ms)].sort((a,b)=>a-b);ds=[...new Set(ds)].sort((a,b)=>a-b);
  const both=ms.filter(x=>ds.includes(x));
  if(both.length)return {error:`${both.map(x=>'m'+x).join(', ')} ${both.length>1?'are':'is'} listed both as a minterm and as a don't-care.`};
  names=(names&&names.length>=n)?names.slice(0,n):'ABCDE'.split('').slice(0,n);
  const zeros=[];for(let i=0;i<N;i++)if(!ms.includes(i)&&!ds.includes(i))zeros.push(i);
  const S=qm(n,ms,ds),Z=qm(n,zeros,ds);
  const epi=S.pis.filter(p=>p.covers.some(mt=>S.pis.filter(q=>q.covset.has(mt)).length===1));
  const cov=minCover(S.pis,ms),covZ=minCover(Z.pis,zeros);
  const sop=sol=>ms.length===0?'0':zeros.length===0?'1':sol.map(p=>termSOP(p,names)).join(' + ');
  const pos=sol=>zeros.length===0?'1':ms.length===0?'0':sol.map(p=>termPOS(p,names)).join(' · ');
  return {n,N,names,ms,ds,zeros,qm:S,qmZ:Z,pis:S.pis,epi,cover:cov,coverZ:covZ,
    epiZ:Z.pis.filter(p=>p.covers.some(mt=>Z.pis.filter(q=>q.covset.has(mt)).length===1)),
    sop:cov.sols.map(sop),pos:covZ.sols.map(pos)};
}
/* evaluate a pattern list (SOP) at minterm x */
function evalSOP(pats,n,x){return pats.some(p=>{for(let b=0;b<n;b++){const c=p[b],bit=(x>>(n-1-b))&1;if(c!=='-'&&+c!==bit)return false;}return true;});}
NETSOLVE.kmap={solve:kmSolve,qm,minCover,evalSOP,termSOP,termPOS};

/* ====================================================================
   UI (browser only)
   ==================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const opts=(list,sel)=>list.map(o=>{const [v,t]=Array.isArray(o)?o:[o,o];return `<option value="${esc(v)}"${v===sel?' selected':''}>${esc(t)}</option>`;}).join('');
const chips=items=>`<div class="coa-ans">${items.filter(Boolean).map(([l,v,c])=>`<div class="coa-a${c?' '+c:''}"><span>${l}</span><b>${v}</b></div>`).join('')}</div>`;
const sec=(title,body,cls)=>`<section class="coa-sec${cls?' '+cls:''}"><h4 class="coa-h">${title}</h4>${body}</section>`;
const errBox=msgs=>`<div class="coa-err" role="alert"><b>Check the input.</b> ${[].concat(msgs).map(esc).join('<br>')}</div>`;
const convBox=list=>`<div class="coa-conv"><b>Conventions</b><ul>${list.map(x=>`<li>${x}</li>`).join('')}</ul></div>`;
const fbox=lines=>`<div class="coa-f">${lines.join('\n')}</div>`;
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=a=>a[Math.floor(Math.random()*a.length)];
const seg=(k,list)=>`<div class="seg" data-k="${k}" role="group">${list.map(([v,t])=>`<button type="button" data-v="${esc(v)}" aria-pressed="false">${esc(t)}</button>`).join('')}</div>`;
const shell=(form,extraBtns)=>`<div class="coa"><div class="ax-ctrls coa-form">${form}</div><div class="coa-btns"><button type="button" class="btn sm" data-act="rand">🎲 Random example</button><button type="button" class="btn sm ghost" data-act="dflt">Default example</button>${extraBtns||''}</div><div class="coa-out" aria-live="polite"></div></div>`;
/* form wiring: data-k inputs, .seg toggles, data-show="k:v|v" */
function wireForm(stage,onChange){
  const get=k=>stage.querySelector(`[data-k="${k}"]`);
  const setSeg=(sg,v)=>{sg.dataset.v=v;sg.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===v)));};
  function read(){const o={};stage.querySelectorAll('.coa-form [data-k]').forEach(el=>{o[el.dataset.k]=el.type==='checkbox'?el.checked:el.classList.contains('seg')?el.dataset.v:el.value;});return o;}
  function sync(){const o=read();stage.querySelectorAll('[data-show]').forEach(el=>{const [k,vs]=el.dataset.show.split(':');el.hidden=!vs.split('|').includes(String(o[k]));});return o;}
  function set(vals){for(const k in vals){const el=get(k);if(!el)continue;if(el.type==='checkbox')el.checked=!!vals[k];else if(el.classList.contains('seg'))setSeg(el,vals[k]);else el.value=vals[k];}}
  stage.querySelectorAll('.coa-form .seg[data-k]').forEach(sg=>sg.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{setSeg(sg,b.dataset.v);onChange();})));
  stage.addEventListener('input',e=>{if(e.target.closest('.coa-form'))onChange();});
  return {read,sync,set,get};
}
/* step-through control; render(k) for k = 0..n */
function stepper(host,n,render,label){
  if(host._coaT)clearTimeout(host._coaT);
  let k=n,playing=false;
  host.innerHTML=`<div class="coa-step" role="group" aria-label="Step through"><button type="button" class="btn sm" data-s="rs" aria-label="Go to the start">↺</button><button type="button" class="btn sm" data-s="pv" aria-label="Previous step">◀</button><button type="button" class="btn sm primary" data-s="pl">▶ Play</button><button type="button" class="btn sm" data-s="nx" aria-label="Next step">▶|</button><button type="button" class="btn sm" data-s="all">Show all</button><input type="range" min="0" max="${n}" step="1" value="${n}" aria-label="Step"><span class="coa-stepn"></span></div>`;
  const q=s=>host.querySelector(`[data-s="${s}"]`),rng=host.querySelector('input'),lab=host.querySelector('.coa-stepn'),pl=q('pl');
  function go(i){k=Math.max(0,Math.min(n,i));rng.value=k;lab.textContent=label?label(k,n):`Step ${k} of ${n}`;q('pv').disabled=k<=0;q('nx').disabled=k>=n;render(k);}
  function stop(){playing=false;clearTimeout(host._coaT);pl.textContent='▶ Play';}
  function tick(){if(!playing||!host.isConnected||k>=n){stop();return;}go(k+1);host._coaT=setTimeout(tick,900);}
  pl.onclick=()=>{if(playing){stop();return;}if(k>=n)go(0);playing=true;pl.textContent='❚❚ Pause';host._coaT=setTimeout(tick,700);};
  q('nx').onclick=()=>{stop();go(k+1);};q('pv').onclick=()=>{stop();go(k-1);};
  q('rs').onclick=()=>{stop();go(0);};q('all').onclick=()=>{stop();go(n);};
  rng.oninput=()=>{stop();go(+rng.value);};
  go(n);
  return {go};
}
function bitbar(fields){
  const total=fields.reduce((a,f)=>a+f.bits,0);let hi=total-1;
  return `<div class="coa-bar" role="img" aria-label="${esc(fields.filter(f=>f.bits).map(f=>f.name+' '+f.bits+' bits').join(', '))}">${fields.filter(f=>f.bits>0).map(f=>{const lo=hi-f.bits+1;
    const s=`<div class="coa-bf ${f.cls}" style="flex:${f.bits} 1 0"><b>${esc(f.name)}</b><span>${f.bits} bit${f.bits===1?'':'s'}</span><i><em>${hi}</em><em>${lo}</em></i></div>`;hi=lo-1;return s;}).join('')}</div>`;
}

/* ---------------------------------------------------------------- cachemap UI */
ANIM.register('cachemap',{title:'Cache mapping solver',steps:false,
 caption:'Enter the memory and cache sizes to get the tag / index / offset split and tag memory, then simulate a reference sequence to count hits and misses.',
 build(stage){
  const DEF={mm:'64',mmu:'KB',addr:'byte',wb:'4',cs:'128',csu:'B',bs:'16',bsu:'B',map:'set',k:'2',valid:false,dirty:false,seq:'0 1 4 0 2 1 4 8 0 5 1 4',kind:'block',pol:'LRU'};
  stage.innerHTML=shell(`
   <label>Main memory<span class="coa-pair"><input data-k="mm" inputmode="decimal" aria-label="Main memory size"><select data-k="mmu" aria-label="Main memory unit">${opts(['B','KB','MB','GB','TB','K words','M words',['bits','address bits']])}</select></span></label>
   <label>Addressing<select data-k="addr">${opts([['byte','Byte addressable'],['word','Word addressable']])}</select></label>
   <label>Word size (bytes)<input data-k="wb" inputmode="numeric"></label>
   <label>Cache size<span class="coa-pair"><input data-k="cs" inputmode="decimal" aria-label="Cache size"><select data-k="csu" aria-label="Cache size unit">${opts(['B','KB','MB','words','K words'])}</select></span></label>
   <label>Block (line) size<span class="coa-pair"><input data-k="bs" inputmode="decimal" aria-label="Block size"><select data-k="bsu" aria-label="Block size unit">${opts(['B','words'])}</select></span></label>
   <label>Mapping<select data-k="map">${opts([['direct','Direct mapped'],['set','k-way set associative'],['full','Fully associative']])}</select></label>
   <label data-show="map:set">k (lines per set)<input data-k="k" inputmode="numeric"></label>
   <div class="coa-checks"><span>Tag entry also stores</span><label class="chk"><input type="checkbox" data-k="valid"> valid bit</label><label class="chk"><input type="checkbox" data-k="dirty"> dirty bit</label></div>
   <label class="coa-wide">Reference sequence (decimal, or 0x… hex)<input data-k="seq" spellcheck="false"></label>
   <label>Sequence gives<select data-k="kind">${opts([['block','Block numbers'],['addr','Memory addresses']])}</select></label>
   <label>Replacement<select data-k="pol">${opts([['LRU','LRU'],['FIFO','FIFO']])}</select></label>`);
  const out=stage.querySelector('.coa-out');
  const F=wireForm(stage,run);
  function run(){
    const o=F.sync(),errs=[];
    const wb=parseNum(o.wb),unit=o.addr==='word'?wb:1;
    const num=(s,nm)=>{const v=parseNum(s);if(!(v>0))errs.push(`${nm}: enter a positive number.`);return v;};
    const mmv=num(o.mm,'Main memory'),cs=num(o.cs,'Cache size'),bs=num(o.bs,'Block size');
    if(!(wb>0)||!isP2(wb))errs.push('Word size must be a power of 2 bytes (1, 2, 4, 8 …).');
    if(errs.length){out.innerHTML=errBox(errs);return;}
    const g=cmGeometry({mmBytes:o.mmu==='bits'?undefined:cmSizeBytes(mmv,o.mmu,wb),addrBits:o.mmu==='bits'?mmv:undefined,unitBytes:unit,
      cacheBytes:cmSizeBytes(cs,o.csu,wb),blockBytes:cmSizeBytes(bs,o.bsu,wb),mapping:o.map,k:parseNum(o.k),valid:o.valid,dirty:o.dirty});
    if(g.error){out.innerHTML=errBox(g.error);return;}
    const U=unit===1?'bytes':'words',ixName=g.mapping==='direct'?'Line (index)':g.mapping==='full'?'Index':'Set (index)',setW=g.mapping==='direct'?'line':'set';
    const offName=unit===1?'Byte offset':'Word offset';
    let html=chips([['Address bits',g.addrBits],['Tag',g.tagBits+' bits','hi'],[ixName,g.indexBits+' bits','hi'],[offName,g.offsetBits+' bits','hi'],
      ['Cache lines',g.lines],[g.mapping==='direct'?'Lines = sets':'Sets',g.sets],['Tag memory',fmtBits(g.tagMemBits),'hi']]);
    html+=sec('Address split',bitbar([{name:'Tag',bits:g.tagBits,cls:'t'},{name:g.mapping==='direct'?'Line':'Set',bits:g.indexBits,cls:'i'},{name:'Offset',bits:g.offsetBits,cls:'o'}])+
      (g.mapping==='full'?'<p class="coa-note">Fully associative: there is no index field. A block can go in any line, so every tag is compared (one comparator per line).</p>':''));
    const unitTxt=unit===1?'byte':`${unit}-byte word`;
    const w=[];
    w.push(`Addressable units = main memory ÷ unit = ${fmtBytes(g.mmBytes)} ÷ ${unit} B = ${g.units} = 2<sup>${g.addrBits}</sup> ⇒ <b>${g.addrBits} address bits</b>`);
    w.push(`Offset = log₂(block ÷ unit) = log₂(${fmtBytes(g.blockBytes)} ÷ ${unit} B) = log₂ ${g.blockUnits} = <b>${g.offsetBits} bits</b>`);
    w.push(`Lines = cache ÷ block = ${fmtBytes(g.cacheBytes)} ÷ ${fmtBytes(g.blockBytes)} = <b>${g.lines}</b>`);
    if(g.mapping==='set')w.push(`Sets = lines ÷ k = ${g.lines} ÷ ${g.ways} = ${g.sets} ⇒ index = log₂ ${g.sets} = <b>${g.indexBits} bits</b>`);
    else if(g.mapping==='direct')w.push(`Direct mapped: sets = lines = ${g.lines} ⇒ line index = log₂ ${g.lines} = <b>${g.indexBits} bits</b>`);
    else w.push(`Fully associative: one set of ${g.lines} lines ⇒ index = <b>0 bits</b>`);
    w.push(`Tag = address − index − offset = ${g.addrBits} − ${g.indexBits} − ${g.offsetBits} = <b>${g.tagBits} bits</b>`);
    w.push(`Tag memory = lines × (tag${g.extra?(o.valid?' + valid':'')+(o.dirty?' + dirty':''):''}) = ${g.lines} × ${g.perLine} = <b>${fmtBits(g.tagMemBits)}</b>`);
    w.push(`Main-memory blocks = ${g.mmBlocks}; each ${setW} is shared by ${g.mmBlocks} ÷ ${g.sets} = ${g.blocksPerSet} = 2<sup>${g.tagBits}</sup> blocks (that is what the tag tells apart)`);
    w.push(`${g.mapping==='full'?'A block may go in any line':`Mapping rule: ${setW} = block number mod ${g.sets}`}; comparators needed = ${g.ways}, each ${g.tagBits} bits wide`);
    html+=sec('Working',`<ol class="coa-work">${w.map(x=>`<li>${x}</li>`).join('')}</ol>`);
    html+=convBox([`Addressable unit = one ${unitTxt}. Sizes are powers of two: 1 KB = 1024 B.`,
      'Tag memory counts only the tag bits per line, plus the valid and dirty bits if you tick them. Replacement (LRU) bits are not counted.',
      'Block number = ⌊address ÷ block size⌋, offset = address mod block size, set = block mod number of sets, tag = ⌊block ÷ number of sets⌋.',
      `Simulation: the cache starts empty; an empty line in the set is filled first (lowest way number); otherwise the ${o.pol==='LRU'?'least recently used':'first loaded (FIFO)'} line is replaced. Hit ratio = hits ÷ references, compulsory misses included.`]);
    html+=`<div class="cm-sim"></div>`;
    out.innerHTML=html;
    simulate(g,o,out.querySelector('.cm-sim'));
  }
  function simulate(g,o,host){
    const P=parseList(o.seq);
    if(!o.seq.trim()){host.innerHTML=sec('Simulation','<p class="coa-note">Enter a reference sequence to simulate hits and misses.</p>');return;}
    const lim=o.kind==='addr'?g.units:g.mmBlocks;
    const bad=P.bad.slice();P.vals.forEach(v=>{if(v>=lim)bad.push(String(v));});
    if(bad.length){host.innerHTML=sec('Simulation',errBox(`${bad.join(', ')}: each ${o.kind==='addr'?'address':'block number'} must be a whole number from 0 to ${lim-1}.`));return;}
    if(P.vals.length>200){host.innerHTML=sec('Simulation',errBox('Keep the sequence to 200 references or fewer.'));return;}
    const refs=P.vals,r=cmSim({sets:g.sets,ways:g.ways,blockUnits:g.blockUnits,kind:o.kind,refs,policy:o.pol});
    const setW=g.mapping==='direct'?'Line':'Set';
    host.innerHTML=sec('Simulation: hits and misses',
      chips([['Hits',r.hits,'ok'],['Misses',`${r.misses} (${r.cold} compulsory)`,'bad'],['Hit ratio',`${r.hits}/${refs.length} = ${fmt(r.ratio)} = ${fmt(r.ratio*100,2)}%`,'hi']])+
      fbox([`Hit ratio = hits ÷ references = ${r.hits} ÷ ${refs.length} = <b>${fmt(r.ratio)}</b>     Miss ratio = ${r.misses} ÷ ${refs.length} = ${fmt(1-r.ratio)}`])+
      `<div class="cm-stp"></div><p class="coa-cap cm-cap" aria-live="polite"></p><div class="cm-grid coa-scroll"></div><div class="coa-scroll cm-trace"></div>`);
    const gridEl=host.querySelector('.cm-grid'),cap=host.querySelector('.cm-cap'),trace=host.querySelector('.cm-trace');
    const showSets=g.sets<=16?[...Array(g.sets).keys()]:[...new Set(r.steps.map(s=>s.set))].sort((a,b)=>a-b);
    const hexish=o.seq.includes('0x');
    const A=v=>hexish?'0x'+v.toString(16).toUpperCase():v;
    trace.innerHTML=`<table class="coa-tbl cm-tr"><thead><tr><th>#</th>${o.kind==='addr'?'<th>Address</th>':''}<th>Block</th>${o.kind==='addr'?'<th>Offset</th>':''}<th>${setW}</th><th>Tag</th><th>Result</th><th>Replaced</th></tr></thead><tbody>${r.steps.map(s=>
      `<tr data-t="${s.t}"><td>${s.t+1}</td>${o.kind==='addr'?`<td>${A(s.a)}</td>`:''}<td>${s.b}</td>${o.kind==='addr'?`<td>${s.off}</td>`:''}<td>${g.mapping==='full'?'—':s.set}</td><td>${s.tag}</td><td class="${s.hit?'cm-h':'cm-m'}">${s.hit?'Hit':'Miss'+(s.cold?' (cold)':'')}</td><td>${s.ev==null?'—':'B'+s.ev}</td></tr>`).join('')}</tbody></table>`;
    stepper(host.querySelector('.cm-stp'),refs.length,k=>{
      const part=cmSim({sets:g.sets,ways:g.ways,blockUnits:g.blockUnits,kind:o.kind,refs:refs.slice(0,k),policy:o.pol});
      const cur=k?part.steps[k-1]:null;
      const occWays=g.ways<=16?g.ways:Math.max(1,...[...part.state.values()].map(w=>w.filter(Boolean).length));
      let t=`<table class="coa-tbl cm-cache"><thead><tr><th>${g.mapping==='full'?'':setW}</th>${Array.from({length:occWays},(_,w)=>`<th>Way ${w}</th>`).join('')}</tr></thead><tbody>`;
      showSets.forEach(si=>{const ways=part.state.get(si)||[];
        t+=`<tr${cur&&cur.set===si?' class="cm-cur"':''}><th>${g.mapping==='full'?'':si}</th>`;
        for(let w=0;w<occWays;w++){const x=ways[w];const c=cur&&cur.set===si&&cur.way===w?(cur.hit?' cm-hit':' cm-new'):'';
          t+=`<td class="cm-cell${c}">${x?`<b>B${x.b}</b><small>tag ${x.tag}</small>`:'<span class="cm-empty">empty</span>'}</td>`;}
        t+='</tr>';});
      t+='</tbody></table>';
      if(g.sets>16)t+=`<p class="coa-note">Showing only the ${showSets.length} ${setW.toLowerCase()}s this sequence touches (of ${g.sets}).</p>`;
      if(g.ways>16&&g.lines>occWays)t+=`<p class="coa-note">${g.lines-occWays} more lines are still empty.</p>`;
      gridEl.innerHTML=t;
      trace.querySelectorAll('tbody tr').forEach(tr=>{const i=+tr.dataset.t;tr.classList.toggle('coa-fut',i>=k);tr.classList.toggle('coa-now',i===k-1);});
      if(!cur){cap.innerHTML='The cache starts empty. Press <b>Play</b> or <b>▶|</b> to apply one reference at a time.';return;}
      const where=g.mapping==='full'?'':` → ${setW.toLowerCase()} ${cur.b} mod ${g.sets} = <b>${cur.set}</b>`;
      cap.innerHTML=`Ref ${k}: ${o.kind==='addr'?`address ${A(cur.a)} → block ⌊${cur.a} ÷ ${g.blockUnits}⌋ = <b>${cur.b}</b>`:`block <b>${cur.b}</b>`}${where}, tag ${cur.tag}. `+
        (cur.hit?'<b class="cm-h">Hit</b>: the block is already there.':`<b class="cm-m">Miss</b>${cur.cold?' (compulsory: first use of this block)':''}; `+(cur.ev==null?`loaded into empty way ${cur.way}.`:`replaces B${cur.ev} (${o.pol==='LRU'?'least recently used':'loaded first'}) in way ${cur.way}.`))+
        ` Hits so far: ${part.hits}/${k}.`;
    },(k,n)=>`Reference ${k} of ${n}`);
  }
  function random(){
    const unit=pick([1,1,1,2,4]),wb=unit===1?pick([2,4]):unit;
    const bsB=pick([8,16,32,64]),lines=pick([4,8,8,16]),mapping=pick(['direct','set','set','full']),k=pick([2,4]);
    const mmK=pick([16,64,256,1024]);
    const cfg={mm:String(mmK),mmu:'KB',addr:unit===1?'byte':'word',wb:String(wb),cs:String(bsB*lines),csu:'B',bs:String(bsB),bsu:'B',map:mapping,k:String(Math.min(k,lines)),valid:Math.random()<.4,dirty:Math.random()<.25,pol:pick(['LRU','LRU','FIFO'])};
    const kind=pick(['block','addr']),blocks=[];const pool=Array.from({length:Math.min(lines*2,12)},()=>rnd(0,lines*4));
    for(let i=0;i<12;i++)blocks.push(pick(pool));
    const bu=bsB/unit;
    cfg.kind=kind;cfg.seq=kind==='block'?blocks.join(' '):blocks.map(b=>b*bu+rnd(0,bu-1)).join(' ');
    F.set(cfg);run();
  }
  stage.querySelector('[data-act="rand"]').onclick=random;
  stage.querySelector('[data-act="dflt"]').onclick=()=>{F.set(DEF);run();};
  F.set(DEF);run();
 }});

/* ---------------------------------------------------------------- amat UI */
ANIM.register('amat',{title:'Memory access time calculator',steps:false,
 caption:'Average access time for a cache hierarchy (hierarchical or simultaneous access), TLB effective access time, and page-fault EAT, with the formula and numbers shown.',
 build(stage){
  const DEF={tab:'cache',mode:'hier',tm:'100',unit:'ns',levels:[['2','0.8'],['10','0.9']],t:'20',m:'100',h:'0.8',L:'1',tmode:'seq',
    ma:'200',p:'0.001',sc:'8',scu:'ms',d:'0',sd:'20',sdu:'ms',addma:false,tgt:''};
  stage.innerHTML=shell(`
   <div class="coa-wide">${seg('tab',[['cache','Cache levels'],['tlb','TLB'],['pf','Page fault']])}</div>
   <div class="coa-wide coa-sub" data-show="tab:cache">
     <div class="coa-wide">${seg('mode',[['hier','Hierarchical (look-through)'],['simul','Simultaneous (look-aside)']])}</div>
     <div class="coa-wide"><table class="coa-tbl am-lv"><thead><tr><th>Level</th><th>Access time</th><th>Hit ratio</th><th></th></tr></thead><tbody></tbody></table>
       <button type="button" class="btn sm" data-act="addlv">+ Add level</button></div>
     <label>Main memory access time<input data-k="tm" inputmode="decimal"></label>
     <label>Time unit<select data-k="unit">${opts(['ns','cycles','µs'])}</select></label>
   </div>
   <div class="coa-wide coa-sub" data-show="tab:tlb">
     <label>TLB access time t (ns)<input data-k="t" inputmode="decimal"></label>
     <label>Memory access time m (ns)<input data-k="m" inputmode="decimal"></label>
     <label>TLB hit ratio h<input data-k="h" inputmode="decimal"></label>
     <label>Page-table levels<input data-k="L" inputmode="numeric"></label>
     <div class="coa-wide">${seg('tmode',[['seq','TLB first, then memory'],['par','TLB and page table in parallel']])}</div>
   </div>
   <div class="coa-wide coa-sub" data-show="tab:pf">
     <label>Memory access time (ns)<input data-k="ma" inputmode="decimal"></label>
     <label>Page-fault rate p<input data-k="p" inputmode="decimal"></label>
     <label>Service time (clean victim)<span class="coa-pair"><input data-k="sc" inputmode="decimal" aria-label="Service time"><select data-k="scu" aria-label="Service time unit">${opts(['ms','µs','ns'])}</select></span></label>
     <label>Fraction of victims dirty<input data-k="d" inputmode="decimal"></label>
     <label data-show="dshow:1">Service time (dirty victim)<span class="coa-pair"><input data-k="sd" inputmode="decimal" aria-label="Dirty service time"><select data-k="sdu" aria-label="Dirty service time unit">${opts(['ms','µs','ns'])}</select></span></label>
     <label>Target EAT (ns, optional)<input data-k="tgt" inputmode="decimal" placeholder="e.g. 220"></label>
     <label class="chk coa-wide"><input type="checkbox" data-k="addma"> After servicing the fault, count one more memory access</label>
     <input type="hidden" data-k="dshow">
   </div>`);
  const out=stage.querySelector('.coa-out'),tb=stage.querySelector('.am-lv tbody');
  function addRow(t,h){const tr=document.createElement('tr');tr.innerHTML=`<td class="am-ln"></td><td><input data-f="t" inputmode="decimal" aria-label="Access time" value="${esc(t)}"></td><td><input data-f="h" inputmode="decimal" aria-label="Hit ratio" value="${esc(h)}"></td><td><button type="button" class="btn sm ghost" aria-label="Remove level">×</button></td>`;
    tr.querySelector('button').onclick=()=>{if(tb.children.length>1){tr.remove();run();}};tb.appendChild(tr);}
  function setLevels(L){tb.innerHTML='';L.forEach(x=>addRow(x[0],x[1]));}
  const F=wireForm(stage,run);
  stage.querySelector('[data-act="addlv"]').onclick=()=>{if(tb.children.length<4){const last=tb.lastElementChild;addRow(String((parseNum(last&&last.querySelector('[data-f=t]').value)||1)*5),'0.95');run();}};
  function run(){
    const dsh=parseNum(F.get('d').value)>0?'1':'0';F.get('dshow').value=dsh;
    const o=F.sync();
    [...tb.children].forEach((tr,i)=>tr.querySelector('.am-ln').textContent='L'+(i+1));
    stage.querySelector('[data-act="addlv"]').disabled=tb.children.length>=4;
    if(o.tab==='cache')return runCache(o);if(o.tab==='tlb')return runTLB(o);return runPF(o);
  }
  function runCache(o){
    const lv=[...tb.children].map(tr=>({t:parseNum(tr.querySelector('[data-f=t]').value),h:parseNum(tr.querySelector('[data-f=h]').value)}));
    const tm=parseNum(o.tm),r=amatLevels(lv,tm,o.mode);
    if(r.error){out.innerHTML=errBox(r.error);return;}
    const u=o.unit,n=lv.length,H=o.mode==='hier';
    const sym=[],num=[];let pre=[],preN=[];
    for(let i=0;i<=n;i++){
      const last=i===n;
      const ts=H?Array.from({length:i+(last?0:1)},(_,j)=>'t'+(j+1)).concat(last?['tm']:[]):[last?'tm':'t'+(i+1)];
      const tn=H?lv.slice(0,i+(last?0:1)).map(x=>fmt(x.t)).concat(last?[fmt(tm)]:[]):[last?fmt(tm):fmt(lv[i].t)];
      const ps=pre.concat(last?[]:['h'+(i+1)]),pn=preN.concat(last?[]:[fmt(lv[i].h)]);
      sym.push((ps.length?ps.join('·')+'·':'')+(ts.length>1?'('+ts.join(' + ')+')':ts[0]));
      num.push((pn.length?pn.join(' × ')+' × ':'')+(tn.length>1?'('+tn.join(' + ')+')':tn[0]));
      if(!last){pre.push('(1−h'+(i+1)+')');preN.push(fmt(1-lv[i].h));}
    }
    let nest='';
    if(H){let sN='',sT='';for(let i=n-1;i>=0;i--){const inner=i===n-1?fmt(tm):sN;const innerS=i===n-1?'tm':sT;sN=`${fmt(lv[i].t)} + ${fmt(1-lv[i].h)} × (${inner})`;sT=`t${i+1} + (1−h${i+1})·(${innerS})`;if(i===0){nest=`Same thing, nested (miss-penalty form):\nT = ${sT}\n  = ${sN}\n  = <b>${fmt(r.T)} ${u}</b>`;}}}
    out.innerHTML=chips([['Average access time T',fmt(r.T)+' '+u,'hi'],['Served by main memory',fmt(r.missAll*100,4)+'% of accesses'],['Access model',H?'Hierarchical':'Simultaneous']])+
      sec('Formula with numbers',fbox([`T = ${sym.join('\n  + ')}`,'',`T = ${num.join('\n  + ')}`,`  = ${r.rows.map(x=>fmt(x.c)).join(' + ')}`,`  = <b>${fmt(r.T)} ${u}</b>`].concat(nest?['',nest]:[])))+
      sec('Where each access is served',`<div class="coa-scroll"><table class="coa-tbl"><thead><tr><th>Served by</th><th>Probability</th><th>Time taken (${u})</th><th>Contribution</th></tr></thead><tbody>${r.rows.map(x=>`<tr><td>${x.where}</td><td>${fmt(x.p,6)}</td><td>${fmt(x.time)}</td><td>${fmt(x.c)}</td></tr>`).join('')}<tr class="coa-tot"><td>Total</td><td>${fmt(r.rows.reduce((a,x)=>a+x.p,0),6)}</td><td></td><td><b>${fmt(r.T)}</b></td></tr></tbody></table></div>`)+
      convBox([H?'<b>Hierarchical</b> (look-through, sequential): a level is searched only after the level above misses, so a miss at L1 costs t1 and then the next level’s time too.':'<b>Simultaneous</b> (look-aside, parallel): all levels are searched at once; an access served by level i costs only t<sub>i</sub>.',
        'Main memory always hits (hit ratio 1). Hit ratios are local: h2 is the fraction of L1 misses that hit in L2.',
        'Block transfer time and write traffic are ignored; if a question adds them, put them into the level’s access time.']);
  }
  function runTLB(o){
    const t=parseNum(o.t),m=parseNum(o.m),h=parseNum(o.h),L=parseNum(o.L),r=tlbEAT({t,m,h,L,mode:o.tmode});
    if(r.error){out.innerHTML=errBox(r.error);return;}
    const P=o.tmode==='par',Lp=L+1;
    const missS=P?`${Lp}m`:`t + ${Lp}m`,missN=P?`${Lp} × ${fmt(m)}`:`${fmt(t)} + ${Lp} × ${fmt(m)}`;
    out.innerHTML=chips([['Effective access time',fmt(r.EAT)+' ns','hi'],['TLB hit',fmt(r.hit)+' ns'],['TLB miss',fmt(r.miss)+' ns'],['Without a TLB',fmt(r.noTLB)+' ns']])+
      sec('Formula with numbers',fbox([`EAT = h·(t + m) + (1 − h)·(${missS})`,`    = ${fmt(h)} × (${fmt(t)} + ${fmt(m)}) + ${fmt(1-h)} × (${missN})`,`    = ${fmt(h)} × ${fmt(r.hit)} + ${fmt(1-h)} × ${fmt(r.miss)}`,`    = ${fmt(h*r.hit)} + ${fmt((1-h)*r.miss)} = <b>${fmt(r.EAT)} ns</b>`,'',`Slow-down over one plain memory access = ${fmt(r.EAT)} ÷ ${fmt(m)} = ${fmt(r.EAT/m)}×`]))+
      convBox([`TLB hit: one TLB lookup + one memory access for the data.`,`TLB miss: ${L} page-table access${L>1?'es (one per level)':''} + one data access = ${Lp} memory accesses${P?'; the TLB lookup overlaps the page-table walk, so its time is not added':'; the TLB lookup time is paid first'}.`,
        'No page faults and no data cache are assumed here; use the Page fault tab for fault rates.']);
  }
  function runPF(o){
    const U={ms:1e6,'µs':1e3,ns:1};
    const ma=parseNum(o.ma),p=parseNum(o.p),d=o.d.trim()?parseNum(o.d):0,sc=parseNum(o.sc)*U[o.scu],sd=parseNum(o.sd)*U[o.sdu],tg=o.tgt.trim()?parseNum(o.tgt):null;
    if(o.tgt.trim()&&!(tg>=0)){out.innerHTML=errBox('Target EAT must be a number (ns), or leave it blank.');return;}
    const r=pfEAT({ma,p,sClean:sc,sDirty:sd,d,addMa:o.addma,target:tg});
    if(r.error){out.innerHTML=errBox(r.error);return;}
    const sLine=d>0?[`Service time s = (1 − d)·s_clean + d·s_dirty = ${fmt(1-d)} × ${fmt(sc)} + ${fmt(d)} × ${fmt(sd)} = ${fmt(r.s)} ns`]:[`Service time s = ${fmt(sc/U[o.scu])} ${o.scu} = ${fmt(r.s)} ns`];
    const f=[...sLine,'',`EAT = (1 − p)·ma + p·${o.addma?'(s + ma)':'s'}`,`    = ${fmt(1-p,8)} × ${fmt(ma)} + ${fmt(p)} × ${fmt(r.sEff)}`,`    = ${fmt((1-p)*ma)} + ${fmt(p*r.sEff)} = <b>${fmt(r.EAT)} ns</b>${r.EAT>=1000?' = '+fmt(r.EAT/1000)+' µs':''}`,'',`Slow-down = EAT ÷ ma = ${fmt(r.EAT/ma)}×`];
    if(tg!=null){f.push('',`For EAT ≤ ${fmt(tg)} ns:  (1 − p)·ma + p·s′ ≤ ${fmt(tg)}  ⇒  p ≤ (${fmt(tg)} − ${fmt(ma)}) ÷ (${fmt(r.sEff)} − ${fmt(ma)})`);
      f.push(r.pMax==null?'   (service time must exceed ma)':r.pMax<0?'   target is below ma: impossible for any p ≥ 0':`   p ≤ <b>${fmt(r.pMax)}</b>  (about 1 fault in ${fmt(Math.round(1/r.pMax),0)} accesses)`);}
    out.innerHTML=chips([['Effective access time',fmt(r.EAT)+' ns','hi'],['Service time used',fmt(r.sEff)+' ns'],['Slow-down',fmt(r.EAT/ma)+'×'],tg!=null&&r.pMax!=null&&r.pMax>=0?['Max fault rate p',fmt(r.pMax),'hi']:null])+
      sec('Formula with numbers',fbox(f))+
      convBox(['All times are converted to ns (1 ms = 10<sup>6</sup> ns, 1 µs = 10<sup>3</sup> ns).',o.addma?'On a fault, the service time is followed by the memory access itself: p·(s + ma).':'The service time already includes the final memory access: p·s (the usual textbook form, e.g. Silberschatz).',
        'If a fraction d of victim pages are dirty, s = (1 − d)·s_clean + d·s_dirty (a dirty page must be written back first).']);
  }
  function setAll(v){F.set(v);setLevels(v.levels);run();}
  stage.querySelector('[data-act="dflt"]').onclick=()=>{const tab=F.read().tab;setAll(Object.assign({},DEF,{tab}));};
  stage.querySelector('[data-act="rand"]').onclick=()=>{
    const tab=F.read().tab,nl=rnd(1,3),lv=[];let t=pick([1,2,5]);for(let i=0;i<nl;i++){lv.push([String(t),String(pick([0.8,0.85,0.9,0.95,0.98]))]);t*=pick([5,10]);}
    setAll({tab,mode:pick(['hier','simul']),tm:String(pick([50,100,200,500])),unit:'ns',levels:lv,t:String(pick([5,10,20])),m:String(pick([50,100,200])),h:String(pick([0.8,0.9,0.95,0.98])),L:String(pick([1,1,2,3])),tmode:pick(['seq','seq','par']),
      ma:String(pick([100,200])),p:pick(['0.001','1e-6','0.0001','2e-5']),sc:String(pick([8,10,20])),scu:'ms',d:pick(['0','0','0.3','0.7']),sd:String(pick([20,25])),sdu:'ms',addma:false,tgt:pick(['','220',''])});
  };
  setAll(DEF);
 }});

/* ---------------------------------------------------------------- pipeline UI */
const PCOL=['#E8B4B8','#A8D5BA','#AFC8F0','#F3D9A4','#D4C1EC','#B5E3E0','#F5C6A5','#C9D8A7'];
ANIM.register('pipeline',{title:'Pipeline performance solver',steps:false,
 caption:'Enter k stages and n instructions (stage delays, latch delay, stalls) to get the space-time diagram, total time, speedup, efficiency and throughput.',
 build(stage){
  const DEF={k:'4',n:'6',del:'60 50 90 80',latch:'10',tnp:'',names:'',view:'stage',ev:[['stall','3','3','1'],['branch','5','','2']]};
  stage.innerHTML=shell(`
   <label>Stages k<input data-k="k" inputmode="numeric"></label>
   <label>Instructions n<input data-k="n" inputmode="numeric"></label>
   <label class="coa-wide">Stage delays in ns (one value = all equal)<input data-k="del" spellcheck="false"></label>
   <label>Latch / buffer delay (ns)<input data-k="latch" inputmode="decimal"></label>
   <label>Non-pipelined time per instruction (ns)<input data-k="tnp" inputmode="decimal" placeholder="blank = Σ stage delays"></label>
   <label class="coa-wide">Stage names (optional)<input data-k="names" spellcheck="false" placeholder="e.g. IF ID EX MEM WB"></label>
   <div class="coa-wide"><span class="lbl">Stalls and branch penalties</span><div class="pl-evs"></div>
     <div class="coa-btns"><button type="button" class="btn sm" data-act="addst">+ Data stall</button><button type="button" class="btn sm" data-act="addbr">+ Branch penalty</button></div></div>
   <div class="coa-wide"><span class="lbl">Diagram</span>${seg('view',[['stage','Stages × cycles'],['instr','Instructions × cycles']])}</div>`);
  const out=stage.querySelector('.coa-out'),evs=stage.querySelector('.pl-evs');
  function addEv(type,i,j,c){const d=document.createElement('div');d.className='pl-ev';
    d.innerHTML=`<select data-f="type" aria-label="Event type">${opts([['stall','Data stall'],['branch','Branch penalty']],type)}</select><label>on I<input data-f="i" inputmode="numeric" value="${esc(i)}" aria-label="Instruction number"></label><label class="pl-j">before stage<input data-f="j" inputmode="numeric" value="${esc(j)}" aria-label="Stage number"></label><label>cycles<input data-f="c" inputmode="numeric" value="${esc(c)}" aria-label="Cycles"></label><button type="button" class="btn sm ghost" aria-label="Remove">×</button>`;
    d.querySelector('button').onclick=()=>{d.remove();run();};evs.appendChild(d);}
  const F=wireForm(stage,run);
  stage.querySelector('[data-act="addst"]').onclick=()=>{const k=parseNum(F.get('k').value)||3;addEv('stall','2',String(Math.min(3,Math.max(2,k))),'1');run();};
  stage.querySelector('[data-act="addbr"]').onclick=()=>{addEv('branch','2','','2');run();};
  function run(){
    const o=F.sync();
    [...evs.children].forEach(d=>{d.querySelector('.pl-j').hidden=d.querySelector('[data-f=type]').value!=='stall';});
    const errs=[];
    const k=parseNum(o.k),n=parseNum(o.n);
    const dl=o.del.split(/[\s,;]+/).filter(Boolean).map(parseNum);
    if(!dl.length||dl.some(x=>isNaN(x)))errs.push('Stage delays: enter numbers separated by spaces, e.g. 60 50 90 80.');
    const latch=o.latch.trim()?parseNum(o.latch):0,tnp=o.tnp.trim()?parseNum(o.tnp):null;
    if(isNaN(latch))errs.push('Latch delay must be a number (0 if none).');
    if(o.tnp.trim()&&!(tnp>0))errs.push('Non-pipelined time must be a positive number, or leave it blank.');
    const events=[...evs.children].map(d=>({type:d.querySelector('[data-f=type]').value,i:parseNum(d.querySelector('[data-f=i]').value),j:parseNum(d.querySelector('[data-f=j]').value),c:parseNum(d.querySelector('[data-f=c]').value)}));
    if(errs.length){out.innerHTML=errBox(errs);return;}
    const r=pipeSim({k,n,delays:dl,latch,tnp,events});
    if(r.error){out.innerHTML=errBox(r.error);return;}
    let names=o.names.trim()?o.names.trim().split(/[\s,]+/):[];
    if(names.length!==r.k)names=Array.from({length:r.k},(_,j)=>'S'+(j+1));
    const eqd=r.d.every(x=>x===r.d[0]);
    const w=[];
    w.push(`Cycle time τ = max(stage delays) + latch = max(${r.d.map(x=>fmt(x)).join(', ')}) + ${fmt(r.latch)} = <b>${fmt(r.tau)} ns</b>`);
    w.push(`Cycles = k + n − 1${r.extra?' + stall cycles':''} = ${r.k} + ${r.n} − 1${r.extra?' + '+r.extra:''} = <b>${r.cycles}</b>`);
    w.push(`Pipelined time T<sub>p</sub> = cycles × τ = ${r.cycles} × ${fmt(r.tau)} = <b>${fmt(r.Tp)} ns</b>`);
    w.push(`Non-pipelined time per instruction t<sub>n</sub> = ${tnp!=null?'given = ':'sum of stage delays = '+(eqd&&r.k>1?`${r.k} × ${fmt(r.d[0])}`:r.d.map(x=>fmt(x)).join(' + '))+' = '}${fmt(r.tnp)} ns; for n instructions: ${r.n} × ${fmt(r.tnp)} = ${fmt(r.Tseq)} ns`);
    w.push(`Speedup S = n·t<sub>n</sub> ÷ T<sub>p</sub> = ${fmt(r.Tseq)} ÷ ${fmt(r.Tp)} = <b>${fmt(r.speedup)}</b>   (as n → ∞: t<sub>n</sub> ÷ τ = ${fmt(r.Sinf)})`);
    w.push(`Efficiency η = n ÷ cycles = ${r.n} ÷ ${r.cycles} = <b>${fmt(r.eff)}</b> (${fmt(r.eff*100,2)}% of stage-slots busy);   S ÷ k = ${fmt(r.speedup)} ÷ ${r.k} = ${fmt(r.effSk)}`);
    w.push(`Throughput = n ÷ T<sub>p</sub> = ${r.n} ÷ ${fmt(r.Tp)} ns = ${fmt(r.thr,6)} instr/ns = <b>${fmt(r.thr*1000)} MIPS</b>`);
    let html=chips([['Cycle time τ',fmt(r.tau)+' ns'],['Total cycles',r.cycles+(r.extra?` (${r.ideal} + ${r.extra} stall)`:''),'hi'],['Pipelined time',fmt(r.Tp)+' ns','hi'],['Non-pipelined time',fmt(r.Tseq)+' ns'],['Speedup',fmt(r.speedup),'hi'],['Efficiency',fmt(r.eff),'hi'],['Throughput',fmt(r.thr*1000)+' MIPS']])+
      sec('Working',`<ol class="coa-work">${w.map(x=>`<li>${x}</li>`).join('')}</ol>`);
    const LIM=80;
    if(r.cycles>LIM){html+=sec('Space-time diagram',`<p class="coa-note">The diagram is drawn for up to ${LIM} cycles; this run has ${r.cycles}. Reduce n to see it.</p>`);}
    else html+=sec('Space-time diagram',`<div class="pl-stp"></div><p class="coa-cap pl-cap" aria-live="polite"></p><div class="coa-scroll pl-dg"></div><p class="coa-note">Hatched cells: the instruction is held in that stage (stall). Empty cells in a stage row are bubbles.</p>`);
    html+=convBox(['Cycle time is set by the slowest stage plus the latch delay; every stage uses this clock.','Non-pipelined time = sum of the stage delays with no latch (unless you enter a value). Speedup compares n instructions on both machines.',
      'Efficiency here = fraction of stage-cycles doing useful work = n ÷ total cycles. Some books use S ÷ k; the two agree when stages are equal and there is no latch.',
      'A data stall of c cycles before stage j holds the instruction in stage j − 1, and everything behind it waits. A branch penalty of c cycles delays the fetch of the next instruction.']);
    out.innerHTML=html;
    if(r.cycles<=LIM)diagram(r,names,o.view);
  }
  function diagram(r,names,view){
    const g=pipeOcc(r),host=out.querySelector('.pl-dg'),cap=out.querySelector('.pl-cap');
    const cell=(x,c,k)=>{if(c>=k)return '<td class="pl-fut"></td>';if(!x)return '<td class="pl-bub"></td>';
      return `<td class="pl-c${x.held?' pl-held':''}" style="background:${PCOL[x.i%PCOL.length]}">${view==='stage'?'I'+(x.i+1):''}</td>`;};
    stepper(out.querySelector('.pl-stp'),r.cycles,k=>{
      const head=`<tr><th>${view==='stage'?'Stage':'Instr'}</th>${Array.from({length:r.cycles},(_,c)=>`<th class="${c===k-1?'pl-now':''}">${c+1}</th>`).join('')}</tr>`;
      let body='';
      if(view==='stage')body=g.map((row,j)=>`<tr><th>${esc(names[j])}</th>${row.map((x,c)=>cell(x,c,k)).join('')}</tr>`).join('');
      else{
        for(let i=0;i<r.n;i++){body+=`<tr><th>I${i+1}</th>`;for(let c=0;c<r.cycles;c++){let x=null,j0=-1;for(let j=0;j<r.k;j++)if(g[j][c]&&g[j][c].i===i){x=g[j][c];j0=j;}
          body+=c>=k?'<td class="pl-fut"></td>':x?`<td class="pl-c${x.held?' pl-held':''}" style="background:${PCOL[i%PCOL.length]}">${x.held?'stall':esc(names[j0])}</td>`:'<td></td>';}body+='</tr>';}
      }
      host.innerHTML=`<table class="coa-tbl pl-t">${head}${body}</table>`;
      if(!k){cap.innerHTML='Cycle 0: the pipeline is empty. Step through to fill it one clock at a time.';return;}
      const busy=g.map((row,j)=>row[k-1]?`I${row[k-1].i+1} in ${esc(names[j])}${row[k-1].held?' (held)':''}`:null).filter(Boolean);
      const done=r.start.filter(s=>s[r.k-1]<=k-1).length;
      cap.innerHTML=`<b>Cycle ${k}</b> (t = ${fmt((k-1)*r.tau)}–${fmt(k*r.tau)} ns): ${busy.length?busy.join(', '):'all stages idle (bubble)'}. Completed: ${done} of ${r.n}.`;
    },(k,n)=>`Cycle ${k} of ${n}`);
  }
  function setAll(v){F.set(v);evs.innerHTML='';(v.ev||[]).forEach(e=>addEv(...e));run();}
  stage.querySelector('[data-act="dflt"]').onclick=()=>setAll(DEF);
  stage.querySelector('[data-act="rand"]').onclick=()=>{
    const k=rnd(3,6),n=rnd(4,9),eq=Math.random()<.4,dd=eq?[pick([10,20,25,50])]:Array.from({length:k},()=>rnd(2,10)*10);
    const ev=[];if(Math.random()<.6)ev.push(['stall',String(rnd(2,n)),String(rnd(2,k)),String(rnd(1,2))]);if(Math.random()<.4)ev.push(['branch',String(rnd(1,n-1)),'',String(rnd(1,3))]);
    setAll({k:String(k),n:String(n),del:dd.join(' '),latch:String(pick([0,0,5,10])),tnp:'',names:k===5&&Math.random()<.5?'IF ID EX MEM WB':'',view:F.read().view,ev});
  };
  setAll(DEF);
 }});

/* ---------------------------------------------------------------- ieee754 UI */
ANIM.register('ieee754',{title:'IEEE 754 converter',steps:false,
 caption:'Convert a decimal to IEEE 754 single or double precision (or decode hex back to a value), with every step: binary, normalise, bias, round, pack.',
 build(stage){
  const DEF={dir:'enc',fmt:'single',rnd:'rne',x:'-13.625',hx:'41480000'};
  stage.innerHTML=shell(`
   <div class="coa-wide">${seg('dir',[['enc','Decimal → IEEE'],['dec','Hex → decimal']])}</div>
   <div>${seg('fmt',[['single','Single (32-bit)'],['double','Double (64-bit)']])}</div>
   <label data-show="dir:enc">Rounding<select data-k="rnd">${opts([['rne','Nearest, ties to even'],['trunc','Truncate (chop)']])}</select></label>
   <label class="coa-wide" data-show="dir:enc">Decimal number<input data-k="x" spellcheck="false" placeholder="e.g. -13.625, 0.1, 1e-40, inf, nan"></label>
   <label class="coa-wide" data-show="dir:dec">Hex pattern<input data-k="hx" spellcheck="false" placeholder="e.g. C15A0000"></label>`);
  const out=stage.querySelector('.coa-out');
  const F=wireForm(stage,run);
  const grp=s=>s.replace(/(.{4})(?=.)/g,'$1 ');
  function fields(r){
    return `<div class="ie-bits" role="img" aria-label="sign ${r.sign}, exponent ${r.expBits}, mantissa ${r.fracBits}">
      <div class="ie-f s"><b>Sign</b><code>${r.sign}</code><span>1 bit</span></div>
      <div class="ie-f e"><b>Exponent</b><code>${grp(r.expBits)}</code><span>${r.E} bits · ${r.biased}</span></div>
      <div class="ie-f m"><b>Mantissa (fraction)</b><code>${grp(r.fracBits)}</code><span>${r.fb} bits</span></div></div>`;
  }
  const hexg=h=>h.replace(/(.{2})(?=.)/g,'$1 ');
  const zc=s=>s.replace(/0{14,}/g,z=>`0…(${z.length} zeros)…`);
  function run(){
    const o=F.sync();
    if(o.dir==='dec')return runDec(o);
    const r=ieeeEncode(o.x,o.fmt,o.rnd);
    if(r.error){out.innerHTML=errBox(r.error);return;}
    let html=chips([['Hex','0x'+hexg(r.hex),'hi'],['Sign',r.sign],['Biased exponent',`${r.biased} = ${r.expBits}`],['Class',r.cls,r.special?'':'hi'],r.special?null:['Stored value',r.overflow&&r.round==='rne'?'∞':esc(r.storedExact.length>24?'≈ '+(r.sign?'-':'')+ratToSci(r.storedNum,r.storedDen,9):r.storedExact)]]);
    html+=sec('Bit pattern',fields(r));
    const st=[];
    const bias=r.bias,fb=r.fb;
    if(r.special){
      if(r.cls==='NaN')st.push('NaN is stored with the exponent all 1s and a non-zero fraction (here the quiet-NaN pattern, fraction MSB = 1).');
      else if(r.zero)st.push(`Zero is special: exponent all 0s and fraction all 0s. The sign bit is ${r.sign}, so this is ${r.sign?'−0':'+0'}.`);
      else st.push(`Infinity is stored with the exponent all 1s (${(1<<r.E)-1}) and fraction all 0s; sign ${r.sign}.`);
      html+=sec('Steps',`<ol class="coa-work">${st.map(x=>`<li>${x}</li>`).join('')}</ol>`);
    }else{
      st.push(`<b>Sign.</b> The number is ${r.sign?'negative':'positive'}, so s = <b>${r.sign}</b>. Work with |x| = ${esc(r.xAbs.length>40?r.xSci:r.xAbs)}.`);
      let b2=`<b>Convert to binary.</b> Integer part ${r.intPart} = ${r.intPart>0n?r.intBin.replace(/^0+(?=.)/,''):'0'}<sub>2</sub>`;
      if(r.intPart>0n&&r.intPart<=255n){const rows=[];let v=r.intPart;while(v>0n){rows.push(`${v} ÷ 2 = ${v/2n} r <b>${v%2n}</b>`);v/=2n;}b2+=`<div class="coa-mini">${rows.join('<br>')}<br><i>read the remainders bottom-up</i></div>`;}
      if(r.fracNum>0n&&r.eTrue<-8)b2+=`<br>The fraction part is tiny (below 2<sup>−8</sup>), so the ×2 table would print ${-r.eTrue-1} zero bits before the first 1; the expansion below compresses them.<br>`;
      else if(r.fracNum>0n){
        const D=r.D,dl=D.toString().length-1,dec=v=>{const s=v.toString().padStart(dl,'0').replace(/0+$/,'');return '0.'+(s||'0');};
        const rows=[],seen=new Map();let f=r.fracNum,rep=null;
        for(let i=0;i<12&&f>0n;i++){if(seen.has(f)){rep=seen.get(f);break;}seen.set(f,i);const t=f*2n,bit=t>=D?1:0;rows.push(`${dec(f)} × 2 = ${bit}.${dec(t%D).slice(2)} → <b>${bit}</b>`);f=t%D;}
        b2+=`<br>Fraction part ${dec(r.fracNum)}: multiply by 2 and take the integer bit each time:<div class="coa-mini">${rows.join('<br>')}${f>0n?(rep!=null?`<br><i>the fraction ${dec(f)} repeats (row ${rep+1}), so the bits recur forever</i>`:'<br><i>…continues</i>'):'<br><i>fraction reached 0: exact</i>'}</div>`;
      }
      b2+=`|x| = <code class="coa-wrap">${esc(r.intBin.replace(/^0+(?=.)/,''))}${(r.more?r.fracBin:r.fracBin.replace(/0+$/,''))?'.'+esc(zc(r.more?r.fracBin:r.fracBin.replace(/0+$/,''))):''}${r.more?'…':''}</code><sub>2</sub>`;
      st.push(b2);
      if(r.eTrue>=r.emin)st.push(`<b>Normalise.</b> Move the binary point so one 1 is left of it: |x| = 1.${esc(zc(fracPreview(r)))}${r.more?'…':''} × 2<sup>${r.eTrue}</sup>. The true exponent e = <b>${r.eTrue}</b>.`);
      else st.push(`<b>Too small to normalise.</b> |x| &lt; 2<sup>${r.emin}</sup> (the smallest normal), so it is stored as a <b>denormal</b>: 0.fraction × 2<sup>${r.emin}</sup>, with exponent field 0.`);
      if(r.overflow)st.push(`<b>Overflow.</b> e = ${r.eTrue} is more than the largest exponent ${bias}. ${r.round==='rne'?'Round-to-nearest gives <b>∞</b>: exponent all 1s, fraction 0.':'Truncation gives the <b>largest finite</b> number instead.'}`);
      if(!(r.overflow&&r.round==='rne')){
        if(r.normal)st.push(`<b>Bias the exponent.</b> Stored exponent E = e + bias = ${r.eu} + ${bias} = <b>${r.biased}</b> = ${r.expBits}<sub>2</sub>.${r.carry?' (Rounding carried into the exponent: the mantissa overflowed to 10.000…, so e went up by 1.)':''}${r.eTrue<r.emin?' (Rounding pushed the denormal up to the smallest normal.)':''}`);
        else st.push(`<b>Exponent field.</b> Denormals store E = 0 (meaning 2<sup>${r.emin}</sup>, not 2<sup>${-bias}</sup>).`);
        const fr0=(r.M0&((1n<<B(fb))-1n)).toString(2).padStart(fb,'0');
        st.push(`<b>Round to ${fb} fraction bits.</b> First ${fb} bits after the ${r.eTrue>=r.emin?'leading 1':'binary point (×2<sup>'+r.emin+'</sup>)'}: <code class="coa-wrap">${grp(fr0)}</code>; next bits: guard ${r.G}, round ${r.Rb}, sticky ${r.St?1:0}. `+
          (!r.inexact?'Nothing is lost: the value is <b>exact</b>.':r.round==='trunc'?'Truncate: drop the extra bits.':r.up?`The dropped part is ${r.G&&!(r.Rb||r.St)?'exactly half, and the last kept bit is 1 (odd), so round up to make it even':'more than half an ulp'}: <b>round up</b> (+1 in the last place).`:`The dropped part is ${r.G&&!(r.Rb||r.St)?'exactly half and the last bit is already 0 (even), so keep it':'less than half an ulp'}: <b>round down</b> (keep).`));
        st.push(`<b>Pack.</b> s | E | fraction = ${r.sign} | ${r.expBits} | ${grp(r.fracBits)} = <b>0x${r.hex}</b>.`);
        if(r.inexact)st.push(`<b>Check.</b> Stored value = <code class="coa-wrap">${esc(r.storedExact.length>70?r.storedExact.slice(0,70)+'…':r.storedExact)}</code>; rounding error = ${esc(r.errSci)}.`);
      }else st.push(`<b>Pack.</b> ${r.sign} | ${r.expBits} | ${grp(r.fracBits)} = <b>0x${r.hex}</b>.`);
      html+=sec('Steps',`<ol class="coa-work">${st.map(x=>`<li>${x}</li>`).join('')}</ol>`);
      html+=sec('Formula',fbox([r.normal||r.overflow?`value = (−1)<sup>s</sup> × 1.fraction × 2<sup>E − ${bias}</sup>`:`value = (−1)<sup>s</sup> × 0.fraction × 2<sup>${r.emin}</sup>  (denormal)`,
        r.overflow&&r.round==='rne'?'':r.normal?`      = (−1)<sup>${r.sign}</sup> × 1.${r.fracBits.replace(/0+$/,'')||'0'}<sub>2</sub> × 2<sup>${r.biased} − ${bias}</sup>`:r.M===0n?'      = 0 (underflow)':`      = (−1)<sup>${r.sign}</sup> × 0.${r.fracBits.replace(/0+$/,'')}<sub>2</sub> × 2<sup>${r.emin}</sup>`]));
    }
    html+=convBox([`${r.fmt==='single'?'Single: 1 sign + 8 exponent + 23 fraction bits, bias 127, normal exponents −126…127.':'Double: 1 sign + 11 exponent + 52 fraction bits, bias 1023, normal exponents −1022…1023.'}`,
      o.rnd==='rne'?'Rounding: round to nearest, ties to even (the IEEE default).':'Rounding: truncate (drop the extra bits, round toward zero).',
      'Exponent all 0s = zero or denormal (no hidden 1); all 1s = ∞ (fraction 0) or NaN (fraction ≠ 0).']);
    out.innerHTML=html;
  }
  function fracPreview(r){const s=(r.intBin+r.fracBin).replace(/^0+/,'');let t=s.slice(1,r.fb+4);if(!r.more)t=t.replace(/0+$/,'');return t||'0';}
  function runDec(o){
    const r=ieeeDecode(o.hx,o.fmt);
    if(r.error){out.innerHTML=errBox(r.error);return;}
    const bias=r.bias;let html=chips([['Value',esc(r.value.length>40?r.value.slice(0,40)+'…':r.value),'hi'],['Class',r.cls,'hi'],['Sign',r.sign],['Exponent field',`${r.biased} = ${r.expBits}`],isFinite(r.num)&&r.num!==0?['≈',r.fmt==='single'?String(+r.num.toPrecision(9)):String(r.num)]:null]);
    html+=sec('Bit pattern',fields(r));
    const st=[`<b>Split the bits.</b> 0x${r.hex} = ${r.sign} | ${r.expBits} | ${grp(r.fracBits)}.`,`<b>Sign</b> s = ${r.sign} ⇒ ${r.sign?'negative':'positive'}.`];
    if(r.cls.includes('∞'))st.push('Exponent all 1s and fraction 0 ⇒ <b>'+r.cls+'</b>.');
    else if(r.cls.includes('NaN'))st.push(`Exponent all 1s and fraction ≠ 0 ⇒ <b>NaN</b>. Fraction MSB ${r.fracBits[0]} ⇒ ${r.cls}.`);
    else if(r.M===0n)st.push(`Exponent 0 and fraction 0 ⇒ <b>${r.cls}</b>.`);
    else if(r.cls==='normal'){
      st.push(`<b>Exponent.</b> E = ${r.expBits}<sub>2</sub> = ${r.biased}; e = E − ${bias} = <b>${r.e}</b>.`);
      st.push(`<b>Significand.</b> Put back the hidden 1: 1.${r.fracBits.replace(/0+$/,'')||'0'}<sub>2</sub> = ${esc(exactDec(r.M,-r.fb))}.`);
      st.push(`<b>Value</b> = (−1)<sup>${r.sign}</sup> × ${esc(exactDec(r.M,-r.fb))} × 2<sup>${r.e}</sup> = <code class="coa-wrap">${esc(r.value.length>90?r.value.slice(0,90)+'…':r.value)}</code>.`);
    }else{
      st.push(`<b>Exponent field 0, fraction ≠ 0 ⇒ denormal.</b> No hidden 1; the exponent is fixed at 1 − ${bias} = ${r.e}.`);
      st.push(`<b>Value</b> = (−1)<sup>${r.sign}</sup> × 0.${r.fracBits.replace(/0+$/,'')}<sub>2</sub> × 2<sup>${r.e}</sup> = <code class="coa-wrap">${esc(r.value.length>90?r.value.slice(0,90)+'…':r.value)}</code>.`);
    }
    html+=sec('Steps',`<ol class="coa-work">${st.map(x=>`<li>${x}</li>`).join('')}</ol>`);
    html+=convBox(['The value shown is exact (every binary fraction has a finite decimal expansion); ≈ is the shortest decimal that rounds back to the same bits.',
      'Exponent all 0s = zero or denormal; all 1s = ∞ or NaN. NaN with fraction MSB 1 is quiet, with MSB 0 signalling.']);
    out.innerHTML=html;
  }
  const SAMPLES=['0.1','-13.625','0.15625','3.75','-0.375','1e-40','100.2','0.7','-2.5','65504','1e39','5e-324','1','0.3','255.5','-0.0'];
  stage.querySelector('[data-act="dflt"]').onclick=()=>{const cur=F.read();F.set(Object.assign({},DEF,{dir:cur.dir}));run();};
  stage.querySelector('[data-act="rand"]').onclick=()=>{
    const cur=F.read();
    if(cur.dir==='enc'){const x=Math.random()<.5?pick(SAMPLES):((Math.random()<.3?'-':'')+(rnd(0,300)+rnd(0,999)/1000*(Math.random()<.5?1:0)+pick([0.5,0.25,0.125,0.1,0.2,0.75,0.0625])).toFixed(pick([1,2,3,4])).replace(/0+$/,'').replace(/\.$/,''));F.set({x});}
    else{const W=cur.fmt==='single'?8:16;let h;const r=Math.random();
      if(r<.15)h=pick(cur.fmt==='single'?['7F800000','FF800000','7FC00000','80000000','00000001','00800000','7F7FFFFF']:['7FF0000000000000','8000000000000000','0000000000000001','7FF8000000000000']);
      else{const tops=cur.fmt==='single'?['3F','40','41','42','BF','C0','C1','3E','3D']:['3F','40','BF','C0'];h=pick(tops)+Array.from({length:W-2},(_,i)=>i<2?'0123456789ABCDEF'[rnd(0,15)]:pick(['0','0','0','8','4','C'])).join('');}
      F.set({hx:h});}
    run();
  };
  F.set(DEF);run();
 }});

/* ---------------------------------------------------------------- kmap UI */
ANIM.register('kmap',{title:'K-map minimiser',steps:false,
 caption:'Enter minterms and don\'t-cares (2–5 variables) to get the K-map with grouped prime implicants, the minimal SOP and POS, and optional Quine–McCluskey working.',
 build(stage){
  const DEF={n:'4',names:'A B C D',ms:'0 1 2 5 8 9 10',ds:'',view:'sop',qm:false};
  stage.innerHTML=shell(`
   <label>Variables<select data-k="n">${opts([['2','2'],['3','3'],['4','4'],['5','5']])}</select></label>
   <label>Variable names (MSB first)<input data-k="names" spellcheck="false"></label>
   <label class="coa-wide">Minterms Σm( … )<input data-k="ms" spellcheck="false" placeholder="e.g. 0 1 2 5 8 9 10"></label>
   <label class="coa-wide">Don't-cares d( … )<input data-k="ds" spellcheck="false" placeholder="optional"></label>
   <div class="coa-wide"><span class="lbl">Show groups for</span>${seg('view',[['sop','Minimal SOP (1s)'],['pos','Minimal POS (0s)'],['all','All prime implicants']])}</div>
   <label class="chk coa-wide"><input type="checkbox" data-k="qm"> Show Quine–McCluskey steps</label>`);
  const out=stage.querySelector('.coa-out');
  const F=wireForm(stage,run);
  let lastN=null;
  const clean=s=>String(s||'').replace(/[Σ∑]/g,' ').replace(/\b(sum|m|d|dc)\s*\(/gi,' ').replace(/[()]/g,' ');
  function run(){
    const o=F.sync(),n=+o.n;
    if(lastN!==null&&lastN!==n){const cur=o.names.trim().split(/[\s,]+/).filter(Boolean);if(cur.length!==n){F.get('names').value='ABCDE'.slice(0,n).split('').join(' ');o.names=F.get('names').value;}}
    lastN=n;
    const P=parseList(clean(o.ms),true),Q=parseList(clean(o.ds),true);
    const errs=[];
    if(P.bad.length)errs.push(`Minterms: "${P.bad.join(' ')}" ${P.bad.length>1?'are not whole numbers':'is not a whole number'}.`);
    if(Q.bad.length)errs.push(`Don't-cares: "${Q.bad.join(' ')}" ${Q.bad.length>1?'are not whole numbers':'is not a whole number'}.`);
    const names=o.names.trim().split(/[\s,]+/).filter(Boolean);
    if(names.length!==n)errs.push(`Give exactly ${n} variable names (you gave ${names.length}).`);
    else if(new Set(names).size!==n)errs.push('Variable names must be different.');
    else if(names.some(x=>!/^[A-Za-z][A-Za-z0-9]{0,3}$/.test(x)))errs.push('Variable names must be short and start with a letter (e.g. A B C D, or x y z w).');
    if(errs.length){out.innerHTML=errBox(errs);return;}
    const r=kmSolve(n,P.vals,Q.vals,names);
    if(r.error){out.innerHTML=errBox(r.error);return;}
    render(r,o);
  }
  function lay(n){
    const G1=[0,1],G2=[0,1,3,2];
    const rv=n<=3?1:2,cv=n===2?1:2;
    return (n===5?[0,1]:[null]).map(a=>({a,rowG:rv===1?G1:G2,colG:cv===1?G1:G2,rv,cv,idx:(rr,c)=>((a||0)<<(rv+cv))|(rr<<cv)|c}));
  }
  const bin=(v,w)=>v.toString(2).padStart(w,'0');
  function render(r,o){
    const {n,names}=r,view=o.view;
    const L=lay(n),rowVars=n===2?[names[0]]:n===3?[names[0]]:n===4?names.slice(0,2):names.slice(1,3),colVars=n===2?[names[1]]:n===3?names.slice(1):n===4?names.slice(2):names.slice(3);
    const val=i=>r.ms.includes(i)?'1':r.ds.includes(i)?'X':'0';
    /* groups for the chosen view, EPIs first */
    let groups=[],kind;
    if(view==='all'){groups=r.pis.slice();kind='all';}
    else{
      const sol=(view==='pos'?r.coverZ:r.cover).sols[0]||[],epi=view==='pos'?r.epiZ:r.epi;
      groups=sol.slice().sort((a,b)=>(epi.includes(b)-epi.includes(a))||a.id-b.id);kind=view;
    }
    const epiSet=new Set((view==='pos'?r.epiZ:r.epi).map(p=>p.id));
    const isEpi=p=>view==='all'?r.epi.includes(p):epiSet.has(p.id);
    const term=p=>view==='pos'?termPOS(p,names):termSOP(p,names);
    const sopMain=r.sop[0],posMain=r.pos[0];
    const trivial=r.ms.length===0||r.zeros.length===0;
    let html=chips([['Minimal SOP','F = '+esc(sopMain),'hi'],['Minimal POS','F = '+esc(posMain),'hi'],['Prime implicants',r.pis.filter(p=>p.covers.length).length+(r.pis.some(p=>!p.covers.length)?` (+${r.pis.filter(p=>!p.covers.length).length} covering only don't-cares)`:'')],['Essential PIs',r.epi.length],['Cost',trivial?'—':`${r.cover.terms} terms, ${r.cover.lits} literals`]]);
    if(r.sop.length>1)html+=`<p class="coa-note"><b>${r.sop.length} minimal SOPs</b> (equal cost): ${r.sop.slice(0,6).map(s=>'F = '+esc(s)).join(';&nbsp; ')}${r.sop.length>6?' …':''}</p>`;
    if(r.pos.length>1)html+=`<p class="coa-note"><b>${r.pos.length} minimal POS forms</b>: ${r.pos.slice(0,4).map(s=>'F = '+esc(s)).join(';&nbsp; ')}${r.pos.length>4?' …':''}</p>`;
    html+=sec('K-map',`<div class="km-stp"></div><p class="coa-cap km-cap" aria-live="polite"></p><div class="km-maps"></div><div class="km-leg"></div>`);
    if(o.qm)html+=sec('Quine–McCluskey',qmHTML(r));
    html+=convBox(['Variable order: '+names.join(', ')+' with '+names[0]+' as the most significant bit; minterm number = binary value of '+names.join('')+'.',
      'Rows and columns use Gray-code order (00, 01, 11, 10), so neighbouring cells, and the outer edges, differ in one bit.',
      'Minimal means fewest terms first, then fewest literals. Don\'t-cares (X) are used only when they make a group bigger; they never have to be covered.',
      'POS is found by grouping the 0s (plus useful X) to get F′ in SOP form, then applying De Morgan. A complemented variable is written with a prime: A′ = NOT A.']);
    out.innerHTML=html;
    const maps=out.querySelector('.km-maps'),cap=out.querySelector('.km-cap'),leg=out.querySelector('.km-leg');
    const inG=(p,i)=>(i&~p.m)===p.v;
    leg.innerHTML=groups.length?`<ol class="km-l">${groups.map((p,gi)=>`<li data-g="${gi}"><i style="background:var(--kc${gi%8})"></i><code>${p.pat}</code> <b>${esc(term(p))}</b> <span>${view==='pos'?'M':'m'}(${p.terms.join(',')})</span>${isEpi(p)?' <em>essential</em>':''}${!p.covers.length?' <em class="km-dc">only X</em>':''}</li>`).join('')}</ol>`:'';
    stepper(out.querySelector('.km-stp'),groups.length,k=>{
      const shown=groups.slice(0,k),cur=k?groups[k-1]:null;
      maps.innerHTML=L.map(M=>`<div class="km-map">${n===5?`<div class="km-mt">${esc(names[0])} = ${M.a}</div>`:''}<table class="km-t"><thead><tr><th class="km-cn"><span>${esc(rowVars.join(''))}</span>\\<span>${esc(colVars.join(''))}</span></th>${M.colG.map(c=>`<th>${bin(c,M.cv)}</th>`).join('')}</tr></thead><tbody>${M.rowG.map(rr=>`<tr><th>${bin(rr,M.rv)}</th>${M.colG.map(c=>{
        const i=M.idx(rr,c),v=val(i),rings=[];shown.forEach((p,gi)=>{if(inG(p,i))rings.push(gi);});
        const sh=rings.map((gi,x)=>`inset 0 0 0 ${3*(x+1)}px var(--kc${gi%8})`).join(',');
        const bg=cur&&inG(cur,i)?`background:color-mix(in srgb,var(--kc${(k-1)%8}) 26%,var(--surface));`:'';
        const dim=(view==='pos'&&v==='1')||(view!=='pos'&&v==='0');
        return `<td class="km-c v${v==='X'?'x':v}${dim?' km-dim':''}" style="${bg}${sh?'box-shadow:'+sh:''}"><b>${v}</b><small>${i}</small></td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`).join('');
      leg.querySelectorAll('li').forEach(li=>{const g=+li.dataset.g;li.classList.toggle('coa-fut',g>=k);li.classList.toggle('coa-now',g===k-1);});
      if(!groups.length){cap.innerHTML=trivial?(r.ms.length===0?'No minterms: F = 0 everywhere, so there is nothing to group.':'Every cell is 1 or X: F = 1.'):'No groups.';return;}
      if(!cur){cap.innerHTML=`The map with ${view==='pos'?'its 0s highlighted (group the 0s for POS)':'the 1s and don\'t-cares'}. Step through to add one group at a time${view==='all'?'':', essential prime implicants first'}.`;return;}
      const sz=cur.terms.length,why=isEpi(cur)?`<b>essential</b>: it is the only prime implicant covering ${view==='pos'?'M':'m'}${cur.covers.find(mt=>(view==='pos'?r.qmZ:r.qm).pis.filter(q=>q.covset.has(mt)).length===1)}`:view==='all'?'a prime implicant (it cannot be made bigger)':'chosen to cover what is left at the least cost';
      cap.innerHTML=`Group ${k}: ${sz} cell${sz>1?'s':''} ${view==='pos'?'M':'m'}(${cur.terms.join(', ')}), pattern <code>${cur.pat}</code> → <b>${esc(term(cur))}</b>. ${why}.${view==='pos'?' (A 0-group gives a sum term: 0 in the pattern → plain variable, 1 → primed.)':''}`;
    },(k,n2)=>`Group ${k} of ${n2}`);
  }
  function qmHTML(r){
    const n=r.n;let h='';
    r.qm.cols.forEach((col,ci)=>{
      const byOnes=new Map();col.forEach(x=>{const c=popc(x.v);if(!byOnes.has(c))byOnes.set(c,[]);byOnes.get(c).push(x);});
      const ks=[...byOnes.keys()].sort((a,b)=>a-b);
      h+=`<div class="coa-scroll"><table class="coa-tbl km-q"><caption>${ci===0?'Column 1: minterms and don\'t-cares grouped by number of 1s':`Column ${ci+1}: pairs from column ${ci} that differ in one bit`}</caption><thead><tr><th>#1s</th><th>Terms</th><th>Pattern</th><th>Combined?</th></tr></thead><tbody>${ks.map(c=>byOnes.get(c).map((x,j)=>`<tr${j===0?' class="km-gsep"':''}><td>${j===0?c:''}</td><td>${x.terms.map(t=>r.ds.includes(t)?`<i>${t}</i>`:t).join(',')}</td><td><code>${patOf(x.v,x.m,n)}</code></td><td>${x.used?'✓':'<b>PI</b>'}</td></tr>`).join('')).join('')}</tbody></table></div>`;
    });
    const pis=r.pis.filter(p=>p.covers.length);
    if(r.ms.length&&pis.length){
      h+=`<div class="coa-scroll"><table class="coa-tbl km-chart"><caption>Prime implicant chart (don't-cares are not columns). ★ = essential; ⊗ = the only cover of that minterm.</caption><thead><tr><th>PI</th><th>Term</th>${r.ms.map(m=>`<th>${m}</th>`).join('')}</tr></thead><tbody>${pis.map(p=>{const e=r.epi.includes(p);
        return `<tr${e?' class="km-epi"':''}><td><code>${p.pat}</code>${e?' ★':''}</td><td>${esc(termSOP(p,r.names))}</td>${r.ms.map(m=>{if(!p.covset.has(m))return '<td></td>';const only=pis.filter(q=>q.covset.has(m)).length===1;return `<td class="${only?'km-only':''}">${only?'⊗':'×'}</td>`;}).join('')}</tr>`;}).join('')}</tbody></table></div>`;
      const E=r.epi,covered=new Set(E.flatMap(p=>p.covers)),left=r.ms.filter(m=>!covered.has(m));
      h+=`<ol class="coa-work"><li>Essential prime implicants: ${E.length?E.map(p=>`<b>${esc(termSOP(p,r.names))}</b>`).join(', '):'none'}.</li><li>Minterms still uncovered after the EPIs: ${left.length?left.join(', '):'none. The EPIs alone give the answer'}.</li>${left.length?`<li>Cover them with the fewest extra PIs (Petrick’s method / exhaustive search): ${r.cover.sols[0].filter(p=>!E.includes(p)).map(p=>`<b>${esc(termSOP(p,r.names))}</b>`).join(', ')}${r.cover.sols.length>1?` (one of ${r.cover.sols.length} equally cheap choices)`:''}.</li>`:''}<li>F = <b>${esc(r.sop[0])}</b></li></ol>`;
    }
    return h;
  }
  stage.querySelector('[data-act="dflt"]').onclick=()=>{F.set(DEF);lastN=4;run();};
  stage.querySelector('[data-act="rand"]').onclick=()=>{
    const n=pick([3,4,4,4,5]),N=1<<n,ms=[],ds=[];
    for(let i=0;i<N;i++){const x=Math.random();if(x<.42)ms.push(i);else if(x<.52)ds.push(i);}
    if(!ms.length)ms.push(rnd(0,N-1));
    F.set({n:String(n),names:'ABCDE'.slice(0,n).split('').join(' '),ms:ms.join(' '),ds:ds.filter(d=>!ms.includes(d)).join(' ')});lastN=n;run();
  };
  F.set(DEF);lastN=4;run();
 }});
})();

/* ================= UGC NET solvers: group db (fdtool, serial, bptree) =================
   Pure algorithms live on NETSOLVE.fdtool / NETSOLVE.serial / NETSOLVE.bptree so they can be
   tested in Node (global.window = {}). Everything is wrapped in an IIFE so no global names are
   declared (several net-*.js files are concatenated into one script). */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;
const pc=m=>{let c=0;while(m){m&=m-1;c++;}return c;};
const bitsOf=m=>{const r=[];for(let i=0;m;i++,m>>>=1)if(m&1)r.push(i);return r;};
const cmpMask=(a,b)=>{const d=pc(a)-pc(b);if(d)return d;const x=bitsOf(a),y=bitsOf(b);for(let i=0;i<x.length;i++)if(x[i]!==y[i])return x[i]-y[i];return 0;};

/* ======================================================================
   FDTOOL core
   ====================================================================== */
const FD={};
FD.parseRel=function(text){
  let s=String(text==null?'':text).trim();
  const m=s.match(/^[A-Za-z_]\w*\s*\(([\s\S]*)\)$/);if(m)s=m[1].trim();
  if(!s)return {err:'Enter the relation’s attributes, e.g. ABCDE or emp, dept, mgr.'};
  const names=/[\s,]/.test(s)?s.split(/[\s,]+/).filter(Boolean):[...s];
  for(const nm of names)if(!/^[A-Za-z_][A-Za-z0-9_']*$/.test(nm))return {err:`"${nm}" is not a valid attribute name (use letters, digits, _).`};
  const seen=new Set();for(const nm of names){if(seen.has(nm))return {err:`Attribute "${nm}" is listed twice.`};seen.add(nm);}
  if(names.length>16)return {err:'At most 16 attributes, please (the solver enumerates subsets).'};
  const single=names.every(x=>x.length===1);
  return {names,n:names.length,single,all:(1<<names.length)-1};
};
FD.parseSide=function(rel,s,where){
  s=s.trim();if(!s)return {err:`Empty side in "${where}".`};
  const toks=rel.single?[...s.replace(/[\s,{}]/g,'')]:s.replace(/[{}]/g,' ').split(/[\s,]+/).filter(Boolean);
  let m=0;for(const t of toks){const i=rel.names.indexOf(t);if(i<0)return {err:`Unknown attribute "${t}" in "${where}". Attributes: ${rel.names.join(rel.single?'':', ')}.`};m|=1<<i;}
  return {m};
};
FD.parseFDs=function(rel,text){
  const t=String(text==null?'':text).replace(/→|⟶|=>|—>|-+>/g,'->');
  const chunks=t.split(rel.single?/[,;\n]+/:/[;\n]+/).map(x=>x.trim()).filter(Boolean);
  const F=[];
  for(const c of chunks){
    const parts=c.split('->');
    if(parts.length!==2)return {err:`"${c}" is not an FD. Write it like AB->C${rel.single?'':' (separate FDs with ; or new lines)'}.`};
    const L=FD.parseSide(rel,parts[0],c);if(L.err)return L;
    const R=FD.parseSide(rel,parts[1],c);if(R.err)return R;
    F.push({L:L.m,R:R.m});
  }
  if(F.length>40)return {err:'At most 40 FDs, please.'};
  return {F};
};
FD.parseDecomp=function(rel,text){
  const s=String(text==null?'':text).trim();if(!s)return {err:'Enter a decomposition, e.g. AB, BCD.'};
  let parts;
  if(/\(/.test(s)){parts=[];const re=/\(([^)]*)\)/g;let m;while((m=re.exec(s)))parts.push(m[1]);}
  else parts=rel.single?s.split(/[,;\s]+/):s.split(/[;\n]+/);
  parts=parts.map(x=>x.trim()).filter(Boolean);
  if(parts.length<2)return {err:'A decomposition needs at least two relations.'};
  const D=[];for(const p of parts){const r=FD.parseSide(rel,p,p);if(r.err)return r;D.push(r.m);}
  const cov=D.reduce((a,b)=>a|b,0);
  if(cov!==rel.all)return {err:'The relations do not cover every attribute (missing: '+bitsOf(rel.all&~cov).map(i=>rel.names[i]).join(', ')+').',D};
  return {D};
};
FD.closure=function(F,X,withSteps){
  let c=X;const steps=[];let ch=true;
  while(ch){ch=false;for(let i=0;i<F.length;i++){const f=F[i];if((f.L&~c)===0&&(f.R&~c)!==0){const add=f.R&~c;if(withSteps)steps.push({i,L:f.L,R:f.R,add,before:c,after:c|add});c|=add;ch=true;}}}
  return withSteps?{c,steps}:c;
};
/* Candidate keys: Lucchesi–Osborn (1978). Output-polynomial; every key found exactly once. */
FD.keys=function(n,F){
  const all=(1<<n)-1,cl=X=>FD.closure(F,X);
  const minimize=S=>{for(let a=0;a<n;a++){const b=1<<a;if((S&b)&&cl(S&~b)===all)S&=~b;}return S;};
  const keys=[minimize(all)];
  for(let i=0;i<keys.length;i++){const K=keys[i];for(const f of F){const S=f.L|(K&~f.R);if(!keys.some(k=>(k&~S)===0))keys.push(minimize(S));}}
  return keys.sort(cmpMask);
};
FD.keysBrute=function(n,F){
  const all=(1<<n)-1,ks=[];const ms=[];for(let m=0;m<=all;m++)ms.push(m);ms.sort(cmpMask);
  for(const m of ms){if(ks.some(k=>(k&~m)===0))continue;if(FD.closure(F,m)===all)ks.push(m);}
  return ks.sort(cmpMask);
};
FD.countSuperkeys=function(n,keys){let c=0;const all=(1<<n)-1;for(let m=0;m<=all;m++)if(keys.some(k=>(k&~m)===0))c++;return c;};
FD.classify=function(n,F){
  let lhs=0,rhs=0;for(const f of F){lhs|=f.L;rhs|=f.R&~f.L;}
  const all=(1<<n)-1,core=all&~rhs,rhsOnly=rhs&~lhs;return {core,rhsOnly,both:all&~core&~rhsOnly};
};
FD.split=function(F){const G=[];F.forEach((f,src)=>{for(const i of bitsOf(f.R&~f.L)){const b=1<<i;if(!G.some(g=>g.L===f.L&&g.R===b))G.push({L:f.L,R:b,src});}});return G;};
FD.minimalCover=function(F){
  const steps=[];
  const triv=[];F.forEach(f=>{if(f.R&f.L)triv.push({L:f.L,R:f.R&f.L});});
  let G=FD.split(F).map(g=>({L:g.L,R:g.R}));
  steps.push({k:'split',G:G.map(g=>({...g})),triv});
  for(const g of G){
    if(pc(g.L)<2)continue;
    for(const i of bitsOf(g.L)){const b=1<<i;if(pc(g.L)<2)break;const L2=g.L&~b;const c=FD.closure(G,L2);
      if(c&g.R){steps.push({k:'ext',L:g.L,R:g.R,b,L2,c});g.L=L2;}
      else steps.push({k:'extno',L:g.L,R:g.R,b,L2,c});}
  }
  const H=[];for(const g of G){if(H.some(h=>h.L===g.L&&h.R===g.R))steps.push({k:'dup',L:g.L,R:g.R});else H.push(g);}G=H;
  for(let i=0;i<G.length;){const g=G[i];const rest=G.filter((_,j)=>j!==i);const c=FD.closure(rest,g.L);
    if(c&g.R){steps.push({k:'red',L:g.L,R:g.R,c});G=rest;}else{steps.push({k:'keep',L:g.L,R:g.R,c});i++;}}
  const canon=[];for(const g of G){const h=canon.find(x=>x.L===g.L);if(h)h.R|=g.R;else canon.push({L:g.L,R:g.R});}
  return {minimal:G,canonical:canon,steps};
};
FD.equivalent=function(F,G){return F.every(f=>(f.R&~FD.closure(G,f.L))===0)&&G.every(g=>(g.R&~FD.closure(F,g.L))===0);};
FD.normalForm=function(n,F,keys){
  const all=(1<<n)-1;keys=keys||FD.keys(n,F);
  const prime=keys.reduce((a,b)=>a|b,0),nonprime=all&~prime;
  const isSuper=X=>FD.closure(F,X)===all;
  const rows=FD.split(F).map(g=>{
    const sup=isSuper(g.L),pr=!!(g.R&prime),sub=keys.some(K=>(g.L&~K)===0&&g.L!==K);
    let v;if(sup)v='ok';else if(pr)v='bcnf';else if(sub)v='partial';else v='transitive';
    return {L:g.L,R:g.R,src:g.src,sup,prime:pr,sub,v};});
  const partial=[];
  for(const K of keys)for(const i of bitsOf(K)){const S0=K&~(1<<i);const got=FD.closure(F,S0)&nonprime&~S0;
    for(const a of bitsOf(got)){let S=S0;for(const x of bitsOf(S)){const T=S&~(1<<x);if(FD.closure(F,T)&(1<<a))S=T;}
      if(!partial.some(p=>p.S===S&&p.a===(1<<a)))partial.push({K,S,a:1<<a});}}
  const v3=rows.some(r=>r.v==='partial'||r.v==='transitive'),vB=rows.some(r=>r.v!=='ok');
  const highest=partial.length?'1NF':v3?'2NF':vB?'3NF':'BCNF';
  return {keys,prime,nonprime,rows,partial,highest};
};
FD.synth3NF=function(n,F,keys){
  keys=keys||FD.keys(n,F);const mc=FD.minimalCover(F),Fc=mc.canonical;
  const list=Fc.map(f=>({S:f.L|f.R,why:'fd',f}));const steps=[];
  if(!list.some(s=>keys.some(K=>(K&~s.S)===0))){list.push({S:keys[0],why:'key'});steps.push({k:'addkey',K:keys[0]});}
  else{const s=list.find(s=>keys.some(K=>(K&~s.S)===0));steps.push({k:'haskey',S:s.S,K:keys.find(K=>(K&~s.S)===0)});}
  const out=[];list.forEach((s,i)=>{const j=list.findIndex((t,j)=>j!==i&&(s.S&~t.S)===0&&(t.S!==s.S||j<i));if(j>=0)steps.push({k:'drop',S:s.S,by:list[j].S});else out.push(s);});
  return {Fc,schemas:out,steps};
};
FD.bcnf=function(n,F){
  const all=(1<<n)-1;let work=[all];const done=[],steps=[];const cache=new Map();
  const cl=X=>{let v=cache.get(X);if(v===undefined){v=FD.closure(F,X);cache.set(X,v);}return v;};
  let guard=0;
  while(work.length&&guard++<200){
    const Ri=work.shift();let X=null,from=null;
    for(let i=0;i<F.length&&X===null;i++){const f=F[i];if((f.L&~Ri)===0){const C=cl(f.L)&Ri;if(C!==Ri&&(C&~f.L)!==0){X=f.L;from='fd';}}}
    if(X===null&&pc(Ri)>2){const subs=[];for(let s=(Ri-1)&Ri;s>0;s=(s-1)&Ri)subs.push(s);subs.sort(cmpMask);
      for(const s of subs){const C=cl(s)&Ri;if(C!==Ri&&C!==s){X=s;from='derived';break;}}}
    if(X===null){done.push(Ri);steps.push({k:'ok',Ri});continue;}
    const C=cl(X)&Ri,R1=C,R2=Ri&~(C&~X);
    steps.push({k:'split',Ri,X,Y:C&~X,R1,R2,from});
    work.unshift(R2);work.unshift(R1);
  }
  return {schemas:done,steps};
};
FD.chase=function(n,F,D){
  const Fs=FD.split(F);const rows=D.map((m,r)=>Array.from({length:n},(_,j)=>(m>>j)&1?-1:r));
  const snaps=[{rows:rows.map(r=>r.slice()),note:'init'}];
  const win=()=>rows.findIndex(r=>r.every(v=>v===-1));
  let ch=true,guard=0;
  while(ch&&win()<0&&guard++<500){ch=false;
    for(const f of Fs){const col=bitsOf(f.R)[0],Lc=bitsOf(f.L);const groups=new Map();
      rows.forEach((r,i)=>{const k=Lc.map(j=>r[j]).join(',');if(!groups.has(k))groups.set(k,[]);groups.get(k).push(i);});
      for(const g of groups.values()){if(g.length<2)continue;const vals=[...new Set(g.map(i=>rows[i][col]))];if(vals.length<2)continue;
        const to=vals.includes(-1)?-1:Math.min(...vals);const changed=[];
        rows.forEach((r,i)=>{if(vals.includes(r[col])&&r[col]!==to){r[col]=to;changed.push(i);}});
        ch=true;snaps.push({rows:rows.map(r=>r.slice()),f,col,group:g,to,changed});
        if(win()>=0)break;}
      if(win()>=0)break;}}
  const w=win();return {lossless:w>=0,row:w,snaps};
};
FD.preserve=function(F,D){
  const res=F.map(f=>{let Z=f.L;const steps=[];const local=D.findIndex(R=>((f.L|f.R)&~R)===0);let ch=true;
    while(ch&&(f.R&~Z)){ch=false;D.forEach((Ri,i)=>{const t=FD.closure(F,Z&Ri)&Ri;if(t&~Z){steps.push({i,from:Z&Ri,add:t&~Z});Z|=t;ch=true;}});}
    return {L:f.L,R:f.R,Z,ok:(f.R&~Z)===0,local,steps};});
  return {all:res.every(r=>r.ok),res};
};
FD.solve=function(attrText,fdText){
  const rel=FD.parseRel(attrText);if(rel.err)return rel;
  const p=FD.parseFDs(rel,fdText);if(p.err)return p;
  const F=p.F,keys=FD.keys(rel.n,F),nf=FD.normalForm(rel.n,F,keys),mc=FD.minimalCover(F);
  return {rel,F,keys,nf,mc};
};
NETSOLVE.fdtool=FD;

/* ======================================================================
   SERIAL core
   ====================================================================== */
const SE={};
SE.parse=function(text){
  const s=String(text==null?'':text);const ops=[];const re=/\s*([RrWw])\s*(\d+)\s*[\(\[]\s*([A-Za-z_]\w*)\s*[\)\]]|\s*([CcAa])\s*(\d+)\b|\s*([,;]+)|\s*(\S+)/g;let m;
  while((m=re.exec(s))){
    if(m[1])ops.push({t:m[1].toUpperCase(),tx:+m[2],item:m[3]});
    else if(m[4])ops.push({t:m[4].toUpperCase(),tx:+m[5]});
    else if(m[6]){}
    else if(m[7])return {err:`Could not read "${m[7]}". Use R1(A), W2(B), C1 (commit), A1 (abort).`};
  }
  if(!ops.length)return {err:'Enter a schedule, e.g. R1(A) W2(A) R2(B) W1(B) C1 C2.'};
  if(ops.length>60)return {err:'At most 60 operations, please.'};
  const end={};
  for(let i=0;i<ops.length;i++){const o=ops[i];o.i=i;
    if(o.tx<1)return {err:'Transaction numbers start at 1.'};
    if(end[o.tx]!==undefined)return {err:`T${o.tx} has an operation (${SE.name(o)}) after it ${ops[end[o.tx]].t==='C'?'committed':'aborted'}.`};
    if(o.t==='C'||o.t==='A')end[o.tx]=i;}
  const txs=[...new Set(ops.map(o=>o.tx))].sort((a,b)=>a-b);
  if(txs.length>8)return {err:'At most 8 transactions, please.'};
  return {ops,txs};
};
SE.name=o=>o.t==='C'||o.t==='A'?o.t+o.tx:`${o.t}${o.tx}(${o.item})`;
SE.term=function(ops){const t={};ops.forEach(o=>{if(o.t==='C'||o.t==='A')t[o.tx]={t:o.t,i:o.i};});return t;};
SE.conflicts=function(ops,txSet){
  const d=ops.filter(o=>(o.t==='R'||o.t==='W')&&(!txSet||txSet.has(o.tx)));const pairs=[];
  for(let a=0;a<d.length;a++)for(let b=a+1;b<d.length;b++){const x=d[a],y=d[b];if(x.tx!==y.tx&&x.item===y.item&&(x.t==='W'||y.t==='W'))pairs.push([x.i,y.i]);}
  return pairs;
};
SE.graph=function(ops,txs,committedOnly){
  const term=SE.term(ops);const use=committedOnly?txs.filter(t=>term[t]&&term[t].t==='C'):txs.slice();const set=new Set(use);
  const pairs=SE.conflicts(ops,set);const edges=[];
  for(const [a,b] of pairs){const f=ops[a].tx,t=ops[b].tx;let e=edges.find(e=>e.f===f&&e.t===t);if(!e){e={f,t,pairs:[],items:[]};edges.push(e);}e.pairs.push([a,b]);if(!e.items.includes(ops[a].item))e.items.push(ops[a].item);}
  const adj={};use.forEach(t=>adj[t]=[]);edges.forEach(e=>adj[e.f].push(e.t));
  // cycle (DFS)
  let cycle=null;const col={},par={};
  const dfs=u=>{col[u]=1;for(const v of adj[u].slice().sort((a,b)=>a-b)){if(cycle)return;if(col[v]===1){const c=[v];let x=u;while(x!==v){c.push(x);x=par[x];}c.push(v);cycle=c.reverse();return;}if(!col[v]){par[v]=u;dfs(v);}}col[u]=2;};
  for(const t of use){if(!col[t]&&!cycle)dfs(t);}
  // topological orders (all, capped)
  const orders=[];if(!cycle){const indeg={};use.forEach(t=>indeg[t]=0);edges.forEach(e=>indeg[e.t]++);
    const rec=(ord)=>{if(orders.length>=24)return;if(ord.length===use.length){orders.push(ord.slice());return;}
      for(const t of use){if(indeg[t]===0&&!ord.includes(t)){ord.push(t);adj[t].forEach(v=>indeg[v]--);rec(ord);adj[t].forEach(v=>indeg[v]++);ord.pop();}}};
    rec([]);}
  return {txs:use,pairs,edges,cycle,orders,cs:!cycle};
};
SE.readsFromLog=function(seq){ // seq: R/W ops (each with tx,k,item); returns reads-from map and final writers
  const last={},rf={},fw={};
  for(const o of seq){if(o.t==='W')last[o.item]=o.tx;else if(o.t==='R')rf[o.tx+':'+o.k]=last[o.item]||0;}
  for(const it in last)fw[it]=last[it];return {rf,fw};
};
SE.view=function(ops,txs,committedOnly){
  const term=SE.term(ops);const use=committedOnly?txs.filter(t=>term[t]&&term[t].t==='C'):txs.slice();
  const cnt={};const d=[];for(const o of ops){if(o.t!=='R'&&o.t!=='W')continue;if(!use.includes(o.tx))continue;cnt[o.tx]=(cnt[o.tx]||0);d.push({t:o.t,tx:o.tx,item:o.item,k:cnt[o.tx]++,i:o.i});}
  const S=SE.readsFromLog(d);
  const blind=[];const readSoFar={};for(const o of d){if(o.t==='R')readSoFar[o.tx+':'+o.item]=1;else if(!readSoFar[o.tx+':'+o.item])blind.push(o.i);}
  if(use.length>5)return {skipped:true,S,d,blind,use};
  const perms=[];const rec=(a,r)=>{if(!r.length){perms.push(a);return;}r.forEach((x,i)=>rec(a.concat([x]),r.filter((_,j)=>j!==i)));};rec([],use);
  const results=perms.map(p=>{const seq=[];p.forEach(t=>d.filter(o=>o.tx===t).forEach(o=>seq.push(o)));const V=SE.readsFromLog(seq);
    let why=null;for(const o of d){if(o.t!=='R')continue;const key=o.tx+':'+o.k;if(V.rf[key]!==S.rf[key]){why={k:'rf',i:o.i,s:S.rf[key],v:V.rf[key]};break;}}
    if(!why)for(const it in S.fw){if(V.fw[it]!==S.fw[it]){why={k:'fw',item:it,s:S.fw[it],v:V.fw[it]};break;}}
    return {order:p,ok:!why,why};});
  return {skipped:false,S,d,blind,use,results,vs:results.some(r=>r.ok)};
};
SE.recover=function(ops){
  const term=SE.term(ops);const rf=[];
  const abortedBefore=(tx,p)=>term[tx]&&term[tx].t==='A'&&term[tx].i<p;
  ops.forEach((o,p)=>{if(o.t!=='R')return;for(let q=p-1;q>=0;q--){const w=ops[q];if(w.t==='W'&&w.item===o.item&&!abortedBefore(w.tx,p)){if(w.tx!==o.tx)rf.push({r:p,w:q,reader:o.tx,writer:w.tx,item:o.item});break;}}});
  const rec=[],aca=[],strict=[];
  for(const x of rf){const tr=term[x.reader],tw=term[x.writer];
    let recOk=true,recWhy;
    if(tr&&tr.t==='C'){if(!tw||tw.t!=='C'||tw.i>tr.i){recOk=false;recWhy=!tw?`T${x.writer} has not committed when T${x.reader} commits`:tw.t==='A'?`T${x.writer} aborts but T${x.reader} has committed`:`C${x.reader} comes before C${x.writer}`;}
      else recWhy=`C${x.writer} comes before C${x.reader}`;}
    else recWhy=`T${x.reader} does not commit in this schedule`;
    const acaOk=!!(tw&&tw.t==='C'&&tw.i<x.r);
    rec.push({...x,ok:recOk,why:recWhy});aca.push({...x,ok:acaOk});}
  ops.forEach((o,p)=>{if(o.t!=='R'&&o.t!=='W')return;for(let q=0;q<p;q++){const w=ops[q];if(w.t==='W'&&w.item===o.item&&w.tx!==o.tx){const tw=term[w.tx];if(!tw||tw.i>p){strict.push({op:p,w:q});break;}}}});
  return {rf,rec,aca,strict,recoverable:rec.every(r=>r.ok),cascadeless:aca.every(r=>r.ok),strictOk:strict.length===0,
    incomplete:[...new Set(ops.map(o=>o.tx))].filter(t=>!term[t])};
};
SE.solve=function(text,committedOnly){
  const p=SE.parse(text);if(p.err)return p;
  return {ops:p.ops,txs:p.txs,g:SE.graph(p.ops,p.txs,committedOnly),v:SE.view(p.ops,p.txs,committedOnly),r:SE.recover(p.ops)};
};
NETSOLVE.serial=SE;

/* ======================================================================
   BPTREE core
   ====================================================================== */
const BT={};
BT.limits=function(o){
  if(o.def==='mindeg'){const t=o.order;return {maxK:2*t-1,minK:t-1,maxC:2*t,minC:t};}
  const m=o.order;return {maxK:m-1,minK:Math.ceil(m/2)-1,maxC:m,minC:Math.ceil(m/2)};
};
BT.parseKeys=function(text){
  const toks=String(text==null?'':text).split(/[\s,;]+/).filter(Boolean);if(!toks.length)return {err:'Enter some keys, e.g. 10 20 5 6 12.'};
  const ks=[];for(const t of toks){if(!/^-?\d+$/.test(t))return {err:`"${t}" is not a whole number.`};ks.push(+t);}
  if(ks.length>40)return {err:'At most 40 keys, please.'};return {keys:ks};
};
BT.build=function(keys,o){
  const kind=o.kind||'B',def=o.def||'knuth',order=+o.order,bias=o.bias||'left';
  if(!Number.isInteger(order))return {err:'The order must be a whole number.'};
  if(def==='knuth'&&(order<3||order>12))return {err:'Order m (max children) must be between 3 and 12.'};
  if(def==='mindeg'&&(order<2||order>6))return {err:'Minimum degree t must be between 2 and 6.'};
  const L=BT.limits({def,order});const maxK=L.maxK;
  const topdown=o.split==='topdown'&&kind==='B'&&maxK%2===1;
  let uid=0;const mk=leaf=>({id:++uid,keys:[],kids:[],leaf});let root=mk(true);
  const frames=[];const seen=new Set();
  const clone=n=>({id:n.id,keys:n.keys.slice(),leaf:n.leaf,kids:n.kids.map(clone)});
  const snap=(cap,hl,key,kind2,lab)=>frames.push({tree:clone(root),cap,hl:hl||{},key,kind:kind2||'step',lab});
  const ks=a=>'['+a.join(', ')+']';
  const cidx=(n,k)=>kind==='B+'?n.keys.filter(x=>x<=k).length:n.keys.filter(x=>x<k).length;
  const midOf=cnt=>cnt%2?(cnt-1)/2:(bias==='left'?cnt/2:cnt/2-1);
  function splitNode(n){ // returns {left,right,up,copy}
    const right=mk(n.leaf);const cnt=n.keys.length;let up,copy=false;
    if(n.leaf&&kind==='B+'){const lc=cnt%2?(bias==='left'?(cnt+1)/2:(cnt-1)/2):cnt/2;right.keys=n.keys.slice(lc);n.keys=n.keys.slice(0,lc);up=right.keys[0];copy=true;}
    else{const mid=midOf(cnt);up=n.keys[mid];right.keys=n.keys.slice(mid+1);if(!n.leaf)right.kids=n.kids.slice(mid+1);n.keys=n.keys.slice(0,mid);if(!n.leaf)n.kids=n.kids.slice(0,mid+1);}
    return {left:n,right,up,copy};
  }
  const desc=(s,parentIsNew)=>`${s.copy?'copy':'move'} <b>${s.up}</b> up`;
  snap('Start with an empty tree (one empty leaf).',{},null,'start');
  for(const k of keys){
    if(seen.has(k)){snap(`Key <b>${k}</b> is already in the tree, so it is skipped (keys are distinct).`,{},k,'dup');continue;}
    seen.add(k);
    if(!topdown){
      const path=[];let n=root;while(!n.leaf){const i=cidx(n,k);path.push([n,i]);n=n.kids[i];}
      const pos=n.keys.filter(x=>x<k).length;n.keys.splice(pos,0,k);
      if(n.keys.length<=maxK){snap(`Insert <b>${k}</b>: ${path.length?'follow the pointers down to the leaf':'the root is a leaf'}; it now holds ${ks(n.keys)} (${n.keys.length} ≤ ${maxK} keys), so no split.`,{[n.id]:'new'},k,'ins');continue;}
      snap(`Insert <b>${k}</b> into ${path.length?'its leaf':'the root leaf'}: ${ks(n.keys)} has ${n.keys.length} keys, more than the maximum ${maxK}, so the node <b>overflows</b>.`,{[n.id]:'over'},k,'over');
      while(n.keys.length>maxK){
        const before=n.keys.slice();const pe=path.pop();const s=splitNode(n);
        const how=s.copy?`split the leaf ${ks(before)} into ${ks(s.left.keys)} and ${ks(s.right.keys)} and <b>copy</b> <b>${s.up}</b> (first key of the right leaf) up`:`split ${ks(before)} at the median <b>${s.up}</b>: ${ks(s.left.keys)} | <b>${s.up}</b> | ${ks(s.right.keys)}; <b>${s.up}</b> moves up`;
        if(!pe){const r=mk(false);r.keys=[s.up];r.kids=[s.left,s.right];root=r;
          snap(`${how[0].toUpperCase()+how.slice(1)}. There is no parent, so a <b>new root</b> [${s.up}] is created and the height grows by one.`,{[s.left.id]:'hi',[s.right.id]:'new',[r.id]:'new'},k,'split',`${k}: split ${ks(before)}, new root`);break;}
        const [p,i]=pe;p.keys.splice(i,0,s.up);p.kids.splice(i+1,0,s.right);
        const over=p.keys.length>maxK;
        snap(`${how[0].toUpperCase()+how.slice(1)} into the parent, which becomes ${ks(p.keys)}${over?` (${p.keys.length} > ${maxK}: the parent overflows too)`:''}.`,{[s.left.id]:'hi',[s.right.id]:'new',[p.id]:over?'over':'hi'},k,'split',`${k}: split ${ks(before)}`);
        n=p;
      }
    }else{
      if(root.keys.length===maxK){const s=mk(false);s.kids=[root];const old=root.keys.slice();const sp=splitNode(root);s.keys=[sp.up];s.kids=[sp.left,sp.right];root=s;
        snap(`Insert <b>${k}</b>: the root ${ks(old)} is full (${maxK} keys), so it is split <b>before</b> descending: median <b>${sp.up}</b> becomes a new root.`,{[sp.left.id]:'hi',[sp.right.id]:'new',[s.id]:'new'},k,'split',`${k}: split root ${ks(old)}`);}
      let n=root;
      while(!n.leaf){let i=cidx(n,k);const c=n.kids[i];
        if(c.keys.length===maxK){const old=c.keys.slice();const sp=splitNode(c);n.keys.splice(i,0,sp.up);n.kids.splice(i+1,0,sp.right);
          snap(`On the way down to insert <b>${k}</b>, child ${ks(old)} is full, so it is split first: median <b>${sp.up}</b> moves up into ${ks(n.keys)}.`,{[sp.left.id]:'hi',[sp.right.id]:'new',[n.id]:'hi'},k,'split',`${k}: split ${ks(old)}`);
          if(k>sp.up)i++;}
        n=n.kids[i];}
      const pos=n.keys.filter(x=>x<k).length;n.keys.splice(pos,0,k);
      snap(`Insert <b>${k}</b> into the leaf, which becomes ${ks(n.keys)}. (Pre-emptive splitting guarantees the leaf had room.)`,{[n.id]:'new'},k,'ins');
    }
  }
  return {frames,limits:L,topdown,kind,def,order,bias};
};
BT.stats=function(t){
  let nodes=0,leaves=0,keys=0,h=0;const leafKeys=[];
  const walk=(n,d)=>{nodes++;h=Math.max(h,d);if(n.leaf){leaves++;keys+=n.keys.length;leafKeys.push(...n.keys);}else keys+=n.keys.length;n.kids.forEach(c=>walk(c,d+1));};
  walk(t,1);if(t.leaf&&!t.keys.length)return {nodes:0,leaves:0,internal:0,keys:0,levels:0,leafKeys:[]};
  return {nodes,leaves,internal:nodes-leaves,keys,levels:h,leafKeys};
};
BT.check=function(t,o,L,kind){ // invariant check used by tests
  const errs=[];let leafDepth=-1;
  const walk=(n,d,lo,hi,isRoot)=>{
    for(let i=1;i<n.keys.length;i++)if(n.keys[i]<=n.keys[i-1])errs.push('unsorted');
    if(n.keys.length>L.maxK)errs.push('overfull '+n.id);
    if(!isRoot&&n.keys.length<L.minK)errs.push('underfull '+n.id);
    for(const k of n.keys){if(lo!==null&&(kind==='B+'?k<lo:k<=lo))errs.push('range');if(hi!==null&&(kind==='B+'&&!n.leaf?k>=hi:k>=hi))errs.push('range');}
    if(n.leaf){if(leafDepth<0)leafDepth=d;else if(leafDepth!==d)errs.push('depth');if(n.kids.length)errs.push('leafkids');return;}
    if(n.kids.length!==n.keys.length+1)errs.push('kids');
    n.kids.forEach((c,i)=>walk(c,d+1,i?n.keys[i-1]:lo,i<n.keys.length?n.keys[i]:hi,false));};
  walk(t,0,null,null,true);return errs;
};
/* height bounds for a B-tree holding n keys (levels counted from 1) */
BT.bounds=function(n,L){
  if(n<1)return null;let minLv=1;while(Math.pow(L.maxC,minLv)-1<n)minLv++;
  let hE=0;while(2*Math.pow(L.minC,hE+1)-1<=n)hE++;return {minLevels:minLv,maxLevels:hE+1};
};
NETSOLVE.bptree=BT;

/* ======================================================================
   UI (browser only)
   ====================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let UID=0;
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=a=>a[Math.floor(Math.random()*a.length)];
const shuffle=a=>{a=a.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
function debounce(fn,ms){let t;return (...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
/* generic step-through control: frames 0..n-1, render(i) sets the whole state for step i */
function stepper(host,p,n,render,start){
  let i=0,timer=null;
  host.innerHTML=`<div class="${p}-stp"><button type="button" class="btn sm" data-a="rs" aria-label="Back to the first step">↺</button><button type="button" class="btn sm" data-a="pv">◀ Prev</button><button type="button" class="btn sm primary" data-a="pl">▶ Play</button><button type="button" class="btn sm" data-a="nx">Next ▶</button><input type="range" min="0" max="${Math.max(0,n-1)}" value="0" aria-label="Jump to step"><span class="${p}-stpc" aria-live="polite"></span></div>`;
  const pl=host.querySelector('[data-a=pl]'),rg=host.querySelector('input'),ct=host.querySelector(`.${p}-stpc`);
  const stop=()=>{clearTimeout(timer);timer=null;pl.textContent='▶ Play';};
  const go=k=>{i=Math.max(0,Math.min(n-1,k));rg.value=i;ct.textContent=`Step ${i+1} of ${n}`;render(i);};
  const tick=()=>{if(!document.body.contains(host)){stop();return;}if(i>=n-1){stop();return;}go(i+1);timer=setTimeout(tick,1500);};
  host.querySelector('[data-a=rs]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-a=pv]').onclick=()=>{stop();go(i-1);};
  host.querySelector('[data-a=nx]').onclick=()=>{stop();go(i+1);};
  pl.onclick=()=>{if(timer){stop();return;}if(i>=n-1)go(0);pl.textContent='❚❚ Pause';timer=setTimeout(tick,900);};
  rg.oninput=()=>{stop();go(+rg.value);};
  go(start==null?0:start);return {go,stop,get i(){return i;}};
}
function tabs(host,p,names,cur,onPick){
  host.innerHTML=names.map((nm,k)=>`<button type="button" aria-pressed="${k===cur}" data-k="${k}">${nm}</button>`).join('');
  host.querySelectorAll('button').forEach(b=>b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(+b.dataset.k);});
}
const Y=P=>(ok,t,f)=>`<span class="${P}-${ok?'ok':'bad'}">${ok?'✓ '+(t||'Yes'):'✗ '+(f||'No')}</span>`;

/* ---------------------------------------------------------------- fdtool UI */
ANIM.register('fdtool',{title:'Functional dependency solver',steps:false,
 caption:'Type a relation and its FDs. The solver finds closures, all candidate keys, a minimal cover and the highest normal form, decomposes to 3NF and BCNF, and tests any decomposition, showing every step.',
 build(stage){
  const P='fdtool',yes=Y(P);
  const EX=[
    {nm:'Keys ACD, BCD, CDE (3NF)',a:'ABCDE',f:'A->B, BC->E, ED->A',x:'AC',d:'ABE, CDE'},
    {nm:'Korth: R(A,B,C,G,H,I)',a:'ABCGHI',f:'A->B, A->C, CG->H, CG->I, B->H',x:'AG',d:'ABC, CGHI, AG'},
    {nm:'Transitive chain (2NF)',a:'ABCDE',f:'AB->C, C->D, D->E',x:'C',d:'ABC, CD, DE'},
    {nm:'Minimal-cover drill',a:'ABC',f:'A->BC, B->C, A->B, AB->C',x:'A',d:'AB, BC'},
    {nm:'Cyclic keys (BCNF)',a:'ABCD',f:'A->B, B->C, C->D, D->A',x:'B',d:'AB, BC, CD'},
    {nm:'Chase: lossless 5-way',a:'ABCDE',f:'A->C, B->C, C->D, DE->C, CE->A',x:'BE',d:'AD, AB, BE, CDE, AE'},
    {nm:'Named attributes',a:'student, course, teacher',f:'student, course -> teacher; teacher -> course',x:'teacher',d:'student, teacher; teacher, course'}];
  const st={a:EX[0].a,f:EX[0].f,x:EX[0].x,d:EX[0].d,tab:0};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${P}">
   <div class="${P}-in">
     <label class="${P}-lab">Relation attributes<input type="text" id="${P}A" spellcheck="false" autocomplete="off"></label>
     <label class="${P}-lab ${P}-wide">Functional dependencies<textarea id="${P}F" rows="2" spellcheck="false"></textarea></label>
     <div class="${P}-btns"><label class="${P}-lab">Example<select id="${P}Ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" id="${P}Rnd">🎲 Random example</button></div>
     <p class="${P}-hint">Single-letter attributes: type <code>ABCDE</code> and FDs like <code>AB->C, C->D</code>. Longer names: separate names with commas or spaces and FDs with <code>;</code> or new lines (<code>emp, dept -> mgr; mgr -> dept</code>).</p>
     <div class="${P}-err" role="alert" hidden></div>
   </div>
   <div class="${P}-ans"></div>
   <div class="${P}-tabs" role="group" aria-label="Working"></div>
   <div class="${P}-pane"></div>
  </div>`;
  const $=s=>stage.querySelector(s);
  const inA=$(`#${P}A`),inF=$(`#${P}F`),err=$(`.${P}-err`),ans=$(`.${P}-ans`),pane=$(`.${P}-pane`),tabHost=$(`.${P}-tabs`);
  inA.value=st.a;inF.value=st.f;
  let S=null;
  const TABS=['Closure','Candidate keys','Minimal cover','Normal form','3NF & BCNF','Test a decomposition'];
  tabs(tabHost,P,TABS,st.tab,k=>{st.tab=k;renderPane();});
  const fs=m=>{if(!S)return '';const r=S.rel;if(!m)return '∅';const b=bitsOf(m).map(i=>r.names[i]);return r.single?b.join(''):b.join(', ');};
  const fset=m=>{const s=fs(m);return S.rel.single||!m?s:'{'+s+'}';};
  const ffd=(L,R)=>`${fs(L)} → ${fs(R)}`;
  const mono=s=>`<span class="${P}-m">${E(s)}</span>`;
  function compute(){
    const r=FD.solve(st.a,st.f);
    if(r.err){err.hidden=false;err.textContent=r.err;stage.querySelector(`.${P}`).classList.add(`${P}-stale`);return;}
    err.hidden=true;stage.querySelector(`.${P}`).classList.remove(`${P}-stale`);S=r;
    S.syn=FD.synth3NF(r.rel.n,r.F,r.keys);S.bc=FD.bcnf(r.rel.n,r.F);S.bcp=FD.preserve(r.F,S.bc.schemas);
    S.sk=FD.countSuperkeys(r.rel.n,r.keys);
    renderAns();renderPane();
  }
  function renderAns(){
    const {rel,keys,nf,mc}=S;
    ans.innerHTML=`<div class="${P}-card"><span class="${P}-k">Candidate key${keys.length>1?'s':''} (${keys.length})</span><b class="${P}-big">${keys.map(k=>E(fset(k))).join(', ')}</b></div>
     <div class="${P}-card"><span class="${P}-k">Prime attributes</span><b>${E(fs(nf.prime))}</b><span>non-prime: <b>${nf.nonprime?E(fs(nf.nonprime)):'none'}</b></span></div>
     <div class="${P}-card"><span class="${P}-k">Highest normal form</span><b class="${P}-big">${nf.highest}</b></div>
     <div class="${P}-card"><span class="${P}-k">Canonical cover</span><b>${mc.canonical.length?mc.canonical.map(f=>E(ffd(f.L,f.R))).join(', '):'none (no non-trivial FDs)'}</b></div>
     <div class="${P}-card"><span class="${P}-k">Super keys</span><b>${S.sk}</b> <span class="${P}-mut">of 2<sup>${rel.n}</sup> = ${1<<rel.n} subsets</span></div>`;
  }
  function renderPane(){
    if(!S){pane.innerHTML='';return;}
    [paneClosure,paneKeys,paneCover,paneNF,paneDecomp,paneTest][st.tab]();
  }
  function paneClosure(){
    pane.innerHTML=`<div class="${P}-row"><label class="${P}-lab">Find the closure of<input type="text" id="${P}X" spellcheck="false" autocomplete="off" value="${E(st.x)}"></label></div><div id="${P}XO"></div>`;
    const inX=pane.querySelector(`#${P}X`),out=pane.querySelector(`#${P}XO`);
    const run=()=>{st.x=inX.value;const p=FD.parseSide(S.rel,st.x,st.x);
      if(p.err){out.innerHTML=`<p class="${P}-err">${E(st.x.trim()?p.err:'Enter a set of attributes, e.g. '+(S.rel.single?'AB':'a, b')+'.')}</p>`;return;}
      const {c,steps}=FD.closure(S.F,p.m,true);const all=S.rel.all;const sup=c===all;const key=sup&&S.keys.includes(p.m);
      out.innerHTML=`<p class="${P}-res">${mono(fset(p.m))}<sup>+</sup> = <b>${mono(fset(c))}</b> &nbsp; ${sup?(key?yes(true,'a candidate key'):yes(true,'a superkey (not minimal)')):yes(false,'','not a superkey (misses '+E(fs(all&~c))+')')}</p>
       <p class="${P}-conv"><b>Method.</b> Start with X⁺ = X. Scan the FDs; whenever an FD's left side is inside X⁺, add its right side. Repeat full passes until a pass adds nothing.</p>
       <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>#</th><th>FD applied</th><th>LHS ⊆ X⁺?</th><th>Adds</th><th>X⁺ so far</th></tr></thead><tbody>
       <tr><td>0</td><td>start</td><td></td><td></td><td>${mono(fs(p.m))}</td></tr>
       ${steps.map((s,k)=>`<tr><td>${k+1}</td><td>${mono(ffd(s.L,s.R))}</td><td>${E(fs(s.L))} ⊆ ${E(fs(s.before))}</td><td class="${P}-add">${E(fs(s.add))}</td><td>${mono(fs(s.after))}</td></tr>`).join('')}
       </tbody></table></div>${steps.length?'':`<p class="${P}-mut">No FD has its left side inside ${E(fset(p.m))}, so the closure is the set itself.</p>`}`;};
    inX.oninput=run;run();
  }
  function paneKeys(){
    const {rel,F,keys}=S;const c=FD.classify(rel.n,F);const coreCl=FD.closure(F,c.core);
    const verify=keys.map(K=>{const drops=bitsOf(K).map(i=>{const T=K&~(1<<i);return `${E(fset(T))}⁺ = ${E(fset(FD.closure(F,T)))}`;});return `<tr><td><b>${mono(fset(K))}</b></td><td>${mono(fset(FD.closure(F,K)))} = R ✓</td><td>${drops.join('<br>')||'—'}</td></tr>`;}).join('');
    pane.innerHTML=`<ol class="${P}-steps">
      <li><b>Never on a right side</b> (must be in every key): ${mono(fs(c.core)||'none')}.</li>
      <li><b>Only on right sides</b> (never in any key): ${mono(fs(c.rhsOnly)||'none')}.</li>
      <li>Closure of the must-have part: ${mono(fset(c.core))}<sup>+</sup> = ${mono(fset(coreCl))}. ${coreCl===rel.all?`It is all of R, so <b>${E(fset(c.core))} is the only candidate key</b>.`:'It is not all of R, so the remaining attributes must be added in every minimal way.'}</li>
      <li>All keys are found with the <b>Lucchesi–Osborn</b> algorithm: shrink R to one minimal key; then for each key K and FD X→Y, the set X ∪ (K − Y) is also a superkey. If it contains no known key, shrink it to a new key. Repeat until nothing new appears. This finds every key without trying all 2<sup>n</sup> subsets.</li></ol>
      <p class="${P}-res">Candidate keys: <b>${keys.map(k=>E(fset(k))).join(', ')}</b>. Prime attributes (in some key): <b>${E(fs(S.nf.prime))}</b>. Non-prime: <b>${E(fs(S.nf.nonprime)||'none')}</b>.</p>
      <p class="${P}-mut">Check each key: its closure is R (superkey), and dropping any one attribute breaks that (minimal).</p>
      <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Key K</th><th>K⁺</th><th>Drop one attribute</th></tr></thead><tbody>${verify}</tbody></table></div>
      <p class="${P}-conv"><b>Super keys:</b> every superset of some candidate key; here ${S.sk} of the ${1<<rel.n} attribute subsets.</p>`;
  }
  function paneCover(){
    const mc=S.mc;const s1=mc.steps[0];const ext=[],red=[];
    for(const s of mc.steps){
      if(s.k==='ext')ext.push(`<li>${mono(ffd(s.L,s.R))}: ${mono(fset(s.L2))}⁺ = ${mono(fset(s.c))} contains ${E(fs(s.R))}, so <b>${E(fs(s.b))} is extraneous</b> → ${mono(ffd(s.L2,s.R))}.</li>`);
      else if(s.k==='extno')ext.push(`<li>${mono(ffd(s.L,s.R))}: ${mono(fset(s.L2))}⁺ = ${mono(fset(s.c))} lacks ${E(fs(s.R))}, so ${E(fs(s.b))} stays.</li>`);
      else if(s.k==='dup')ext.push(`<li>Duplicate ${mono(ffd(s.L,s.R))} removed.</li>`);
      else if(s.k==='red')red.push(`<li>${mono(ffd(s.L,s.R))}: without it ${mono(fset(s.L))}⁺ = ${mono(fset(s.c))} ∋ ${E(fs(s.R))}, so it is <b>redundant</b> (removed).</li>`);
      else if(s.k==='keep')red.push(`<li>${mono(ffd(s.L,s.R))}: without it ${mono(fset(s.L))}⁺ = ${mono(fset(s.c))}, which lacks ${E(fs(s.R))}, so it is <b>kept</b>.</li>`);
    }
    const li=[`<li><b>Singleton right sides.</b> ${s1.G.map(g=>mono(ffd(g.L,g.R))).join(', ')||'none'}${s1.triv.length?`. Trivial parts dropped: ${s1.triv.map(t=>mono(ffd(t.L,t.R))).join(', ')}`:''}.</li>`,
      `<li><b>Extraneous left-side attributes.</b> For each FD with 2+ attributes on the left, drop one attribute if (LHS minus it)⁺ still contains the right side.${ext.length?`<ul class="${P}-sub">${ext.join('')}</ul>`:' No FD has 2+ attributes on the left.'}</li>`,
      `<li><b>Redundant FDs.</b> Drop X→A if X⁺, computed from the other FDs, still contains A.${red.length?`<ul class="${P}-sub">${red.join('')}</ul>`:''}</li>`];
    pane.innerHTML=`<ol class="${P}-steps">${li.join('')}</ol>
     <p class="${P}-res">Minimal cover: <b>${mc.minimal.map(f=>E(ffd(f.L,f.R))).join(', ')||'∅'}</b></p>
     <p class="${P}-res">Canonical cover (same left sides merged): <b>${mc.canonical.map(f=>E(ffd(f.L,f.R))).join(', ')||'∅'}</b></p>
     <p class="${P}-conv"><b>Convention.</b> Extraneous attributes are removed before redundant FDs (that order is required), scanning FDs and attributes in the order typed. A different scan order can give a different, equally valid minimal cover, so check exam options for equivalence, not for identical text.</p>`;
  }
  function paneNF(){
    const nf=S.nf;const V={ok:[yes(true,'BCNF'),'LHS is a superkey'],bcnf:[`<span class="${P}-warn">violates BCNF</span>`,'LHS is not a superkey, but the RHS is prime (allowed in 3NF)'],partial:[`<span class="${P}-bad">violates 2NF</span>`,'partial dependency: LHS is a proper subset of a candidate key and the RHS is non-prime'],transitive:[`<span class="${P}-bad">violates 3NF</span>`,'transitive dependency: LHS is not a superkey (nor part of a key) and the RHS is non-prime']};
    const lad=['1NF','2NF','3NF','BCNF'],hi=lad.indexOf(nf.highest);
    pane.innerHTML=`<div class="${P}-ladder">${lad.map((l,k)=>`<span class="${k<=hi?'on':'off'}">${k<=hi?'✓':'✗'} ${l}</span>`).join('')}</div>
     <p class="${P}-res">Highest normal form: <b>${nf.highest}</b>. Candidate keys: ${S.keys.map(k=>E(fset(k))).join(', ')}; prime: ${E(fs(nf.prime))}.</p>
     <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>FD (split)</th><th>LHS superkey?</th><th>RHS prime?</th><th>LHS ⊂ a key?</th><th>Verdict and reason</th></tr></thead><tbody>
     ${nf.rows.map(r=>`<tr><td>${mono(ffd(r.L,r.R))}</td><td>${r.sup?'yes':'no'}</td><td>${r.prime?'yes':'no'}</td><td>${r.sub?'yes':'no'}</td><td>${V[r.v][0]} <span class="${P}-mut">${V[r.v][1]}</span></td></tr>`).join('')||`<tr><td colspan="5">No non-trivial FDs, so R is in BCNF.</td></tr>`}
     </tbody></table></div>
     ${nf.partial.length?`<p><b>Partial dependencies</b> (non-prime attribute determined by part of a key, checked on F⁺): ${nf.partial.map(p=>`${mono(ffd(p.S,p.a))} with ${mono(fs(p.S))} ⊂ key ${mono(fset(p.K))}`).join('; ')}. So R is <b>not in 2NF</b>.</p>`:`<p>No non-prime attribute depends on a proper part of any key (checked on F⁺), so R is in 2NF.</p>`}
     <p class="${P}-conv"><b>Conventions.</b> 1NF is assumed (atomic values). 2NF: no non-prime attribute is partially dependent on a candidate key. 3NF: for every non-trivial X→A, X is a superkey <i>or</i> A is prime. BCNF: for every non-trivial X→A, X is a superkey. Checking the given FDs (split) is enough for 3NF and BCNF; 2NF is checked on F⁺ by testing each key minus one attribute.</p>`;
  }
  function paneDecomp(){
    const {syn,bc,bcp}=S;
    const synSteps=syn.steps.map(s=>s.k==='addkey'?`<li>No relation contains a candidate key, so add R(${E(fs(s.K))}) for key ${E(fset(s.K))}.</li>`:s.k==='haskey'?`<li>R(${E(fs(s.S))}) already contains key ${E(fset(s.K))}, so no key relation is needed.</li>`:`<li>R(${E(fs(s.S))}) is contained in R(${E(fs(s.by))}), so it is dropped.</li>`).join('');
    const proj=m=>FD.split(S.F).filter(f=>((f.L|f.R)&~m)===0).map(f=>ffd(f.L,f.R));
    const bSteps=bc.steps.map(s=>s.k==='ok'?`<li>R(${E(fs(s.Ri))}) is in BCNF: no subset X of it has X⁺ ∩ R<sub>i</sub> strictly between X and R<sub>i</sub>.</li>`:`<li>In R(${E(fs(s.Ri))}), ${mono(ffd(s.X,s.Y))} ${s.from==='fd'?'(from F)':'(derived, in F⁺)'} violates BCNF because ${E(fset(s.X))} is not a key of it. Split into R1 = X⁺ ∩ R<sub>i</sub> = <b>(${E(fs(s.R1))})</b> and R2 = R<sub>i</sub> − (X⁺ − X) = <b>(${E(fs(s.R2))})</b>.</li>`).join('');
    pane.innerHTML=`<h4 class="${P}-h">3NF synthesis (from the canonical cover)</h4>
     <ol class="${P}-steps"><li>One relation per canonical FD X→Y, holding XY: ${syn.Fc.map(f=>`R(${E(fs(f.L|f.R))})`).join(', ')||'none'}.</li>${synSteps}</ol>
     <p class="${P}-res">3NF: <b>${syn.schemas.map(s=>'R('+E(fs(s.S))+')').join(', ')}</b></p>
     <p class="${P}-mut">Always lossless and dependency preserving.</p>
     <h4 class="${P}-h">BCNF decomposition (repeated splitting)</h4>
     <ol class="${P}-steps">${bSteps}</ol>
     <p class="${P}-res">BCNF: <b>${bc.schemas.map(s=>'R('+E(fs(s))+')').join(', ')}</b></p>
     <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Relation</th><th>Given FDs inside it</th></tr></thead><tbody>${bc.schemas.map(s=>`<tr><td>${mono('R('+fs(s)+')')}</td><td>${proj(s).map(E).join(', ')||'—'}</td></tr>`).join('')}</tbody></table></div>
     <p>Lossless: ${yes(true,'always (each split is on X→Y with X⁺)')}. Dependency preserving: ${bcp.all?yes(true):yes(false,'','no, lost: '+bcp.res.filter(r=>!r.ok).map(r=>E(ffd(r.L,r.R))).join(', '))}.</p>
     <p class="${P}-conv"><b>Convention.</b> The BCNF split uses the first violating FD in the order typed (then derived FDs, smallest left side first). Another choice of violating FD can give a different, equally correct BCNF decomposition.</p>
     <p><button type="button" class="btn sm" id="${P}UseB">Test this BCNF result in "Test a decomposition" →</button></p>`;
    pane.querySelector(`#${P}UseB`).onclick=()=>{st.d=bc.schemas.map(s=>fs(s)).join(S.rel.single?', ':'; ');st.tab=5;tabs(tabHost,P,TABS,5,k=>{st.tab=k;renderPane();});renderPane();};
  }
  function paneTest(){
    pane.innerHTML=`<div class="${P}-row"><label class="${P}-lab ${P}-wide">Decomposition<input type="text" id="${P}D" spellcheck="false" autocomplete="off" value="${E(st.d)}"></label></div>
     <p class="${P}-hint">${S.rel.single?'Relations separated by commas, e.g. <code>AB, BCD</code> or <code>R1(A,B), R2(B,C,D)</code>.':'Relations separated by <code>;</code>, e.g. <code>student, teacher; teacher, course</code>.'}</p><div id="${P}DO"></div>`;
    const inD=pane.querySelector(`#${P}D`),out=pane.querySelector(`#${P}DO`);
    const run=()=>{st.d=inD.value;const p=FD.parseDecomp(S.rel,st.d);if(p.err){out.innerHTML=`<p class="${P}-err">${E(p.err)}</p>`;return;}
      const D=p.D,n=S.rel.n,ch=FD.chase(n,S.F,D),pr=FD.preserve(S.F,D);
      let bin='';if(D.length===2){const I=D[0]&D[1],c=FD.closure(S.F,I);const ok=(D[0]&~c)===0||(D[1]&~c)===0;
        bin=`<p><b>Two-relation shortcut:</b> R1 ∩ R2 = ${mono(fset(I))}, and (R1 ∩ R2)⁺ = ${mono(fset(c))}. ${ok?`It contains ${(D[0]&~c)===0?'R1':'R2'}, so the common attributes are a key of one side: <b>lossless</b>.`:'It contains neither R1 nor R2: <b>lossy</b>.'}</p>`;}
      out.innerHTML=`<p class="${P}-res">Lossless join: ${yes(ch.lossless,'lossless','lossy')} &nbsp; Dependency preserving: ${yes(pr.all)}</p>${bin}
       <h4 class="${P}-h">Chase (tableau) test</h4>
       <p class="${P}-conv">One row per relation R<sub>i</sub>: <b>a</b><sub>j</sub> where R<sub>i</sub> has attribute j, else <b>b</b><sub>ij</sub>. For each FD X→A (split), rows that agree on X are made equal on A: to <b>a</b> if any row has <b>a</b>, else to the smallest-numbered <b>b</b>. Stop when some row is all <b>a</b> (lossless) or nothing changes (lossy).</p>
       <div id="${P}CS"></div><div id="${P}CT"></div>
       <h4 class="${P}-h">Dependency preservation</h4>
       <p class="${P}-conv">For each FD X→Y: start Z = X; repeatedly, for each R<sub>i</sub>, add (Z ∩ R<sub>i</sub>)⁺ ∩ R<sub>i</sub>. The FD is preserved if Y ends up in Z. No F⁺ needed.</p>
       <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>FD</th><th>Working</th><th>Z</th><th>Preserved?</th></tr></thead><tbody>
       ${pr.res.map(r=>`<tr><td>${mono(ffd(r.L,r.R))}</td><td>${r.local>=0?`inside R${r.local+1}(${E(fs(D[r.local]))})`:r.steps.map(s=>`R${s.i+1}: (${E(fs(s.from))})⁺∩R${s.i+1} adds ${E(fs(s.add))}`).join('<br>')||'nothing added'}</td><td>${mono(fs(r.Z))}</td><td>${yes(r.ok)}</td></tr>`).join('')}
       </tbody></table></div>`;
      const cell=(v,r,j)=>v===-1?`<td class="${P}-a">a<sub>${j+1}</sub></td>`:`<td>b<sub>${v+1}${j+1}</sub></td>`;
      const tHost=out.querySelector(`#${P}CT`);
      stepper(out.querySelector(`#${P}CS`),P,ch.snaps.length,i=>{const s=ch.snaps[i];const last=i===ch.snaps.length-1;
        tHost.innerHTML=`<p class="${P}-cap">${i===0?'Initial tableau.':`Apply ${mono(ffd(s.f.L,s.f.R))}: rows ${s.group.map(g=>g+1).join(', ')} agree on ${E(fs(s.f.L))}, so column ${E(S.rel.names[s.col])} becomes ${s.to===-1?'<b>a</b>':'<b>b</b><sub>'+(s.to+1)+(s.col+1)+'</sub>'} in row${s.changed.length>1?'s':''} ${s.changed.map(g=>g+1).join(', ')}.`}${last?(ch.lossless?` <b>Row ${ch.row+1} is all a: lossless.</b>`:' <b>No more changes and no all-a row: lossy.</b>'):''}</p>
         <div class="${P}-scroll"><table class="${P}-tbl ${P}-tab"><thead><tr><th></th>${S.rel.names.map(nm=>`<th>${E(nm)}</th>`).join('')}</tr></thead><tbody>${s.rows.map((r,ri)=>`<tr class="${last&&ri===ch.row?P+'-win':''}"><th>R${ri+1}(${E(fs(D[ri]))})</th>${r.map((v,j)=>{const c=cell(v,ri,j);return i&&j===s.col&&s.changed.includes(ri)?c.replace('<td','<td data-ch="1"'):c;}).join('')}</tr>`).join('')}</tbody></table></div>`;});
    };
    inD.oninput=debounce(run,200);run();
  }
  const recompute=debounce(()=>{st.a=inA.value;st.f=inF.value;compute();},220);
  inA.oninput=recompute;inF.oninput=recompute;
  $(`#${P}Ex`).onchange=e=>{const x=EX[+e.target.value];if(!x)return;Object.assign(st,{a:x.a,f:x.f,x:x.x,d:x.d});inA.value=x.a;inF.value=x.f;compute();};
  $(`#${P}Rnd`).onclick=()=>{
    const n=rnd(4,6),names='ABCDEF'.slice(0,n).split('');const F=[];const k=rnd(3,5);let guard=0;
    while(F.length<k&&guard++<100){const L=shuffle(names).slice(0,Math.random()<.6?1:2).sort();const rest=names.filter(x=>!L.includes(x));const R=shuffle(rest).slice(0,Math.random()<.8?1:2).sort();const s=L.join('')+'->'+R.join('');if(!F.includes(s))F.push(s);}
    st.a=names.join('');st.f=F.join(', ');st.x=F[0].split('->')[0];
    const half=Math.ceil(n/2);st.d=names.slice(0,half+1).join('')+', '+names.slice(half).join('');
    inA.value=st.a;inF.value=st.f;$(`#${P}Ex`).value='';compute();};
  compute();
 }});

/* ---------------------------------------------------------------- serial UI */
ANIM.register('serial',{title:'Schedule serializability solver',steps:false,
 caption:'Type a schedule. The solver draws the precedence graph, tests conflict and view serializability, and checks recoverable, cascadeless and strict, with the reason for each verdict.',
 build(stage){
  const P='serial',yes=Y(P);
  const EX=[
    {nm:'Two-way conflict (not CS)',s:'R1(A) W2(A) R2(B) W1(B) C1 C2'},
    {nm:'Lost update',s:'R1(A) R2(A) W1(A) W2(A) C1 C2'},
    {nm:'Blind writes: VS but not CS',s:'R1(A) W2(A) W1(A) W3(A) C1 C2 C3'},
    {nm:'Three transactions, CS',s:'R2(A) R1(B) W2(A) R3(A) W1(B) W3(A) R2(B) W2(B) C1 C2 C3'},
    {nm:'Not recoverable',s:'W1(A) R2(A) C2 C1'},
    {nm:'Recoverable, not cascadeless',s:'W1(A) R2(A) W1(B) C1 C2'},
    {nm:'Cascadeless, not strict',s:'W1(A) W2(A) C1 C2'},
    {nm:'With an abort',s:'W1(A) R2(A) A1 C2'}];
  const st={s:EX[0].s,tab:0,co:false};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${P}">
   <div class="${P}-in">
     <label class="${P}-lab ${P}-wide">Schedule<textarea id="${P}S" rows="2" spellcheck="false"></textarea></label>
     <div class="${P}-btns"><label class="${P}-lab">Example<select id="${P}Ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" id="${P}Rnd">🎲 Random example</button>
     <label class="${P}-lab">Serializability over<select id="${P}Co"><option value="0">all transactions</option><option value="1">committed transactions only</option></select></label></div>
     <p class="${P}-hint"><code>R1(A)</code> read, <code>W2(B)</code> write, <code>C1</code> commit, <code>A1</code> abort, separated by spaces. Transaction numbers are T1, T2, and so on.</p>
     <div class="${P}-err" role="alert" hidden></div>
   </div>
   <div class="${P}-ans"></div>
   <div class="${P}-tabs" role="group" aria-label="Working"></div>
   <div class="${P}-pane"></div></div>`;
  const $=s=>stage.querySelector(s);
  const inS=$(`#${P}S`),err=$(`.${P}-err`),ans=$(`.${P}-ans`),pane=$(`.${P}-pane`),tabHost=$(`.${P}-tabs`);inS.value=st.s;
  let R=null;const uid='sg'+(++UID);
  const TABS=['Precedence graph','View serializability','Recoverability'];
  tabs(tabHost,P,TABS,0,k=>{st.tab=k;renderPane();});
  const on=o=>E(SE.name(o));
  const T=t=>`T<sub>${t}</sub>`;
  function compute(){
    const r=SE.solve(st.s,st.co);
    if(r.err){err.hidden=false;err.textContent=r.err;$(`.${P}`).classList.add(`${P}-stale`);return;}
    err.hidden=true;$(`.${P}`).classList.remove(`${P}-stale`);R=r;renderAns();renderPane();
  }
  function renderAns(){
    const {g,v,r}=R;
    const vsTxt=g.cs?yes(true,'Yes (every CS schedule is VS)'):v.skipped?`<span class="${P}-warn">not checked (more than 5 transactions)</span>`:v.vs?yes(true,'Yes: '+v.results.filter(x=>x.ok).map(x=>x.order.map(t=>'T'+t).join('→')).join(', ')):yes(false,'','No');
    ans.innerHTML=`<div class="${P}-card"><span class="${P}-k">Conflict serializable</span><b class="${P}-big">${g.cs?yes(true,'Yes'):yes(false,'','No (cycle)')}</b>${g.cs?`<span>serial order: <b>${g.orders[0].map(t=>'T'+t).join(' → ')}</b>${g.orders.length>1?` <span class="${P}-mut">(${g.orders.length>=24?'24+':g.orders.length} orders valid)</span>`:''}</span>`:`<span>cycle: <b>${g.cycle.map(t=>'T'+t).join(' → ')}</b></span>`}</div>
     <div class="${P}-card"><span class="${P}-k">View serializable</span><b>${vsTxt}</b></div>
     <div class="${P}-card"><span class="${P}-k">Recoverable</span><b>${yes(r.recoverable)}</b></div>
     <div class="${P}-card"><span class="${P}-k">Cascadeless (ACA)</span><b>${yes(r.cascadeless)}</b></div>
     <div class="${P}-card"><span class="${P}-k">Strict</span><b>${yes(r.strictOk)}</b></div>`;
  }
  function graphSVG(txs,edges){
    const n=txs.length,W=300,H=230,cx=150,cy=115,rad=n<=1?0:n===2?95:Math.min(95,40+n*12),nr=19;
    const pos={};txs.forEach((t,k)=>{const a=n===2?(k?0:Math.PI):-Math.PI/2+2*Math.PI*k/n;pos[t]=[cx+rad*Math.cos(a),cy+rad*Math.sin(a)];});
    const mk=(id,cls)=>`<marker id="${uid}${id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" class="${cls}"/></marker>`;
    let body='';
    for(const e of edges){const [x1,y1]=pos[e.f],[x2,y2]=pos[e.t];const both=edges.some(o=>o.f===e.t&&o.t===e.f);
      const dx=x2-x1,dy=y2-y1,len=Math.hypot(dx,dy)||1,ux=dx/len,uy=dy/len;const off=both?26:0;
      const mx=(x1+x2)/2+(-uy)*off,my=(y1+y2)/2+ux*off;
      const s1=Math.hypot(mx-x1,my-y1)||1,s2=Math.hypot(x2-mx,y2-my)||1;
      const ax=x1+(mx-x1)/s1*nr,ay=y1+(my-y1)/s1*nr,bx=x2-(x2-mx)/s2*(nr+2),by=y2-(y2-my)/s2*(nr+2);
      const lx=.25*ax+.5*mx+.25*bx,ly=.25*ay+.5*my+.25*by;const cls=e.cyc?'cyc':e.nw?'nw':'';
      body+=`<path d="M${ax.toFixed(1)},${ay.toFixed(1)} Q${mx.toFixed(1)},${my.toFixed(1)} ${bx.toFixed(1)},${by.toFixed(1)}" class="${P}-e ${cls}" marker-end="url(#${uid}${cls||'n'})"/><text x="${lx.toFixed(1)}" y="${(ly-4).toFixed(1)}" class="${P}-el ${cls}" text-anchor="middle">${E(e.items.join(','))}</text>`;}
    for(const t of txs){const [x,y]=pos[t];body+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${nr}" class="${P}-nd"/><text x="${x.toFixed(1)}" y="${(y+5).toFixed(1)}" text-anchor="middle" class="${P}-nt">T${t}</text>`;}
    return `<svg viewBox="0 0 ${W} ${H}" class="${P}-svg" role="img" aria-label="Precedence graph with ${edges.length} edge(s)"><defs>${mk('n',P+'-ah')}${mk('nw',P+'-ah nw')}${mk('cyc',P+'-ah cyc')}</defs>${body}</svg>`;
  }
  function schedTable(upto,hiOps){
    const {ops,txs}=R;
    return `<div class="${P}-scroll"><table class="${P}-tbl ${P}-grid"><thead><tr><th>t</th>${txs.map(t=>`<th>${T(t)}</th>`).join('')}</tr></thead><tbody>${ops.map((o,k)=>`<tr class="${k===upto?P+'-cur':k>upto?P+'-fut':''}"><td>${k+1}</td>${txs.map(t=>`<td class="${hiOps&&hiOps.includes(k)&&o.tx===t?P+'-pair':''}">${o.tx===t?on(o):''}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function paneGraph(){
    const {ops,g}=R;const n=ops.length+1;
    const cycSet=new Set();if(g.cycle)for(let k=0;k<g.cycle.length-1;k++)cycSet.add(g.cycle[k]+'>'+g.cycle[k+1]);
    pane.innerHTML=`<div id="${P}St"></div><div class="${P}-two"><div id="${P}Gt"></div><div id="${P}Gg"></div></div><p class="${P}-cap" id="${P}Gc"></p>
      <h4 class="${P}-h">All conflicting pairs</h4>
      <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Earlier op</th><th>Later op</th><th>Edge</th></tr></thead><tbody>${g.pairs.map(([a,b])=>`<tr><td>${on(ops[a])} <span class="${P}-mut">(t=${a+1})</span></td><td>${on(ops[b])} <span class="${P}-mut">(t=${b+1})</span></td><td>${T(ops[a].tx)} → ${T(ops[b].tx)}</td></tr>`).join('')||`<tr><td colspan="3">No conflicting pairs.</td></tr>`}</tbody></table></div>
      <p class="${P}-res">${g.cs?`No cycle, so the schedule is <b>conflict serializable</b>. A topological sort gives the equivalent serial order${g.orders.length>1?'s':''}: <b>${g.orders.map(o=>o.map(t=>'T'+t).join(' → ')).join('; ')}</b>${g.orders.length>=24?' …':''}.`:`Cycle <b>${g.cycle.map(t=>'T'+t).join(' → ')}</b>, so the schedule is <b>not conflict serializable</b>.`}</p>
      <p class="${P}-conv"><b>Convention.</b> Two operations conflict if they belong to different transactions, touch the same item and at least one is a write (RW, WR, WW). Each conflict adds edge T<sub>i</sub> → T<sub>j</sub> when T<sub>i</sub>'s operation comes first. Commit and abort are not operations on data. ${st.co?'Only committed transactions are included (committed projection).':'All transactions are included, committed or not.'}</p>`;
    const gt=pane.querySelector(`#${P}Gt`),gg=pane.querySelector(`#${P}Gg`),gc=pane.querySelector(`#${P}Gc`);
    stepper(pane.querySelector(`#${P}St`),P,n,i=>{const upto=i-1;
      const seen=g.edges.map(e=>({...e,firstAt:Math.min(...e.pairs.map(p=>p[1]))})).filter(e=>e.firstAt<=upto);
      const newPairs=upto>=0?g.pairs.filter(p=>p[1]===upto):[];
      const es=seen.map(e=>({...e,nw:e.firstAt===upto,cyc:i===n-1&&cycSet.has(e.f+'>'+e.t)}));
      gt.innerHTML=schedTable(upto,newPairs.length?[upto,...newPairs.map(p=>p[0])]:null);gg.innerHTML=graphSVG(g.txs,es);
      if(i===0)gc.innerHTML='Before any operation: one node per transaction, no edges yet.';
      else{const o=ops[upto];const inc=g.txs.includes(o.tx);
        if(o.t==='C'||o.t==='A')gc.innerHTML=`t=${upto+1}: ${on(o)} ${o.t==='C'?'commits':'aborts'}; no data access, so no new conflict.`;
        else if(!inc)gc.innerHTML=`t=${upto+1}: ${on(o)} belongs to T${o.tx}, which does not commit, so it is left out (committed projection).`;
        else if(!newPairs.length)gc.innerHTML=`t=${upto+1}: ${on(o)} conflicts with no earlier operation of another transaction.`;
        else gc.innerHTML=`t=${upto+1}: ${on(o)} conflicts with ${newPairs.map(p=>on(ops[p[0]])).join(', ')} → edge${newPairs.length>1?'s':''} ${[...new Set(newPairs.map(p=>'T'+ops[p[0]].tx+' → T'+o.tx))].join(', ')}${es.some(e=>e.nw)?'':' (already present)'}.`;
        if(i===n-1)gc.innerHTML+=g.cs?' <b>No cycle: conflict serializable.</b>':` <b>Cycle ${g.cycle.map(t=>'T'+t).join(' → ')}: not conflict serializable.</b>`;}
    },n-1);
  }
  function paneView(){
    const {ops,v,g}=R;const src=x=>x?'T'+x:'initial value';
    const reads=v.d.filter(o=>o.t==='R');
    let perm='';
    if(v.skipped)perm=`<p class="${P}-res">${g.cs?'Conflict serializable, hence view serializable (no brute force needed).':'More than 5 transactions: brute force over n! orders is not attempted.'}</p>`;
    else perm=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Serial order</th><th>View equivalent?</th></tr></thead><tbody>${v.results.map(r=>`<tr><td>${r.order.map(t=>'T'+t).join(' → ')}</td><td>${r.ok?yes(true,'yes: same reads-from and final writes'):yes(false,'',r.why.k==='rf'?`${on(ops[r.why.i])} reads from ${src(r.why.v)} here, but from ${src(r.why.s)} in S`:`final write of ${E(r.why.item)} is by ${src(r.why.v)} here, but by ${src(r.why.s)} in S`)}</td></tr>`).join('')}</tbody></table></div>
      <p class="${P}-res">${v.vs?`<b>View serializable</b>, equivalent to ${v.results.filter(r=>r.ok).map(r=>r.order.map(t=>'T'+t).join(' → ')).join(', ')}.`:'<b>Not view serializable</b>: no serial order matches.'}${!g.cs&&v.vs?' It is view but not conflict serializable, which is possible only with <b>blind writes</b>.':''}</p>`;
    pane.innerHTML=`<p class="${P}-conv"><b>Method.</b> S is view equivalent to a serial order if (1) every read reads from the same writer (or the initial value) and (2) the final write of each item is by the same transaction. The solver tries every order of the ${v.use.length} transaction${v.use.length>1?'s':''} (${v.use.length<=5?`${[1,1,2,6,24,120][v.use.length]} orders`:'too many'}).</p>
     <div class="${P}-two"><div><h4 class="${P}-h">Reads-from in S</h4><div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Read</th><th>Reads from</th></tr></thead><tbody>${reads.map(o=>`<tr><td>${on(ops[o.i])} <span class="${P}-mut">(t=${o.i+1})</span></td><td>${src(v.S.rf[o.tx+':'+o.k])}</td></tr>`).join('')||`<tr><td colspan="2">No reads.</td></tr>`}</tbody></table></div></div>
     <div><h4 class="${P}-h">Final writes in S</h4><div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Item</th><th>Final writer</th></tr></thead><tbody>${Object.keys(v.S.fw).sort().map(it=>`<tr><td>${E(it)}</td><td>T${v.S.fw[it]}</td></tr>`).join('')||`<tr><td colspan="2">No writes.</td></tr>`}</tbody></table></div></div></div>
     <p>Blind writes (a write of an item the transaction has not read): ${v.blind.length?v.blind.map(i=>on(ops[i])).join(', '):'none'}.</p>${perm}`;
  }
  function paneRec(){
    const {ops,r}=R;const src=x=>`${on(ops[x.r])} reads ${E(x.item)} from ${on(ops[x.w])}`;
    pane.innerHTML=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Dirty read (T<sub>i</sub> reads from T<sub>j</sub>)</th><th>Recoverable?</th><th>Cascadeless?</th></tr></thead><tbody>
     ${r.rec.map((x,k)=>`<tr><td>${src(x)}</td><td>${yes(x.ok)} <span class="${P}-mut">${E(x.why)}</span></td><td>${yes(r.aca[k].ok)} <span class="${P}-mut">${r.aca[k].ok?`T${x.writer} committed before the read`:`read happens before T${x.writer} commits`}</span></td></tr>`).join('')||`<tr><td colspan="3">No transaction reads a value written by another transaction.</td></tr>`}</tbody></table></div>
     <h4 class="${P}-h">Strict check</h4>
     <p>${r.strict.length?`Not strict: ${r.strict.map(x=>`${on(ops[x.op])} (t=${x.op+1}) touches ${E(ops[x.op].item)} after ${on(ops[x.w])} (t=${x.w+1}) before T${ops[x.w].tx} commits or aborts`).join('; ')}.`:'Strict: no transaction reads or writes an item after another transaction wrote it and before that writer committed or aborted.'}</p>
     <p class="${P}-res">Recoverable ${yes(r.recoverable)} · Cascadeless ${yes(r.cascadeless)} · Strict ${yes(r.strictOk)}</p>
     ${r.incomplete.length?`<p class="${P}-mut">${r.incomplete.map(t=>'T'+t).join(', ')} ${r.incomplete.length>1?'have':'has'} no commit or abort in the schedule, so ${r.incomplete.length>1?'they are':'it is'} treated as still active.</p>`:''}
     <p class="${P}-conv"><b>Definitions.</b> T<sub>i</sub> reads from T<sub>j</sub> if it reads the value of the last write by T<sub>j</sub> that has not aborted. <b>Recoverable:</b> if T<sub>i</sub> reads from T<sub>j</sub> and commits, then T<sub>j</sub> commits first. <b>Cascadeless:</b> T<sub>i</sub> reads only values from already committed transactions. <b>Strict:</b> no item written by T<sub>j</sub> is read or overwritten until T<sub>j</sub> commits or aborts. Strict ⊂ cascadeless ⊂ recoverable.</p>`;
  }
  function renderPane(){if(R)[paneGraph,paneView,paneRec][st.tab]();}
  const recompute=debounce(()=>{st.s=inS.value;compute();},220);inS.oninput=recompute;
  $(`#${P}Ex`).onchange=e=>{const x=EX[+e.target.value];if(!x)return;st.s=x.s;inS.value=x.s;compute();};
  $(`#${P}Co`).onchange=e=>{st.co=e.target.value==='1';compute();};
  $(`#${P}Rnd`).onclick=()=>{
    const nt=rnd(2,3),items=Math.random()<.8?['A','B']:['A'];
    const seqs=[];for(let t=1;t<=nt;t++){const k=rnd(2,3);const s=[];for(let j=0;j<k;j++){const it=pick(items);s.push({t:Math.random()<.5?'R':'W',tx:t,item:it});}s.push({t:Math.random()<.85?'C':'A',tx:t});seqs.push(s);}
    const out=[];const idx=seqs.map(()=>0);let left=seqs.reduce((a,s)=>a+s.length,0);
    while(left){const c=seqs.map((s,k)=>k).filter(k=>idx[k]<seqs[k].length);const k=pick(c);out.push(seqs[k][idx[k]++]);left--;}
    st.s=out.map(o=>SE.name(o)).join(' ');inS.value=st.s;$(`#${P}Ex`).value='';compute();};
  compute();
 }});

/* ---------------------------------------------------------------- bptree UI */
ANIM.register('bptree',{title:'B-tree and B+ tree insertion',steps:false,
 caption:'Choose B-tree or B+ tree, the order and its definition, then step through the inserts. Each split shows which key moves (B-tree) or is copied (B+ leaf) up.',
 build(stage){
  const P='bptree',yes=Y(P);
  const st={kind:'B',def:'knuth',order:3,split:'bottomup',bias:'left',keys:'10 20 30 40 50 60 70 80 90',frame:null};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${P}">
   <div class="${P}-in">
     <div class="${P}-lab"><span>Tree</span><div class="seg ${P}-seg" id="${P}K"><button type="button" aria-pressed="true" data-v="B">B-tree</button><button type="button" aria-pressed="false" data-v="B+">B+ tree</button></div></div>
     <label class="${P}-lab">Order is defined as<select id="${P}D"><option value="knuth">m = max children (Knuth)</option><option value="mindeg">t = min degree (CLRS)</option></select></label>
     <label class="${P}-lab"><span id="${P}OL">Order m</span><input type="number" id="${P}O" min="2" max="12" value="3"></label>
     <label class="${P}-lab">Split timing<select id="${P}Sp"><option value="bottomup">bottom-up, on overflow</option><option value="topdown">top-down, pre-emptive</option></select></label>
     <label class="${P}-lab">Uneven split<select id="${P}B"><option value="left">extra key in left node</option><option value="right">extra key in right node</option></select></label>
     <label class="${P}-lab ${P}-wide">Keys to insert, in order<input type="text" id="${P}I" spellcheck="false" autocomplete="off"></label>
     <div class="${P}-btns"><button type="button" class="btn sm" id="${P}Rnd">🎲 Random example</button></div>
     <div class="${P}-err" role="alert" hidden></div>
   </div>
   <div class="${P}-rules"></div>
   <div id="${P}St"></div>
   <p class="${P}-cap" id="${P}C" aria-live="polite"></p>
   <div class="${P}-scroll ${P}-view"><div class="${P}-canvas"><svg class="${P}-lines" aria-hidden="true"></svg><div class="${P}-tree"></div></div></div>
   <div class="${P}-ans"></div>
   <div class="${P}-log"></div></div>`;
  const $=s=>stage.querySelector(s);
  const err=$(`.${P}-err`),rules=$(`.${P}-rules`),cap=$(`#${P}C`),treeEl=$(`.${P}-tree`),svg=$(`.${P}-lines`),canvas=$(`.${P}-canvas`),ans=$(`.${P}-ans`),log=$(`.${P}-log`);
  $(`#${P}I`).value=st.keys;
  let res=null,cur=0,stp=null;
  function nodeHTML(n,hl,isB){
    const cls=hl[n.id]?' '+hl[n.id]:'';
    const keys=n.keys.length?n.keys.map(k=>`<span class="${P}-key">${k}</span>`).join(''):`<span class="${P}-key ${P}-empty">empty</span>`;
    const me=`<div class="${P}-node${n.leaf?' leaf':''}${cls}" data-id="${n.id}">${keys}</div>`;
    if(!n.kids.length)return `<div class="${P}-sub">${me}</div>`;
    return `<div class="${P}-sub">${me}<div class="${P}-kids">${n.kids.map(c=>nodeHTML(c,hl,isB)).join('')}</div></div>`;
  }
  function drawLines(){
    if(!res)return;const f=res.frames[cur];const base=canvas.getBoundingClientRect();
    const W=canvas.scrollWidth,H=canvas.scrollHeight;svg.setAttribute('width',W);svg.setAttribute('height',H);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    let d='',chain='';
    const walk=n=>{if(!n.kids.length)return;const pe=treeEl.querySelector(`[data-id="${n.id}"]`);if(!pe)return;const pr=pe.getBoundingClientRect();const cells=[...pe.children];
      n.kids.forEach((c,i)=>{const ce=treeEl.querySelector(`[data-id="${c.id}"]`);if(!ce)return;const cr=ce.getBoundingClientRect();
        const x1=(i<cells.length?cells[i].getBoundingClientRect().left:pr.right-1)-base.left,y1=pr.bottom-base.top,x2=cr.left+cr.width/2-base.left,y2=cr.top-base.top;
        d+=`M${x1.toFixed(1)},${y1.toFixed(1)}L${x2.toFixed(1)},${y2.toFixed(1)}`;walk(c);});};
    walk(f.tree);
    if(res.kind==='B+'){const leaves=[...treeEl.querySelectorAll(`.${P}-node.leaf`)];for(let i=0;i+1<leaves.length;i++){const a=leaves[i].getBoundingClientRect(),b=leaves[i+1].getBoundingClientRect();const y=a.top+a.height/2-base.top;chain+=`M${(a.right-base.left+1).toFixed(1)},${y.toFixed(1)}L${(b.left-base.left-3).toFixed(1)},${y.toFixed(1)}`;}}
    const mid='bm'+(++UID);
    const segs=chain.split('M').filter(Boolean).map(x=>`<path d="M${x}" class="${P}-chain" marker-end="url(#${mid})"/>`).join('');
    svg.innerHTML=`<defs><marker id="${mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0L10,5L0,10z" class="${P}-ah"/></marker></defs><path d="${d}" class="${P}-ln"/>${segs}`;
  }
  function show(i){
    cur=i;const f=res.frames[i];treeEl.innerHTML=nodeHTML(f.tree,f.hl,res.kind==='B');cap.innerHTML=f.cap;drawLines();
    const s=BT.stats(f.tree);
    ans.innerHTML=`<div class="${P}-card"><span class="${P}-k">Height</span><b class="${P}-big">${s.levels}</b><span>level${s.levels===1?'':'s'} (${Math.max(0,s.levels-1)} edge${s.levels===2?'':'s'} root→leaf)</span></div>
     <div class="${P}-card"><span class="${P}-k">Nodes</span><b class="${P}-big">${s.nodes}</b><span>${s.internal} internal, ${s.leaves} leaf</span></div>
     <div class="${P}-card"><span class="${P}-k">Keys stored</span><b class="${P}-big">${s.keys}</b><span>${res.kind==='B+'?`${s.leafKeys.length} in leaves + ${s.keys-s.leafKeys.length} copies in index nodes`:'each key stored once'}</span></div>
     <div class="${P}-card"><span class="${P}-k">Splits so far</span><b class="${P}-big">${res.frames.slice(0,i+1).filter(x=>x.kind==='split').length}</b></div>`;
    log.querySelectorAll('li').forEach(li=>li.classList.toggle('on',+li.dataset.f===i));
  }
  function compute(){
    const kp=BT.parseKeys(st.keys);
    const o={kind:st.kind,def:st.def,order:+st.order,split:st.split,bias:st.bias};
    let r=kp.err?kp:BT.build(kp.keys,o);
    if(r.err){err.hidden=false;err.textContent=r.err;$(`.${P}`).classList.add(`${P}-stale`);return;}
    err.hidden=true;$(`.${P}`).classList.remove(`${P}-stale`);res=r;const L=r.limits;
    const tdOK=st.kind==='B'&&L.maxK%2===1;$(`#${P}Sp`).disabled=!tdOK;if(!tdOK)$(`#${P}Sp`).value='bottomup';
    const nk=new Set(kp.keys).size,bd=st.kind==='B'?BT.bounds(nk,L):null;
    rules.innerHTML=`<p><b>${st.def==='knuth'?`Order m = ${st.order} (Knuth: maximum number of children)`:`Minimum degree t = ${st.order} (CLRS)`}.</b> Every node holds at most <b>${L.maxK}</b> keys (${L.maxC} children). Every non-root node holds at least <b>${L.minK}</b> key${L.minK===1?'':'s'}${st.kind==='B'?` (internal: ≥ ${L.minC} children)`:''}; the root needs only 1 key.${st.kind==='B+'?' In the B+ tree, leaves hold every key and are chained left to right; index nodes hold copies used only for searching (a key equal to a separator goes right).':''}</p>
     <p class="${P}-conv">${r.topdown?'Pre-emptive (CLRS): on the way down, any full node is split before entering it, so the leaf always has room.':`Bottom-up: insert into the leaf; if it holds ${L.maxK+1} keys, split it and push ${st.kind==='B+'?'(copy, for a leaf) ':''}the middle key into the parent, repeating upward.`} ${st.bias==='left'?'When the halves cannot be equal, the left node keeps the extra key.':'When the halves cannot be equal, the right node gets the extra key.'}${bd?` For ${nk} keys a ${st.def==='knuth'?'B-tree of order '+st.order:'B-tree with t = '+st.order} has between <b>${bd.minLevels}</b> (every node full: ${L.maxC}<sup>h</sup> − 1 ≥ n) and <b>${bd.maxLevels}</b> levels (minimum fill: n ≥ 2·${L.minC}<sup>h−1</sup> − 1).`:''}</p>`;
    log.innerHTML=`<h4 class="${P}-h">Splits (click to jump)</h4><ul>${r.frames.map((f,k)=>f.kind==='split'||f.kind==='dup'?`<li data-f="${k}"><button type="button">${E(f.kind==='dup'?f.key+': duplicate, skipped':f.lab)}</button></li>`:'').join('')||'<li>No splits: every key fitted in the root leaf.</li>'}</ul>`;
    log.querySelectorAll('li[data-f] button').forEach(b=>b.onclick=()=>stp.go(+b.parentNode.dataset.f));
    stp=stepper($(`#${P}St`),P,r.frames.length,show);stp.go(r.frames.length-1);
  }
  const sync=()=>{$(`#${P}OL`).textContent=st.def==='knuth'?'Order m (max children)':'Minimum degree t';const o=$(`#${P}O`);o.min=st.def==='knuth'?3:2;o.max=st.def==='knuth'?12:6;};
  stage.querySelectorAll(`#${P}K button`).forEach(b=>b.onclick=()=>{st.kind=b.dataset.v;stage.querySelectorAll(`#${P}K button`).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));compute();});
  $(`#${P}D`).onchange=e=>{st.def=e.target.value;if(st.def==='mindeg'&&st.order>6)st.order=2;if(st.def==='knuth'&&st.order<3)st.order=3;$(`#${P}O`).value=st.order;sync();compute();};
  $(`#${P}O`).oninput=debounce(e=>{st.order=e.target.value;compute();},250);
  $(`#${P}Sp`).onchange=e=>{st.split=e.target.value;compute();};
  $(`#${P}B`).onchange=e=>{st.bias=e.target.value;compute();};
  $(`#${P}I`).oninput=debounce(e=>{st.keys=e.target.value;compute();},250);
  $(`#${P}Rnd`).onclick=()=>{const n=rnd(9,14);const s=new Set();while(s.size<n)s.add(rnd(1,99));st.keys=[...s].join(' ');st.order=st.def==='knuth'?rnd(3,5):rnd(2,3);$(`#${P}O`).value=st.order;$(`#${P}I`).value=st.keys;compute();};
  if(typeof ResizeObserver!=='undefined'){const ro=new ResizeObserver(()=>drawLines());ro.observe(treeEl);}
  sync();compute();
 }});
})();

/* ================= UGC NET solvers: group dm (truthtable, lpp, transport, assign) =================
   Pure algorithms live on NETSOLVE.truthtable / NETSOLVE.lpp / NETSOLVE.transport / NETSOLVE.assign
   so they can be tested in Node (global.window = {}). Everything is wrapped in an IIFE so no global
   names are declared (several net-*.js files are concatenated into one script). */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;

/* ======================================================================
   Exact rationals (BigInt) for the LPP solvers
   ====================================================================== */
const gcdB=(a,b)=>{a=a<0n?-a:a;b=b<0n?-b:b;while(b){const t=a%b;a=b;b=t;}return a;};
class Q{
  constructor(n,d){n=BigInt(n);d=d===undefined?1n:BigInt(d);if(d===0n)throw new Error('Q: zero denominator');if(d<0n){n=-n;d=-d;}const g=gcdB(n,d);if(g>1n){n/=g;d/=g;}this.n=n;this.d=d;}
  add(o){return new Q(this.n*o.d+o.n*this.d,this.d*o.d);}
  sub(o){return new Q(this.n*o.d-o.n*this.d,this.d*o.d);}
  mul(o){return new Q(this.n*o.n,this.d*o.d);}
  div(o){return new Q(this.n*o.d,this.d*o.n);}
  neg(){return new Q(-this.n,this.d);}
  cmp(o){const x=this.n*o.d-o.n*this.d;return x>0n?1:x<0n?-1:0;}
  sgn(){return this.n>0n?1:this.n<0n?-1:0;}
  eq(o){return this.n===o.n&&this.d===o.d;}
  num(){return Number(this.n)/Number(this.d);}
  str(){return this.d===1n?String(this.n):`${this.n}/${this.d}`;}
}
Q.parse=function(s){
  s=String(s==null?'':s).trim().replace(/[−–]/g,'-');
  if(/^[+-]?\d+$/.test(s))return new Q(BigInt(s));
  let m=s.match(/^([+-]?)(\d*)\.(\d+)$/);
  if(m)return new Q(BigInt((m[1]==='-'?'-':'')+(m[2]||'0')+m[3]),10n**BigInt(m[3].length));
  m=s.match(/^([+-]?\d+)\s*\/\s*(\d+)$/);
  if(m&&BigInt(m[2])!==0n)return new Q(BigInt(m[1]),BigInt(m[2]));
  return null;
};
const Q0=new Q(0),Q1=new Q(1);
NETSOLVE.Q=Q;

/* ======================================================================
   TRUTHTABLE core
   ====================================================================== */
const TT={};
TT.OPS={and:{s:'∧',nm:'AND'},nand:{s:'↑',nm:'NAND'},or:{s:'∨',nm:'OR'},xor:{s:'⊕',nm:'XOR'},nor:{s:'↓',nm:'NOR'},imp:{s:'→',nm:'implies'},iff:{s:'↔',nm:'if and only if'}};
const TSYM=[['<->','iff'],['<=>','iff'],['->','imp'],['=>','imp'],['==','iff'],['!=','xor'],['&&','and'],['||','or'],['/\\','and'],['\\/','or'],
  ['↔','iff'],['⇔','iff'],['≡','iff'],['→','imp'],['⇒','imp'],['∧','and'],['&','and'],['·','and'],['∨','or'],['|','or'],['+','or'],
  ['⊕','xor'],['^','xor'],['↑','nand'],['↓','nor'],['¬','not'],['~','not'],['!','not'],['-','not'],['(','('],[')',')'],['[','('],[']',')']];
const TKW={not:'not',and:'and',or:'or',xor:'xor',implies:'imp',iff:'iff',nand:'nand',nor:'nor'};
TT.tokenize=function(src){
  const s=String(src==null?'':src),T=[];let i=0;
  while(i<s.length){
    const ch=s[i];if(/\s/.test(ch)){i++;continue;}
    const hit=TSYM.find(([t])=>s.startsWith(t,i));
    if(hit){T.push({k:hit[1],pos:i,txt:hit[0]});i+=hit[0].length;continue;}
    const m=/^[A-Za-z_][A-Za-z0-9_]*/.exec(s.slice(i));
    if(m){const w=m[0],lw=w.toLowerCase();
      if(TKW[lw])T.push({k:TKW[lw],pos:i,txt:w});
      else if(lw==='true'||lw==='false')T.push({k:'const',v:lw==='true',pos:i,txt:w});
      else if(w==='T'||w==='F')T.push({k:'const',v:w==='T',pos:i,txt:w});
      else T.push({k:'var',v:w,pos:i,txt:w});
      i+=w.length;continue;}
    if(ch==='0'||ch==='1'){T.push({k:'const',v:ch==='1',pos:i,txt:ch});i++;continue;}
    if(ch==='⊤'||ch==='⊥'){T.push({k:'const',v:ch==='⊤',pos:i,txt:ch});i++;continue;}
    return {err:`Unexpected character "${ch}" at position ${i+1}.`};
  }
  return {T};
};
/* precedence, loosest first: ↔ ; → (groups right) ; ∨ ⊕ ↓ ; ∧ ↑ ; ¬ */
const TLEV=[['iff'],['imp'],['or','xor','nor'],['and','nand']];
TT.parse=function(src){
  const s=String(src==null?'':src);
  if(!s.trim())return {err:'Enter a formula, e.g. (p -> q) & p -> q.'};
  if(s.length>240)return {err:'That formula is too long (at most 240 characters).'};
  const tk=TT.tokenize(s);if(tk.err)return tk;
  const T=tk.T;let i=0;const peek=()=>T[i];
  function bin(l){
    if(l===TLEV.length)return un();
    if(TLEV[l][0]==='imp'){const a=bin(l+1);if(peek()&&peek().k==='imp'){i++;const b=bin(l);return {t:'bin',op:'imp',a,b};}return a;}
    let a=bin(l+1);
    while(peek()&&TLEV[l].includes(peek().k)){const op=T[i++].k;const b=bin(l+1);a={t:'bin',op,a,b};}
    return a;
  }
  function un(){
    const t=peek();if(!t)throw 'The formula ends too early: an operand is missing.';
    if(t.k==='not'){i++;return {t:'not',a:un()};}
    if(t.k==='('){i++;const e=bin(0);if(!peek()||peek().k!==')')throw 'A closing bracket ")" is missing.';i++;return e;}
    if(t.k==='var'){i++;return {t:'var',v:t.v};}
    if(t.k==='const'){i++;return {t:'const',v:t.v};}
    throw `Unexpected "${t.txt}" at position ${t.pos+1}: expected a variable, ¬ or "(".`;
  }
  try{
    const ast=bin(0);
    if(i<T.length){const t=T[i];throw t.k===')'?`Unmatched ")" at position ${t.pos+1}.`:`Unexpected "${t.txt}" at position ${t.pos+1}: an operator is missing before it.`;}
    return {ast};
  }catch(e){if(typeof e==='string')return {err:e};throw e;}
};
TT.key=function(a){
  if(a.t==='var')return a.v;
  if(a.t==='const')return a.v?'T':'F';
  if(a.t==='not')return '¬'+TT.key(a.a);
  return '('+TT.key(a.a)+' '+TT.OPS[a.op].s+' '+TT.key(a.b)+')';
};
TT.label=function(a){const k=TT.key(a);return a.t==='bin'?k.slice(1,-1):k;};
TT.vars=function(a,set){set=set||new Set();if(a.t==='var')set.add(a.v);else if(a.t==='not')TT.vars(a.a,set);else if(a.t==='bin'){TT.vars(a.a,set);TT.vars(a.b,set);}return set;};
const natCmp=(x,y)=>x.localeCompare(y,'en',{numeric:true});
TT.apply=function(op,x,y){switch(op){case 'and':return x&&y;case 'or':return x||y;case 'xor':return x!==y;case 'imp':return !x||y;case 'iff':return x===y;case 'nand':return !(x&&y);case 'nor':return !(x||y);}return false;};
TT.eval=function(a,env){
  if(a.t==='var')return env[a.v];
  if(a.t==='const')return a.v;
  if(a.t==='not')return !TT.eval(a.a,env);
  return TT.apply(a.op,TT.eval(a.a,env),TT.eval(a.b,env));
};
TT.columns=function(ast){
  const out=[],seen=new Set();
  (function walk(a){if(a.t==='not')walk(a.a);else if(a.t==='bin'){walk(a.a);walk(a.b);}else return;const k=TT.key(a);if(!seen.has(k)){seen.add(k);out.push(a);}})(ast);
  return out;
};
TT.envOf=(vars,r)=>{const n=vars.length,env={};vars.forEach((v,k)=>env[v]=!!((r>>(n-1-k))&1));return env;};
TT.minterm=(vars,r)=>{const n=vars.length;const lits=vars.map((v,k)=>((r>>(n-1-k))&1)?v:'¬'+v);return n>1?'('+lits.join(' ∧ ')+')':lits[0];};
TT.maxterm=(vars,r)=>{const n=vars.length;const lits=vars.map((v,k)=>((r>>(n-1-k))&1)?'¬'+v:v);return n>1?'('+lits.join(' ∨ ')+')':lits[0];};
TT.MAXV=6;
TT.solve=function(src){
  const p=TT.parse(src);if(p.err)return p;
  const ast=p.ast,vars=[...TT.vars(ast)].sort(natCmp);
  if(vars.length>TT.MAXV)return {err:`${vars.length} variables (${vars.join(', ')}): at most ${TT.MAXV} please (${1<<TT.MAXV} rows).`};
  const n=vars.length,R=1<<n;
  const cols=TT.columns(ast).map(node=>({node,key:TT.key(node),label:TT.label(node),t:node.t,op:node.op,vals:[]}));
  const res=[];
  for(let r=0;r<R;r++){const env=TT.envOf(vars,r);cols.forEach(c=>c.vals.push(TT.eval(c.node,env)));res.push(TT.eval(ast,env));}
  const nT=res.filter(Boolean).length;
  const cls=nT===R?'tautology':nT===0?'contradiction':'contingency';
  const minterms=[],maxterms=[];res.forEach((v,r)=>(v?minterms:maxterms).push(r));
  let dnf,cnf;
  if(!n){dnf=res[0]?'T':'F';cnf=dnf;}
  else{dnf=minterms.length?minterms.map(r=>TT.minterm(vars,r)).join(' ∨ '):'F';cnf=maxterms.length?maxterms.map(r=>TT.maxterm(vars,r)).join(' ∧ '):'T';}
  return {ast,vars,n,R,cols,res,nT,cls,minterms,maxterms,dnf,cnf,label:TT.label(ast)};
};
TT.equiv=function(s1,s2){
  const p1=TT.parse(s1);if(p1.err)return {err:'Formula 1: '+p1.err};
  const p2=TT.parse(s2);if(p2.err)return {err:'Formula 2: '+p2.err};
  const vars=[...TT.vars(p2.ast,TT.vars(p1.ast))].sort(natCmp);
  if(vars.length>TT.MAXV)return {err:`Together the formulas use ${vars.length} variables: at most ${TT.MAXV} please.`};
  const R=1<<vars.length,a=[],b=[],diff=[];
  for(let r=0;r<R;r++){const env=TT.envOf(vars,r);a.push(TT.eval(p1.ast,env));b.push(TT.eval(p2.ast,env));if(a[r]!==b[r])diff.push(r);}
  return {vars,R,a,b,diff,equivalent:!diff.length,l1:TT.label(p1.ast),l2:TT.label(p2.ast),
    f1ImpF2:a.every((x,r)=>!x||b[r]),f2ImpF1:b.every((x,r)=>!x||a[r])};
};
NETSOLVE.truthtable=TT;

/* ======================================================================
   LPP core (exact arithmetic).  Model: {sense:'max'|'min', c:[Q..], cons:[{a:[Q..], op:'<='|'>='|'=', b:Q}]}
   All decision variables are >= 0.
   ====================================================================== */
const LP={};
const dotQ=(a,x)=>a.reduce((s,ai,k)=>s.add(ai.mul(x[k])),Q0);
LP.sat=(k,x)=>{const s=dotQ(k.a,x).cmp(k.b);return k.op==='<='?s<=0:k.op==='>='?s>=0:s===0;};
LP.feasible=(M,x)=>x.every(v=>v.sgn()>=0)&&M.cons.every(k=>LP.sat(k,x));
/* Solve a square system exactly (Gauss-Jordan). Returns null if singular. */
LP.solveSq=function(A,b){
  const n=A.length,M=A.map((r,i)=>[...r,b[i]]);
  for(let c=0;c<n;c++){
    let p=-1;for(let r=c;r<n;r++)if(M[r][c].sgn()){p=r;break;}
    if(p<0)return null;[M[c],M[p]]=[M[p],M[c]];
    const pv=M[c][c];for(let k=c;k<=n;k++)M[c][k]=M[c][k].div(pv);
    for(let r=0;r<n;r++)if(r!==c&&M[r][c].sgn()){const f=M[r][c];for(let k=c;k<=n;k++)M[r][k]=M[r][k].sub(f.mul(M[c][k]));}
  }
  return M.map(r=>r[n]);
};
/* Brute-force vertex enumeration (any n, any constraint types): used for cross-checking. */
LP.vertices=function(M){
  const n=M.c.length,H=M.cons.map(k=>({a:k.a,b:k.b}));
  for(let j=0;j<n;j++)H.push({a:Array.from({length:n},(_,k)=>k===j?Q1:Q0),b:Q0});
  const pts=[];const idx=[];
  (function choose(s){
    if(idx.length===n){const x=LP.solveSq(idx.map(i=>H[i].a),idx.map(i=>H[i].b));if(x&&LP.feasible(M,x)&&!pts.some(p=>p.every((v,k)=>v.eq(x[k]))))pts.push(x);return;}
    for(let i=s;i<H.length;i++){idx.push(i);choose(i+1);idx.pop();}
  })(0);
  const val=x=>dotQ(M.c,x),sg=M.sense==='max'?1:-1;
  let best=null;for(const x of pts){const z=val(x);if(!best||z.cmp(best.z)*sg>0)best={x,z};}
  return {pts,best};
};
LP.graphical=function(M){
  if(M.c.length!==2)return {err:'The graphical method needs exactly 2 variables.'};
  const zero=[Q0,Q0];
  const trivBad=M.cons.map((k,i)=>(!k.a[0].sgn()&&!k.a[1].sgn()&&!LP.sat(k,zero))?i:-1).filter(i=>i>=0);
  const lines=[];M.cons.forEach((k,i)=>{if(k.a[0].sgn()||k.a[1].sgn())lines.push({a:k.a,b:k.b,i});});
  lines.push({a:[Q1,Q0],b:Q0,i:-1},{a:[Q0,Q1],b:Q0,i:-2});
  const pts=[];
  if(!trivBad.length)for(let i=0;i<lines.length;i++)for(let j=i+1;j<lines.length;j++){
    const L1=lines[i],L2=lines[j];const det=L1.a[0].mul(L2.a[1]).sub(L1.a[1].mul(L2.a[0]));
    if(!det.sgn())continue;
    const x=L1.b.mul(L2.a[1]).sub(L2.b.mul(L1.a[1])).div(det),y=L1.a[0].mul(L2.b).sub(L2.a[0].mul(L1.b)).div(det);
    const p=[x,y];if(!LP.feasible(M,p))continue;
    if(!pts.some(q=>q.x[0].eq(x)&&q.x[1].eq(y)))pts.push({x:p});
  }
  pts.forEach(pt=>{pt.on=lines.filter(L=>dotQ(L.a,pt.x).eq(L.b)).map(L=>L.i);pt.z=dotQ(M.c,pt.x);});
  /* order counter-clockwise starting at the lowest-left point */
  if(pts.length>1){
    const cx=pts.reduce((s,p)=>s+p.x[0].num(),0)/pts.length,cy=pts.reduce((s,p)=>s+p.x[1].num(),0)/pts.length;
    pts.forEach(p=>p.ang=Math.atan2(p.x[1].num()-cy,p.x[0].num()-cx));
    pts.sort((a,b)=>a.ang-b.ang);
    let s=0;pts.forEach((p,k)=>{const q=pts[s];if(p.x[0].cmp(q.x[0])<0||(p.x[0].eq(q.x[0])&&p.x[1].cmp(q.x[1])<0))s=k;});
    const rot=pts.splice(0,s);pts.push(...rot);
  }
  let li=0;pts.forEach(p=>{p.name=(!p.x[0].sgn()&&!p.x[1].sgn())?'O':String.fromCharCode(65+li++);});
  /* recession directions (extreme rays of the cone {d>=0 : constraints with b=0}) */
  const cand=[[Q1,Q0],[Q0,Q1]];M.cons.forEach(k=>{if(k.a[0].sgn()||k.a[1].sgn()){cand.push([k.a[1],k.a[0].neg()],[k.a[1].neg(),k.a[0]]);}});
  const rays=[];for(const d of cand){
    if(d[0].sgn()<0||d[1].sgn()<0||(!d[0].sgn()&&!d[1].sgn()))continue;
    if(!M.cons.every(k=>{const s=dotQ(k.a,d).sgn();return k.op==='<='?s<=0:k.op==='>='?s>=0:s===0;}))continue;
    if(!rays.some(r=>r[0].mul(d[1]).eq(r[1].mul(d[0]))))rays.push(d);
  }
  const sg=M.sense==='max'?1:-1;
  const out={pts,rays,lines,trivBad,bounded:!rays.length};
  if(trivBad.length||!pts.length){out.status='infeasible';return out;}
  const upRay=rays.find(d=>dotQ(M.c,d).sgn()*sg>0);
  if(upRay){out.status='unbounded';out.ray=upRay;return out;}
  let best=pts[0];for(const p of pts)if(p.z.cmp(best.z)*sg>0)best=p;
  out.best=best;out.z=best.z;out.opt=pts.filter(p=>p.z.eq(best.z));
  out.flatRay=rays.find(d=>!dotQ(M.c,d).sgn())||null;
  out.status=(out.opt.length>1||out.flatRay)?'alternative':'optimal';
  return out;
};
/* Simplex (Cj - Zj form, as in Indian textbooks) for all-<= problems with b >= 0.
   Entering: most positive Cj-Zj (ties: lowest index). Leaving: minimum ratio (ties: topmost row).
   After 20 iterations Bland's rule is used to rule out cycling. Min Z is solved as Max (-Z). */
LP.simplex=function(M){
  const n=M.c.length,m=M.cons.length;
  if(M.cons.some(k=>k.op!=='<='))return {err:'ge',msg:'The step-through simplex needs every constraint to be ≤ (then the slack variables form the first basis). ≥ and = constraints need artificial variables (Big-M or two-phase).'};
  if(M.cons.some(k=>k.b.sgn()<0))return {err:'neg',msg:'The step-through simplex needs every right-hand side b ≥ 0, so that the all-slack starting solution is feasible.'};
  const isMin=M.sense==='min';
  const names=[...Array.from({length:n},(_,j)=>'x'+(j+1)),...Array.from({length:m},(_,i)=>'s'+(i+1))];
  const cj=[...M.c.map(x=>isMin?x.neg():x),...Array(m).fill(Q0)];
  let A=M.cons.map((k,i)=>[...k.a,...Array.from({length:m},(_,j)=>i===j?Q1:Q0)]);
  let b=M.cons.map(k=>k.b);let basis=M.cons.map((_,i)=>n+i);
  const N=n+m,frames=[];let status=null,bland=false;
  for(let it=0;it<80;it++){
    const zj=Array.from({length:N},(_,j)=>A.reduce((s,r,i)=>s.add(cj[basis[i]].mul(r[j])),Q0));
    const cz=cj.map((c,j)=>c.sub(zj[j]));
    const Z=b.reduce((s,v,i)=>s.add(cj[basis[i]].mul(v)),Q0);
    const snap={A:A.map(r=>r.slice()),b:b.slice(),basis:basis.slice(),zj,cz,Z,enter:-1,leave:-1,ratios:null,bland};
    let e=-1;
    for(let j=0;j<N;j++){if(cz[j].sgn()>0){if(e<0||(!bland&&cz[j].cmp(cz[e])>0))e=j;if(bland)break;}}
    if(e<0){status='optimal';snap.alt=cz.map((v,j)=>(!v.sgn()&&!basis.includes(j))?j:-1).filter(j=>j>=0);frames.push(snap);break;}
    const ratios=A.map((r,i)=>r[e].sgn()>0?b[i].div(r[e]):null);
    snap.enter=e;snap.ratios=ratios;
    let l=-1;ratios.forEach((q,i)=>{if(q&&(l<0||q.cmp(ratios[l])<0||(bland&&q.eq(ratios[l])&&basis[i]<basis[l])))l=i;});
    if(l<0){status='unbounded';frames.push(snap);break;}
    snap.leave=l;snap.tie=ratios.filter(q=>q&&q.eq(ratios[l])).length>1;snap.degen=!ratios[l].sgn();
    frames.push(snap);
    const pv=A[l][e];A=A.map(r=>r.slice());b=b.slice();
    A[l]=A[l].map(v=>v.div(pv));b[l]=b[l].div(pv);
    for(let i=0;i<m;i++)if(i!==l&&A[i][e].sgn()){const f=A[i][e];A[i]=A[i].map((v,j)=>v.sub(f.mul(A[l][j])));b[i]=b[i].sub(f.mul(b[l]));}
    basis=basis.slice();basis[l]=e;
    if(it>=20)bland=true;
  }
  if(!status)return {err:'iter',msg:'The simplex did not finish in 80 iterations.'};
  const last=frames[frames.length-1];
  const x=Array.from({length:N},(_,j)=>{const i=last.basis.indexOf(j);return i>=0?last.b[i]:Q0;});
  const res={names,cj,frames,status,isMin,n,m,x};
  if(status==='optimal'){res.zMax=last.Z;res.z=isMin?last.Z.neg():last.Z;res.alt=last.alt;res.degenerate=last.b.some(v=>!v.sgn());
    res.shadow=last.zj.slice(n).map(v=>isMin?v.neg():v);}
  else res.unboundedVar=last.enter;
  res.anyTie=frames.some(f=>f.tie);res.anyDegenPivot=frames.some(f=>f.degen);
  return res;
};
LP.solve=function(M){
  const out={};
  if(M.c.length===2)out.g=LP.graphical(M);
  const s=LP.simplex(M);if(!s.err)out.s=s;else out.sErr=s;
  if(out.g){out.status=out.g.status;out.z=out.g.z;out.x=out.g.best?out.g.best.x:null;}
  else if(out.s){out.status=out.s.status==='optimal'?(out.s.alt.length?'alternative':'optimal'):'unbounded';out.z=out.s.z;out.x=out.s.status==='optimal'?out.s.x.slice(0,M.c.length):null;}
  else out.status='unsupported';
  return out;
};
NETSOLVE.lpp=LP;

/* ======================================================================
   TRANSPORT core (numbers; costs may be decimals)
   ====================================================================== */
const TR={};
const r9=x=>Math.round(x*1e9)/1e9;
const EPS=1e-9;
TR.balance=function(C,S,D){
  const sS=r9(S.reduce((a,b)=>a+b,0)),sD=r9(D.reduce((a,b)=>a+b,0));
  C=C.map(r=>r.slice());S=S.slice();D=D.slice();let dummy=null;
  if(sS>sD+EPS){const q=r9(sS-sD);C.forEach(r=>r.push(0));D.push(q);dummy={type:'col',q};}
  else if(sD>sS+EPS){const q=r9(sD-sS);C.push(D.map(()=>0));S.push(q);dummy={type:'row',q};}
  return {C,S,D,m:S.length,n:D.length,sS,sD,dummy};
};
const blank=(m,n)=>Array.from({length:m},()=>Array(n).fill(null));
TR.cost=(C,al)=>r9(al.reduce((s,r,i)=>s+r.reduce((t,v,j)=>t+(v?C[i][j]*v:0),0),0));
TR.count=al=>al.reduce((s,r)=>s+r.filter(v=>v!=null&&v>EPS).length,0);
function trAlloc(st,i,j,why,extra){
  const q=r9(Math.min(st.s[i],st.d[j]));st.al[i][j]=r9((st.al[i][j]||0)+q);
  st.s[i]=r9(st.s[i]-q);st.d[j]=r9(st.d[j]-q);
  const rowDone=st.s[i]<=EPS,colDone=st.d[j]<=EPS;
  if(rowDone)st.rows.delete(i);if(colDone)st.cols.delete(j);
  st.steps.push(Object.assign({i,j,q,why,rowDone,colDone,both:rowDone&&colDone&&st.rows.size+st.cols.size>0,al:st.al.map(r=>r.slice()),s:st.s.slice(),d:st.d.slice()},extra||{}));
}
const trState=(B)=>({al:blank(B.m,B.n),s:B.S.slice(),d:B.D.slice(),rows:new Set(B.S.map((_,i)=>i)),cols:new Set(B.D.map((_,j)=>j)),steps:[]});
const trFinish=(B,st,name)=>{const k=TR.count(st.al);return {name,al:st.al,steps:st.steps,cost:TR.cost(B.C,st.al),count:k,need:B.m+B.n-1,degenerate:k<B.m+B.n-1};};
TR.nwcr=function(B){
  const st=trState(B);let i=0,j=0;
  while(i<B.m&&j<B.n){trAlloc(st,i,j,'nw');const last=st.steps[st.steps.length-1];if(last.rowDone)i++;if(last.colDone)j++;}
  return trFinish(B,st,'NWCR');
};
/* least-cost cell among the open cells of the given rows/cols; ties: larger possible allocation, then row-major */
function trBestCell(B,st,rows,cols){
  let best=null;
  for(const i of rows)for(const j of cols){const c=B.C[i][j],q=Math.min(st.s[i],st.d[j]);
    if(!best||c<best.c-EPS||(Math.abs(c-best.c)<=EPS&&(q>best.q+EPS||(Math.abs(q-best.q)<=EPS&&(i<best.i||(i===best.i&&j<best.j))))))best={i,j,c,q};}
  return best;
}
TR.lcm=function(B){
  const st=trState(B);
  while(st.rows.size&&st.cols.size){const b=trBestCell(B,st,[...st.rows].sort((a,b)=>a-b),[...st.cols].sort((a,b)=>a-b));trAlloc(st,b.i,b.j,'min');}
  return trFinish(B,st,'Least cost');
};
TR.vam=function(B){
  const st=trState(B);
  const pen=(costs)=>{const s=costs.slice().sort((a,b)=>a-b);return s.length>1?r9(s[1]-s[0]):null;};
  while(st.rows.size&&st.cols.size){
    const R=[...st.rows].sort((a,b)=>a-b),Cc=[...st.cols].sort((a,b)=>a-b);
    if(R.length===1||Cc.length===1){const b=trBestCell(B,st,R,Cc);trAlloc(st,b.i,b.j,'rest',{rp:null,cp:null});continue;}
    const rp=B.S.map((_,i)=>st.rows.has(i)?pen(Cc.map(j=>B.C[i][j])):null);
    const cp=B.D.map((_,j)=>st.cols.has(j)?pen(R.map(i=>B.C[i][j])):null);
    /* candidate lines: max penalty; ties: smaller least cost in the line, then larger allocation, then rows first, lower index */
    const cands=[];
    R.forEach(i=>{const b=trBestCell(B,st,[i],Cc);cands.push({kind:'row',k:i,p:rp[i],c:b.c,q:b.q,cell:b});});
    Cc.forEach(j=>{const b=trBestCell(B,st,R,[j]);cands.push({kind:'col',k:j,p:cp[j],c:b.c,q:b.q,cell:b});});
    cands.sort((a,b)=>(b.p-a.p)||(a.c-b.c)||(b.q-a.q)||((a.kind==='row'?0:1)-(b.kind==='row'?0:1))||(a.k-b.k));
    const top=cands[0];const tie=cands.filter(x=>Math.abs(x.p-top.p)<=EPS).length>1;
    trAlloc(st,top.cell.i,top.cell.j,'vam',{rp,cp,line:{kind:top.kind,k:top.k,p:top.p},tie});
  }
  return trFinish(B,st,'VAM');
};
/* MODI / u-v method from an initial allocation. Degenerate starts get epsilon (0) cells:
   least-cost cells that do not form a loop, until there are m+n-1 basic cells. */
TR.modi=function(B,al){
  const m=B.m,n=B.n,need=m+n-1;
  let basic=new Map();al.forEach((r,i)=>r.forEach((v,j)=>{if(v!=null&&v>EPS)basic.set(i+','+j,v);}));
  const eps=[];
  if(basic.size<need){
    const par=Array.from({length:m+n},(_,k)=>k);const f=x=>par[x]===x?x:(par[x]=f(par[x]));
    for(const k of basic.keys()){const [i,j]=k.split(',').map(Number);par[f(i)]=f(m+j);}
    const cand=[];for(let i=0;i<m;i++)for(let j=0;j<n;j++)if(!basic.has(i+','+j))cand.push({i,j,c:B.C[i][j]});
    cand.sort((a,b)=>(a.c-b.c)||(a.i-b.i)||(a.j-b.j));
    for(const c of cand){if(basic.size>=need)break;const a=f(c.i),b=f(m+c.j);if(a!==b){par[a]=b;basic.set(c.i+','+c.j,0);eps.push([c.i,c.j]);}}
  }
  const frames=[];let status=null;
  for(let it=0;it<100;it++){
    const u=Array(m).fill(null),v=Array(n).fill(null);u[0]=0;
    const cells=[...basic.keys()].map(k=>k.split(',').map(Number));
    let ch=true;while(ch){ch=false;for(const [i,j] of cells){if(u[i]!=null&&v[j]==null){v[j]=r9(B.C[i][j]-u[i]);ch=true;}else if(v[j]!=null&&u[i]==null){u[i]=r9(B.C[i][j]-v[j]);ch=true;}}}
    const delta=blank(m,n);let e=null;
    for(let i=0;i<m;i++)for(let j=0;j<n;j++)if(!basic.has(i+','+j)){const d=r9(B.C[i][j]-u[i]-v[j]);delta[i][j]=d;if(d<-EPS&&(!e||d<e.d-EPS))e={i,j,d};}
    const fr={basic:new Map(basic),u,v,delta,cost:r9([...basic].reduce((s,[k,x])=>{const [i,j]=k.split(',').map(Number);return s+B.C[i][j]*x;},0))};
    if(!e){status='optimal';fr.alt=[];delta.forEach((r,i)=>r.forEach((d,j)=>{if(d!=null&&Math.abs(d)<=EPS)fr.alt.push([i,j]);}));frames.push(fr);break;}
    /* loop: path in the basic tree from row e.i to column e.j */
    const adj=new Map();const add=(a,b,c)=>{if(!adj.has(a))adj.set(a,[]);adj.get(a).push([b,c]);};
    for(const [i,j] of cells){add('r'+i,'c'+j,[i,j]);add('c'+j,'r'+i,[i,j]);}
    const prev=new Map([['r'+e.i,null]]);const q=['r'+e.i];
    while(q.length){const x=q.shift();if(x==='c'+e.j)break;for(const [y,cell] of adj.get(x)||[])if(!prev.has(y)){prev.set(y,[x,cell]);q.push(y);}}
    const path=[];let x='c'+e.j;while(prev.get(x)){const [px,cell]=prev.get(x);path.push(cell);x=px;}
    /* path lists cells from column e.j back to row e.i: signs alternate -,+,-,... */
    const loop=[{i:e.i,j:e.j,s:'+'}];path.forEach((c,k)=>loop.push({i:c[0],j:c[1],s:k%2===0?'-':'+'}));
    const minus=loop.filter(c=>c.s==='-');let theta=Infinity;minus.forEach(c=>{theta=Math.min(theta,basic.get(c.i+','+c.j));});
    const leave=minus.find(c=>Math.abs(basic.get(c.i+','+c.j)-theta)<=EPS);
    Object.assign(fr,{enter:e,loop,theta,leave});frames.push(fr);
    const nb=new Map(basic);
    for(const c of loop){const k=c.i+','+c.j;nb.set(k,r9((nb.get(k)||0)+(c.s==='+'?theta:-theta)));}
    nb.delete(leave.i+','+leave.j);basic=nb;
  }
  if(!status)return {err:'MODI did not converge in 100 iterations.'};
  const last=frames[frames.length-1];
  return {frames,eps,cost:last.cost,alt:last.alt.length>0,iterations:frames.length-1,degenerateStart:eps.length>0,degeneratePivot:frames.some(f=>f.theta===0)};
};
TR.solve=function(C,S,D,start){
  const B=TR.balance(C,S,D);
  const init={nwcr:TR.nwcr(B),lcm:TR.lcm(B),vam:TR.vam(B)};
  const st=init[start||'vam'];
  const modi=TR.modi(B,st.al);
  return {B,init,start:start||'vam',modi,optimum:modi.cost};
};
NETSOLVE.transport=TR;

/* ======================================================================
   ASSIGN core: Hungarian method.  Entries: numbers, or null for a forbidden cell.
   ====================================================================== */
const AS={};
const z0=x=>Math.abs(x)<=1e-9;
AS.match=function(M){ /* maximum matching on zero cells (Kuhn), rows in order */
  const n=M.length,mc=Array(n).fill(-1),mr=Array(n).fill(-1);
  const tryRow=(i,seen)=>{for(let j=0;j<n;j++)if(z0(M[i][j])&&!seen[j]){seen[j]=1;if(mc[j]<0||tryRow(mc[j],seen)){mc[j]=i;mr[i]=j;return true;}}return false;};
  for(let i=0;i<n;i++)tryRow(i,[]);
  return mr;
};
AS.cover=function(M,mr){ /* Konig: tick unassigned rows, then columns with zeros in ticked rows, then rows assigned in ticked columns */
  const n=M.length,rt=Array(n).fill(false),ct=Array(n).fill(false);const mc=Array(n).fill(-1);mr.forEach((j,i)=>{if(j>=0)mc[j]=i;});
  const q=[];for(let i=0;i<n;i++)if(mr[i]<0){rt[i]=true;q.push(i);}
  while(q.length){const i=q.shift();for(let j=0;j<n;j++)if(z0(M[i][j])&&!ct[j]){ct[j]=true;const r=mc[j];if(r>=0&&!rt[r]){rt[r]=true;q.push(r);}}}
  /* lines: through unticked rows and ticked columns */
  return {rt,ct,rowLine:rt.map(t=>!t),colLine:ct.slice(),lines:rt.filter(t=>!t).length+ct.filter(Boolean).length};
};
AS.countOpt=function(M,cap){
  const n=M.length,used=Array(n).fill(false),sols=[];let cnt=0;const cur=[];
  (function go(i){if(cnt>=cap)return;if(i===n){cnt++;if(sols.length<6)sols.push(cur.slice());return;}for(let j=0;j<n;j++)if(!used[j]&&z0(M[i][j])){used[j]=true;cur.push(j);go(i+1);cur.pop();used[j]=false;}})(0);
  return {count:cnt,sols};
};
AS.solve=function(A,sense){
  const r=A.length,c=A[0].length,n=Math.max(r,c);const isMax=sense==='max';
  const P=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>(i<r&&j<c)?A[i][j]:0));
  const dummyRows=n-r,dummyCols=n-c;
  const frames=[];const cp=M=>M.map(x=>x.slice());
  frames.push({k:'orig',M:cp(P)});
  let M;let mx=null;
  if(isMax){mx=-Infinity;P.forEach(row=>row.forEach(v=>{if(v!=null&&v>mx)mx=v;}));M=P.map(row=>row.map(v=>v==null?Infinity:r9(mx-v)));frames.push({k:'max',M:cp(M),mx});}
  else M=P.map(row=>row.map(v=>v==null?Infinity:v));
  const rmin=M.map(row=>Math.min(...row));
  if(rmin.some(v=>v===Infinity))return {err:'Every cell of row '+(rmin.findIndex(v=>v===Infinity)+1)+' is forbidden, so no assignment exists.'};
  M=M.map((row,i)=>row.map(v=>v===Infinity?v:r9(v-rmin[i])));frames.push({k:'row',M:cp(M),red:rmin});
  const cmin=M[0].map((_,j)=>Math.min(...M.map(row=>row[j])));
  if(cmin.some(v=>v===Infinity))return {err:'Every cell of column '+(cmin.findIndex(v=>v===Infinity)+1)+' is forbidden, so no assignment exists.'};
  M=M.map(row=>row.map((v,j)=>v===Infinity?v:r9(v-cmin[j])));frames.push({k:'col',M:cp(M),red:cmin});
  let mr;
  for(let it=0;it<200;it++){
    mr=AS.match(M);const cv=AS.cover(M,mr);
    frames.push({k:'cover',M:cp(M),mr:mr.slice(),cv});
    if(cv.lines>=n)break;
    let k=Infinity;for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(!cv.rowLine[i]&&!cv.colLine[j])k=Math.min(k,M[i][j]);
    if(k===Infinity)return {err:'The forbidden cells leave no complete assignment.'};
    const ch=[];
    M=M.map((row,i)=>row.map((v,j)=>{if(v===Infinity)return v;if(!cv.rowLine[i]&&!cv.colLine[j]){ch.push([i,j,'-']);return r9(v-k);}if(cv.rowLine[i]&&cv.colLine[j]){ch.push([i,j,'+']);return r9(v+k);}return v;}));
    frames.push({k:'adjust',M:cp(M),kmin:k,ch,cv});
  }
  const pairs=mr.map((j,i)=>({i,j,v:P[i][j],dummy:i>=r||j>=c}));
  const total=r9(pairs.reduce((s,p)=>s+(p.dummy?0:p.v),0));
  const cnt=AS.countOpt(M,1000);
  frames.push({k:'final',M:cp(M),mr:mr.slice()});
  return {n,r,c,dummyRows,dummyCols,isMax,mx,P,frames,pairs,total,count:cnt.count,sols:cnt.sols,iterations:frames.filter(f=>f.k==='adjust').length};
};
AS.brute=function(A,sense){
  const r=A.length,c=A[0].length,n=Math.max(r,c),isMax=sense==='max';
  const P=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>(i<r&&j<c)?A[i][j]:0));
  let best=null;const used=Array(n).fill(false);
  (function go(i,s){if(i===n){if(best===null||(isMax?s>best:s<best))best=s;return;}for(let j=0;j<n;j++)if(!used[j]&&P[i][j]!=null){used[j]=true;go(i+1,s+P[i][j]);used[j]=false;}})(0,0);
  return best==null?null:r9(best);
};
NETSOLVE.assign=AS;

/* ======================================================================
   UI (browser only)
   ====================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=a=>a[Math.floor(Math.random()*a.length)];
function debounce(fn,ms){let t;return (...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
const SUB=n=>String(n).replace(/\d/g,d=>'₀₁₂₃₄₅₆₇₈₉'[d]);
const numRe=/^[+-]?(\d+\.?\d*|\.\d+)$/;
const pnum=s=>{s=String(s==null?'':s).trim().replace(/[−–]/g,'-');return numRe.test(s)?parseFloat(s):null;};
const fmt=x=>x==null?'':x===Infinity?'M':(Math.abs(x-Math.round(x))<1e-9?String(Math.round(x)):String(+x.toFixed(4))).replace('-','−');
const qs=q=>q.str().replace('-','−');
const qpt=x=>'('+x.map(qs).join(', ')+')';
/* generic step-through control: frames 0..n-1, render(i) sets the whole state for step i */
function stepper(host,p,n,render,start){
  let i=0,timer=null;
  host.innerHTML=`<div class="${p}-stp"><button type="button" class="btn sm" data-s="rs" aria-label="Back to the first step">↺</button><button type="button" class="btn sm" data-s="pv">◀ Prev</button><button type="button" class="btn sm primary" data-s="pl">▶ Play</button><button type="button" class="btn sm" data-s="nx">Next ▶</button><input type="range" min="0" max="${Math.max(0,n-1)}" value="0" aria-label="Jump to step"><span class="${p}-stpc" aria-live="polite"></span></div>`;
  const pl=host.querySelector('[data-s=pl]'),rg=host.querySelector('input'),ct=host.querySelector(`.${p}-stpc`);
  const stop=()=>{clearTimeout(timer);timer=null;pl.textContent='▶ Play';};
  const go=k=>{i=Math.max(0,Math.min(n-1,k));rg.value=i;ct.textContent=`Step ${i+1} of ${n}`;render(i);};
  const tick=()=>{if(!document.body.contains(host)){stop();return;}if(i>=n-1){stop();return;}go(i+1);timer=setTimeout(tick,1800);};
  host.querySelector('[data-s=rs]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-s=pv]').onclick=()=>{stop();go(i-1);};
  host.querySelector('[data-s=nx]').onclick=()=>{stop();go(i+1);};
  pl.onclick=()=>{if(timer){stop();return;}if(i>=n-1)go(0);pl.textContent='❚❚ Pause';timer=setTimeout(tick,900);};
  rg.oninput=()=>{stop();go(+rg.value);};
  go(start==null?0:start);return {go,stop,get i(){return i;}};
}
function tabs(host,names,cur,onPick){
  host.innerHTML=names.map((nm,k)=>`<button type="button" aria-pressed="${k===cur}" data-t="${k}">${nm}</button>`).join('');
  host.querySelectorAll('button').forEach(b=>b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(+b.dataset.t);});
}
/* shared skeleton: inputs, answer cards, tabs, pane */
function shell(stage,P,inputs,hint){
  stage.style.padding='0';
  stage.innerHTML=`<div class="${P}"><div class="${P}-in">${inputs}<p class="${P}-hint">${hint}</p><div class="${P}-err" role="alert" hidden></div></div><div class="${P}-ans" aria-live="polite"></div><div class="${P}-tabs" role="group" aria-label="Working"></div><div class="${P}-pane"></div></div>`;
  const $=s=>stage.querySelector(s);
  const root=$(`.${P}`),err=$(`.${P}-err`);
  return {$,root,err,ans:$(`.${P}-ans`),tabHost:$(`.${P}-tabs`),pane:$(`.${P}-pane`),
    fail(msg){err.hidden=false;err.textContent=msg;root.classList.add(`${P}-stale`);},
    okay(){err.hidden=true;root.classList.remove(`${P}-stale`);}};
}
const card=(P,k,v,sub,cls)=>`<div class="${P}-card${cls?' '+P+'-'+cls:''}"><span class="${P}-k">${k}</span><b class="${P}-big">${v}</b>${sub?`<span>${sub}</span>`:''}</div>`;
/* editable number matrix with row/col add/remove */
function matrixEditor(host,P,o){
  /* o: {get:()=>state, rows, cols, rowName(i), colName(j), cell(i,j)->value, setCell, extraCol?, extraRow?, onChange} */
  function render(){
    const s=o.get(),m=o.rows(),n=o.cols();
    let h=`<div class="${P}-scroll"><table class="${P}-ed"><thead><tr><th></th>${Array.from({length:n},(_,j)=>`<th scope="col">${E(o.colName(j))}</th>`).join('')}${o.extraCol?`<th scope="col">${E(o.extraCol.name)}</th>`:''}</tr></thead><tbody>`;
    for(let i=0;i<m;i++){h+=`<tr><th scope="row">${E(o.rowName(i))}</th>`;for(let j=0;j<n;j++)h+=`<td><input type="text" inputmode="decimal" data-k="${o.key}-${i}-${j}" data-i="${i}" data-j="${j}" value="${E(o.cell(i,j))}" aria-label="${E(o.rowName(i)+', '+o.colName(j))}" spellcheck="false" autocomplete="off"></td>`;
      if(o.extraCol)h+=`<td class="${P}-edx"><input type="text" inputmode="decimal" data-k="${o.extraCol.key}-${i}" data-x="c" data-i="${i}" value="${E(o.extraCol.get(i))}" aria-label="${E(o.extraCol.name+' '+o.rowName(i))}" spellcheck="false" autocomplete="off"></td>`;h+='</tr>';}
    if(o.extraRow){h+=`<tr class="${P}-edxr"><th scope="row">${E(o.extraRow.name)}</th>`;for(let j=0;j<n;j++)h+=`<td><input type="text" inputmode="decimal" data-k="${o.extraRow.key}-${j}" data-x="r" data-j="${j}" value="${E(o.extraRow.get(j))}" aria-label="${E(o.extraRow.name+' '+o.colName(j))}" spellcheck="false" autocomplete="off"></td>`;if(o.extraCol)h+='<td></td>';h+='</tr>';}
    h+=`</tbody></table></div><div class="${P}-edb"><button type="button" class="btn sm" data-act="addr" ${m>=o.max?'disabled':''}>+ ${E(o.rowWord)}</button><button type="button" class="btn sm" data-act="delr" ${m<=o.min?'disabled':''}>− ${E(o.rowWord)}</button><button type="button" class="btn sm" data-act="addc" ${n>=o.max?'disabled':''}>+ ${E(o.colWord)}</button><button type="button" class="btn sm" data-act="delc" ${n<=o.min?'disabled':''}>− ${E(o.colWord)}</button></div>`;
    host.innerHTML=h;
    const ch=debounce(()=>o.onChange(),200);
    host.querySelectorAll('input').forEach(inp=>inp.oninput=()=>{const x=inp.dataset.x;if(x==='c')o.extraCol.set(+inp.dataset.i,inp.value);else if(x==='r')o.extraRow.set(+inp.dataset.j,inp.value);else o.setCell(+inp.dataset.i,+inp.dataset.j,inp.value);ch();});
    host.querySelectorAll('[data-act]').forEach(b=>b.onclick=()=>{o.resize(b.dataset.act);render();o.onChange();});
  }
  return {render};
}

/* ====================================================================== truthtable UI */
ANIM.register('truthtable',{title:'Truth table, normal forms and equivalence',steps:false,
 caption:'Type a propositional formula. The solver builds the full truth table column by column, classifies it, writes the DNF and CNF from minterms and maxterms, and checks equivalence with a second formula.',
 build(stage){
  const P='truthtable';
  const EX=[
    {nm:'Modus ponens (tautology)',f:'((p -> q) & p) -> q',g:''},
    {nm:'p → q vs contrapositive',f:'p -> q',g:'~q -> ~p'},
    {nm:'p → q vs converse',f:'p -> q',g:'q -> p'},
    {nm:'De Morgan',f:'~(p & q)',g:'~p | ~q'},
    {nm:'Exportation (3 variables)',f:'(p & q) -> r',g:'p -> (q -> r)'},
    {nm:'A contradiction',f:'(p | q) & ~p & ~q',g:''},
    {nm:'XOR vs biconditional',f:'p ^ q',g:'~(p <-> q)'},
    {nm:'Hypothetical syllogism',f:'((p -> q) & (q -> r)) -> (p -> r)',g:''},
    {nm:'Distributive law',f:'p | (q & r)',g:'(p | q) & (p | r)'}];
  const PAIRS=[['p -> q','~p | q'],['~(p | q)','~p & ~q'],['p -> (q | r)','(p -> q) | (p -> r)'],['(p -> r) & (q -> r)','(p | q) -> r'],['(p -> q) -> r','p -> (q -> r)'],['p <-> q','(p & q) | (~p & ~q)'],['p & (q | r)','(p & q) | r'],['~(p -> q)','p & ~q'],['p | (p & q)','p']];
  const st={f:EX[0].f,g:EX[0].g,order:'tf',vals:'TF',tab:0};
  const S=shell(stage,P,`
     <label class="${P}-lab ${P}-wide">Formula<input type="text" data-k="f" spellcheck="false" autocomplete="off"></label>
     <label class="${P}-lab ${P}-wide">Compare with (optional, for the equivalence check)<input type="text" data-k="g" spellcheck="false" autocomplete="off" placeholder="e.g. ~p | q"></label>
     <label class="${P}-lab">Row order<select data-k="order"><option value="tf">T T T first (textbook)</option><option value="ft">F F F first (binary 000…)</option></select></label>
     <label class="${P}-lab">Show values as<select data-k="vals"><option value="TF">T / F</option><option value="10">1 / 0</option></select></label>
     <div class="${P}-btns"><label class="${P}-lab">Example<select data-k="ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" data-act="rand">🎲 Random example</button></div>`,
    `Type <code>~ ¬ !</code> for NOT, <code>&amp; ∧ and</code>, <code>| ∨ or</code>, <code>-&gt; → implies</code>, <code>&lt;-&gt; ↔ iff</code>, <code>^ ⊕ xor</code> (also <code>↑</code> NAND, <code>↓</code> NOR). <code>T</code>/<code>F</code> or <code>1</code>/<code>0</code> are constants. <b>Precedence:</b> ¬ &gt; ∧ &gt; ∨, ⊕ &gt; → &gt; ↔; → groups to the right (p → q → r = p → (q → r)). Use brackets when unsure.`);
  const {$}=S;
  $('[data-k=f]').value=st.f;$('[data-k=g]').value=st.g;
  const TABS=['Truth table','DNF &amp; CNF','Equivalence check'];
  tabs(S.tabHost,TABS,st.tab,k=>{st.tab=k;renderPane();});
  let R=null,EQ=null;
  const V=b=>st.vals==='TF'?(b?'T':'F'):(b?'1':'0');
  const order=n=>{const a=Array.from({length:n},(_,k)=>k);return st.order==='tf'?a.reverse():a;};
  const code=s=>`<code class="${P}-f">${E(s)}</code>`;
  const RULE={not:'¬A flips the value of A.',and:'A ∧ B is T only when both A and B are T.',or:'A ∨ B is F only when both A and B are F.',imp:'A → B is F only when A is T and B is F (a true premise with a false conclusion); otherwise it is T.',iff:'A ↔ B is T exactly when A and B have the same value.',xor:'A ⊕ B is T exactly when A and B differ.',nand:'A ↑ B = ¬(A ∧ B): F only when both are T.',nor:'A ↓ B = ¬(A ∨ B): T only when both are F.'};
  const CLS={tautology:'Tautology',contradiction:'Contradiction',contingency:'Contingency'};
  function compute(){
    R=TT.solve(st.f);
    if(R.err){S.fail('Formula: '+R.err);R=null;return;}
    EQ=st.g.trim()?TT.equiv(st.f,st.g):null;
    if(EQ&&EQ.err){S.fail(EQ.err.replace('Formula 2','Compare with'));EQ=null;return;}
    S.okay();renderAns();renderPane();
  }
  const rowTxt=(vars,r)=>vars.map((v,k)=>`${v} = ${V((r>>(vars.length-1-k))&1)}`).join(', ');
  function renderAns(){
    const cls=R.cls;
    let h=card(P,'Classification',CLS[cls],cls==='tautology'?`T in all ${R.R} rows`:cls==='contradiction'?`F in all ${R.R} rows`:`T in ${R.nT} of ${R.R} rows (satisfiable, not valid)`,cls==='tautology'?'good':cls==='contradiction'?'badc':'');
    h+=card(P,'Minterms (T rows)',R.n?(R.minterms.length?`Σm(${R.minterms.join(', ')})`:'none'):'—',R.n?`variables ${R.vars.join(', ')} (${R.vars[0]} is the most significant bit)`:'no variables');
    h+=card(P,'Maxterms (F rows)',R.n?(R.maxterms.length?`ΠM(${R.maxterms.join(', ')})`:'none'):'—');
    if(EQ)h+=card(P,'Equivalence',EQ.equivalent?'Equivalent ✓':'Not equivalent ✗',EQ.equivalent?`same value in all ${EQ.R} rows`:`they differ in ${EQ.diff.length} row${EQ.diff.length>1?'s':''}, e.g. ${E(rowTxt(EQ.vars,EQ.diff[0]))}`,EQ.equivalent?'good':'badc');
    S.ans.innerHTML=h;
  }
  function renderPane(){if(!R){S.pane.innerHTML='';return;}[paneTable,paneNF,paneEq][st.tab]();}
  function paneTable(){
    const {vars,cols,n}=R;const rows=order(R.R);const frames=1+cols.length;
    S.pane.innerHTML=`<p class="${P}-res">Parsed as ${code(R.label)}</p>
      <p class="${P}-conv">Every sub-formula gets its own column, innermost first. Rows are numbered by the binary value of the variables with F = 0 and T = 1 (${E(vars[0]||'')} is the most significant bit); that number is the minterm/maxterm index.</p>
      <div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><div class="${P}-scroll"><table class="${P}-tbl ${P}-tt"></table></div>`;
    const tbl=S.pane.querySelector(`.${P}-tt`),cap=S.pane.querySelector(`.${P}-cap`);
    const resIdx=cols.length?cols.length-1:-1;
    function show(i){
      const head=`<thead><tr><th>#</th>${vars.map(v=>`<th class="${P}-v">${E(v)}</th>`).join('')}${cols.map((c,k)=>`<th class="${k<i?'':P+'-fut'}${k===i-1?' '+P+'-cur':''}${k===resIdx?' '+P+'-resh':''}">${E(c.label)}</th>`).join('')}</tr></thead>`;
      const body=rows.map(r=>`<tr><td class="${P}-idx">${r}</td>${vars.map((v,k)=>`<td class="${P}-v">${V((r>>(n-1-k))&1)}</td>`).join('')}${cols.map((c,k)=>{const vis=k<i;const val=c.vals[r];return `<td class="${vis?(val?P+'-t':P+'-fv'):P+'-fut'}${k===i-1?' '+P+'-cur':''}${k===resIdx&&vis?' '+P+'-resc':''}">${vis?V(val):''}</td>`;}).join('')}</tr>`).join('');
      tbl.innerHTML=head+'<tbody>'+body+'</tbody>';
      if(i===0){cap.innerHTML=n?`<b>${n} variable${n>1?'s':''}</b> give 2<sup>${n}</sup> = <b>${R.R} rows</b>. List every combination of ${E(vars.join(', '))}${st.order==='tf'?', starting from all T (the textbook order)':', counting up in binary from all F'}.${cols.length?'':` The formula is just ${code(R.label)}, so this is its truth table: <b>${CLS[R.cls]}</b>.`}`:`The formula has no variables: its value is <b>${V(R.res[0])}</b>.`;return;}
      const c=cols[i-1],nd=c.node;const cnt=c.vals.filter(Boolean).length;
      let t=`<b>Column ${i}:</b> ${code(c.label)}. `;
      if(nd.t==='not')t+=`With A = ${code(TT.label(nd.a))}: ${RULE.not}`;
      else t+=`With A = ${code(TT.label(nd.a))} and B = ${code(TT.label(nd.b))}: ${RULE[nd.op]}`;
      t+=` It is T in ${cnt} of ${R.R} rows.`;
      if(i===frames-1)t+=` This is the whole formula, so it is a <b>${CLS[R.cls].toLowerCase()}</b>.`;
      cap.innerHTML=t;
    }
    stepper(S.pane.querySelector(`.${P}-sh`),P,frames,show,frames-1);
  }
  function paneNF(){
    const {vars,n}=R;
    if(!n){S.pane.innerHTML=`<p class="${P}-res">The formula has no variables; it is simply ${V(R.res[0])}.</p>`;return;}
    const lit=(r,forMax)=>vars.map((v,k)=>{const b=(r>>(n-1-k))&1;return (forMax?b:!b)?'¬'+v:v;});
    const mt=R.minterms.map(r=>`<tr><td>m${SUB(r)}</td><td class="${P}-mono">${vars.map((v,k)=>V((r>>(n-1-k))&1)).join(' ')}</td><td class="${P}-mono">${E(TT.minterm(vars,r))}</td></tr>`).join('');
    const Mt=R.maxterms.map(r=>`<tr><td>M${SUB(r)}</td><td class="${P}-mono">${vars.map((v,k)=>V((r>>(n-1-k))&1)).join(' ')}</td><td class="${P}-mono">${E(TT.maxterm(vars,r))}</td></tr>`).join('');
    S.pane.innerHTML=`<h4 class="${P}-h">Disjunctive normal form (sum of minterms)</h4>
      <p class="${P}-conv">For each row where the formula is <b>T</b>, write a minterm: each variable as it is if it is T, negated if it is F, joined with ∧. OR the minterms together.</p>
      ${R.minterms.length?`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Minterm</th><th>${E(vars.join(' '))}</th><th>Term</th></tr></thead><tbody>${mt}</tbody></table></div>`:''}
      <p class="${P}-res"><b>DNF</b> = ${R.minterms.length?code(R.dnf):`<b>F</b>: no row is T, so there are no minterms (a contradiction has an empty DNF).`}${R.minterms.length?` = Σm(${R.minterms.join(', ')})`:''}</p>
      <h4 class="${P}-h">Conjunctive normal form (product of maxterms)</h4>
      <p class="${P}-conv">For each row where the formula is <b>F</b>, write a maxterm: each variable as it is if it is F, negated if it is T, joined with ∨. AND the maxterms together. Each maxterm is F only on its own row.</p>
      ${R.maxterms.length?`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Maxterm</th><th>${E(vars.join(' '))}</th><th>Clause</th></tr></thead><tbody>${Mt}</tbody></table></div>`:''}
      <p class="${P}-res"><b>CNF</b> = ${R.maxterms.length?code(R.cnf):`<b>T</b>: no row is F, so there are no maxterms (a tautology has an empty CNF).`}${R.maxterms.length?` = ΠM(${R.maxterms.join(', ')})`:''}</p>
      <p class="${P}-mut">Check: ${R.minterms.length} minterms + ${R.maxterms.length} maxterms = ${R.R} rows. The missing minterm indices are exactly the maxterm indices. These are the <i>full</i> (canonical) forms; simplify them with the laws of logic or a K-map.</p>`;
  }
  function paneEq(){
    if(!st.g.trim()){
      S.pane.innerHTML=`<p class="${P}-res">Type a second formula in <b>Compare with</b> to check whether it is logically equivalent to ${code(R.label)}.</p><p class="${P}-conv">Two formulas are equivalent (A ≡ B) when they have the same truth value in every row, that is, when A ↔ B is a tautology.</p><p><button type="button" class="btn sm" data-act="tryeq">Load a random law to check</button></p>`;
      S.pane.querySelector('[data-act=tryeq]').onclick=()=>{const p=pick(PAIRS);st.f=p[0];st.g=p[1];$('[data-k=f]').value=st.f;$('[data-k=g]').value=st.g;compute();};
      return;}
    if(!EQ){S.pane.innerHTML='';return;}
    const {vars,a,b,diff}=EQ;const n=vars.length;const rows=order(EQ.R);
    const body=rows.map(r=>{const d=a[r]!==b[r];return `<tr class="${d?P+'-diff':''}"><td class="${P}-idx">${r}</td>${vars.map((v,k)=>`<td class="${P}-v">${V((r>>(n-1-k))&1)}</td>`).join('')}<td class="${a[r]?P+'-t':P+'-fv'}">${V(a[r])}</td><td class="${b[r]?P+'-t':P+'-fv'}">${V(b[r])}</td><td>${d?'<b>✗ differ</b>':'✓'}</td></tr>`;}).join('');
    const ce=diff.length?diff[0]:null;
    S.pane.innerHTML=`<p class="${P}-res">F₁ = ${code(EQ.l1)} &nbsp; F₂ = ${code(EQ.l2)}<br>${EQ.equivalent?`<span class="${P}-ok">✓ Equivalent:</span> F₁ ≡ F₂, the columns agree in all ${EQ.R} rows, so F₁ ↔ F₂ is a tautology.`:`<span class="${P}-bad">✗ Not equivalent.</span> Counterexample: <b>${E(rowTxt(vars,ce))}</b> gives F₁ = ${V(a[ce])} but F₂ = ${V(b[ce])}.`}</p>
      <p class="${P}-conv">One-way checks: F₁ ⇒ F₂ (every row with F₁ = T has F₂ = T): <b>${EQ.f1ImpF2?'yes':'no'}</b>. F₂ ⇒ F₁: <b>${EQ.f2ImpF1?'yes':'no'}</b>. Variables missing from one formula are simply ignored by it.</p>
      <div class="${P}-scroll"><table class="${P}-tbl ${P}-tt"><thead><tr><th>#</th>${vars.map(v=>`<th class="${P}-v">${E(v)}</th>`).join('')}<th>F₁</th><th>F₂</th><th>Same?</th></tr></thead><tbody>${body}</tbody></table></div>`;
  }
  $('[data-k=f]').oninput=debounce(e=>{st.f=e.target.value;compute();},250);
  $('[data-k=g]').oninput=debounce(e=>{st.g=e.target.value;compute();},250);
  $('[data-k=order]').onchange=e=>{st.order=e.target.value;renderPane();};
  $('[data-k=vals]').onchange=e=>{st.vals=e.target.value;renderAns();renderPane();};
  $('[data-k=ex]').onchange=e=>{const x=EX[+e.target.value];if(!x)return;st.f=x.f;st.g=x.g;$('[data-k=f]').value=st.f;$('[data-k=g]').value=st.g;compute();};
  function randFormula(d,vars){if(d===0||Math.random()<0.2)return (Math.random()<0.3?'~':'')+pick(vars);const op=pick(['&','|','->','->','<->','^']);const s='('+randFormula(d-1,vars)+' '+op+' '+randFormula(d-1,vars)+')';return Math.random()<0.2?'~'+s:s;}
  $('[data-act=rand]').onclick=()=>{
    if(Math.random()<0.5){const p=pick(PAIRS);st.f=p[0];st.g=p[1];}
    else{const vars=Math.random()<0.5?['p','q']:['p','q','r'];let f;do{f=randFormula(3,vars);}while(TT.solve(f).n<2);st.f=f.replace(/^\((.*)\)$/,'$1');st.g='';}
    $('[data-k=f]').value=st.f;$('[data-k=g]').value=st.g;$('[data-k=ex]').value='';compute();};
  compute();
 }});

/* ====================================================================== lpp UI */
ANIM.register('lpp',{title:'Linear programming solver',steps:false,
 caption:'Enter a 2-variable LPP for the graphical method (constraint lines, shaded feasible region, corner points), or up to 4 variables with ≤ constraints for the simplex tableau step-through.',
 build(stage){
  const P='lpp';
  const mk=(sense,c,rows)=>({sense,n:c.length,c:c.map(String),rows:rows.map(([a,op,b])=>({a:a.map(String),op,b:String(b)}))});
  const EX=[
    {nm:'Max, ≤ constraints (Hillier)',...mk('max',[3,5],[[[1,0],'<=',4],[[0,2],'<=',12],[[3,2],'<=',18]])},
    {nm:'Max with 4 constraints (Taha)',...mk('max',[5,4],[[[6,4],'<=',24],[[1,2],'<=',6],[[-1,1],'<=',1],[[0,1],'<=',2]])},
    {nm:'Min, ≥ constraints (diet)',...mk('min',[2,3],[[[1,1],'>=',4],[[1,3],'>=',6]])},
    {nm:'Alternative optima',...mk('max',[2,4],[[[1,2],'<=',5],[[1,1],'<=',4]])},
    {nm:'Unbounded solution',...mk('max',[2,1],[[[1,-1],'<=',1],[[1,0],'>=',2]])},
    {nm:'Infeasible',...mk('max',[1,1],[[[1,1],'<=',1],[[1,1],'>=',3]])},
    {nm:'Equality constraint',...mk('max',[1,2],[[[1,1],'=',4],[[1,0],'<=',3],[[0,1],'<=',3]])},
    {nm:'Degenerate (tie in ratio)',...mk('max',[3,9],[[[1,4],'<=',8],[[1,2],'<=',4]])},
    {nm:'3 variables (simplex, Taha)',...mk('max',[3,2,5],[[[1,2,1],'<=',430],[[3,0,2],'<=',460],[[1,4,0],'<=',420]])},
    {nm:'4 variables (simplex)',...mk('max',[2,3,1,4],[[[1,1,1,1],'<=',10],[[2,1,0,3],'<=',18],[[0,1,2,1],'<=',12]])}];
  const st=JSON.parse(JSON.stringify(EX[0]));st.tab=0;delete st.nm;
  const XN=j=>'x'+SUB(j+1);
  const OPS={'<=':'≤','>=':'≥','=':'='};
  const S=shell(stage,P,`
     <div class="${P}-wide ${P}-obj"><label class="${P}-lab">Objective<select data-k="sense"><option value="max">Maximise</option><option value="min">Minimise</option></select></label>
       <label class="${P}-lab">Variables<select data-k="n"><option>2</option><option>3</option><option>4</option></select></label></div>
     <div class="${P}-wide ${P}-form"></div>
     <div class="${P}-btns"><label class="${P}-lab">Example<select data-k="ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" data-act="rand">🎲 Random example</button></div>`,
    `x₁, x₂, … ≥ 0 is always assumed. Coefficients may be integers, decimals or fractions such as <code>3/2</code>; negatives are fine. Up to 6 constraints. The graphical method needs 2 variables; the simplex step-through needs ≤ constraints with b ≥ 0.`);
  const {$}=S;const form=$(`.${P}-form`);
  let res=null,M=null,tabNames=[];
  function renderForm(){
    const n=st.n;
    let h=`<div class="${P}-scroll"><table class="${P}-ed"><tbody><tr class="${P}-zrow"><th scope="row">Z =</th>${st.c.map((v,j)=>`<td><input type="text" inputmode="decimal" data-k="c-${j}" data-c="${j}" value="${E(v)}" aria-label="Objective coefficient of ${XN(j)}" spellcheck="false" autocomplete="off"></td><td class="${P}-xv">${XN(j)}${j<n-1?' +':''}</td>`).join('')}<td></td><td></td><td></td></tr>`;
    st.rows.forEach((r,i)=>{h+=`<tr><th scope="row">L${i+1}</th>${r.a.map((v,j)=>`<td><input type="text" inputmode="decimal" data-k="a-${i}-${j}" data-i="${i}" data-j="${j}" value="${E(v)}" aria-label="Constraint ${i+1}, coefficient of ${XN(j)}" spellcheck="false" autocomplete="off"></td><td class="${P}-xv">${XN(j)}${j<n-1?' +':''}</td>`).join('')}
      <td><select data-k="op-${i}" data-i="${i}" aria-label="Constraint ${i+1} sign">${Object.keys(OPS).map(o=>`<option value="${o}" ${o===r.op?'selected':''}>${OPS[o]}</option>`).join('')}</select></td>
      <td><input type="text" inputmode="decimal" data-k="b-${i}" data-b="${i}" value="${E(r.b)}" aria-label="Constraint ${i+1} right-hand side" spellcheck="false" autocomplete="off"></td>
      <td><button type="button" class="btn sm ${P}-del" data-del="${i}" aria-label="Remove constraint ${i+1}" ${st.rows.length<=1?'disabled':''}>✕</button></td></tr>`;});
    h+=`</tbody></table></div><div class="${P}-edb"><button type="button" class="btn sm" data-act="addrow" ${st.rows.length>=6?'disabled':''}>+ Add constraint</button></div>`;
    form.innerHTML=h;
    const ch=debounce(compute,220);
    form.querySelectorAll('input').forEach(inp=>inp.oninput=()=>{const d=inp.dataset;if(d.c!=null)st.c[+d.c]=inp.value;else if(d.b!=null)st.rows[+d.b].b=inp.value;else st.rows[+d.i].a[+d.j]=inp.value;ch();});
    form.querySelectorAll('select').forEach(s=>s.onchange=()=>{st.rows[+s.dataset.i].op=s.value;compute();});
    form.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{st.rows.splice(+b.dataset.del,1);renderForm();compute();});
    form.querySelector('[data-act=addrow]').onclick=()=>{st.rows.push({a:Array(st.n).fill('1'),op:'<=',b:'10'});renderForm();compute();};
  }
  function syncTop(){$('[data-k=sense]').value=st.sense;$('[data-k=n]').value=String(st.n);renderForm();}
  const lin=(co,names)=>{let s='';co.forEach((c,k)=>{if(!c.sgn())return;const neg=c.sgn()<0,a=neg?c.neg():c;const cf=a.eq(Q1)?'':(a.d===1n?a.str():'('+a.str()+')');s+=(s?(neg?' − ':' + '):(neg?'−':''))+cf+names[k];});return s||'0';};
  const NAMES=()=>Array.from({length:st.n},(_,j)=>XN(j));
  const consTxt=k=>`${lin(k.a,NAMES())} ${OPS[k.op]} ${qs(k.b)}`;
  function parse(){
    const bad=(where,v)=>({err:`${where}: “${v}” is not a number (use e.g. 4, −2.5 or 3/2).`});
    const c=[];for(let j=0;j<st.n;j++){const q=Q.parse(st.c[j]);if(!q)return bad(`Objective coefficient of ${XN(j)}`,st.c[j]);c.push(q);}
    const cons=[];for(let i=0;i<st.rows.length;i++){const r=st.rows[i];const a=[];for(let j=0;j<st.n;j++){const q=Q.parse(r.a[j]);if(!q)return bad(`Constraint L${i+1}, coefficient of ${XN(j)}`,r.a[j]);a.push(q);}
      const b=Q.parse(r.b);if(!b)return bad(`Constraint L${i+1}, right-hand side`,r.b);
      if(a.every(x=>!x.sgn())&&st.n>2)return {err:`Constraint L${i+1} has all coefficients 0.`};
      if([...a,b].some(x=>x.n>10n**9n||x.d>10n**6n))return {err:`Constraint L${i+1}: please keep numbers below 10⁹.`};
      cons.push({a,op:r.op,b});}
    if(c.some(x=>x.n>10n**9n||x.d>10n**6n))return {err:'Please keep objective coefficients below 10⁹.'};
    return {M:{sense:st.sense,c,cons}};
  }
  function compute(){
    const p=parse();if(p.err){S.fail(p.err);return;}
    M=p.M;res=LP.solve(M);
    if(res.status==='unsupported'){S.fail(`With ${st.n} variables the solver uses the simplex method, which needs every constraint to be ≤ with b ≥ 0 (then the slack variables give the starting solution). ${res.sErr.err==='neg'?'A right-hand side is negative.':'Some constraint is ≥ or =; that needs Big-M or two-phase.'} Switch to 2 variables to use the graphical method for any constraint type.`);return;}
    S.okay();
    const names=st.n===2?['Graphical method','Corner points','Simplex tableau']:['Simplex tableau'];
    if(names.join()!==tabNames.join()){tabNames=names;if(st.tab>=names.length)st.tab=0;tabs(S.tabHost,names,st.tab,k=>{st.tab=k;renderPane();});}
    renderAns();renderPane();
  }
  const ST={optimal:['Unique optimum','good'],alternative:['Alternative optima','warnc'],unbounded:['Unbounded solution','badc'],infeasible:['Infeasible','badc']};
  function renderAns(){
    const s=ST[res.status];const Zn=st.sense==='max'?'Max Z':'Min Z';let h=card(P,'Status',s[0],res.status==='infeasible'?'no point satisfies every constraint':res.status==='unbounded'?`Z can ${st.sense==='max'?'increase':'decrease'} without limit`:res.status==='alternative'?'several points give the same best Z':'',s[1]);
    if(res.z){h+=card(P,Zn,qs(res.z),res.z.d!==1n?'≈ '+(+res.z.num().toFixed(4)):'');
      h+=card(P,res.status==='alternative'?'One optimal point':'Optimal point',res.x.map((v,j)=>`${XN(j)} = ${qs(v)}`).join(', '),res.g&&res.status==='alternative'?(res.g.opt.length>1?'also '+res.g.opt.filter(p=>p!==res.g.best).map(p=>p.name+qpt(p.x)).join(', ')+' and every point between':'and every point along the optimal ray'):'');}
    if(res.g)h+=card(P,'Feasible region',res.status==='infeasible'?'Empty':res.g.bounded?'Bounded':'Unbounded',res.g.pts.length?`${res.g.pts.length} corner point${res.g.pts.length>1?'s':''}`:'');
    else if(res.s)h+=card(P,'Simplex',`${res.s.frames.length-1} iteration${res.s.frames.length===2?'':'s'}`,res.s.degenerate||res.s.anyTie?'degeneracy occurred':'');
    S.ans.innerHTML=h;
  }
  function renderPane(){const nm=tabNames[st.tab];if(nm==='Graphical method')paneGraph();else if(nm==='Corner points')paneCorners();else paneSimplex();}
  /* ---------- graphical */
  const niceStep=x=>{const e=Math.pow(10,Math.floor(Math.log10(x)));const f=x/e;return (f<=1?1:f<=2?2:f<=5?5:10)*e;};
  function plotBox(g){
    const xs=[1],ys=[1];
    g.pts.forEach(p=>{xs.push(p.x[0].num());ys.push(p.x[1].num());});
    M.cons.forEach(k=>{const a1=k.a[0].num(),a2=k.a[1].num(),b=k.b.num();if(a1&&b/a1>0)xs.push(b/a1);if(a2&&b/a2>0)ys.push(b/a2);});
    let X=Math.max(...xs),Y=Math.max(...ys);
    if(!g.bounded||g.status==='unbounded'){X*=1.35;Y*=1.35;}else{X*=1.12;Y*=1.12;}
    const sx=niceStep(X/6),sy=niceStep(Y/6);return {X:Math.ceil(X/sx)*sx,Y:Math.ceil(Y/sy)*sy,sx,sy};
  }
  function clip(poly,a1,a2,b,sgn){ /* keep sgn*(a.p - b) <= 0 */
    const f=p=>sgn*(a1*p[0]+a2*p[1]-b);const out=[];
    for(let k=0;k<poly.length;k++){const P1=poly[k],P2=poly[(k+1)%poly.length],f1=f(P1),f2=f(P2);
      if(f1<=1e-9)out.push(P1);if((f1<-1e-9&&f2>1e-9)||(f1>1e-9&&f2<-1e-9)){const t=f1/(f1-f2);out.push([P1[0]+t*(P2[0]-P1[0]),P1[1]+t*(P2[1]-P1[1])]);}}
    return out;
  }
  function segInBox(a1,a2,b,X,Y){
    const pts=[];const add=(x,y)=>{if(x>=-1e-9&&x<=X+1e-9&&y>=-1e-9&&y<=Y+1e-9&&!pts.some(p=>Math.abs(p[0]-x)<1e-9&&Math.abs(p[1]-y)<1e-9))pts.push([x,y]);};
    if(a2){add(0,b/a2);add(X,(b-a1*X)/a2);}if(a1){add(b/a1,0);add((b-a2*Y)/a1,Y);}
    if(pts.length<2)return null;let best=[pts[0],pts[1]],bd=-1;
    for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const d=Math.hypot(pts[i][0]-pts[j][0],pts[i][1]-pts[j][1]);if(d>bd){bd=d;best=[pts[i],pts[j]];}}
    return best;
  }
  function svg(g,fr,box){
    const W=460,H=330,ml=44,mr=18,mt=14,mb=34,{X,Y}=box;
    const px=x=>ml+x/X*(W-ml-mr),py=y=>H-mb-y/Y*(H-mt-mb);
    const f1=v=>(+v.toFixed(2));
    let s=`<svg class="${P}-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Graph of the constraints and feasible region">`;
    for(let x=0;x<=X+1e-9;x+=box.sx){s+=`<line class="${P}-grid" x1="${px(x)}" y1="${py(0)}" x2="${px(x)}" y2="${py(Y)}"/><text class="${P}-tk" x="${px(x)}" y="${H-mb+15}" text-anchor="middle">${f1(x)}</text>`;}
    for(let y=box.sy;y<=Y+1e-9;y+=box.sy){s+=`<line class="${P}-grid" x1="${px(0)}" y1="${py(y)}" x2="${px(X)}" y2="${py(y)}"/><text class="${P}-tk" x="${ml-6}" y="${py(y)+4}" text-anchor="end">${f1(y)}</text>`;}
    s+=`<line class="${P}-axis" x1="${px(0)}" y1="${py(0)}" x2="${px(X)}" y2="${py(0)}"/><line class="${P}-axis" x1="${px(0)}" y1="${py(0)}" x2="${px(0)}" y2="${py(Y)}"/>
      <text class="${P}-axl" x="${px(X)}" y="${H-4}" text-anchor="end">x₁</text><text class="${P}-axl" x="${ml+6}" y="${mt+8}">x₂</text>`;
    if(fr.region&&g.status!=='infeasible'){
      let poly=[[0,0],[X,0],[X,Y],[0,Y]];
      M.cons.forEach(k=>{const a1=k.a[0].num(),a2=k.a[1].num(),b=k.b.num();if(!a1&&!a2)return;if(k.op!=='>=')poly=clip(poly,a1,a2,b,1);if(k.op!=='<=')poly=clip(poly,a1,a2,b,-1);});
      if(poly.length)s+=`<polygon class="${P}-reg${poly.length<3?' '+P+'-seg':''}" points="${poly.map(p=>px(p[0]).toFixed(1)+','+py(p[1]).toFixed(1)).join(' ')}"/>`;
    }
    M.cons.forEach((k,i)=>{
      if(i>fr.lines)return;const a1=k.a[0].num(),a2=k.a[1].num(),b=k.b.num();if(!a1&&!a2)return;
      const sg=segInBox(a1,a2,b,X,Y);if(!sg)return;
      const cur=i===fr.cur;
      s+=`<line class="${P}-ln ${P}-c${i%6}${cur?' '+P+'-now':''}" x1="${px(sg[0][0]).toFixed(1)}" y1="${py(sg[0][1]).toFixed(1)}" x2="${px(sg[1][0]).toFixed(1)}" y2="${py(sg[1][1]).toFixed(1)}"/>`;
      const mx=(px(sg[0][0])+px(sg[1][0]))/2,my=(py(sg[0][1])+py(sg[1][1]))/2;
      if(k.op!=='='){const sgn=k.op==='<='?-1:1;let dx=sgn*a1*(W-ml-mr)/X,dy=-sgn*a2*(H-mt-mb)/Y;const L=Math.hypot(dx,dy)||1;dx=dx/L*16;dy=dy/L*16;
        s+=`<line class="${P}-arr ${P}-c${i%6}" x1="${mx.toFixed(1)}" y1="${my.toFixed(1)}" x2="${(mx+dx).toFixed(1)}" y2="${(my+dy).toFixed(1)}" marker-end="url(#${uid}a${i%6})"/>`;}
      const e=sg[0][1]>sg[1][1]?sg[0]:sg[1];let lx=px(e[0]),ly=py(e[1]);lx=Math.min(Math.max(lx+4,ml+10),W-26);ly=Math.min(Math.max(ly+(ly<mt+12?12:-4),mt+10),H-mb-4);
      s+=`<text class="${P}-lt ${P}-c${i%6}" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}">L${i+1}</text>`;
    });
    if(fr.corners)g.pts.forEach(p=>{const x=px(p.x[0].num()),y=py(p.x[1].num());const o=fr.opt&&g.opt&&g.opt.includes(p);
      s+=`<circle class="${P}-pt${o?' '+P+'-opt':''}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${o?6.5:4.5}"/><text class="${P}-pl" x="${(x+7).toFixed(1)}" y="${(y-7).toFixed(1)}">${p.name}</text>`;});
    if(fr.opt&&g.best){
      const c1=M.c[0].num(),c2=M.c[1].num(),z=g.z.num();const sg=(c1||c2)?segInBox(c1,c2,z,X,Y):null;
      if(sg)s+=`<line class="${P}-iso" x1="${px(sg[0][0]).toFixed(1)}" y1="${py(sg[0][1]).toFixed(1)}" x2="${px(sg[1][0]).toFixed(1)}" y2="${py(sg[1][1]).toFixed(1)}"/>`;
    }
    if(fr.opt&&g.status==='unbounded'){
      const d=g.ray;const dx=d[0].num()*(W-ml-mr)/X,dy=-d[1].num()*(H-mt-mb)/Y;const L=Math.hypot(dx,dy)||1;
      let from=g.pts[0];g.pts.forEach(p=>{if(p.z.cmp(from.z)*(st.sense==='max'?1:-1)>0)from=p;});
      const x=px(from.x[0].num()),y=py(from.x[1].num());
      s+=`<line class="${P}-ray" x1="${x}" y1="${y}" x2="${(x+dx/L*70).toFixed(1)}" y2="${(y+dy/L*70).toFixed(1)}" marker-end="url(#${uid}r)"/><text class="${P}-pl ${P}-rayt" x="${(x+dx/L*74).toFixed(1)}" y="${(y+dy/L*74-6).toFixed(1)}">Z ${st.sense==='max'?'→ +∞':'→ −∞'}</text>`;
    }
    s+=`<defs>${[0,1,2,3,4,5].map(k=>`<marker id="${uid}a${k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0L10,5L0,10z" class="${P}-mk ${P}-c${k}"/></marker>`).join('')}<marker id="${uid}r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0L10,5L0,10z" class="${P}-mkr"/></marker></defs></svg>`;
    return s;
  }
  const uid='lppm'+Math.random().toString(36).slice(2,7);
  function paneGraph(){
    const g=res.g,m=M.cons.length;const box=plotBox(g);
    const frames=[];M.cons.forEach((k,i)=>frames.push({lines:i,cur:i,kind:'line',i}));
    frames.push({lines:m,cur:-1,region:true,kind:'region'});
    if(g.status!=='infeasible'){frames.push({lines:m,cur:-1,region:true,corners:true,kind:'corners'});frames.push({lines:m,cur:-1,region:true,corners:true,opt:true,kind:'opt'});}
    const legend=M.cons.map((k,i)=>`<li><span class="${P}-sw ${P}-c${i%6}"></span><b>L${i+1}</b> <span class="${P}-mono">${E(consTxt(k))}</span></li>`).join('');
    S.pane.innerHTML=`<p class="${P}-conv">Draw each constraint as a line, find the side that satisfies it (arrow), shade the region common to all of them in the first quadrant, then evaluate Z at every corner point (extreme-point theorem).</p><div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><div class="${P}-plot"><div class="${P}-svgw"></div><ul class="${P}-leg">${legend}<li><span class="${P}-sw ${P}-regsw"></span>feasible region</li>${g.best?`<li><span class="${P}-sw ${P}-isosw"></span>iso-${st.sense==='max'?'profit':'cost'} line Z = ${qs(g.z)}</li>`:''}</ul></div>`;
    const w=S.pane.querySelector(`.${P}-svgw`),cap=S.pane.querySelector(`.${P}-cap`);
    const ptList=()=>g.pts.map(p=>`${p.name}${qpt(p.x)}`).join(', ');
    function show(i){
      const fr=frames[i];w.innerHTML=svg(g,fr,box);
      if(fr.kind==='line'){
        const k=M.cons[fr.i],a1=k.a[0],a2=k.a[1],b=k.b;
        if(!a1.sgn()&&!a2.sgn()){cap.innerHTML=`<b>L${fr.i+1}: ${E(consTxt(k))}</b> has no variables: 0 ${OPS[k.op]} ${qs(b)} is ${LP.sat(k,[Q0,Q0])?'always true, so it removes nothing':'<b>never true</b>, so the problem is infeasible'}.`;return;}
        let thru;
        if(!a2.sgn())thru=`the vertical line x₁ = ${qs(b.div(a1))}`;
        else if(!a1.sgn())thru=`the horizontal line x₂ = ${qs(b.div(a2))}`;
        else if(!b.sgn())thru=`the line through the origin and (${qs(a2)}, ${qs(a1.neg())})`;
        else thru=`the line through (${qs(b.div(a1))}, 0) and (0, ${qs(b.div(a2))})`;
        let test;
        if(k.op==='=')test='Only points <b>on</b> the line satisfy an equality, so the feasible region can only be part of this line.';
        else{const O=b.sgn()?[Q0,Q0]:(a1.sgn()?[Q1,Q0]:[Q0,Q1]);const lhs=a1.mul(O[0]).add(a2.mul(O[1]));const t=LP.sat(k,O);
          test=`Test ${b.sgn()?'the origin (0, 0)':'the point '+qpt(O)}: ${qs(lhs)} ${OPS[k.op]} ${qs(b)} is <b>${t?'true':'false'}</b>, so the feasible side is the one ${t?'containing':'away from'} ${b.sgn()?'the origin':'that point'} (arrow).`;}
        cap.innerHTML=`<b>L${fr.i+1}: ${E(consTxt(k))}.</b> Draw ${lin([a1,a2],['x₁','x₂'])} = ${qs(b)}, ${thru}. ${test}`;
      }else if(fr.kind==='region'){
        cap.innerHTML=g.status==='infeasible'?`The half-planes have <b>no common point</b> with x₁, x₂ ≥ 0, so there is no feasible region: the LPP is <b>infeasible</b>.`:`The <b>feasible region</b> is where all ${m} constraints and x₁, x₂ ≥ 0 hold together (shaded). It is <b>${g.bounded?'bounded':'unbounded'}</b>${g.bounded?' (a closed polygon)':': it extends without limit, so only a corner can be optimal if Z does not improve along the open direction'}.`;
      }else if(fr.kind==='corners'){
        cap.innerHTML=`<b>Corner points</b> (where two boundary lines meet inside the region): ${E(ptList())}. See the Corner points tab for Z at each.`;
      }else{
        const zt=st.sense==='max'?'largest':'smallest';
        if(g.status==='unbounded')cap.innerHTML=`The region is unbounded and Z = ${lin(M.c,['x₁','x₂'])} keeps ${st.sense==='max'?'increasing':'decreasing'} along the direction (${qs(g.ray[0])}, ${qs(g.ray[1])}) inside it, so there is <b>no finite optimum</b>: an <b>unbounded solution</b>.`;
        else if(g.status==='alternative')cap.innerHTML=`The ${zt} value Z = <b>${qs(g.z)}</b> occurs at ${g.opt.map(p=>p.name+qpt(p.x)).join(' and ')}${g.flatRay?` and along the unbounded edge in direction (${qs(g.flatRay[0])}, ${qs(g.flatRay[1])})`:''}. The iso-${st.sense==='max'?'profit':'cost'} line (dashed) lies along a boundary edge, so there are <b>alternative optima</b>: every point on that edge is optimal.`;
        else cap.innerHTML=`Evaluate Z at every corner: the ${zt} is Z = <b>${qs(g.z)}</b> at <b>${g.best.name}${qpt(g.best.x)}</b>. The dashed iso-${st.sense==='max'?'profit':'cost'} line ${lin(M.c,['x₁','x₂'])} = ${qs(g.z)} touches the region only there.`;
      }
    }
    stepper(S.pane.querySelector(`.${P}-sh`),P,frames.length,show,frames.length-1);
  }
  function paneCorners(){
    const g=res.g;
    if(g.status==='infeasible'){S.pane.innerHTML=`<p class="${P}-res"><span class="${P}-bad">No feasible corner points:</span> the constraints contradict each other${g.trivBad.length?` (L${g.trivBad[0]+1} can never hold)`:''}, so the LPP is <b>infeasible</b>.</p>`;return;}
    const lineName=i=>i===-1?'x₁ = 0':i===-2?'x₂ = 0':'L'+(i+1);
    const sub=p=>M.c.map((c,j)=>`${qs(c)}(${qs(p.x[j])})`).join(' + ').replace(/\+ −/g,'− ');
    const rows=g.pts.map(p=>{const o=g.opt&&g.opt.includes(p);return `<tr class="${o?P+'-best':''}"><td><b>${p.name}</b></td><td>${qs(p.x[0])}</td><td>${qs(p.x[1])}</td><td>${p.on.map(lineName).join(', ')}</td><td class="${P}-mono">${E(sub(p))}</td><td><b>${qs(p.z)}</b>${o?' ★':''}</td></tr>`;}).join('');
    S.pane.innerHTML=`<p class="${P}-conv">Z = ${E(lin(M.c,['x₁','x₂']))}. Each corner is the solution of the two (or more) boundary lines through it. ${st.sense==='max'?'The largest':'The smallest'} Z is optimal, provided Z does not improve along an unbounded edge.</p>
      <div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Point</th><th>x₁</th><th>x₂</th><th>Lines meeting</th><th>Z = ${E(lin(M.c,['x₁','x₂']))}</th><th>Value</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="${P}-res">${g.status==='unbounded'?`<span class="${P}-bad">Unbounded:</span> the corner values are finite, but Z ${st.sense==='max'?'increases':'decreases'} without limit along (${qs(g.ray[0])}, ${qs(g.ray[1])}), so no corner is optimal.`:g.status==='alternative'?`<span class="${P}-warn">Alternative optima:</span> Z = ${qs(g.z)} at ${g.opt.map(p=>p.name).join(', ')}${g.flatRay?' and along an unbounded edge':''}; every point on the segment${g.opt.length>1?' '+g.opt.map(p=>p.name).join(''):''} is optimal.`:`<span class="${P}-ok">Optimum:</span> ${st.sense==='max'?'Max':'Min'} Z = <b>${qs(g.z)}</b> at ${g.best.name}: x₁ = ${qs(g.best.x[0])}, x₂ = ${qs(g.best.x[1])}.`}${!g.bounded&&g.status!=='unbounded'?' The region is unbounded, but Z has a finite optimum because it does not improve along any open direction.':''}</p>`;
  }
  /* ---------- simplex */
  function paneSimplex(){
    if(!res.s){S.pane.innerHTML=`<p class="${P}-res"><span class="${P}-warn">Simplex step-through not available for this problem.</span> ${E(res.sErr.msg)}</p><p class="${P}-conv">Use the graphical method for this problem. In the Big-M method each ≥ constraint gets a surplus variable −sᵢ and an artificial variable Aᵢ with cost −M (max) or +M (min); each = constraint gets an artificial variable only.</p>`;return;}
    const s=res.s,n=s.n,m=s.m,names=s.names.map(x=>x.replace(/\d/,d=>SUB(d)));
    const obj=lin(s.cj.slice(0,n),names.slice(0,n));
    const std=M.cons.map((k,i)=>`${lin(k.a,names.slice(0,n))} + ${names[n+i]} = ${qs(k.b)}`);
    S.pane.innerHTML=`<p class="${P}-res"><b>Standard form.</b> ${s.isMin?`Min Z = ${E(lin(M.c,names.slice(0,n)))} is solved as Max Z′ = −Z = ${E(obj)}.`:`Max Z = ${E(obj)} + ${names.slice(n).map(x=>'0'+x).join(' + ')}`}<br>${std.map(E).join('<br>')}<br>all variables ≥ 0.</p>
      <p class="${P}-conv">Add a slack variable to each ≤ constraint; the slacks form the first basis. <b>Entering:</b> the most positive Cj − Zj (ties: the lowest-numbered variable). <b>Leaving:</b> the smallest ratio b / (entering column) over positive entries only (ties: the topmost row, and the next solution is degenerate). Optimal when every Cj − Zj ≤ 0.${s.frames.some(f=>f.bland)?' After 20 iterations Bland’s rule is used to avoid cycling.':''}</p>
      <div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><div class="${P}-scroll"><table class="${P}-tbl ${P}-tab"></table></div><div class="${P}-sres"></div>`;
    const tbl=S.pane.querySelector(`.${P}-tab`),cap=S.pane.querySelector(`.${P}-cap`);
    const N=n+m;
    function show(i){
      const f=s.frames[i],e=f.enter,l=f.leave;
      let h=`<thead><tr><th colspan="3" class="${P}-cjh">C<sub>j</sub> →</th>${s.cj.map(c=>`<th>${qs(c)}</th>`).join('')}<th></th></tr><tr><th>C<sub>B</sub></th><th>Basis</th><th>b (x<sub>B</sub>)</th>${names.map((nm,j)=>`<th class="${j===e?P+'-ec':''}">${nm}</th>`).join('')}<th>Ratio</th></tr></thead><tbody>`;
      f.A.forEach((row,r)=>{h+=`<tr class="${r===l?P+'-lr':''}"><td>${qs(s.cj[f.basis[r]])}</td><td><b>${names[f.basis[r]]}</b></td><td>${qs(f.b[r])}</td>${row.map((v,j)=>`<td class="${j===e?P+'-ec':''}${r===l&&j===e?' '+P+'-piv':''}">${qs(v)}</td>`).join('')}<td>${f.ratios?(f.ratios[r]?`${qs(f.b[r])}/${qs(row[e])} = ${qs(f.ratios[r])}`:'—'):''}</td></tr>`;});
      h+=`<tr class="${P}-zj"><td colspan="2">Z<sub>j</sub></td><td><b>${qs(f.Z)}</b></td>${f.zj.map(v=>`<td>${qs(v)}</td>`).join('')}<td></td></tr>
        <tr class="${P}-cz"><td colspan="3">C<sub>j</sub> − Z<sub>j</sub></td>${f.cz.map((v,j)=>`<td class="${j===e?P+'-ec':''}${v.sgn()>0?' '+P+'-pos':''}">${qs(v)}</td>`).join('')}<td></td></tr></tbody>`;
      tbl.innerHTML=h;
      const pre=i===0?'<b>Initial tableau:</b> the slacks are basic, so x = 0 and Z = 0. ':`<b>Tableau ${i+1}</b> (Z${s.isMin?'′':''} = ${qs(f.Z)}). `;
      if(e<0){
        const xs=s.x.slice(0,n).map((v,j)=>`${names[j]} = ${qs(v)}`).join(', ');
        cap.innerHTML=pre+`Every C<sub>j</sub> − Z<sub>j</sub> ≤ 0, so this tableau is <b>optimal</b>: ${xs}, ${s.isMin?`Min Z = −(${qs(f.Z)}) = <b>${qs(s.z)}</b>`:`Max Z = <b>${qs(s.z)}</b>`}.${s.alt.length?` Non-basic ${s.alt.map(j=>names[j]).join(', ')} ha${s.alt.length>1?'ve':'s'} C<sub>j</sub> − Z<sub>j</sub> = 0, so <b>alternative optima</b> exist (bringing it in changes x but not Z).`:''}${s.degenerate?' A basic variable is 0: the solution is <b>degenerate</b>.':''}`;
      }else if(l<0){
        cap.innerHTML=pre+`${names[e]} should enter (C<sub>j</sub> − Z<sub>j</sub> = ${qs(f.cz[e])} &gt; 0), but no entry in its column is positive, so no ratio exists: Z can grow without limit. <b>Unbounded solution.</b>`;
      }else{
        cap.innerHTML=pre+`Most positive C<sub>j</sub> − Z<sub>j</sub> is ${qs(f.cz[e])} under ${names[e]}, so <b>${names[e]} enters</b>. Minimum ratio ${qs(f.b[l])}/${qs(f.A[l][e])} = ${qs(f.ratios[l])} in row ${names[f.basis[l]]}, so <b>${names[f.basis[l]]} leaves</b>. Pivot element = <b>${qs(f.A[l][e])}</b>: divide its row by it, then clear the rest of the column.${f.tie?' <b>Tie</b> in the minimum ratio: the next solution is degenerate (a basic variable becomes 0).':''}${f.degen?' The ratio is 0: a <b>degenerate</b> pivot (Z does not change).':''}`;
      }
    }
    stepper(S.pane.querySelector(`.${P}-sh`),P,s.frames.length,show,s.frames.length-1);
    const sr=S.pane.querySelector(`.${P}-sres`);
    if(s.status==='optimal'&&!s.isMin)sr.innerHTML=`<p class="${P}-mut">Shadow prices (dual values) are the Z<sub>j</sub> values under the slack columns in the final tableau: ${s.shadow.map((v,i)=>`y${SUB(i+1)} = ${qs(v)}`).join(', ')}. Each is the gain in Z per extra unit of that constraint’s right-hand side, and Σ bᵢyᵢ = ${qs(M.cons.reduce((a,k,i)=>a.add(k.b.mul(s.shadow[i])),Q0))} = Z (duality).</p>`;
  }
  $('[data-k=sense]').onchange=e=>{st.sense=e.target.value;compute();};
  $('[data-k=n]').onchange=e=>{const n=+e.target.value;st.n=n;const fit=a=>{a=a.slice(0,n);while(a.length<n)a.push('0');return a;};st.c=fit(st.c);st.rows.forEach(r=>r.a=fit(r.a));renderForm();compute();};
  $('[data-k=ex]').onchange=e=>{const x=EX[+e.target.value];if(!x)return;Object.assign(st,JSON.parse(JSON.stringify(x)));delete st.nm;st.tab=0;tabNames=[];syncTop();compute();};
  $('[data-act=rand]').onclick=()=>{
    const n=st.n;let x;
    if(n>2){x=mk('max',Array.from({length:n},()=>rnd(1,9)),Array.from({length:rnd(2,4)},()=>[Array.from({length:n},()=>rnd(0,6)),'<=',rnd(10,40)]));}
    else{const t=Math.random();
      if(t<0.55)x=mk('max',[rnd(1,9),rnd(1,9)],Array.from({length:rnd(2,4)},()=>[[rnd(0,6),rnd(0,6)],'<=',rnd(6,36)]));
      else if(t<0.85)x=mk('min',[rnd(1,9),rnd(1,9)],Array.from({length:rnd(2,3)},()=>[[rnd(1,6),rnd(1,6)],'>=',rnd(4,24)]));
      else x=mk(pick(['max','min']),[rnd(1,6),rnd(1,6)],[[[rnd(1,4),rnd(1,4)],'<=',rnd(10,24)],[[rnd(1,4),rnd(1,4)],'>=',rnd(3,8)],[[1,0],'<=',rnd(3,8)]]);
      x.rows.forEach(r=>{if(r.a.every(v=>v==='0'))r.a[rnd(0,1)]='1';});
      [0,1].forEach(j=>{if(x.rows.every(r=>r.a[j]==='0'))x.rows[0].a[j]=String(rnd(1,5));});}
    Object.assign(st,x);st.tab=0;tabNames=[];$('[data-k=ex]').value='';syncTop();compute();};
  syncTop();compute();
 }});

/* ====================================================================== transport UI */
ANIM.register('transport',{title:'Transportation problem solver',steps:false,
 caption:'Enter a cost matrix with supply and demand. The solver balances it, finds NWCR, least-cost and VAM starting solutions, then runs the MODI (u-v) test and improves to the optimum, showing every allocation and loop.',
 build(stage){
  const P='transport';
  const mk=(nm,C,S,D)=>({nm,C:C.map(r=>r.map(String)),S:S.map(String),D:D.map(String)});
  const EX=[
    mk('Classic 3 × 4 (Kapoor)',[[19,30,50,10],[70,30,40,60],[40,8,70,20]],[7,9,18],[5,8,7,14]),
    mk('3 × 4 (Taha)',[[10,2,20,11],[12,7,9,20],[4,14,16,18]],[15,25,10],[5,15,15,15]),
    mk('3 × 4 (Sharma)',[[2,3,11,7],[1,0,6,1],[5,8,15,9]],[6,1,10],[7,5,3,2]),
    mk('Unbalanced: supply > demand',[[4,8,8],[16,24,16],[8,16,24]],[76,82,77],[72,102,41]),
    mk('Unbalanced: demand > supply',[[3,2,7],[2,5,4]],[30,25],[20,25,30]),
    mk('Degenerate NWCR',[[8,6,10],[9,12,13],[14,9,16]],[20,30,25],[20,30,25])];
  const st={C:EX[0].C.map(r=>r.slice()),S:EX[0].S.slice(),D:EX[0].D.slice(),start:'vam',tab:3};
  const Sh=shell(stage,P,`
     <div class="${P}-wide ${P}-grid"></div>
     <label class="${P}-lab">Start MODI from<select data-k="start"><option value="vam">VAM</option><option value="lcm">Least cost</option><option value="nwcr">North-west corner</option></select></label>
     <div class="${P}-btns"><label class="${P}-lab">Example<select data-k="ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" data-act="rand">🎲 Random example</button></div>`,
    `Cells hold unit costs (minimisation). If total supply ≠ total demand, a <b>dummy</b> source or destination with cost 0 absorbs the difference. Ties: least-cost picks the cell allowing the larger allocation, then the first in row order; VAM breaks penalty ties by the smaller least cost in the line, then the larger allocation, then rows before columns.`);
  const {$}=Sh;
  const ed=matrixEditor($(`.${P}-grid`),P,{key:'c',get:()=>st,rows:()=>st.S.length,cols:()=>st.D.length,rowName:i=>'S'+(i+1),colName:j=>'D'+(j+1),cell:(i,j)=>st.C[i][j],setCell:(i,j,v)=>st.C[i][j]=v,
    extraCol:{name:'Supply',key:'s',get:i=>st.S[i],set:(i,v)=>st.S[i]=v},extraRow:{name:'Demand',key:'d',get:j=>st.D[j],set:(j,v)=>st.D[j]=v},
    min:2,max:6,rowWord:'Source',colWord:'Destination',
    resize(a){if(a==='addr'){st.C.push(st.D.map(()=>String(rnd(1,20))));st.S.push('10');}else if(a==='delr'){st.C.pop();st.S.pop();}else if(a==='addc'){st.C.forEach(r=>r.push(String(rnd(1,20))));st.D.push('10');}else{st.C.forEach(r=>r.pop());st.D.pop();}},
    onChange:()=>compute()});
  let R=null;
  tabs(Sh.tabHost,['North-west corner','Least cost','VAM','MODI → optimum'],st.tab,k=>{st.tab=k;renderPane();});
  const rn=i=>R.B.dummy&&R.B.dummy.type==='row'&&i===R.B.m-1?'Dummy':'S'+(i+1);
  const cn=j=>R.B.dummy&&R.B.dummy.type==='col'&&j===R.B.n-1?'Dummy':'D'+(j+1);
  const cell=(i,j)=>`(${rn(i)}, ${cn(j)})`;
  function parse(){
    const m=st.S.length,n=st.D.length,C=[],S=[],D=[];
    for(let i=0;i<m;i++){C.push([]);for(let j=0;j<n;j++){const v=pnum(st.C[i][j]);if(v==null)return {err:`Cost at (S${i+1}, D${j+1}): “${st.C[i][j]}” is not a number.`};if(Math.abs(v)>1e6)return {err:'Please keep costs below 10⁶.'};C[i].push(v);}}
    for(let i=0;i<m;i++){const v=pnum(st.S[i]);if(v==null||v<=0)return {err:`Supply of S${i+1}: enter a positive number.`};if(v>1e6)return {err:'Please keep supply below 10⁶.'};S.push(v);}
    for(let j=0;j<n;j++){const v=pnum(st.D[j]);if(v==null||v<=0)return {err:`Demand of D${j+1}: enter a positive number.`};if(v>1e6)return {err:'Please keep demand below 10⁶.'};D.push(v);}
    return {C,S,D};
  }
  function compute(){
    const p=parse();if(p.err){Sh.fail(p.err);return;}
    R=TR.solve(p.C,p.S,p.D,st.start);
    if(R.modi.err){Sh.fail(R.modi.err);return;}
    Sh.okay();renderAns();renderPane();
  }
  function renderAns(){
    const B=R.B,d=B.dummy;
    let h=card(P,'Balance',d?'Unbalanced':'Balanced',d?`Σ supply ${fmt(B.sS)} ${d.type==='col'?'&gt;':'&lt;'} Σ demand ${fmt(B.sD)}: dummy ${d.type==='col'?'destination':'source'} of ${fmt(d.q)} at cost 0`:`Σ supply = Σ demand = ${fmt(B.sS)}`);
    const I=R.init;const lab={nwcr:'NWCR cost',lcm:'Least-cost cost',vam:'VAM cost'};
    for(const k of ['nwcr','lcm','vam'])h+=card(P,lab[k],fmt(I[k].cost),`${I[k].count} occupied cell${I[k].count>1?'s':''}${I[k].degenerate?` &lt; m + n − 1 = ${I[k].need}: <b>degenerate</b>`:` = m + n − 1`}`);
    h+=card(P,'Optimal cost (MODI)',fmt(R.optimum),`${R.modi.iterations} improvement${R.modi.iterations===1?'':'s'} from ${{vam:'VAM',lcm:'least cost',nwcr:'NWCR'}[R.start]}${R.modi.alt?'; <b>alternative optimum</b> exists':''}${R.modi.degenerateStart?'; ε used (degenerate start)':''}`,'good');
    Sh.ans.innerHTML=h;
  }
  /* grid renderer */
  function grid(o){
    const B=R.B,m=B.m,n=B.n;
    const val=(i,j)=>o.basic?(o.basic.has(i+','+j)?o.basic.get(i+','+j):null):o.al[i][j];
    const sg=new Map();(o.loop||[]).forEach(c=>sg.set(c.i+','+c.j,c.s));
    let h=`<table class="${P}-tbl ${P}-g"><thead><tr><th></th>${Array.from({length:n},(_,j)=>`<th class="${o.cc&&o.cc.has(j)?P+'-x':''}">${cn(j)}</th>`).join('')}<th>Supply</th>${o.u?'<th>u<sub>i</sub></th>':''}${o.rp?'<th>Row penalty</th>':''}</tr></thead><tbody>`;
    for(let i=0;i<m;i++){
      h+=`<tr><th class="${o.cr&&o.cr.has(i)?P+'-x':''}">${rn(i)}</th>`;
      for(let j=0;j<n;j++){
        const v=val(i,j),k=i+','+j,s=sg.get(k);const hi=o.hi&&o.hi[0]===i&&o.hi[1]===j;const lv=o.leave&&o.leave.i===i&&o.leave.j===j;
        const crossed=(o.cr&&o.cr.has(i))||(o.cc&&o.cc.has(j));
        const d=o.delta&&v==null?o.delta[i][j]:null;
        const lineHi=o.line&&((o.line.kind==='row'&&o.line.k===i)||(o.line.kind==='col'&&o.line.k===j));
        h+=`<td class="${P}-cell${v!=null?' '+P+'-occ':''}${hi?' '+P+'-hi':''}${lv?' '+P+'-lv':''}${crossed&&v==null?' '+P+'-xc':''}${lineHi?' '+P+'-line':''}${s?' '+P+'-lp':''}"><span class="${P}-cost">${fmt(B.C[i][j])}</span>${v!=null?`<b class="${P}-q">${o.basic&&v===0?'ε':fmt(v)}</b>`:d!=null?`<i class="${P}-d${d<-1e-9?' '+P+'-neg':Math.abs(d)<1e-9?' '+P+'-zero':''}">${fmt(d)}</i>`:''}${s?`<em class="${P}-sg">${s==='+'?'+':'−'}</em>`:''}</td>`;
      }
      h+=`<td class="${P}-sd">${fmt(B.S[i])}${o.s&&o.s[i]!==B.S[i]?` <small>→ ${fmt(o.s[i])}</small>`:''}</td>${o.u?`<td class="${P}-uv">${fmt(o.u[i])}</td>`:''}${o.rp?`<td class="${P}-pen${o.line&&o.line.kind==='row'&&o.line.k===i?' '+P+'-pmax':''}">${o.rp[i]==null?'':fmt(o.rp[i])}</td>`:''}</tr>`;
    }
    h+=`<tr class="${P}-dem"><th>Demand</th>${Array.from({length:n},(_,j)=>`<td class="${P}-sd">${fmt(B.D[j])}${o.d&&o.d[j]!==B.D[j]?` <small>→ ${fmt(o.d[j])}</small>`:''}</td>`).join('')}<td class="${P}-sd">${fmt(B.sS>B.sD?B.sS:B.sD)}</td>${o.u?'<td></td>':''}${o.rp?'<td></td>':''}</tr>`;
    if(o.v)h+=`<tr class="${P}-vr"><th>v<sub>j</sub></th>${o.v.map(x=>`<td class="${P}-uv">${fmt(x)}</td>`).join('')}<td></td><td></td></tr>`;
    if(o.cp)h+=`<tr class="${P}-vr"><th>Col penalty</th>${o.cp.map((x,j)=>`<td class="${P}-pen${o.line&&o.line.kind==='col'&&o.line.k===j?' '+P+'-pmax':''}">${x==null?'':fmt(x)}</td>`).join('')}<td></td>${o.rp?'<td></td>':''}</tr>`;
    return h+'</tbody></table>';
  }
  const costSum=(al)=>{const t=[];al.forEach((r,i)=>r.forEach((v,j)=>{if(v)t.push(`${fmt(R.B.C[i][j])}×${fmt(v)}`);}));return t.join(' + ');};
  function renderPane(){if(!R){Sh.pane.innerHTML='';return;}if(st.tab<3)paneInit(['nwcr','lcm','vam'][st.tab]);else paneModi();}
  function paneInit(k){
    const I=R.init[k],B=R.B;
    const intro={nwcr:'Start at the north-west (top-left) cell. Allocate as much as possible, min(supply, demand); cross out the row or column that is exhausted and move right (column done) or down (row done).',
      lcm:'Pick the cheapest cell that is still open and allocate as much as possible there; cross out the exhausted row or column and repeat.',
      vam:'For every open row and column, the penalty is the difference between its two lowest costs. Choose the line with the largest penalty, allocate as much as possible to its cheapest cell, cross out, and recompute the penalties.'}[k];
    Sh.pane.innerHTML=`<p class="${P}-conv">${intro} If a supply and a demand run out together, both are crossed out (this makes the solution degenerate).</p><div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><p class="${P}-key">Small boxed number: unit cost c<sub>ij</sub>. Bold: allocation. Striped: crossed out. Supply/demand “a → b”: remaining after this step.</p><div class="${P}-scroll ${P}-gw"></div>
      <p class="${P}-res">Total cost = ${costSum(I.al)} = <b>${fmt(I.cost)}</b><br>Occupied cells = ${I.count}; m + n − 1 = ${B.m} + ${B.n} − 1 = ${I.need}: ${I.degenerate?`<span class="${P}-warn">degenerate</span> (fewer than m + n − 1; MODI will add ε cells)`:`<span class="${P}-ok">non-degenerate</span>`}.</p>`;
    const gw=Sh.pane.querySelector(`.${P}-gw`),cap=Sh.pane.querySelector(`.${P}-cap`);
    const n=I.steps.length+1;
    function show(i){
      if(i===0){gw.innerHTML=grid({al:blank(B.m,B.n)});cap.innerHTML=`The problem is ${B.dummy?'balanced with the dummy':'balanced'}: ${B.m} sources, ${B.n} destinations. A basic feasible solution needs m + n − 1 = ${B.m+B.n-1} occupied cells.`;return;}
      const s=I.steps[i-1];
      const cr=new Set(),cc=new Set();s.s.forEach((v,r)=>{if(v<=1e-9)cr.add(r);});s.d.forEach((v,c)=>{if(v<=1e-9)cc.add(c);});
      gw.innerHTML=grid({al:s.al,hi:[s.i,s.j],cr,cc,s:s.s,d:s.d,rp:s.rp,cp:s.cp,line:s.line});
      const before=[r9(s.s[s.i]+s.q),r9(s.d[s.j]+s.q)];
      let t=`<b>Step ${i}.</b> `;
      if(s.why==='nw')t+=`North-west open cell ${cell(s.i,s.j)}.`;
      else if(s.why==='min')t+=`Cheapest open cell is ${cell(s.i,s.j)} with cost ${fmt(B.C[s.i][s.j])}.`;
      else if(s.why==='rest')t+=`Only one row or one column is still open, so penalties are no longer needed: the rest is allocated by least cost, here ${cell(s.i,s.j)}.`;
      else t+=`Largest penalty is <b>${fmt(s.line.p)}</b> in ${s.line.kind==='row'?'row '+rn(s.line.k):'column '+cn(s.line.k)}${s.tie?' (a tie, broken by the rule above)':''}; its cheapest cell is ${cell(s.i,s.j)} with cost ${fmt(B.C[s.i][s.j])}.`;
      t+=` Allocate min(${fmt(before[0])}, ${fmt(before[1])}) = <b>${fmt(s.q)}</b>. `;
      t+=s.rowDone&&s.colDone?(s.both?`Both ${rn(s.i)} and ${cn(s.j)} are exhausted: cross out both (<b>degeneracy</b>).`:'Everything is allocated.'):s.rowDone?`${rn(s.i)} is exhausted: cross out the row.`:`${cn(s.j)} is satisfied: cross out the column.`;
      cap.innerHTML=t;
    }
    stepper(Sh.pane.querySelector(`.${P}-sh`),P,n,show,n-1);
  }
  function paneModi(){
    const md=R.modi,B=R.B;const I=R.init[R.start];
    Sh.pane.innerHTML=`<p class="${P}-conv"><b>MODI (u-v) method.</b> For every occupied cell uᵢ + vⱼ = cᵢⱼ, starting with u₁ = 0. For every empty cell the opportunity cost is Δᵢⱼ = cᵢⱼ − (uᵢ + vⱼ). If every Δᵢⱼ ≥ 0 the solution is optimal; otherwise the most negative Δ enters (ties: first in row order), a closed loop of occupied cells is traced, and θ = the smallest allocation at a “−” corner is shifted around the loop.</p>
      ${md.degenerateStart?`<p class="${P}-res"><span class="${P}-warn">Degenerate start:</span> the ${{vam:'VAM',lcm:'least-cost',nwcr:'NWCR'}[R.start]} solution has ${I.count} occupied cells, fewer than m + n − 1 = ${I.need}. An ε (a tiny amount, treated as 0) is placed in ${md.eps.map(c=>cell(c[0],c[1])).join(', ')}: the cheapest empty cell${md.eps.length>1?'s':''} that do${md.eps.length>1?'':'es'} not form a closed loop.</p>`:''}
      <div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><p class="${P}-key">Small boxed number: unit cost c<sub>ij</sub>. Bold: allocation (ε = 0 kept as basic). Plain number in an empty cell: Δ<sub>ij</sub> (red if negative). + / − mark the loop corners; blue outline = entering cell, red outline = leaving cell.</p><div class="${P}-scroll ${P}-gw"></div><div class="${P}-final"></div>`;
    const gw=Sh.pane.querySelector(`.${P}-gw`),cap=Sh.pane.querySelector(`.${P}-cap`);
    function show(i){
      const f=md.frames[i];
      gw.innerHTML=grid({basic:f.basic,u:f.u,v:f.v,delta:f.delta,loop:f.loop,hi:f.enter?[f.enter.i,f.enter.j]:null,leave:f.leave});
      const uvTxt=`u = (${f.u.map(fmt).join(', ')}), v = (${f.v.map(fmt).join(', ')})`;
      if(!f.enter){cap.innerHTML=`<b>Iteration ${i+1}</b> (cost ${fmt(f.cost)}): ${uvTxt}. Every Δᵢⱼ ≥ 0, so this solution is <b>optimal</b>. Minimum transportation cost = <b>${fmt(f.cost)}</b>.${f.alt.length?` Δ = 0 at ${f.alt.map(c=>cell(c[0],c[1])).join(', ')}: an <b>alternative optimal</b> solution exists (entering there changes the allocation, not the cost).`:' No Δ is 0, so the optimum is unique.'}`;return;}
      const loop=f.loop.map(c=>`${cell(c.i,c.j)}${c.s==='+'?'+':'−'}`).join(' → ');
      const mins=f.loop.filter(c=>c.s==='-').map(c=>{const v=f.basic.get(c.i+','+c.j);return v===0?'ε':fmt(v);});
      cap.innerHTML=`<b>Iteration ${i+1}</b> (cost ${fmt(f.cost)}): ${uvTxt}. Most negative Δ = <b>${fmt(f.enter.d)}</b> at ${cell(f.enter.i,f.enter.j)}, so it enters. Loop: ${loop}. θ = min(${mins.join(', ')}) = <b>${f.theta===0?'ε (0)':fmt(f.theta)}</b>; ${cell(f.leave.i,f.leave.j)} leaves. New cost = ${fmt(f.cost)} + (${fmt(f.enter.d)})(${fmt(f.theta)}) = ${fmt(r9(f.cost+f.enter.d*f.theta))}.${f.theta===0?' θ = 0 is a <b>degenerate</b> pivot: the cost does not change.':''}`;
    }
    stepper(Sh.pane.querySelector(`.${P}-sh`),P,md.frames.length,show,md.frames.length-1);
    const last=md.frames[md.frames.length-1];const al=blank(B.m,B.n);last.basic.forEach((v,k)=>{const [i,j]=k.split(',').map(Number);al[i][j]=v;});
    const list=[];al.forEach((r,i)=>r.forEach((v,j)=>{if(v)list.push(`${rn(i)} → ${cn(j)}: ${fmt(v)}`);}));
    Sh.pane.querySelector(`.${P}-final`).innerHTML=`<p class="${P}-res"><b>Optimal shipments:</b> ${list.join('; ')}.<br>Minimum cost = ${costSum(al)} = <b>${fmt(last.cost)}</b>.${B.dummy?` Shipments to or from the dummy are ${B.dummy.type==='col'?'unused supply left at the source':'unmet demand'}.`:''}</p>`;
  }
  $('[data-k=start]').onchange=e=>{st.start=e.target.value;compute();};
  $('[data-k=ex]').onchange=e=>{const x=EX[+e.target.value];if(!x)return;st.C=x.C.map(r=>r.slice());st.S=x.S.slice();st.D=x.D.slice();ed.render();compute();};
  $('[data-act=rand]').onclick=()=>{
    const m=rnd(3,4),n=rnd(3,5);st.C=Array.from({length:m},()=>Array.from({length:n},()=>String(rnd(1,25))));
    const tot=rnd(8,16)*5;const split=(k,t)=>{const a=Array(k).fill(5);let left=t-5*k;while(left>0){a[rnd(0,k-1)]+=5;left-=5;}return a.map(String);};
    st.S=split(m,tot);st.D=split(n,Math.random()<0.7?tot:tot+rnd(-3,3)*5);$('[data-k=ex]').value='';ed.render();compute();};
  ed.render();compute();
 }});

/* ====================================================================== assign UI */
ANIM.register('assign',{title:'Assignment problem: Hungarian method',steps:false,
 caption:'Enter a cost or profit matrix. The solver balances it, reduces rows and columns, covers the zeros with the fewest lines, adjusts until n lines are needed, and reads off the optimal assignment.',
 build(stage){
  const P='assign';
  const mk=(nm,sense,A)=>({nm,sense,A:A.map(r=>r.map(v=>v==null?'M':String(v)))});
  const EX=[
    mk('4 × 4 minimise cost',"min",[[10,12,19,11],[5,10,7,8],[12,14,13,11],[8,15,11,9]]),
    mk('5 × 5 needs line adjustments',"min",[[11,17,8,16,20],[9,7,12,6,15],[13,16,15,12,16],[21,24,17,28,26],[14,10,12,11,15]]),
    mk('Maximise profit',"max",[[42,35,28,21],[30,25,20,15],[30,25,20,15],[24,20,16,12]]),
    mk('Unbalanced 3 × 4 (dummy row)',"min",[[9,26,15,13],[13,27,6,35],[35,20,15,14]]),
    mk('Forbidden cells (M)',"min",[[null,4,6,3],[5,null,2,7],[3,7,null,4],[6,3,5,null]]),
    mk('3 × 3 (hand check)',"min",[[1,2,3],[2,4,6],[3,6,9]])];
  const st={A:EX[1].A.map(r=>r.slice()),sense:'min'};
  const Sh=shell(stage,P,`
     <div class="${P}-wide ${P}-grid"></div>
     <label class="${P}-lab">Objective<select data-k="sense"><option value="min">Minimise cost</option><option value="max">Maximise profit</option></select></label>
     <div class="${P}-btns"><label class="${P}-lab">Example<select data-k="ex"><option value="">Choose…</option>${EX.map((e,k)=>`<option value="${k}">${E(e.nm)}</option>`).join('')}</select></label><button type="button" class="btn sm" data-act="rand">🎲 Random example</button></div>`,
    `Rows are workers (W), columns are jobs (J). Type <code>M</code> or <code>-</code> for a forbidden assignment. A non-square matrix gets dummy rows or columns of 0. For maximisation every entry is subtracted from the largest entry first (the regret matrix).`);
  const {$}=Sh;
  const ed=matrixEditor($(`.${P}-grid`),P,{key:'a',get:()=>st,rows:()=>st.A.length,cols:()=>st.A[0].length,rowName:i=>'W'+(i+1),colName:j=>'J'+(j+1),cell:(i,j)=>st.A[i][j],setCell:(i,j,v)=>st.A[i][j]=v,
    min:2,max:8,rowWord:'Worker',colWord:'Job',
    resize(a){const n=st.A[0].length;if(a==='addr')st.A.push(Array.from({length:n},()=>String(rnd(1,20))));else if(a==='delr')st.A.pop();else if(a==='addc')st.A.forEach(r=>r.push(String(rnd(1,20))));else st.A.forEach(r=>r.pop());},
    onChange:()=>compute()});
  let R=null;
  function parse(){
    const A=[];for(let i=0;i<st.A.length;i++){A.push([]);for(let j=0;j<st.A[i].length;j++){const s=String(st.A[i][j]).trim();
      if(/^(m|-|x|∞)$/i.test(s)){A[i].push(null);continue;}const v=pnum(s);if(v==null)return {err:`Entry (W${i+1}, J${j+1}): “${s}” is not a number (use M or - for forbidden).`};if(Math.abs(v)>1e6)return {err:'Please keep entries below 10⁶.'};A[i].push(v);}}
    return {A};
  }
  const rn=i=>i<R.r?'W'+(i+1):'Dummy W'+(i+1);
  const cn=j=>j<R.c?'J'+(j+1):'Dummy J'+(j+1);
  function compute(){
    const p=parse();if(p.err){Sh.fail(p.err);return;}
    R=AS.solve(p.A,st.sense);if(R.err){Sh.fail(R.err);R=null;return;}
    Sh.okay();renderAns();renderPane();
  }
  function renderAns(){
    const real=R.pairs.filter(p=>!p.dummy);
    let h=card(P,st.sense==='max'?'Maximum profit':'Minimum cost',fmt(R.total),real.map(p=>fmt(p.v)).join(' + '),'good');
    h+=card(P,'Optimal assignment',real.map(p=>`W${p.i+1}→J${p.j+1}`).join(', '),R.pairs.some(p=>p.dummy)?R.pairs.filter(p=>p.dummy).map(p=>p.i>=R.r?`J${p.j+1} gets no worker`:`W${p.i+1} gets no job`).join('; '):'');
    h+=card(P,'Line adjustments',String(R.iterations),R.iterations?'times the zeros needed fewer than n lines':'row and column reduction were enough');
    h+=card(P,'Optimal assignments',R.count>=1000?'1000+':String(R.count),R.count>1?'<b>alternative optima</b> exist (same total)':'unique');
    Sh.ans.innerHTML=h;
  }
  function mat(f,opt){
    const n=R.n,M=f.M;const as=new Set();(f.mr||[]).forEach((j,i)=>{if(j>=0)as.add(i+','+j);});
    const ch=new Map();(f.ch||[]).forEach(c=>ch.set(c[0]+','+c[1],c[2]));
    const cv=f.k==='cover'?f.cv:null;
    let h=`<table class="${P}-tbl ${P}-m"><thead><tr><th></th>${Array.from({length:n},(_,j)=>`<th class="${cv&&cv.colLine[j]?P+'-lc':''}">${cn(j)}</th>`).join('')}${f.k==='row'?`<th class="${P}-red">Row min</th>`:''}${cv?'<th>✓</th>':''}</tr></thead><tbody>`;
    for(let i=0;i<n;i++){
      h+=`<tr><th class="${cv&&cv.rowLine[i]?P+'-lr':''}">${rn(i)}</th>`;
      for(let j=0;j<n;j++){const v=M[i][j],k=i+','+j;const z=v!=null&&v!==Infinity&&Math.abs(v)<1e-9;
        const cls=[];if(cv){if(cv.rowLine[i])cls.push(P+'-cr');if(cv.colLine[j])cls.push(P+'-cc');}
        if((f.k==='cover'||f.k==='final')&&as.has(k))cls.push(P+'-as');else if(f.k==='cover'&&z)cls.push(P+'-zx');
        if(ch.has(k))cls.push(P+(ch.get(k)==='-'?'-dn':'-up'));
        if(opt&&opt.dummy&&(i>=R.r||j>=R.c))cls.push(P+'-dm');
        h+=`<td class="${cls.join(' ')}">${v==null||v===Infinity?'M':fmt(v)}${ch.has(k)?`<small>${ch.get(k)==='-'?'−':'+'}${fmt(f.kmin)}</small>`:''}</td>`;}
      if(f.k==='row')h+=`<td class="${P}-red">${fmt(f.red[i])}</td>`;
      if(cv)h+=`<td class="${P}-tk">${cv.rt[i]?'✓':''}</td>`;
      h+='</tr>';
    }
    if(f.k==='col')h+=`<tr><th class="${P}-red">Col min</th>${f.red.map(v=>`<td class="${P}-red">${fmt(v)}</td>`).join('')}</tr>`;
    if(cv)h+=`<tr><th>✓</th>${cv.ct.map(t=>`<td class="${P}-tk">${t?'✓':''}</td>`).join('')}<td></td></tr>`;
    return h+'</tbody></table>';
  }
  function renderPane(){
    const fr=R.frames,n=R.n;
    Sh.pane.innerHTML=`<p class="${P}-conv"><b>Covering rule.</b> Assign one zero per row where possible (boxed) using a maximum matching; tick rows with no assignment, then columns having a zero in a ticked row, then rows with an assignment in a ticked column, until nothing changes. Draw lines through <b>unticked rows</b> and <b>ticked columns</b>: this is the minimum number of lines that cover every zero.</p>
      <div class="${P}-sh"></div><p class="${P}-cap" aria-live="polite"></p><div class="${P}-scroll ${P}-mw"></div><div class="${P}-final"></div>`;
    const mw=Sh.pane.querySelector(`.${P}-mw`),cap=Sh.pane.querySelector(`.${P}-cap`);
    function show(i){
      const f=fr[i];
      if(f.k==='final'){mw.innerHTML=mat({k:'final',M:R.P,mr:f.mr},{dummy:true});
        cap.innerHTML=`<b>Optimal assignment</b> (boxed, read on the original ${st.sense==='max'?'profits':'costs'}): ${R.pairs.filter(p=>!p.dummy).map(p=>`W${p.i+1}→J${p.j+1} (${fmt(p.v)})`).join(', ')}. Total = <b>${fmt(R.total)}</b>.`;return;}
      mw.innerHTML=mat(f);
      if(f.k==='orig')cap.innerHTML=`The matrix is ${R.r} × ${R.c}${R.dummyRows||R.dummyCols?`, so it is <b>unbalanced</b>: add ${R.dummyRows?R.dummyRows+' dummy row'+(R.dummyRows>1?'s':''):R.dummyCols+' dummy column'+(R.dummyCols>1?'s':'')} of 0s to make it ${n} × ${n}`:', already square'}.${R.P.some(r=>r.some(v=>v==null))?' M marks a forbidden cell (a very large cost).':''}`;
      else if(f.k==='max')cap.innerHTML=`<b>Maximisation:</b> subtract every entry from the largest entry, ${fmt(f.mx)}. Minimising this regret (opportunity-loss) matrix maximises the profit.`;
      else if(f.k==='row')cap.innerHTML=`<b>Row reduction:</b> subtract each row’s minimum (right) from every entry in that row.`;
      else if(f.k==='col')cap.innerHTML=`<b>Column reduction:</b> subtract each column’s minimum (bottom) from its entries. Every row and column now has at least one 0.`;
      else if(f.k==='cover'){const ok=f.cv.lines>=n;cap.innerHTML=`<b>Cover the zeros:</b> ${f.mr.filter(j=>j>=0).length} zero${f.mr.filter(j=>j>=0).length>1?'s':''} can be assigned (boxed; other zeros crossed), so the minimum number of lines is <b>${f.cv.lines}</b> for n = ${n}. ${ok?'Lines = n, so an <b>optimal assignment</b> exists among the zeros.':'Fewer lines than n: not optimal yet, so adjust.'}`;}
      else if(f.k==='adjust')cap.innerHTML=`<b>Adjust:</b> the smallest uncovered entry is k = <b>${fmt(f.kmin)}</b>. Subtract it from every uncovered entry (−) and add it at every intersection of two lines (+). Entries covered by one line stay. This creates a new zero.`;
    }
    stepper(Sh.pane.querySelector(`.${P}-sh`),P,fr.length,show,fr.length-1);
    const rows=R.pairs.map(p=>`<tr class="${p.dummy?P+'-dmr':''}"><td>${rn(p.i)}</td><td>${cn(p.j)}</td><td>${p.dummy?'0 (dummy)':fmt(p.v)}</td></tr>`).join('');
    Sh.pane.querySelector(`.${P}-final`).innerHTML=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Worker</th><th>Job</th><th>${st.sense==='max'?'Profit':'Cost'}</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="${P}-res">${st.sense==='max'?'Maximum profit':'Minimum cost'} = ${R.pairs.filter(p=>!p.dummy).map(p=>fmt(p.v)).join(' + ')} = <b>${fmt(R.total)}</b>.${R.count>1?` There ${R.count>=1000?'are 1000+':'are '+R.count} optimal assignments with this total, e.g. ${R.sols.slice(0,3).map(s=>s.map((j,i)=>i<R.r&&j<R.c?`W${i+1}→J${j+1}`:'').filter(Boolean).join(', ')).join(' | ')}.`:''}</p>`;
  }
  $('[data-k=sense]').onchange=e=>{st.sense=e.target.value;compute();};
  $('[data-k=ex]').onchange=e=>{const x=EX[+e.target.value];if(!x)return;st.A=x.A.map(r=>r.slice());st.sense=x.sense;$('[data-k=sense]').value=st.sense;ed.render();compute();};
  $('[data-act=rand]').onclick=()=>{const r=rnd(3,5),c=Math.random()<0.25?r+1:r;st.A=Array.from({length:r},()=>Array.from({length:c},()=>String(rnd(2,30))));st.sense=Math.random()<0.7?'min':'max';$('[data-k=sense]').value=st.sense;$('[data-k=ex]').value='';ed.render();compute();};
  ed.render();compute();
 }});

})();

/* ===== NET solvers: data structures & algorithms =====
   sorttrace · treeops · graphalgo · hashprobe · infix
   Pure cores live on window.NETSOLVE.<id> (testable in Node with global.window = {}). */
(function(){
'use strict';
const NETSOLVE=NS_ROOT.NETSOLVE;

/* ---------------- shared parsing ---------------- */
function toks(s){return String(s==null?'':s).trim().split(/[\s,;]+/).filter(Boolean);}
function parseInts(s,o){
  o=o||{};const min=o.min==null?1:o.min,max=o.max||40,name=o.name||'numbers';
  const t=toks(s);
  if(t.length<min)return {err:`Enter at least ${min} ${name}.`};
  if(t.length>max)return {err:`Use at most ${max} ${name} (you entered ${t.length}).`};
  const bad=t.find(x=>!/^[-+]?\d+$/.test(x));
  if(bad!==undefined)return {err:`“${bad}” is not a whole number.`};
  const v=t.map(Number);
  if(v.some(x=>Math.abs(x)>999999))return {err:'Keep every value between −999999 and 999999.'};
  return {vals:v};
}
const mod=(a,m)=>((a%m)+m)%m;

/* =====================================================================
   1. SORTING TRACES
   ===================================================================== */
const SORT_NAMES={bubble:'Bubble sort',selection:'Selection sort',insertion:'Insertion sort',quick:'Quick sort',merge:'Merge sort',heap:'Heap sort',counting:'Counting sort',radix:'Radix sort (LSD)'};
const SORT_INFO={
  bubble:{stable:true,inplace:true,best:'O(n) with early stop',avg:'O(n²)',worst:'O(n²)'},
  selection:{stable:false,inplace:true,best:'O(n²)',avg:'O(n²)',worst:'O(n²)'},
  insertion:{stable:true,inplace:true,best:'O(n)',avg:'O(n²)',worst:'O(n²)'},
  quick:{stable:false,inplace:true,best:'O(n log n)',avg:'O(n log n)',worst:'O(n²)'},
  merge:{stable:true,inplace:false,best:'O(n log n)',avg:'O(n log n)',worst:'O(n log n)'},
  heap:{stable:false,inplace:true,best:'O(n log n)',avg:'O(n log n)',worst:'O(n log n)'},
  counting:{stable:true,inplace:false,best:'O(n + k)',avg:'O(n + k)',worst:'O(n + k)'},
  radix:{stable:true,inplace:false,best:'O(d(n + b))',avg:'O(d(n + b))',worst:'O(d(n + b))'}
};
function sortTrace(input,algo,o){
  o=o||{};
  if(!SORT_NAMES[algo])return {err:'Unknown algorithm.'};
  if(!Array.isArray(input)||!input.length)return {err:'Enter at least one number.'};
  const a=input.slice(),n=a.length,steps=[];let C=0,S=0,moveName='swaps',passLabel='Passes';
  const mk=f=>{const c=[];for(let i=0;i<n;i++)c.push(f(i)||'');return c;};
  const snap=(title,note,cls,extra)=>steps.push(Object.assign({title,note,arr:a.slice(),cls:cls||[],comps:C,swaps:S},extra||{}));
  const swap=(i,j)=>{const t=a[i];a[i]=a[j];a[j]=t;};
  const pl=(k,w)=>`${k} ${w}${k===1?'':'s'}`;
  snap('Start','Input array.',[]);
  if(algo==='bubble'){
    const early=o.early!==false;
    for(let p=0;p<n-1;p++){
      let s=0;const moved=new Set();const c=n-1-p;
      for(let j=0;j<n-1-p;j++){C++;if(a[j]>a[j+1]){swap(j,j+1);S++;s++;moved.add(j);moved.add(j+1);}}
      const stop=early&&s===0;const fixedFrom=(stop||p===n-2)?0:n-1-p;
      snap(`Pass ${p+1}`,`Compared ${pl(c,'adjacent pair')}, made ${pl(s,'swap')}. `+(stop?'No swaps in this pass, so the array is already sorted: stop early.':`${a[n-1-p]} has bubbled up to index ${n-1-p}, its final place.`),mk(i=>i>=fixedFrom?'ok':moved.has(i)?'sw':''));
      if(stop)break;
    }
  }else if(algo==='selection'){
    for(let i=0;i<n-1;i++){
      let m=i;for(let j=i+1;j<n;j++){C++;if(a[j]<a[m])m=j;}
      const val=a[m];let note;
      if(m!==i){swap(i,m);S++;note=`The minimum of indices ${i}–${n-1} is ${val} (index ${m}); swap it with index ${i}.`;}
      else note=`The minimum of indices ${i}–${n-1} is ${val}, already at index ${i}: no swap.`;
      snap(`Pass ${i+1}`,note+` ${pl(n-1-i,'comparison')}.`,mk(k=>(k<=i||i===n-2)?'ok':(k===m&&m!==i)?'sw':''));
    }
  }else if(algo==='insertion'){
    moveName='shifts';
    for(let i=1;i<n;i++){
      const key=a[i];let j=i-1,c=0,sh=0;
      while(j>=0){C++;c++;if(a[j]>key){a[j+1]=a[j];j--;S++;sh++;}else break;}
      a[j+1]=key;
      snap(`Pass ${i}`,`Insert ${key} into the sorted part a[0..${i-1}]: ${pl(c,'comparison')}, ${pl(sh,'shift')}; it lands at index ${j+1}.`,mk(k=>k===j+1?'key':k<=i?'ok':''));
    }
  }else if(algo==='quick'){
    passLabel='Partition calls';
    const lomuto=o.scheme!=='hoare';const pc=o.pivot||(lomuto?'last':'first');
    const pick=(lo,hi)=>pc==='first'?lo:pc==='middle'?Math.floor((lo+hi)/2):hi;
    const placed=new Set();
    const partL=(lo,hi)=>{
      const c0=C,s0=S,pi=pick(lo,hi);let pre='';
      if(pi!==hi){pre=`Move the pivot ${a[pi]} (index ${pi}) to the end: swap with index ${hi}. `;swap(pi,hi);S++;}
      const x=a[hi];let i=lo-1;
      for(let j=lo;j<hi;j++){C++;if(a[j]<=x){i++;if(i!==j){swap(i,j);S++;}}}
      if(i+1!==hi){swap(i+1,hi);S++;}
      const p=i+1;placed.add(p);
      const left=a.slice(lo,p),right=a.slice(p+1,hi+1);
      snap(`Partition [${lo}..${hi}]`,pre+`Pivot = ${x} (${pc} element). Elements ≤ ${x} move left: [${left.join(', ')}] ${x} [${right.join(', ')}]. The pivot is fixed at index ${p}. ${pl(C-c0,'comparison')}, ${pl(S-s0,'swap')}.`,
        mk(k=>k===p?'pv':placed.has(k)?'ok':(k<lo||k>hi)?'dim':''),{pivot:x,range:[lo,hi]});
      return p;
    };
    const partH=(lo,hi)=>{
      const c0=C,s0=S,pi=pick(lo,hi);let pre='';
      if(pi!==lo){pre=`Move the pivot ${a[pi]} (index ${pi}) to the front: swap with index ${lo}. `;swap(pi,lo);S++;}
      const x=a[lo];let i=lo-1,j=hi+1;const pairs=[];
      for(;;){
        do{j--;C++;}while(a[j]>x);
        do{i++;C++;}while(a[i]<x);
        if(i<j){pairs.push(`${a[i]}↔${a[j]}`);swap(i,j);S++;}else break;
      }
      snap(`Partition [${lo}..${hi}]`,pre+`Pivot = ${x} (${pc} element). ${pairs.length?'Swapped pairs: '+pairs.join(', ')+'.':'No pair needed swapping.'} Pointers cross, split at j = ${j}: [${a.slice(lo,j+1).join(', ')}] | [${a.slice(j+1,hi+1).join(', ')}]. ${pl(C-c0,'comparison')}, ${pl(S-s0,'swap')}.`,
        mk(k=>(k<lo||k>hi)?'dim':k<=j?'lp':''),{pivot:x,range:[lo,hi],split:j});
      return j;
    };
    const qs=(lo,hi)=>{
      if(lo<hi){const p=lomuto?partL(lo,hi):partH(lo,hi);if(lomuto){qs(lo,p-1);qs(p+1,hi);}else{qs(lo,p);qs(p+1,hi);}}
      else if(lo===hi)placed.add(lo);
    };
    qs(0,n-1);
  }else if(algo==='merge'){
    moveName='writes';
    const merge=(lo,mid,hi)=>{
      const L=a.slice(lo,mid+1),R=a.slice(mid+1,hi+1);let i=0,j=0,k=lo,c=0;
      while(i<L.length&&j<R.length){C++;c++;if(L[i]<=R[j])a[k++]=L[i++];else a[k++]=R[j++];}
      while(i<L.length)a[k++]=L[i++];while(j<R.length)a[k++]=R[j++];S+=hi-lo+1;return {L,R,c};
    };
    if(o.mstyle==='bu'){
      for(let w=1,p=1;w<n;w*=2,p++){
        const c0=C;const runs=[];
        for(let lo=0;lo+w<n;lo+=2*w){const hi=Math.min(lo+2*w-1,n-1);merge(lo,lo+w-1,hi);}
        for(let lo=0;lo<n;lo+=2*w)runs.push('['+a.slice(lo,Math.min(lo+2*w,n)).join(' ')+']');
        snap(`Pass ${p}`,`Merge neighbouring runs of size ${w} into runs of size ${2*w}: ${runs.join(' ')}. ${pl(C-c0,'comparison')}.`,mk(k=>k%(2*w)===0&&k>0?'gs':''));
      }
    }else{
      passLabel='Merge calls';
      const ms=(lo,hi)=>{
        if(lo>=hi)return;const mid=Math.floor((lo+hi)/2);ms(lo,mid);ms(mid+1,hi);
        const r=merge(lo,mid,hi);
        snap(`Merge [${lo}..${mid}] + [${mid+1}..${hi}]`,`Merge [${r.L.join(', ')}] and [${r.R.join(', ')}] → [${a.slice(lo,hi+1).join(', ')}]: ${pl(r.c,'comparison')}.`,mk(k=>k>=lo&&k<=hi?'sw':'dim'),{range:[lo,hi]});
      };
      ms(0,n-1);
    }
  }else if(algo==='heap'){
    passLabel='Steps';
    const sift=(i,size)=>{let sw=[];for(;;){const l=2*i+1,r=l+1;let g=i;if(l<size){C++;if(a[l]>a[g])g=l;}if(r<size){C++;if(a[r]>a[g])g=r;}if(g===i)break;sw.push(`${a[i]}↔${a[g]}`);swap(i,g);S++;i=g;}return sw;};
    for(let i=(n>>1)-1;i>=0;i--){
      const v=a[i],sw=sift(i,n);
      snap(`Build heap: heapify(${i})`,`Sift down ${v} from index ${i}: ${sw.length?'swaps '+sw.join(', '):'already ≥ its children, no swap'}.`+(i===0?' The array is now a max-heap.':''),mk(k=>k===i?'pv':''),{heapSize:n});
    }
    for(let end=n-1;end>0;end--){
      const mx=a[0];swap(0,end);S++;const sw=sift(0,end);
      snap(`Extract max ${mx}`,`Swap the root ${mx} with a[${end}] and shrink the heap to size ${end}; sift down the new root: ${sw.length?sw.join(', '):'no swap'}.`,mk(k=>k>=end||end===1?'ok':''),{heapSize:end});
    }
  }else if(algo==='counting'){
    moveName='writes';passLabel='Steps';
    const mn=Math.min(...a),mx=Math.max(...a),K=mx-mn+1;
    if(K>100)return {err:`Counting sort needs a small key range; here max − min + 1 = ${K}. Keep it at 100 or less.`};
    const cnt=Array(K).fill(0);for(const v of a)cnt[v-mn]++;
    const heads=[];for(let i=0;i<K;i++)heads.push(i+mn);
    const inHead=a.map((_,i)=>i);
    steps.push({title:'Count',note:`Count the occurrences of every value ${mn}..${mx}: C[v] = number of times v appears.`,arr:a.slice(),cls:[],comps:0,swaps:0,arrLabel:'Input A',aux:[{label:'C',heads,vals:cnt.slice()}]});
    for(let i=1;i<K;i++)cnt[i]+=cnt[i-1];
    steps.push({title:'Cumulative counts',note:'Running sum: C[v] = number of elements ≤ v, which is the last (1-based) position that v may occupy.',arr:a.slice(),cls:[],comps:0,swaps:0,arrLabel:'Input A',aux:[{label:'C',heads,vals:cnt.slice()}]});
    const out=Array(n).fill(null);
    for(let i=n-1;i>=0;i--){
      const v=a[i];const pos=cnt[v-mn]-1;cnt[v-mn]--;out[pos]=v;S++;
      steps.push({title:`Place A[${i}] = ${v}`,note:`C[${v}] = ${pos+1}, so ${v} goes to output index ${pos}; decrement C[${v}] to ${pos}. (Scanning right to left keeps equal keys in order.)`,arr:out.slice(),cls:out.map((x,k)=>k===pos?'sw':''),comps:0,swaps:S,arrLabel:'Output B',aux:[{label:'A',heads:inHead,vals:a.slice(),hi:i},{label:'C',heads,vals:cnt.slice(),hi:v-mn}]});
    }
    for(let i=0;i<n;i++)a[i]=out[i];
  }else if(algo==='radix'){
    moveName='writes';
    if(a.some(v=>v<0))return {err:'This radix sort works on non-negative integers. Remove the negative values.'};
    const d=String(Math.max(...a)).length;const PN=['units','tens','hundreds','thousands','ten-thousands','hundred-thousands'];
    for(let p=0,e=1;p<d;p++,e*=10){
      const B=[];for(let b=0;b<10;b++)B.push([]);
      for(const v of a)B[Math.floor(v/e)%10].push(v);
      const na=[].concat(...B);for(let i=0;i<n;i++)a[i]=na[i];S+=n;
      snap(`Pass ${p+1}: ${PN[p]} digit`,`Distribute by the ${PN[p]} digit into buckets 0–9 (keeping the current order), then collect the buckets from 0 to 9.`,[],{digit:p,width:d,aux:[{label:'Bucket',heads:[0,1,2,3,4,5,6,7,8,9],vals:B.map(b=>b.length?b.join(' '):'—')}]});
    }
  }
  return {steps,comps:C,swaps:S,sorted:a.slice(),moveName,passLabel};
}
NETSOLVE.sorttrace={run:sortTrace,NAMES:SORT_NAMES,INFO:SORT_INFO,parse:parseInts};

/* =====================================================================
   2. TREES: BST, AVL, binary heap, reconstruction
   ===================================================================== */
const tnode=k=>({k,l:null,r:null});
const tclone=n=>n?{k:n.k,l:tclone(n.l),r:tclone(n.r)}:null;
const tht=n=>n?1+Math.max(tht(n.l),tht(n.r)):0;           /* levels */
const tbf=n=>tht(n.l)-tht(n.r);
function trav(root){
  const ino=[],pre=[],post=[],lvl=[];
  (function go(x){if(!x)return;pre.push(x.k);go(x.l);ino.push(x.k);go(x.r);post.push(x.k);})(root);
  const q=root?[root]:[];while(q.length){const x=q.shift();lvl.push(x.k);if(x.l)q.push(x.l);if(x.r)q.push(x.r);}
  return {ino,pre,post,lvl};
}
function tcount(n){return n?1+tcount(n.l)+tcount(n.r):0;}
function bstIns(root,k){
  if(!root)return tnode(k);let p=root;
  for(;;){const s=k<p.k?'l':'r';if(!p[s]){p[s]=tnode(k);return root;}p=p[s];}
}
function bstDel(n,k,succ,info){
  if(!n){info.missing=true;return null;}
  if(k<n.k){n.l=bstDel(n.l,k,succ,info);return n;}
  if(k>n.k){n.r=bstDel(n.r,k,succ,info);return n;}
  if(!n.l&&!n.r){info.kase='leaf';return null;}
  if(!n.l||!n.r){info.kase='one';info.child=(n.l||n.r).k;return n.l||n.r;}
  info.kase='two';
  if(succ){let s=n.r;while(s.l)s=s.l;info.rep=s.k;n.k=s.k;n.r=bstDel(n.r,s.k,succ,{});}
  else{let s=n.l;while(s.r)s=s.r;info.rep=s.k;n.k=s.k;n.l=bstDel(n.l,s.k,succ,{});}
  return n;
}
const rotR=y=>{const x=y.l;y.l=x.r;x.r=y;return x;};
const rotL=x=>{const y=x.r;x.r=y.l;y.l=x;return y;};
function findUnbal(n,parent,side){
  if(!n)return null;
  return findUnbal(n.l,n,'l')||findUnbal(n.r,n,'r')||(Math.abs(tbf(n))>1?{n,parent,side}:null);
}
/* rebalance bottom-up; onRot(info, root) after every rotation */
function avlFix(root,onRot){
  for(let guard=0;guard<100;guard++){
    const u=findUnbal(root,null,null);if(!u)break;
    const n=u.n,bf=tbf(n);let kase,nw,child,cbf;
    if(bf>1){child=n.l.k;cbf=tbf(n.l);if(cbf>=0){kase='LL';nw=rotR(n);}else{kase='LR';n.l=rotL(n.l);nw=rotR(n);}}
    else{child=n.r.k;cbf=tbf(n.r);if(cbf<=0){kase='RR';nw=rotL(n);}else{kase='RL';n.r=rotR(n.r);nw=rotL(n);}}
    if(u.parent)u.parent[u.side]=nw;else root=nw;
    onRot&&onRot({kase,at:n.k,bf,child,cbf,up:nw.k},root);
  }
  return root;
}
function rotNote(r){
  const sg=v=>v>0?'+'+v:v<0?'−'+(-v):'0';
  const base=`Node ${r.at} has balance ${sg(r.bf)}`;
  if(r.kase==='LL')return `${base} and its left child ${r.child} has balance ${sg(r.cbf)}: <b>LL case</b>, one right rotation at ${r.at}. ${r.up} moves up.`;
  if(r.kase==='RR')return `${base} and its right child ${r.child} has balance ${sg(r.cbf)}: <b>RR case</b>, one left rotation at ${r.at}. ${r.up} moves up.`;
  if(r.kase==='LR')return `${base} and its left child ${r.child} has balance ${sg(r.cbf)}: <b>LR case</b>, left-rotate ${r.child}, then right-rotate ${r.at} (double rotation). ${r.up} moves up.`;
  return `${base} and its right child ${r.child} has balance ${sg(r.cbf)}: <b>RL case</b>, right-rotate ${r.child}, then left-rotate ${r.at} (double rotation). ${r.up} moves up.`;
}
function parseTreeOps(s,heap){
  const t=toks(s);if(!t.length)return {err:'Enter at least one key.'};
  if(t.length>40)return {err:'Use at most 40 operations.'};
  const ops=[];
  for(const x of t){
    if(heap&&/^(x|del|delete|extract)$/i.test(x)){ops.push({op:'delroot'});continue;}
    if(!/^-?\d+$/.test(x))return {err:`“${x}” is not a key. Use whole numbers${heap?', x to delete the root,':''} and −key to delete a key.`};
    const v=Number(x);if(Math.abs(v)>99999)return {err:'Keep keys below 100000.'};
    ops.push(x[0]==='-'?{op:'del',k:-v}:{op:'ins',k:v});
  }
  return {ops};
}
function treeRun(mode,ops,o){
  o=o||{};const succ=o.rep!=='pred';const avl=mode==='avl';
  let root=null;const steps=[],rots=[];
  const push=(title,note,hi,extra)=>steps.push(Object.assign({title,note,tree:tclone(root),hi:hi||{}},extra||{}));
  push('Start','The tree is empty.');
  const fix=()=>{if(!avl)return;root=avlFix(root,(r,rt)=>{root=rt;rots.push(r);push(`${r.kase} rotation at ${r.at}`,rotNote(r),{[r.up]:'hi',[r.at]:'dirty'},{rot:r.kase});});};
  const imb=()=>{if(!avl)return '';const u=findUnbal(root,null,null);return u?` Node ${u.n.k} is now unbalanced (balance ${tbf(u.n)>0?'+':'−'}${Math.abs(tbf(u.n))}): a rotation is needed.`:' Every balance factor is −1, 0 or +1: no rotation needed.';};
  for(const op of ops){
    if(op.op==='ins'){
      const k=op.k;let p=root;const path=[];
      while(p){path.push(p.k);if(k===p.k)break;p=k<p.k?p.l:p.r;}
      if(p){push(`Insert ${k}`,`${k} is already in the tree: duplicate ignored.`,{[k]:'dirty'});continue;}
      root=bstIns(root,k);
      const last=path[path.length-1];
      const note=path.length?`Compare: ${path.map(x=>`${k} ${k<x?'<':'>'} ${x}`).join(', ')}. ${k} becomes the ${k<last?'left':'right'} child of ${last}.`:`${k} becomes the root.`;
      push(`Insert ${k}`,note+imb(),{[k]:'new'});fix();
    }else if(op.op==='del'){
      const k=op.k,info={};root=bstDel(root,k,succ,info);
      if(info.missing){push(`Delete ${k}`,`${k} is not in the tree: nothing to delete.`);continue;}
      let note;
      if(info.kase==='leaf')note=`${k} is a leaf: remove it.`;
      else if(info.kase==='one')note=`${k} has one child (${info.child}): the child takes its place.`;
      else note=`${k} has two children: replace it with its inorder ${succ?'successor':'predecessor'} ${info.rep} (the ${succ?'smallest key in the right':'largest key in the left'} subtree), then remove ${info.rep} from that subtree.`;
      push(`Delete ${k}`,note+imb(),info.rep!=null?{[info.rep]:'dirty'}:{});fix();
    }
  }
  const t=trav(root);
  return {steps,root,rots,trav:t,height:tht(root)-1,count:tcount(root)};
}
function heapRun(ops,o){
  o=o||{};const min=o.kind==='min';const better=(x,y)=>min?x<y:x>y;const word=min?'smaller':'larger';
  const a=[],steps=[];let SW=0,CMP=0;
  const push=(title,note,hi,extra)=>steps.push(Object.assign({title,note,arr:a.slice(),hi:hi||{},swaps:SW},extra||{}));
  const up=i=>{const log=[];while(i>0){const p=(i-1)>>1;CMP++;if(better(a[i],a[p])){log.push(`${a[i]}↔${a[p]}`);[a[i],a[p]]=[a[p],a[i]];SW++;i=p;}else break;}return {log,i};};
  const down=i=>{const log=[];const n=a.length;for(;;){const l=2*i+1,r=l+1;let b=i;if(l<n){CMP++;if(better(a[l],a[b]))b=l;}if(r<n){CMP++;if(better(a[r],a[b]))b=r;}if(b===i)break;log.push(`${a[i]}↔${a[b]}`);[a[i],a[b]]=[a[b],a[i]];SW++;i=b;}return {log,i};};
  push('Start','The heap is empty.');
  let k0=0;
  if(o.build!=='ins'){
    while(k0<ops.length&&ops[k0].op==='ins'){a.push(ops[k0].k);k0++;}
    if(a.length){
      push('Load array',`Place the ${a.length} keys in the array as given. This is a complete binary tree but not yet a heap.`,{});
      for(let i=(a.length>>1)-1;i>=0;i--){
        const v=a[i],r=down(i);
        push(`heapify(${i})`,`Sift down ${v} from index ${i}: ${r.log.length?'swap with the '+word+' child: '+r.log.join(', '):'it is already '+(min?'≤':'≥')+' its children, no swap'}.`+(i===0?` The array is now a ${min?'min':'max'}-heap.`:''),{[i]:'dirty',[r.i]:'hi'});
      }
    }
  }
  for(let q=k0;q<ops.length;q++){
    const op=ops[q];
    if(op.op==='ins'){
      a.push(op.k);const at=a.length-1;const r=up(at);
      push(`Insert ${op.k}`,`Put ${op.k} at index ${at} (the next free leaf), then sift up: ${r.log.length?r.log.join(', ')+`; it stops at index ${r.i}`:'its parent is already '+(min?'smaller or equal':'larger or equal')+', no swap'}.`,{[r.i]:'new'});
    }else if(op.op==='delroot'){
      if(!a.length){push('Delete root','The heap is empty: nothing to delete.');continue;}
      const top=a[0],last=a.pop();
      if(!a.length){push(`Delete root ${top}`,`${top} was the only key: the heap is now empty.`,{},{removed:top});continue;}
      a[0]=last;const r=down(0);
      push(`Delete root ${top}`,`Remove ${top}; move the last key ${last} to the root and sift down: ${r.log.length?r.log.join(', '):'no swap needed'}.`,{[r.i]:'dirty'},{removed:top});
    }else if(op.op==='del'){
      const idx=a.indexOf(op.k);
      if(idx<0){push(`Delete ${op.k}`,`${op.k} is not in the heap.`);continue;}
      const last=a.pop();
      if(idx===a.length){push(`Delete ${op.k}`,`${op.k} is the last element: just remove it.`,{},{removed:op.k});continue;}
      a[idx]=last;let r=up(idx);let how='sift up';if(!r.log.length){r=down(idx);how='sift down';}
      push(`Delete ${op.k}`,`Replace ${op.k} (index ${idx}) with the last key ${last}, then ${how}: ${r.log.length?r.log.join(', '):'no swap needed'}.`,{[r.i]:'dirty'},{removed:op.k});
    }
  }
  return {steps,arr:a.slice(),swaps:SW,comps:CMP,kind:min?'min':'max'};
}
function heapToTree(arr){
  const mkn=i=>i<arr.length?{k:arr[i],i,l:mkn(2*i+1),r:mkn(2*i+2)}:null;
  return mkn(0);
}
function rebuildTree(ino,other,kind){
  if(!ino.length)return {err:'Enter the inorder sequence.'};
  if(ino.length!==other.length)return {err:`The two sequences have different lengths (${ino.length} and ${other.length}).`};
  if(new Set(ino).size!==ino.length)return {err:'Keys must be distinct to rebuild a unique tree.'};
  const set=new Set(ino);const miss=other.find(x=>!set.has(x));
  if(miss!==undefined)return {err:`“${miss}” appears in the ${kind==='pre'?'preorder':'postorder'} but not in the inorder.`};
  const order=[];let bad=false;
  const go=(inL,inR,oL,oR)=>{
    if(inL>inR||bad)return null;
    const k=kind==='pre'?other[oL]:other[oR];const m=ino.indexOf(k);
    if(m<inL||m>inR){bad=true;return null;}
    const nd=tnode(k),ls=m-inL;
    order.push({k,left:ino.slice(inL,m),right:ino.slice(m+1,inR+1),seg:other.slice(oL,oR+1)});
    if(kind==='pre'){nd.l=go(inL,m-1,oL+1,oL+ls);nd.r=go(m+1,inR,oL+ls+1,oR);}
    else{nd.l=go(inL,m-1,oL,oL+ls-1);nd.r=go(m+1,inR,oL+ls,oR-1);}
    return nd;
  };
  const root=go(0,ino.length-1,0,other.length-1);
  const t=trav(root);
  if(bad||t.ino.join('\u0001')!==ino.join('\u0001')||(kind==='pre'?t.pre:t.post).join('\u0001')!==other.join('\u0001'))
    return {err:'These sequences are inconsistent: no binary tree has both of them.'};
  return {root,order,trav:t,height:tht(root)-1};
}
NETSOLVE.treeops={bst:(ops,o)=>treeRun('bst',ops,o),avl:(ops,o)=>treeRun('avl',ops,o),heap:heapRun,rebuild:rebuildTree,trav,parseOps:parseTreeOps,heapToTree,height:n=>tht(n)-1,bf:tbf};

/* =====================================================================
   3. GRAPH ALGORITHMS
   ===================================================================== */
function vcmp(a,b){const na=/^-?\d+$/.test(a),nb=/^-?\d+$/.test(b);if(na&&nb)return a-b;if(na!==nb)return na?-1:1;return a<b?-1:a>b?1:0;}
function parseGraph(text,directed){
  const chunks=String(text==null?'':text).split(/[\n,;]+/).map(s=>s.trim()).filter(Boolean);
  if(!chunks.length)return {err:'Enter at least one edge, one per line, like “A B 4”.'};
  const V=new Set(),E=[];
  for(const c of chunks){
    const t=c.split(/\s+/);
    if(t.length>3)return {err:`“${c}”: write each edge as “u v weight”.`};
    for(const x of t.slice(0,2))if(!/^[A-Za-z0-9_]{1,5}$/.test(x))return {err:`“${x}” is not a valid vertex name (letters/digits, up to 5 characters).`};
    if(t.length===1){V.add(t[0]);continue;}
    if(t[0]===t[1])return {err:`“${c}” is a self-loop; remove it.`};
    let w=1;if(t.length===3){if(!/^-?\d+(\.\d+)?$/.test(t[2]))return {err:`“${t[2]}” in “${c}” is not a number.`};w=Number(t[2]);}
    V.add(t[0]);V.add(t[1]);E.push({u:t[0],v:t[1],w,id:E.length});
  }
  if(V.size>12)return {err:`Use at most 12 vertices (you have ${V.size}).`};
  if(E.length>40)return {err:'Use at most 40 edges.'};
  return {V:[...V].sort(vcmp),E,directed:!!directed};
}
function adjacency(G,order,undirectedOverride){
  const und=undirectedOverride||!G.directed;const adj={};G.V.forEach(v=>adj[v]=[]);
  for(const e of G.E){adj[e.u].push({v:e.v,w:e.w,id:e.id});if(und)adj[e.v].push({v:e.u,w:e.w,id:e.id});}
  if(order!=='input')for(const v of G.V)adj[v].sort((x,y)=>vcmp(x.v,y.v)||x.id-y.id);
  return adj;
}
function gBFS(G,src,o){
  const adj=adjacency(G,o&&o.order);const dist={},par={};G.V.forEach(v=>{dist[v]=Infinity;par[v]=null;});
  dist[src]=0;const q=[src],seen=new Set([src]),order=[],tree=[],steps=[];
  steps.push({title:'Start',note:`Mark ${src} visited (level 0) and enqueue it.`,queue:q.slice(),order:[],seen:[...seen],tree:[],dist:{...dist}});
  while(q.length){
    const u=q.shift();order.push(u);const disc=[];
    for(const {v,id} of adj[u])if(!seen.has(v)){seen.add(v);dist[v]=dist[u]+1;par[v]=u;q.push(v);disc.push(v);tree.push(id);}
    steps.push({title:`Dequeue ${u}`,note:disc.length?`Dequeue ${u}; its unvisited neighbours ${disc.join(', ')} get level ${dist[u]+1}, parent ${u}, and join the queue.`:`Dequeue ${u}; it has no unvisited neighbours.`,cur:u,queue:q.slice(),order:order.slice(),seen:[...seen],tree:tree.slice(),disc,dist:{...dist}});
  }
  return {order,dist,par,tree,steps,unreached:G.V.filter(v=>!seen.has(v))};
}
function gDFS(G,src,o){
  const adj=adjacency(G,o&&o.order);const col={},d={},f={},par={},cls={};let time=0;const steps=[],order=[],finish=[];
  G.V.forEach(v=>{col[v]='w';par[v]=null;});
  const tree=()=>Object.keys(cls).filter(id=>cls[id]==='tree').map(Number);
  const grey=()=>G.V.filter(v=>col[v]==='g'),black=()=>G.V.filter(v=>col[v]==='b');
  const visit=u=>{
    col[u]='g';d[u]=++time;order.push(u);
    steps.push({title:`Discover ${u}`,note:`d[${u}] = ${d[u]}.`+(par[u]!=null?` Reached from ${par[u]} (tree edge).`:' Start of a new DFS tree.'),cur:u,seen:grey(),done:black(),tree:tree(),d:{...d},f:{...f}});
    for(const {v,id} of adj[u]){
      if(!G.directed&&cls[id])continue;
      if(col[v]==='w'){cls[id]='tree';par[v]=u;visit(v);}
      else if(col[v]==='g')cls[id]='back';
      else cls[id]=d[u]<d[v]?'forward':'cross';
    }
    col[u]='b';f[u]=++time;finish.push(u);
    steps.push({title:`Finish ${u}`,note:`All neighbours of ${u} are done: f[${u}] = ${f[u]}.`,cur:u,seen:grey(),done:black(),tree:tree(),d:{...d},f:{...f}});
  };
  const roots=[src,...G.V.filter(v=>v!==src)];
  for(const r of roots)if(col[r]==='w')visit(r);
  const counts={tree:0,back:0,forward:0,cross:0};Object.values(cls).forEach(c=>counts[c]++);
  return {d,f,par,cls,order,finish,steps,counts};
}
function gDijkstra(G,src,o){
  if(G.E.some(e=>e.w<0))return {err:'Dijkstra needs non-negative edge weights. Use Bellman–Ford for graphs with negative weights.'};
  const adj=adjacency(G,o&&o.order);const dist={},prev={},prevE={},done=new Set(),steps=[];
  G.V.forEach(v=>{dist[v]=Infinity;prev[v]=null;});dist[src]=0;
  steps.push({title:'Start',note:`dist[${src}] = 0, every other distance = ∞.`,dist:{...dist},done:[],upd:[],tree:[]});
  for(;;){
    let u=null;for(const v of G.V)if(!done.has(v)&&dist[v]<Infinity&&(u===null||dist[v]<dist[u]))u=v;
    if(u===null)break;done.add(u);const upd=[],rel=[];
    for(const {v,w,id} of adj[u]){
      if(done.has(v))continue;
      const nd=dist[u]+w;
      if(nd<dist[v]){rel.push(`${v}: min(${fmtN(dist[v])}, ${fmtN(dist[u])} + ${fmtN(w)}) = ${fmtN(nd)}`);dist[v]=nd;prev[v]=u;prevE[v]=id;upd.push(v);}
      else rel.push(`${v}: ${fmtN(dist[u])} + ${fmtN(w)} = ${fmtN(nd)} ≥ ${fmtN(dist[v])}, no change`);
    }
    steps.push({title:`Pick ${u} (dist ${fmtN(dist[u])})`,note:`${u} has the smallest tentative distance, so it is final. `+(rel.length?'Relax its edges: '+rel.join('; ')+'.':'No unfinished neighbours.'),cur:u,dist:{...dist},done:[...done],upd,tree:Object.values(prevE)});
  }
  return {dist,prev,prevE,steps,paths:paths(G,src,dist,prev)};
}
function paths(G,src,dist,prev){const P={};for(const v of G.V){if(dist[v]===Infinity||dist[v]===-Infinity){P[v]=null;continue;}const p=[];let x=v,g=0;while(x!=null&&g++<50){p.unshift(x);x=prev[x];}P[v]=p;}return P;}
function gBellman(G,src){
  const rel=[];for(const e of G.E){rel.push({u:e.u,v:e.v,w:e.w,id:e.id});if(!G.directed)rel.push({u:e.v,v:e.u,w:e.w,id:e.id});}
  const dist={},prev={},prevE={},steps=[];G.V.forEach(v=>{dist[v]=Infinity;prev[v]=null;});dist[src]=0;
  steps.push({title:'Start',note:`dist[${src}] = 0, every other distance = ∞. Each iteration relaxes all ${rel.length} directed edge(s) in input order.`,dist:{...dist},upd:[],relaxed:[],tree:[]});
  let stoppedEarly=0;
  for(let it=1;it<=G.V.length-1;it++){
    const ch=[],log=[],relaxed=[];
    for(const r of rel){if(dist[r.u]!==Infinity&&dist[r.u]+r.w<dist[r.v]){log.push(`${r.u}→${r.v}: ${fmtN(dist[r.u])} + ${fmtN(r.w)} = ${fmtN(dist[r.u]+r.w)} < ${fmtN(dist[r.v])}`);dist[r.v]=dist[r.u]+r.w;prev[r.v]=r.u;prevE[r.v]=r.id;ch.push(r.v);relaxed.push(r.id);}}
    const stop=!ch.length;
    steps.push({title:`Iteration ${it}`,note:(log.length?'Updates: '+log.join('; ')+'.':'No distance changed.')+(stop?' Nothing changed, so later iterations cannot change anything either: stop early.':''),dist:{...dist},upd:[...new Set(ch)],relaxed,tree:Object.values(prevE)});
    if(stop){stoppedEarly=it;break;}
  }
  const bad=rel.filter(r=>dist[r.u]!==Infinity&&dist[r.u]+r.w<dist[r.v]);
  const negCycle=bad.length>0;
  if(negCycle)steps.push({title:'Negative-cycle check',note:`One more pass still improves ${bad.map(r=>r.u+'→'+r.v).join(', ')}: the graph has a negative-weight cycle reachable from ${src}, so shortest paths are undefined.`,dist:{...dist},upd:[],relaxed:bad.map(r=>r.id),tree:Object.values(prevE)});
  else steps.push({title:'Negative-cycle check',note:'An extra pass over all edges improves nothing: no negative cycle is reachable, the distances are final.',dist:{...dist},upd:[],relaxed:[],tree:Object.values(prevE)});
  return {dist,prev,prevE,steps,negCycle,stoppedEarly,paths:negCycle?null:paths(G,src,dist,prev)};
}
function gFloyd(G){
  const V=G.V,n=V.length,ix={};V.forEach((v,i)=>ix[v]=i);
  const D=V.map((_,i)=>V.map((_,j)=>i===j?0:Infinity));
  for(const e of G.E){const i=ix[e.u],j=ix[e.v];D[i][j]=Math.min(D[i][j],e.w);if(!G.directed)D[j][i]=Math.min(D[j][i],e.w);}
  const mats=[{k:null,D:D.map(r=>r.slice()),changed:[]}];
  for(let k=0;k<n;k++){
    const ch=[];
    for(let i=0;i<n;i++)for(let j=0;j<n;j++){if(D[i][k]===Infinity||D[k][j]===Infinity)continue;const nd=D[i][k]+D[k][j];if(nd<D[i][j]){D[i][j]=nd;ch.push([i,j]);}}
    mats.push({k:V[k],D:D.map(r=>r.slice()),changed:ch});
  }
  const negCycle=V.some((_,i)=>D[i][i]<0);
  return {mats,D,negCycle,V};
}
function gPrim(G,src){
  const adj=adjacency(G,'sorted',true);const key={},par={},parE={},inT=new Set(),steps=[],mst=[];let total=0;
  G.V.forEach(v=>{key[v]=Infinity;par[v]=null;});key[src]=0;
  steps.push({title:'Start',note:`key[${src}] = 0, all other keys = ∞.`,key:{...key},done:[],tree:[]});
  for(;;){
    let u=null;for(const v of G.V)if(!inT.has(v)&&key[v]<Infinity&&(u===null||key[v]<key[u]))u=v;
    if(u===null)break;inT.add(u);
    if(par[u]!=null){mst.push({u:par[u],v:u,w:key[u],id:parE[u]});total+=key[u];}
    const upd=[];
    for(const {v,w,id} of adj[u])if(!inT.has(v)&&w<key[v]){key[v]=w;par[v]=u;parE[v]=id;upd.push(v);}
    steps.push({title:par[u]!=null?`Add ${u} via ${par[u]}–${u} (${fmtN(key[u])})`:`Add ${u}`,note:(par[u]!=null?`The lightest edge leaving the tree is ${par[u]}–${u} with weight ${fmtN(key[u])}. `:`Start the tree at ${u}. `)+(upd.length?'Update keys: '+upd.map(v=>`${v} = ${fmtN(key[v])} (via ${u})`).join(', ')+'.':'No key improves.'),cur:u,curE:par[u]!=null?[parE[u]]:[],key:{...key},done:[...inT],tree:mst.map(e=>e.id),upd});
  }
  return {mst,total,steps,unreached:G.V.filter(v=>!inT.has(v))};
}
function gKruskal(G){
  const sorted=G.E.slice().sort((a,b)=>a.w-b.w||a.id-b.id);const P={};G.V.forEach(v=>P[v]=v);
  const find=x=>{while(P[x]!==x)x=P[x];return x;};
  const comps=()=>{const g={};G.V.forEach(v=>{const r=find(v);(g[r]=g[r]||[]).push(v);});return Object.values(g).map(s=>'{'+s.join(',')+'}');};
  const mst=[],steps=[],log=[];let total=0;
  steps.push({title:'Start',note:`Sort the edges by weight: ${sorted.map(e=>`${e.u}–${e.v} (${fmtN(e.w)})`).join(', ')}. Every vertex is its own component.`,tree:[],rej:[],comps:comps()});
  const rej=[];
  for(const e of sorted){
    if(mst.length===G.V.length-1)break;
    const a=find(e.u),b=find(e.v);
    if(a!==b){P[a]=b;mst.push(e);total+=e.w;log.push({e,ok:true,comps:comps()});
      steps.push({title:`Take ${e.u}–${e.v} (${fmtN(e.w)})`,note:`${e.u} and ${e.v} are in different components: add the edge and merge them.`+(mst.length===G.V.length-1?` That makes V − 1 = ${G.V.length-1} edges: done.`:''),curE:[e.id],tree:mst.map(x=>x.id),rej:rej.slice(),comps:comps(),edge:e,ok:true});}
    else{rej.push(e.id);log.push({e,ok:false,comps:comps()});
      steps.push({title:`Skip ${e.u}–${e.v} (${fmtN(e.w)})`,note:`${e.u} and ${e.v} are already connected: this edge would form a cycle, reject it.`,rejE:[e.id],tree:mst.map(x=>x.id),rej:rej.slice(),comps:comps(),edge:e,ok:false});}
  }
  return {mst,total,steps,log,sorted,forest:mst.length<G.V.length-1};
}
function gTopo(G,o){
  if(!G.directed)return {err:'Topological sort needs a directed graph. Tick “Directed”.'};
  if(o&&o.method==='dfs'){
    const r=gDFS(G,G.V[0],o);
    const cyc=r.counts.back>0;
    const topo=r.finish.slice().reverse();
    return {method:'dfs',order:cyc?null:topo,cycle:cyc,dfs:r,steps:r.steps};
  }
  const adj=adjacency(G,'sorted');const indeg={};G.V.forEach(v=>indeg[v]=0);G.E.forEach(e=>indeg[e.v]++);
  const ready=G.V.filter(v=>indeg[v]===0);const out=[],steps=[];
  steps.push({title:'Start',note:`In-degrees: ${G.V.map(v=>`${v}=${indeg[v]}`).join(', ')}. Vertices with in-degree 0: ${ready.join(', ')||'none'}.`,indeg:{...indeg},ready:ready.slice(),out:[],done:[]});
  while(ready.length){
    ready.sort(vcmp);const u=ready.shift();out.push(u);const nz=[];
    for(const {v} of adj[u]){indeg[v]--;if(indeg[v]===0){ready.push(v);nz.push(v);}}
    steps.push({title:`Output ${u}`,note:`Remove ${u} (smallest ready vertex) and its outgoing edges.`+(nz.length?` ${nz.join(', ')} now ${nz.length>1?'have':'has'} in-degree 0.`:''),cur:u,indeg:{...indeg},ready:ready.slice().sort(vcmp),out:out.slice(),done:out.slice()});
  }
  const cycle=out.length<G.V.length;
  return {method:'kahn',order:cycle?null:out,cycle,left:G.V.filter(v=>!out.includes(v)),steps};
}
function fmtN(x){if(x===Infinity)return '∞';if(x===-Infinity)return '−∞';if(typeof x!=='number')return String(x);const s=Number.isInteger(x)?String(x):String(+x.toFixed(4));return s.replace(/^-/,'−');}
NETSOLVE.graphalgo={parse:parseGraph,adjacency,bfs:gBFS,dfs:gDFS,dijkstra:gDijkstra,bellmanFord:gBellman,floyd:gFloyd,prim:gPrim,kruskal:gKruskal,topo:gTopo,vcmp};

/* =====================================================================
   4. HASHING
   ===================================================================== */
function hashRun(m,keys,o){
  o=o||{};const st=o.strategy||'linear';const c1=o.c1==null?0:o.c1,c2=o.c2==null?1:o.c2,R=o.R||7;
  if(!(Number.isInteger(m)&&m>=1&&m<=61))return {err:'Table size m must be a whole number from 1 to 61.'};
  if(st==='double'&&!(Number.isInteger(R)&&R>=1))return {err:'R for h2 must be a whole number ≥ 1.'};
  const h2=k=>o.h2kind==='one'?1+mod(k,R):R-mod(k,R);
  const table=st==='chain'?Array.from({length:m},()=>[]):Array(m).fill(null);
  const rows=[],steps=[];let probeColl=0,keyColl=0,n=0;const failed=[];const seen=new Set();
  for(const k of keys){
    const h=mod(k,m);
    if(seen.has(k)){rows.push({k,h,dup:true,probes:[],coll:0});steps.push({k,dup:true,table:snapT(table),probes:[],h});continue;}
    if(st==='chain'){
      const b=table[h];const coll=b.length?1:0;keyColl+=coll;probeColl+=coll;
      if(o.head)b.unshift(k);else b.push(k);n++;seen.add(k);
      const r={k,h,slot:h,probes:[{i:0,slot:h,occ:b.length>1?(o.head?b.slice(1):b.slice(0,-1)).join(', '):null}],coll,chainLen:b.length};
      rows.push(r);steps.push(Object.assign({table:snapT(table)},r));continue;
    }
    let hv=null;
    if(st==='double'){hv=h2(k);if(mod(hv,m)===0){const r={k,h,h2:hv,probes:[],coll:0,fail:`h2(${k}) = ${hv} is a multiple of m = ${m}, so every probe hits the same slot. Choose another R.`};rows.push(r);failed.push(k);steps.push(Object.assign({table:snapT(table)},r));continue;}}
    const probes=[];let slot=null,coll=0;
    for(let i=0;i<m;i++){
      const s=st==='linear'?mod(h+i,m):st==='quad'?mod(h+c1*i+c2*i*i,m):mod(h+i*hv,m);
      const occ=table[s];probes.push({i,slot:s,occ});
      if(occ===null){table[s]=k;slot=s;break;}
      coll++;
    }
    probeColl+=coll;if(coll)keyColl++;
    const r={k,h,h2:hv,probes,slot,coll};
    if(slot===null){r.fail=`No empty slot found in ${m} probes: ${k} cannot be inserted${st==='quad'?' (quadratic probing does not reach every slot)':''}.`;failed.push(k);}
    else{n++;seen.add(k);}
    rows.push(r);steps.push(Object.assign({table:snapT(table)},r));
  }
  return {table,rows,steps,probeColl,keyColl,failed,n,m,load:n/m};
}
function snapT(t){return t.map(x=>Array.isArray(x)?x.slice():x);}
NETSOLVE.hashprobe={run:hashRun,mod};

/* =====================================================================
   5. INFIX / POSTFIX / PREFIX
   ===================================================================== */
const PREC={'^':3,'*':2,'/':2,'%':2,'+':1,'-':1};
function itok(s){
  s=String(s==null?'':s).replace(/[↑$]/g,'^').replace(/[×]/g,'*').replace(/[÷]/g,'/').replace(/[−]/g,'-');
  const out=[];let i=0;
  while(i<s.length){
    const c=s[i];
    if(/\s/.test(c)){i++;continue;}
    if(/[A-Za-z0-9_.]/.test(c)){let j=i;while(j<s.length&&/[A-Za-z0-9_.]/.test(s[j]))j++;out.push({t:'v',s:s.slice(i,j)});i=j;continue;}
    if(PREC[c]){out.push({t:'o',s:c});i++;continue;}
    if('([{'.includes(c)){out.push({t:'(',s:'('});i++;continue;}
    if(')]}'.includes(c)){out.push({t:')',s:')'});i++;continue;}
    return {err:`Unexpected character “${c}”.`};
  }
  return {toks:out};
}
function checkInfix(tk){
  if(!tk.length)return 'Enter an infix expression, e.g. A+B*C.';
  if(tk.length>60)return 'Use at most 60 tokens.';
  let want=true,depth=0;
  for(const t of tk){
    if(want){
      if(t.t==='v')want=false;
      else if(t.t==='(')depth++;
      else if(t.t==='o')return `Operator “${t.s}” has no left operand. Unary minus is not supported: write (0-x).`;
      else return 'Empty parentheses or a “)” right after an operator.';
    }else{
      if(t.t==='o')want=true;
      else if(t.t===')'){depth--;if(depth<0)return 'A “)” has no matching “(”.';}
      else return `Missing operator before “${t.s}”.`;
    }
  }
  if(want)return 'The expression ends with an operator.';
  if(depth>0)return 'A “(” is never closed.';
  return null;
}
function infixConvert(expr,o){
  o=o||{};const rightPow=o.powAssoc!=='left';
  const r=itok(expr);if(r.err)return {err:r.err};
  const e=checkInfix(r.toks);if(e)return {err:e};
  const tk=r.toks;const isR=op=>op==='^'&&rightPow;
  /* postfix */
  const st=[],out=[],post=[];
  for(const t of tk){
    let act;
    if(t.t==='v'){out.push(t.s);act='Operand: append to output.';}
    else if(t.t==='('){st.push('(');act='Push “(”.';}
    else if(t.t===')'){const p=[];while(st.length&&st[st.length-1]!=='('){const x=st.pop();out.push(x);p.push(x);}st.pop();act=(p.length?`Pop ${p.join(' ')} to output until “(”, `:'Pop until “(”: nothing in between, ')+'discard the “(”.';}
    else{const p=[];while(st.length){const top=st[st.length-1];if(top==='(')break;if(PREC[top]>PREC[t.s]||(PREC[top]===PREC[t.s]&&!isR(t.s))){p.push(st.pop());out.push(p[p.length-1]);}else break;}
      st.push(t.s);act=(p.length?`Pop ${p.join(' ')} (${p.length>1?'they have':'it has'} precedence ${isR(t.s)?'>':'≥'} “${t.s}”), then push “${t.s}”.`:`Push “${t.s}”.`);}
    post.push({tok:t.s,act,stack:st.slice(),out:out.slice()});
  }
  if(st.length){const p=[];while(st.length){const x=st.pop();out.push(x);p.push(x);}post.push({tok:'end',act:`End of input: pop ${p.join(' ')} to output.`,stack:[],out:out.slice()});}
  const postfix=out.slice();
  /* prefix: scan right to left, then reverse */
  const st2=[],out2=[],pre=[];
  for(let i=tk.length-1;i>=0;i--){
    const t=tk[i];let act;
    if(t.t==='v'){out2.push(t.s);act='Operand: append to output.';}
    else if(t.t===')'){st2.push(')');act='Scanning right to left, “)” opens a group: push it.';}
    else if(t.t==='('){const p=[];while(st2.length&&st2[st2.length-1]!==')'){const x=st2.pop();out2.push(x);p.push(x);}st2.pop();act=(p.length?`Pop ${p.join(' ')} to output until “)”, `:'Pop until “)”, ')+'discard it.';}
    else{const p=[];while(st2.length){const top=st2[st2.length-1];if(top===')')break;if(PREC[top]>PREC[t.s]||(PREC[top]===PREC[t.s]&&isR(t.s))){p.push(st2.pop());out2.push(p[p.length-1]);}else break;}
      st2.push(t.s);act=(p.length?`Pop ${p.join(' ')} (precedence ${isR(t.s)?'≥':'>'} “${t.s}”), then push “${t.s}”.`:`Push “${t.s}”.`);}
    pre.push({tok:t.s,act,stack:st2.slice(),out:out2.slice()});
  }
  if(st2.length){const p=[];while(st2.length){const x=st2.pop();out2.push(x);p.push(x);}pre.push({tok:'end',act:`End of input: pop ${p.join(' ')} to output.`,stack:[],out:out2.slice()});}
  const prefix=out2.slice().reverse();
  pre.push({tok:'reverse',act:'Reverse the output to get the prefix expression.',stack:[],out:prefix.slice(),final:true});
  const numeric=tk.every(t=>t.t!=='v'||/^\d+(\.\d+)?$/.test(t.s));
  return {tokens:tk.map(t=>t.s),postfix,prefix,postTrace:post,preTrace:pre,numeric,rightPow};
}
function postTok(s){
  s=String(s==null?'':s).trim().replace(/[↑$]/g,'^').replace(/[×]/g,'*').replace(/[÷]/g,'/').replace(/[−]/g,'-');
  if(!s)return [];
  return /\s|,/.test(s)?s.split(/[\s,]+/).filter(Boolean):s.split('');
}
function evalPostfix(tokens,o){
  o=o||{};const intDiv=o.div==='int';const st=[],rows=[];
  if(!tokens.length)return {err:'Enter a postfix expression, e.g. 2 3 4 * +.'};
  if(tokens.length>80)return {err:'Use at most 80 tokens.'};
  for(const t of tokens){
    if(/^-?\d+(\.\d+)?$/.test(t)){st.push(Number(t));rows.push({tok:t,act:`Push ${fmtN(Number(t))}.`,stack:st.slice()});continue;}
    if(!PREC[t])return {err:`“${t}” is not a number or an operator (+ − * / % ^). Separate multi-digit numbers with spaces.`,rows};
    if(st.length<2)return {err:`Operator “${t}” needs two operands but the stack holds ${st.length}.`,rows};
    const b=st.pop(),a=st.pop();let v;
    if((t==='/'||t==='%')&&b===0)return {err:`Division by zero at “${fmtN(a)} ${t} 0”.`,rows};
    if(t==='+')v=a+b;else if(t==='-')v=a-b;else if(t==='*')v=a*b;
    else if(t==='/')v=intDiv?Math.trunc(a/b):a/b;else if(t==='%')v=a%b;else v=Math.pow(a,b);
    if(!isFinite(v))return {err:`The result of ${fmtN(a)} ${t} ${fmtN(b)} is too large.`,rows};
    st.push(v);rows.push({tok:t,act:`Pop ${fmtN(b)} (right) and ${fmtN(a)} (left); push ${fmtN(a)} ${t} ${fmtN(b)} = ${fmtN(v)}.`,stack:st.slice(),calc:[a,t,b,v]});
  }
  if(st.length!==1)return {err:`The expression leaves ${st.length} values on the stack; it needs exactly one. Check the operator count.`,rows};
  return {value:st[0],rows};
}
NETSOLVE.infix={convert:infixConvert,evalPostfix,postTok,tokenize:itok};

/* =====================================================================
   UI (browser only)
   ===================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=ANIM.esc;
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=arr=>arr[Math.floor(Math.random()*arr.length)];
function field(label,inner,cls,show){return `<label class="dsa-f${cls?' '+cls:''}"${show?` data-show="${show}"`:''}><span>${label}</span>${inner}</label>`;}
function sel(name,opts,val){return `<select data-f="${name}">${opts.map(([v,t])=>`<option value="${v}"${v===val?' selected':''}>${t}</option>`).join('')}</select>`;}
function inp(name,val,o){o=o||{};return `<input data-f="${name}" type="${o.type||'text'}" value="${E(val)}"${o.min!=null?` min="${o.min}"`:''}${o.max!=null?` max="${o.max}"`:''}${o.size?` size="${o.size}"`:''} spellcheck="false" autocomplete="off"${o.aria?` aria-label="${o.aria}"`:''}>`;}
function chk(name,label,on,show){return `<label class="dsa-chk"${show?` data-show="${show}"`:''}><input type="checkbox" data-f="${name}"${on?' checked':''}> <span>${label}</span></label>`;}
function segH(name,opts,val){return `<div class="dsa-seg" role="group" data-seg="${name}">${opts.map(([v,t])=>`<button type="button" data-v="${v}" aria-pressed="${v===val}">${t}</button>`).join('')}</div>`;}
function kpi(k,v,wide){return `<div class="dsa-kpi${wide?' wide':''}"><span>${k}</span><b>${v}</b></div>`;}
function errBox(m){return `<div class="dsa-err" role="alert">${E(m)}</div>`;}
function conv(list){return `<ul class="dsa-conv">${list.map(c=>`<li>${c}</li>`).join('')}</ul>`;}
function T(heads,rows,o){o=o||{};return `<div class="dsa-scroll"><table class="dsa-t${o.cls?' '+o.cls:''}"><thead><tr>${heads.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map((r,i)=>`<tr data-r="${o.rowId?o.rowId(i):i}">${r.map((c,j)=>`<td${o.wrap&&o.wrap.includes(j)?' class="w"':''}>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
const f=fmtN;
/* shared step-through control */
function stepper(host,n,render,o){
  o=o||{};
  host.innerHTML=`<div class="dsa-sc"><div class="dsa-sbar"><button type="button" class="btn sm" data-a="first" aria-label="First step">⏮</button><button type="button" class="btn sm" data-a="prev" aria-label="Previous step">◀</button><button type="button" class="btn sm primary" data-a="play">▶ Play</button><button type="button" class="btn sm" data-a="next" aria-label="Next step">▶|</button><button type="button" class="btn sm" data-a="last" aria-label="Last step">⏭</button><span class="dsa-sn" aria-live="polite"></span><input type="range" min="0" max="${Math.max(0,n-1)}" value="0" aria-label="Step"></div><div class="dsa-sbody"></div></div>`;
  const body=host.querySelector('.dsa-sbody'),sn=host.querySelector('.dsa-sn'),rng=host.querySelector('input[type=range]'),pl=host.querySelector('[data-a=play]');
  let i=0,tm=null;
  const go=k=>{i=Math.max(0,Math.min(n-1,k));rng.value=i;sn.textContent=`${o.label||'Step'} ${i+1} of ${n}`;render(i,body);};
  const stop=()=>{if(tm){clearInterval(tm);tm=null;}pl.textContent='▶ Play';pl.setAttribute('aria-label','Play');};
  pl.onclick=()=>{if(tm){stop();return;}if(i>=n-1)go(0);pl.textContent='❚❚ Pause';pl.setAttribute('aria-label','Pause');tm=setInterval(()=>{if(!host.isConnected||i>=n-1){stop();return;}go(i+1);},o.ms||1500);};
  host.querySelector('[data-a=first]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-a=prev]').onclick=()=>{stop();go(i-1);};
  host.querySelector('[data-a=next]').onclick=()=>{stop();go(i+1);};
  host.querySelector('[data-a=last]').onclick=()=>{stop();go(n-1);};
  rng.oninput=()=>{stop();go(+rng.value);};
  go(o.start==='first'?0:n-1);
  return {stop,go};
}
/* wire a playground: returns helpers */
function wire(stage,run){
  const F=n=>stage.querySelector(`[data-f="${n}"]`);
  const segV=n=>{const b=stage.querySelector(`[data-seg="${n}"] [aria-pressed="true"]`);return b?b.dataset.v:null;};
  stage.querySelectorAll('[data-seg]').forEach(s=>s.querySelectorAll('button').forEach(b=>b.onclick=()=>{s.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));run('seg:'+s.dataset.seg);}));
  let t=null;
  stage.addEventListener('input',e=>{if(!e.target.matches('[data-f]'))return;if(e.target.tagName==='SELECT'||e.target.type==='checkbox')return;clearTimeout(t);t=setTimeout(()=>run('input'),350);});
  stage.addEventListener('change',e=>{if(!e.target.matches('[data-f]'))return;clearTimeout(t);run('change:'+e.target.dataset.f);});
  const showOnly=(key)=>stage.querySelectorAll('[data-show]').forEach(el=>{el.hidden=!el.dataset.show.split(' ').includes(key);});
  return {F,segV,showOnly};
}
const markRow=(root,i)=>root.querySelectorAll('.dsa-work [data-r]').forEach(tr=>tr.classList.toggle('on',tr.dataset.r===String(i)));

/* ---------------- sorttrace ---------------- */
ANIM.register('sorttrace',{title:'Sorting pass-trace solver',steps:false,
 caption:'Type your own array, choose an algorithm and step through each pass. The comparison and swap counts follow the conventions listed.',
 build(stage){
  stage.style.padding='0';
  const DEF='38 27 43 3 9 82 10';
  stage.innerHTML=`<div class="dsa-wrap">
   <div class="dsa-ctrls">
    ${field('Array (spaces or commas)',inp('arr',DEF),'dsa-grow')}
    ${field('Algorithm',sel('algo',Object.entries(SORT_NAMES),'bubble'))}
    ${field('Partition scheme',sel('scheme',[['lomuto','Lomuto'],['hoare','Hoare']],'lomuto'),'','quick')}
    ${field('Pivot',sel('pivot',[['last','Last element'],['first','First element'],['middle','Middle element']],'last'),'','quick')}
    ${field('Merge style',sel('mstyle',[['td','Top-down (recursive)'],['bu','Bottom-up (passes)']],'td'),'','merge')}
    ${chk('early','Stop when a pass makes no swaps',true,'bubble')}
   </div>
   <div class="dsa-btns"><button type="button" class="btn sm" data-b="rand">Random example</button><button type="button" class="btn sm" data-b="reset">Default example</button></div>
   <div class="dsa-out"></div></div>`;
  const out=stage.querySelector('.dsa-out');let sp=null;
  const W=wire(stage,why=>{if(why==='change:scheme')W.F('pivot').value=W.F('scheme').value==='hoare'?'first':'last';run();});
  stage.querySelector('[data-b=rand]').onclick=()=>{const n=rnd(6,9),alg=W.F('algo').value;const hi=alg==='counting'?9:alg==='radix'?999:99;W.F('arr').value=Array.from({length:n},()=>rnd(alg==='counting'?0:1,hi)).join(' ');run();};
  stage.querySelector('[data-b=reset]').onclick=()=>{W.F('arr').value=DEF;run();};
  const LEG={ok:'final / sorted part',sw:'moved in this step',pv:'pivot / heapified node',key:'inserted key',dim:'outside the current sub-array',lp:'left part after the split',emp:'empty output slot'};
  function run(){
    if(sp)sp.stop();
    const algo=W.F('algo').value;W.showOnly(algo);
    const p=parseInts(W.F('arr').value,{min:1,max:24,name:'numbers'});
    if(p.err){out.innerHTML=errBox(p.err);return;}
    const o={early:W.F('early').checked,scheme:W.F('scheme').value,pivot:W.F('pivot').value,mstyle:W.F('mstyle').value};
    const r=sortTrace(p.vals,algo,o);
    if(r.err){out.innerHTML=errBox(r.err);return;}
    const I=SORT_INFO[algo],mv=r.moveName;
    const C=['Sorting in ascending order; indices start at 0.'];
    if(algo==='bubble')C.push('Each pass compares neighbours a[j], a[j+1] and swaps when a[j] > a[j+1]; one comparison per pair checked.',o.early?'Early stop is on: the sort ends after the first pass with no swaps (that pass is counted).':'Early stop is off: always n − 1 passes.');
    if(algo==='selection')C.push('Pass i finds the minimum of a[i..n−1] (n − 1 − i comparisons) and swaps it to index i.','A swap is counted only when the minimum is not already at index i.');
    if(algo==='insertion')C.push('Every key comparison is counted, including the one that stops the scan.','Moving an element one place right is one shift (insertion sort shifts rather than swaps).');
    if(algo==='quick'){if(o.scheme==='hoare')C.push('Hoare partition: pivot = a[lo]. j moves left while a[j] > pivot, i moves right while a[i] < pivot; swap a[i], a[j] while i < j. Recurse on [lo..j] and [j+1..hi].','Each pointer test is one comparison. The pivot is not necessarily in its final place after a partition.');
      else C.push('Lomuto partition (CLRS): pivot = a[hi]; for j = lo..hi−1, if a[j] ≤ pivot then i++ and swap a[i], a[j]; finally swap a[i+1], a[hi].','One comparison per a[j] tested. A swap is counted only when two different positions exchange.');
      if(o.pivot!==(o.scheme==='hoare'?'first':'last'))C.push(`The chosen pivot is first swapped to the ${o.scheme==='hoare'?'front':'end'} (counted as a swap).`);}
    if(algo==='merge')C.push('A comparison is counted each time the heads of the two runs are compared. On a tie the left element goes first (stable).',o.mstyle==='bu'?'Bottom-up: pass k merges runs of length 2^(k−1); a leftover run at the end is carried over. Passes = ⌈log₂ n⌉.':'Top-down: mid = ⌊(lo + hi) / 2⌋, left half sorted first.','Writes = elements copied back into the array.');
    if(algo==='heap')C.push('Ascending order uses a max-heap built bottom-up: heapify(i) for i = ⌊n/2⌋ − 1 down to 0. Children of i are 2i + 1 and 2i + 2.','Each child test in sift-down is one comparison; the root↔last exchange and every sift-down exchange count as swaps.');
    if(algo==='counting')C.push('No key comparisons. C is indexed by value from min to max, made cumulative, and elements are placed from right to left (this keeps the sort stable).','Writes = elements placed in the output array.');
    if(algo==='radix')C.push('LSD radix sort in base 10: one stable bucket pass per digit, from the units digit up; numbers are padded with leading zeros for display.','No key comparisons; writes = n per pass.');
    out.innerHTML=`<div class="dsa-ans">${kpi('Sorted',`[${r.sorted.map(f).join(', ')}]`,1)}${kpi('Comparisons',r.comps)}${kpi(mv[0].toUpperCase()+mv.slice(1),r.swaps)}${kpi(r.passLabel,r.steps.length-1)}</div>
     <div class="dsa-chips"><span class="pill">${I.stable?'Stable':'Not stable'}</span><span class="pill">${I.inplace?'In place':'Needs extra space'}</span><span class="pill">Best ${I.best}</span><span class="pill">Average ${I.avg}</span><span class="pill">Worst ${I.worst}</span></div>
     <div class="dsa-lbl">Conventions</div>${conv(C)}
     <div class="dsa-lbl">Step through</div><div class="dsa-stp"></div>
     <div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Step','Array after the step','Comparisons',mv[0].toUpperCase()+mv.slice(1)],r.steps.map((s,i)=>{const pr=r.steps[i-1]||{comps:0,swaps:0};return [i,E(s.title),`<span class="sorttrace-row">${s.arr.map((v,k)=>`<span class="${s.cls[k]||''}">${v==null?'_':E(radixFmt(v,s))}</span>`).join(' ')}</span>`,i?`${s.comps-pr.comps} <small>(Σ ${s.comps})</small>`:'—',i?`${s.swaps-pr.swaps} <small>(Σ ${s.swaps})</small>`:'—'];}))}</div>`;
    function radixFmt(v,s){return s.width?String(v).padStart(s.width,'0'):f(v);}
    sp=stepper(out.querySelector('.dsa-stp'),r.steps.length,(i,body)=>{
      const s=r.steps[i];
      const cell=(v,k)=>{let txt=v==null?'':E(radixFmt(v,s));if(s.width&&v!=null){const str=String(v).padStart(s.width,'0'),pos=s.width-1-s.digit;txt=E(str.slice(0,pos))+'<u>'+E(str[pos])+'</u>'+E(str.slice(pos+1));}return `<div class="sorttrace-c ${s.cls[k]||''}${v==null?' emp':''}"><b>${txt}</b><small>${k}</small></div>`;};
      const aux=(s.aux||[]).map(a=>`<div class="dsa-lbl2">${E(a.label)}</div><div class="dsa-scroll"><table class="dsa-t sorttrace-aux"><tr><th>${a.label==='Bucket'?'digit':a.label==='A'?'index':'value'}</th>${a.heads.map((h,k)=>`<th class="${k===a.hi?'on':''}">${E(h)}</th>`).join('')}</tr><tr><td>${a.label==='Bucket'?'keys':a.label}</td>${a.vals.map((v,k)=>`<td class="${k===a.hi?'on':''}">${E(v)}</td>`).join('')}</tr></table></div>`).join('');
      const used=[...new Set(s.cls.filter(Boolean))].filter(c=>LEG[c]);
      body.innerHTML=`<div class="dsa-st">${E(s.title)}</div>${s.arrLabel?`<div class="dsa-lbl2">${s.arrLabel}</div>`:''}<div class="dsa-scroll"><div class="sorttrace-arr">${s.arr.map(cell).join('')}</div></div>${used.length?`<div class="sorttrace-leg">${used.map(c=>`<span><i class="sorttrace-c ${c}"></i>${LEG[c]}</span>`).join('')}</div>`:''}${aux}<p class="dsa-note">${E(s.note)}</p><div class="dsa-run">Comparisons so far: <b>${s.comps}</b> · ${mv} so far: <b>${s.swaps}</b></div>`;
      markRow(out,i);
    });
  }
  run();
 }});

/* ---------------- tree drawing (shared by treeops) ---------------- */
function treeView(host){
  host.innerHTML='<div class="dsa-scroll"><div class="treeops-fig"><svg class="treeops-svg" aria-hidden="true"></svg><div class="treeops-empty" hidden>Empty tree</div></div></div>';
  const fig=host.querySelector('.treeops-fig'),svg=host.querySelector('svg'),empty=host.querySelector('.treeops-empty');const map=new Map();
  return function(root,o){
    o=o||{};const list=[];let x=0;
    (function go(n,d,par){if(!n)return;go(n.l,d+1,n);const it={n,x:x++,d,par};list.push(it);go(n.r,d+1,n);})(root,0,null);
    const GX=42,GY=58,PAD=24;const maxD=list.reduce((m,it)=>Math.max(m,it.d),0);
    const W=Math.max(120,x*GX+PAD),H=list.length?(maxD*GY+PAD*2+(o.sub?14:0)):60;
    fig.style.width=W+'px';fig.style.height=H+'px';svg.setAttribute('width',W);svg.setAttribute('height',H);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    empty.hidden=!!list.length;
    const pos=new Map();list.forEach(it=>pos.set(it.n,{x:PAD/2+it.x*GX+GX/2,y:PAD+it.d*GY}));
    svg.innerHTML=list.filter(it=>it.par).map(it=>{const a=pos.get(it.par),b=pos.get(it.n);return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`;}).join('');
    svg.classList.remove('treeops-in');svg.getBoundingClientRect();svg.classList.add('treeops-in');
    const keep=new Set();
    list.forEach(it=>{
      const id=o.id?o.id(it.n):String(it.n.k);keep.add(id);let el=map.get(id);
      const p=pos.get(it.n);
      if(!el){el=document.createElement('div');el.className='treeops-n';map.set(id,el);fig.appendChild(el);el.style.left=(p.x-16)+'px';el.style.top=(p.y-16)+'px';el.classList.add('enter');}
      el.style.left=(p.x-16)+'px';el.style.top=(p.y-16)+'px';
      const c=o.cls?o.cls(it.n):'';el.className='treeops-n'+(c?' '+c:'');
      const sub=o.sub?o.sub(it.n):null;
      el.innerHTML=`<b>${E(it.n.k)}</b>${sub!=null?`<i>${E(sub)}</i>`:''}`;
      el.setAttribute('aria-label',`node ${it.n.k}`);
    });
    for(const [id,el] of map)if(!keep.has(id)){el.remove();map.delete(id);}
  };
}

/* ---------------- treeops ---------------- */
ANIM.register('treeops',{title:'Tree operations solver: BST, AVL, heap',steps:false,
 caption:'Insert and delete keys one at a time, watch the tree change and read off all four traversals. The Rebuild tab reconstructs a tree from two traversals.',
 build(stage){
  stage.style.padding='0';
  const DEF={bst:'50 30 70 20 40 60 80 35 -30 -50',avl:'10 20 30 40 50 25 -40',heap:'4 1 3 2 16 9 10 14 8 7 x',ino:'D B E A F C',seq:'A B D E C F'};
  stage.innerHTML=`<div class="dsa-wrap">
   <div class="dsa-ctrls">
    <div class="dsa-f"><span>Structure</span>${segH('mode',[['bst','BST'],['avl','AVL'],['heap','Heap'],['rebuild','Rebuild']],'bst')}</div>
    ${field('Operations: key inserts, −key deletes',inp('ops',DEF.bst),'dsa-grow','bst')}
    ${field('Operations: key inserts, −key deletes',inp('aops',DEF.avl),'dsa-grow','avl')}
    ${field('Two-child delete uses',sel('rep',[['succ','Inorder successor'],['pred','Inorder predecessor']],'succ'),'','bst avl')}
    ${field('Operations: key inserts, x deletes the root, −key deletes a key',inp('hops',DEF.heap),'dsa-grow','heap')}
    ${field('Heap type',sel('hk',[['max','Max-heap'],['min','Min-heap']],'max'),'','heap')}
    ${field('Leading keys',sel('hb',[['build','Build-heap (bottom-up, O(n))'],['ins','Insert one by one']],'build'),'','heap')}
    ${field('Inorder',inp('ino',DEF.ino),'dsa-grow','rebuild')}
    ${field('Second traversal',sel('ok',[['pre','Preorder'],['post','Postorder']],'pre'),'','rebuild')}
    ${field('Sequence',inp('seq',DEF.seq),'dsa-grow','rebuild')}
   </div>
   <div class="dsa-btns"><button type="button" class="btn sm" data-b="rand">Random example</button><button type="button" class="btn sm" data-b="reset">Default example</button></div>
   <div class="dsa-out"></div></div>`;
  const out=stage.querySelector('.dsa-out');let sp=null;
  const W=wire(stage,why=>{if(why==='change:ok'){const t=rebuildTree(toks(W.F('ino').value),toks(W.F('seq').value),W.F('ok').value==='pre'?'post':'pre');if(t.root){const tr=trav(t.root);W.F('seq').value=(W.F('ok').value==='pre'?tr.pre:tr.post).join(' ');}}run();});
  const uniq=(n,lo,hi)=>{const s=new Set();while(s.size<n)s.add(rnd(lo,hi));return [...s];};
  stage.querySelector('[data-b=rand]').onclick=()=>{
    const m=W.segV('mode');
    if(m==='bst'){const k=uniq(rnd(7,10),1,99);W.F('ops').value=k.join(' ')+' -'+pick(k)+' -'+k[0];}
    else if(m==='avl'){const k=uniq(rnd(7,10),1,99);W.F('aops').value=k.join(' ')+' -'+pick(k);}
    else if(m==='heap'){W.F('hops').value=uniq(rnd(7,10),1,99).join(' ')+' x x';}
    else{const k=uniq(rnd(6,9),1,99);let root=null;k.forEach(v=>root=bstIns(root,v));const tr=trav(root);const L='ABCDEFGHIJ';const nm={};tr.ino.forEach((v,i)=>nm[v]=L[i]);
      /* random shape: relabel by inorder so the letters are not sorted order in preorder */
      W.F('ino').value=tr.ino.map(v=>nm[v]).join(' ');W.F('seq').value=(W.F('ok').value==='pre'?tr.pre:tr.post).map(v=>nm[v]).join(' ');}
    run();};
  stage.querySelector('[data-b=reset]').onclick=()=>{W.F('ops').value=DEF.bst;W.F('aops').value=DEF.avl;W.F('hops').value=DEF.heap;W.F('ino').value=DEF.ino;W.F('seq').value=DEF.seq;W.F('ok').value='pre';run();};
  const travBlock=t=>`<div class="dsa-ans">${kpi('Inorder',E(t.ino.join(' '))||'—',1)}${kpi('Preorder',E(t.pre.join(' '))||'—',1)}${kpi('Postorder',E(t.post.join(' '))||'—',1)}${kpi('Level order',E(t.lvl.join(' '))||'—',1)}</div>`;
  function run(){
    if(sp)sp.stop();
    const mode=W.segV('mode');W.showOnly(mode);
    if(mode==='bst'||mode==='avl'){
      const p=parseTreeOps(W.F(mode==='bst'?'ops':'aops').value,false);if(p.err){out.innerHTML=errBox(p.err);return;}
      const r=treeRun(mode,p.ops,{rep:W.F('rep').value});
      const C=['Keys smaller than a node go left, larger go right; duplicates are ignored.',`A node with two children is replaced by its inorder ${W.F('rep').value==='succ'?'successor (smallest key of the right subtree)':'predecessor (largest key of the left subtree)'}.`,'Height is counted in edges: a single node has height 0, an empty tree −1.'];
      if(mode==='avl')C.push('Balance factor = height(left) − height(right), shown under each node; a node is unbalanced at ±2.','Rotations are named by the path from the unbalanced node to its taller child: LL and RR need one rotation, LR and RL need two. After a delete, when the taller child has balance 0, the single rotation (LL/RR) is used.','After a delete, rebalancing continues up to the root (several rotations are possible).');
      out.innerHTML=travBlock(r.trav)+`<div class="dsa-ans">${kpi('Nodes',r.count)}${kpi('Height',r.height)}${mode==='avl'?kpi('Rotations',r.rots.length?r.rots.map(x=>`${x.kase} at ${x.at}`).join(', '):'none',1):''}</div>
       <div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div>
       <div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Operation','What happens','Level order after'],r.steps.map((s,i)=>[i,E(s.title),s.note.replace(/<(?!\/?b>)/g,'&lt;'),E(trav(s.tree).lvl.join(' '))||'—']),{wrap:[2]})}</div>`;
      let view;
      sp=stepper(out.querySelector('.dsa-stp'),r.steps.length,(i,body)=>{
        const s=r.steps[i];
        if(!body.querySelector('.treeops-host')){body.innerHTML='<div class="dsa-st"></div><div class="treeops-host"></div><p class="dsa-note"></p><div class="treeops-tv"></div>';view=treeView(body.querySelector('.treeops-host'));}
        body.querySelector('.dsa-st').textContent=s.title;
        view(s.tree,{cls:n=>{const b=mode==='avl'?tbf(n):0;return (Math.abs(b)>1?'bad ':'')+(s.hi[n.k]||'');},sub:mode==='avl'?(n=>{const b=tbf(n);return b>0?'+'+b:b<0?'−'+(-b):'0';}):null});
        body.querySelector('.dsa-note').innerHTML=s.note.replace(/<(?!\/?b>)/g,'&lt;');
        const t=trav(s.tree);body.querySelector('.treeops-tv').innerHTML=`<span>Inorder: <b>${E(t.ino.join(' '))||'—'}</b></span><span>Preorder: <b>${E(t.pre.join(' '))||'—'}</b></span><span>Postorder: <b>${E(t.post.join(' '))||'—'}</b></span><span>Level: <b>${E(t.lvl.join(' '))||'—'}</b></span>`;
        markRow(out,i);
      });
    }else if(mode==='heap'){
      const p=parseTreeOps(W.F('hops').value,true);if(p.err){out.innerHTML=errBox(p.err);return;}
      const kind=W.F('hk').value,build=W.F('hb').value;
      const r=heapRun(p.ops,{kind,build});const t=trav(heapToTree(r.arr));
      const C=['The heap is stored level by level in an array a[0..n−1]: children of i are 2i + 1 and 2i + 2, the parent of i is ⌊(i − 1)/2⌋.',build==='build'?'The keys before the first x / −key are loaded as they are and turned into a heap bottom-up: heapify(i) for i = ⌊n/2⌋ − 1 down to 0 (Floyd, O(n)). Later keys are inserted one by one.':'Every key is inserted one at a time: add it at the next leaf and sift it up (O(log n) each).',`Delete root: move the last key to the root and sift it down, swapping with the ${kind==='max'?'larger':'smaller'} child. On equal children the left child is chosen.`,'−key deletes that key: it is replaced by the last key, which then sifts up or down.'];
      out.innerHTML=`<div class="dsa-ans">${kpi('Final array',`[${r.arr.map(f).join(', ')}]`,1)}${kpi('Swaps',r.swaps)}${kpi('Comparisons',r.comps)}${kpi('Size',r.arr.length)}</div>${travBlock(t)}
       <div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div>
       <div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Operation','What happens','Array after'],r.steps.map((s,i)=>[i,E(s.title),E(s.note),`[${s.arr.map(f).join(', ')}]`]),{wrap:[2]})}</div>`;
      let view;
      sp=stepper(out.querySelector('.dsa-stp'),r.steps.length,(i,body)=>{
        const s=r.steps[i];
        if(!body.querySelector('.treeops-host')){body.innerHTML='<div class="dsa-st"></div><div class="treeops-host"></div><div class="dsa-scroll"><div class="treeops-arr"></div></div><p class="dsa-note"></p>';view=treeView(body.querySelector('.treeops-host'));}
        body.querySelector('.dsa-st').textContent=s.title;
        view(heapToTree(s.arr),{id:n=>'i'+n.i,cls:n=>s.hi[n.i]||'',sub:n=>n.i});
        body.querySelector('.treeops-arr').innerHTML=s.arr.length?s.arr.map((v,k)=>`<div class="sorttrace-c ${s.hi[k]==='new'?'ok':s.hi[k]?'sw':''}"><b>${f(v)}</b><small>${k}</small></div>`).join(''):'<span class="dsa-muted">empty array</span>';
        body.querySelector('.dsa-note').textContent=s.note;
        markRow(out,i);
      });
    }else{
      const ino=toks(W.F('ino').value),seq=toks(W.F('seq').value),kind=W.F('ok').value;
      if(ino.length>20){out.innerHTML=errBox('Use at most 20 nodes.');return;}
      const r=rebuildTree(ino,seq,kind);
      if(r.err){out.innerHTML=errBox(r.err);return;}
      const C=[kind==='pre'?'The first key of a preorder segment is the root of that subtree.':'The last key of a postorder segment is the root of that subtree.','The root splits the inorder segment into the left subtree (keys before it) and the right subtree (keys after it); segment sizes carry over to the other traversal.','Keys must be distinct. Preorder + postorder alone would not give a unique tree, so inorder is always required.'];
      const order=r.order;const shown=new Set();
      out.innerHTML=travBlock(r.trav)+`<div class="dsa-ans">${kpi('Nodes',ino.length)}${kpi('Height',r.height)}</div>
       <div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div>
       <div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Root','Left subtree (inorder)','Right subtree (inorder)'],order.map((s,i)=>[i+1,`<b>${E(s.k)}</b>`,E(s.left.join(' '))||'—',E(s.right.join(' '))||'—']),{rowId:i=>i+1})}</div>`;
      /* partial trees: keep only nodes created so far */
      const partial=k=>{const keep=new Set(order.slice(0,k).map(s=>s.k));const cp=n=>n&&keep.has(n.k)?{k:n.k,l:cp(n.l),r:cp(n.r)}:null;return cp(r.root);};
      let view;
      sp=stepper(out.querySelector('.dsa-stp'),order.length+1,(i,body)=>{
        if(!body.querySelector('.treeops-host')){body.innerHTML='<div class="dsa-st"></div><div class="treeops-host"></div><p class="dsa-note"></p>';view=treeView(body.querySelector('.treeops-host'));}
        const s=order[i-1];
        body.querySelector('.dsa-st').textContent=i?`Place ${s.k}`:'Start';
        view(partial(i),{cls:n=>s&&n.k===s.k?'new':''});
        body.querySelector('.dsa-note').textContent=i?`${kind==='pre'?'Preorder':'Postorder'} segment [${s.seg.join(' ')}]: its ${kind==='pre'?'first':'last'} key ${s.k} is the root. Inorder splits into left [${s.left.join(' ')||'empty'}] and right [${s.right.join(' ')||'empty'}].`:`Inorder: ${ino.join(' ')}; ${kind==='pre'?'preorder':'postorder'}: ${seq.join(' ')}.`;
        markRow(out,i);
      },{label:'Step'});
    }
  }
  run();
 }});

/* ---------------- graph drawing ---------------- */
let gUid=0;
function drawGraph(G,st){
  st=st||{};const uid='ga'+(++gUid);const V=G.V,n=V.length,P={};const R=n<=2?70:112,C=150;
  V.forEach((v,i)=>{const a=-Math.PI/2+2*Math.PI*i/n;P[v]={x:C+(n===1?0:R*Math.cos(a)),y:C+(n===1?0:R*Math.sin(a)),a};});
  const S=k=>new Set(st[k]||[]);const on=S('on'),cur=S('curE'),rej=S('rej'),rejE=S('rejE'),dim=S('dimE');
  const has=new Set(G.E.map(e=>e.u+'>'+e.v));
  const mk=(c)=>`<marker id="${uid}-${c}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" class="graphalgo-mk ${c}"/></marker>`;
  let edges='',labels='';
  for(const e of G.E){
    const a=P[e.u],b=P[e.v];const dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy)||1,ux=dx/L,uy=dy/L,nx=-uy,ny=ux;
    const curved=G.directed&&has.has(e.v+'>'+e.u);const off=curved?20:0;
    const cx=(a.x+b.x)/2+nx*off,cy=(a.y+b.y)/2+ny*off;
    const r1=18,r2=G.directed?21:18;
    const t1x=cx-a.x,t1y=cy-a.y,l1=Math.hypot(t1x,t1y)||1,t2x=b.x-cx,t2y=b.y-cy,l2=Math.hypot(t2x,t2y)||1;
    const x1=a.x+t1x/l1*r1,y1=a.y+t1y/l1*r1,x2=b.x-t2x/l2*r2,y2=b.y-t2y/l2*r2;
    const c=cur.has(e.id)?'cur':(rej.has(e.id)||rejE.has(e.id))?'rej':on.has(e.id)?'on':dim.has(e.id)?'dim':'';
    const d=curved?`M${x1.toFixed(1)},${y1.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`:`M${x1.toFixed(1)},${y1.toFixed(1)} L${x2.toFixed(1)},${y2.toFixed(1)}`;
    edges+=`<path d="${d}" class="graphalgo-e ${c}"${G.directed?` marker-end="url(#${uid}-${c||'base'})"`:''}/>`;
    const mx=curved?(0.25*a.x+0.5*cx+0.25*b.x):(a.x+b.x)/2+nx*8,my=curved?(0.25*a.y+0.5*cy+0.25*b.y):(a.y+b.y)/2+ny*8;
    if(!st.noW)labels+=`<text x="${mx.toFixed(1)}" y="${(my+4).toFixed(1)}" class="graphalgo-w ${c}">${E(f(e.w))}</text>`;
    if(st.etag&&st.etag[e.id])labels+=`<text x="${mx.toFixed(1)}" y="${(my+15).toFixed(1)}" class="graphalgo-et">${E(st.etag[e.id])}</text>`;
  }
  const done=S('done'),seen=S('seen');let nodes='';
  for(const v of V){
    const p=P[v];const c=v===st.cur?'cur':done.has(v)?'done':seen.has(v)?'seen':'';
    nodes+=`<g class="graphalgo-v ${c}"><circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="17"/><text x="${p.x.toFixed(1)}" y="${(p.y+4.5).toFixed(1)}">${E(v)}</text></g>`;
    if(st.lab&&st.lab[v]!=null){const lx=p.x+(n===1?0:Math.cos(p.a)*34),ly=p.y+(n===1?34:Math.sin(p.a)*34)+4;nodes+=`<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" class="graphalgo-lab">${E(st.lab[v])}</text>`;}
  }
  return `<svg class="graphalgo-svg" viewBox="-18 -18 336 336" role="img" aria-label="Graph drawing"><defs>${['base','on','cur','rej','dim'].map(mk).join('')}</defs>${edges}${labels}${nodes}</svg>`;
}

/* ---------------- graphalgo ---------------- */
const GEX={
  und:'A B 4\nA C 2\nB C 1\nB D 5\nC D 8\nC E 10\nD E 2\nD F 6\nE F 3',
  neg:'S A 6\nS B 7\nA C 5\nA B 8\nA D -4\nC A -2\nB C -3\nB D 9\nD C 7\nD S 2',
  dag:'A C\nB C\nB D\nC E\nD F\nE F\nE G\nF H\nG H'
};
ANIM.register('graphalgo',{title:'Graph algorithm solver',steps:false,
 caption:'Type an edge list, pick an algorithm and a source, then step through the distance tables, queues or edge choices. Vertices are drawn on a circle.',
 build(stage){
  stage.style.padding='0';
  const ALG=[['bfs','BFS'],['dfs','DFS (times, edge types)'],['dijkstra','Dijkstra'],['bellman','Bellman–Ford'],['floyd','Floyd–Warshall'],['prim','Prim (MST)'],['kruskal','Kruskal (MST)'],['topo','Topological sort']];
  stage.innerHTML=`<div class="dsa-wrap">
   <div class="dsa-ctrls">
    <label class="dsa-f graphalgo-ta"><span>Edges: one per line, “u v weight” (weight optional, default 1)</span><textarea data-f="edges" rows="6" spellcheck="false">${E(GEX.und)}</textarea></label>
    <div class="dsa-col">
     ${field('Algorithm',sel('alg',ALG,'dijkstra'))}
     <div class="dsa-f"><span>Edges are</span>${segH('dir',[['u','Undirected'],['d','Directed']],'u')}</div>
     ${field('Source',sel('src',[],''),'','bfs dfs dijkstra bellman prim')}
     ${field('Neighbour order',sel('ord',[['sorted','Alphabetical / numeric'],['input','Edge-list order']],'sorted'),'','bfs dfs dijkstra')}
     ${field('Method',sel('tm',[['kahn','Kahn (in-degree queue)'],['dfs','DFS finishing times']],'kahn'),'','topo')}
    </div>
   </div>
   <div class="dsa-btns"><button type="button" class="btn sm" data-b="rand">Random example</button><button type="button" class="btn sm" data-b="ex">Example for this algorithm</button></div>
   <div class="dsa-out"></div></div>`;
  const out=stage.querySelector('.dsa-out');let sp=null;
  const W=wire(stage,()=>run());
  const setDir=d=>stage.querySelectorAll('[data-seg=dir] button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===d)));
  stage.querySelector('[data-b=ex]').onclick=()=>{const a=W.F('alg').value;
    if(a==='topo'){W.F('edges').value=GEX.dag;setDir('d');}else if(a==='bellman'){W.F('edges').value=GEX.neg;setDir('d');}else{W.F('edges').value=GEX.und;setDir(a==='dfs'?'d':'u');if(a==='dfs')W.F('edges').value='A B\nA D\nB C\nC D\nD B\nE C\nE F\nF E';}
    W.F('src').value='';run();};
  stage.querySelector('[data-b=rand]').onclick=()=>{
    const a=W.F('alg').value;const n=rnd(5,7);const L='ABCDEFG'.slice(0,n).split('');const E2=[];const have=new Set();
    const add=(u,v,w)=>{const k=u<v?u+v:v+u;if(u===v||have.has(k))return;have.add(k);E2.push(`${u} ${v} ${w}`);};
    if(a==='topo'){for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(Math.random()<0.4)add(L[i],L[j],1);for(let i=1;i<n;i++)if(!E2.some(e=>e.split(' ')[1]===L[i]))add(L[i-1],L[i],1);
      const perm=L.slice().sort(()=>Math.random()-0.5);const mp={};L.forEach((v,i)=>mp[v]=perm[i]);W.F('edges').value=E2.map(e=>{const [u,v]=e.split(' ');return mp[u]+' '+mp[v];}).join('\n');setDir('d');}
    else{for(let i=1;i<n;i++)add(L[i],L[rnd(0,i-1)],rnd(1,9));const extra=rnd(2,4);for(let t=0;t<extra*3&&E2.length<n-1+extra;t++)add(pick(L),pick(L),rnd(1,9));
      let lines=E2;if(a==='bellman'){lines=E2.map((e,i)=>{const [u,v,w]=e.split(' ');return i%3===1?`${u} ${v} ${-rnd(1,3)}`:e;});setDir('d');}
      else if(a==='dfs')setDir('d');else setDir('u');
      W.F('edges').value=lines.join('\n');}
    W.F('src').value='';run();};
  function run(){
    if(sp)sp.stop();
    const alg=W.F('alg').value;W.showOnly(alg);
    const directed=W.segV('dir')==='d';
    const G=parseGraph(W.F('edges').value,directed);
    if(G.err){out.innerHTML=errBox(G.err);return;}
    const srcSel=W.F('src');const prev=srcSel.value;srcSel.innerHTML=G.V.map(v=>`<option${v===prev?' selected':''}>${E(v)}</option>`).join('');
    if(!G.V.includes(prev))srcSel.value=G.V[0];
    const src=srcSel.value,ord=W.F('ord').value;
    const C=['Vertices are listed in alphabetical / numeric order; ties between equal choices go to the vertex that comes first.'];
    if(['bfs','dfs','dijkstra'].includes(alg))C.push(ord==='sorted'?'Neighbours are explored in alphabetical / numeric order.':'Neighbours are explored in the order their edges appear in the list.');
    if(!directed&&!['prim','kruskal','floyd'].includes(alg))C.push('Undirected: every edge can be used in both directions.');
    let html='',steps=[],renderStep,work='';
    const V=G.V;
    const pathTxt=(P,v)=>P&&P[v]?P[v].join(' → '):'unreachable';
    if(alg==='bfs'){
      const r=gBFS(G,src,{order:ord});
      C.push('BFS visits vertices level by level with a FIFO queue; a vertex is marked visited when it is enqueued. Level = number of edges from the source.');
      html=`<div class="dsa-ans">${kpi('BFS order',r.order.join(' → '),1)}${kpi('Levels',V.map(v=>`${v}:${f(r.dist[v])}`).join(' '),1)}${kpi('BFS tree edges',r.tree.map(id=>{const e=G.E[id];return e.u+'–'+e.v;}).join(', ')||'none',1)}</div>`+(r.unreached.length?`<p class="dsa-warn">Not reachable from ${E(src)}: ${E(r.unreached.join(', '))}.</p>`:'');
      steps=r.steps;
      work=T(['#','Step','Discovered','Queue after (front → back)','Visited order'],steps.map((s,i)=>[i,E(s.title),E((s.disc||[]).join(', '))||'—',E(s.queue.join(' '))||'empty',E((s.order||[]).join(' '))||'—']));
      renderStep=s=>({g:{cur:s.cur,done:s.order,seen:s.seen,on:s.tree,lab:Object.fromEntries(V.filter(v=>s.dist[v]!==Infinity).map(v=>[v,'L'+s.dist[v]]))},side:`<div class="dsa-lbl2">Queue (front → back)</div><div class="graphalgo-q">${s.queue.length?s.queue.map(v=>`<span class="pill">${E(v)}</span>`).join(''):'<span class="dsa-muted">empty</span>'}</div><div class="dsa-lbl2">Visited order</div><div>${E((s.order||[]).join(' → '))||'—'}</div>`});
    }else if(alg==='dfs'){
      const r=gDFS(G,src,{order:ord});
      C.push('DFS starts at the source, then restarts from the next unvisited vertex in order (a DFS forest). Timestamps start at 1: d = discovery, f = finish.',directed?'Edge types (directed): tree (to an unvisited vertex), back (to an ancestor still open), forward (to a finished descendant, d[u] < d[v]), cross (to a finished vertex with d[v] < d[u]).':'Edge types (undirected): only tree and back edges exist.');
      html=`<div class="dsa-ans">${kpi('Discovery order',r.order.join(' → '),1)}${kpi('Finish order',r.finish.join(' → '),1)}${kpi('Tree / back / forward / cross',`${r.counts.tree} / ${r.counts.back} / ${r.counts.forward} / ${r.counts.cross}`,1)}</div>`+(directed?`<p class="dsa-note">${r.counts.back?'There is a back edge, so the graph has a cycle.':'No back edge: the graph is acyclic (a DAG).'}</p>`:'');
      steps=r.steps;
      work=T(['Vertex','d','f','Parent'],V.map(v=>[E(v),r.d[v],r.f[v],E(r.par[v]||'—')]),{rowId:()=>'x'})+T(['Edge','Type'],G.E.map(e=>[E(e.u+(directed?' → ':' – ')+e.v),`<span class="graphalgo-tag ${r.cls[e.id]}">${r.cls[e.id]}</span>`]),{rowId:()=>'x'})+T(['#','Event','Time'],steps.map((s,i)=>[i+1,E(s.title),s.title.startsWith('Discover')?s.d[s.cur]:s.f[s.cur]]),{rowId:i=>i});
      renderStep=s=>{const lab={};V.forEach(v=>{if(s.d[v]!=null)lab[v]=s.d[v]+'/'+(s.f[v]!=null?s.f[v]:'·');});return {g:{cur:s.cur,done:s.done,seen:s.seen,on:s.tree,lab,etag:null},side:`<div class="dsa-lbl2">Open (grey) vertices</div><div>${E(s.seen.join(' → '))||'none'}</div><div class="dsa-lbl2">Label d/f</div><div class="dsa-muted">discovery / finish time; · = not finished yet</div>`};};
      const last=steps.length-1;const orig=renderStep;renderStep=(s,i)=>{const o=orig(s);if(i===last){o.g.etag=Object.fromEntries(Object.entries(r.cls).map(([id,c])=>[id,c==='tree'?'':c[0].toUpperCase()]));}return o;};
    }else if(alg==='dijkstra'||alg==='bellman'){
      const r=alg==='dijkstra'?gDijkstra(G,src,{order:ord}):gBellman(G,src);
      if(r.err){out.innerHTML=errBox(r.err);return;}
      if(alg==='dijkstra')C.push('Each step finalises the unvisited vertex with the smallest tentative distance, then relaxes its edges: dist[v] = min(dist[v], dist[u] + w(u, v)).','A relaxation that only ties the current distance does not change the predecessor.');
      else C.push('Relax every edge V − 1 times: dist[v] = min(dist[v], dist[u] + w(u, v)). Edges are relaxed in the order of the list'+(directed?'.':' (for an undirected edge u–v: u→v first, then v→u).'),'Updates made earlier in the same iteration are used immediately.','Stops early if an iteration changes nothing; one extra pass detects a negative cycle.'+(!directed&&G.E.some(e=>e.w<0)?' Note: an undirected negative edge is itself a negative cycle.':''));
      html=r.negCycle?`<div class="dsa-err">Negative-weight cycle reachable from ${E(src)}: shortest paths are not defined.</div>`:`<div class="dsa-ans">${V.map(v=>kpi(`dist(${E(v)})`,f(r.dist[v]))).join('')}</div>`+T(['Vertex','Distance','Shortest path'],V.map(v=>[E(v),f(r.dist[v]),E(pathTxt(r.paths,v))]),{rowId:()=>'x'});
      steps=r.steps;
      work=T(['#',alg==='dijkstra'?'Picked':'Iteration',...V.map(E)],steps.map((s,i)=>[i,E(s.title),...V.map(v=>{const d=f(s.dist[v]);const u=(s.upd||[]).includes(v);const dn=alg==='dijkstra'&&(s.done||[]).includes(v);return `<span class="${u?'graphalgo-chg':''}${dn?' graphalgo-fin':''}">${d}${dn&&s.cur===v?' ✓':''}</span>`;})]));
      if(alg==='dijkstra')C.push('In the working table ✓ marks the vertex finalised in that step; changed distances are highlighted.');
      renderStep=s=>({g:{cur:s.cur,done:s.done,on:s.tree,curE:s.relaxed||[],lab:Object.fromEntries(V.map(v=>[v,f(s.dist[v])]))},side:`<div class="dsa-lbl2">Distances</div><div class="graphalgo-dl">${V.map(v=>`<span class="${(s.upd||[]).includes(v)?'chg':''}">${E(v)}: <b>${f(s.dist[v])}</b></span>`).join('')}</div>`});
    }else if(alg==='floyd'){
      const r=gFloyd(G);
      C.push('D⁽⁰⁾ is the weight matrix (0 on the diagonal, ∞ where there is no edge). D⁽ᵏ⁾[i][j] = min(D⁽ᵏ⁻¹⁾[i][j], D⁽ᵏ⁻¹⁾[i][k] + D⁽ᵏ⁻¹⁾[k][j]); intermediate vertices are taken in vertex order.','Changed cells are highlighted.'+(directed?'':' Undirected edges fill both D[u][v] and D[v][u].'));
      const mat=(m,k)=>`<div class="dsa-scroll"><table class="dsa-t graphalgo-mat"><tr><th>${m.k==null?'D⁽⁰⁾':'k = '+E(m.k)}</th>${V.map(v=>`<th class="${v===m.k?'on':''}">${E(v)}</th>`).join('')}</tr>${m.D.map((row,i)=>`<tr><th class="${V[i]===m.k?'on':''}">${E(V[i])}</th>${row.map((x,j)=>`<td class="${m.changed.some(c=>c[0]===i&&c[1]===j)?'chg':''}${V[i]===m.k||V[j]===m.k?' kk':''}">${f(x)}</td>`).join('')}</tr>`).join('')}</table></div>`;
      html=(r.negCycle?`<div class="dsa-err">A diagonal entry is negative: the graph has a negative-weight cycle.</div>`:'')+`<div class="dsa-lbl2">Final distance matrix D⁽${V.length}⁾</div>${mat({k:null,D:r.D,changed:[]}).replace('D⁽⁰⁾','from \\ to')}`;
      steps=r.mats.map((m,i)=>({title:i?`k = ${m.k} (D⁽${i}⁾)`:'D⁽⁰⁾: edge weights',m,cur:m.k}));
      work=`<div class="graphalgo-mats">${r.mats.map((m,i)=>`<div data-r="${i}" class="graphalgo-mw"><div class="dsa-lbl2">D⁽${i}⁾${m.k!=null?' via '+E(m.k):''}: ${m.changed.length} change${m.changed.length===1?'':'s'}</div>${mat(m)}</div>`).join('')}</div>`;
      renderStep=s=>({g:{cur:s.cur,noW:false},side:`${mat(s.m)}<p class="dsa-note">${s.m.k==null?'Direct edge weights only.':`Paths may now pass through ${E(s.m.k)}. ${s.m.changed.length?s.m.changed.map(([i,j])=>`D[${E(V[i])}][${E(V[j])}] = ${f(s.m.D[i][j])}`).join(', '):'No entry improves.'}`}</p>`});
    }else if(alg==='prim'||alg==='kruskal'){
      if(directed)C.push('A minimum spanning tree is defined for undirected graphs, so edge directions are ignored here.');
      const r=alg==='prim'?gPrim(G,src):gKruskal(G);
      if(alg==='prim')C.push('Prim grows one tree from the source: each step adds the lightest edge from the tree to a new vertex (key = that edge’s weight). Ties go to the vertex that comes first.');
      else C.push('Kruskal takes edges in increasing weight (ties keep list order) and accepts an edge only if it joins two different components (union–find). It stops after V − 1 edges.');
      const Gu=Object.assign({},G,{directed:false});
      const partial=alg==='prim'?r.unreached.length>0:r.forest;
      html=`<div class="dsa-ans">${kpi(partial?'Spanning forest weight':'MST weight',f(r.total))}${kpi('Edges chosen',r.mst.map(e=>`${e.u}–${e.v} (${f(e.w)})`).join(', ')||'none',1)}</div>`+(partial?`<p class="dsa-warn">The graph is disconnected: ${alg==='prim'?'Prim spans only the component of '+E(src)+'.':'Kruskal gives a spanning forest.'}</p>`:'');
      steps=r.steps;
      if(alg==='prim'){work=T(['#','Step',...V.map(E)],steps.map((s,i)=>[i,E(s.title),...V.map(v=>`<span class="${(s.upd||[]).includes(v)?'graphalgo-chg':''}${s.done.includes(v)?' graphalgo-fin':''}">${f(s.key[v])}</span>`)]));
        renderStep=s=>({G:Gu,g:{cur:s.cur,done:s.done,on:s.tree,curE:s.curE,lab:Object.fromEntries(V.filter(v=>!s.done.includes(v)&&s.key[v]!==Infinity).map(v=>[v,'key '+f(s.key[v])]))},side:`<div class="dsa-lbl2">Keys</div><div class="graphalgo-dl">${V.map(v=>`<span class="${(s.upd||[]).includes(v)?'chg':''}">${E(v)}: <b>${s.done.includes(v)?'in tree':f(s.key[v])}</b></span>`).join('')}</div>`});}
      else{work=T(['#','Edge','Weight','Decision','Components after'],steps.slice(1).map((s,i)=>[i+1,E(s.edge.u+'–'+s.edge.v),f(s.edge.w),s.ok?'<b>accept</b>':'reject (cycle)',E(s.comps.join(' '))]),{rowId:i=>i+1,wrap:[4]});
        renderStep=s=>({G:Gu,g:{on:s.tree,curE:s.curE,rejE:s.rejE,rej:s.rej,dimE:[]},side:`<div class="dsa-lbl2">Components</div><div>${E(s.comps.join(' '))}</div>`});}
    }else if(alg==='topo'){
      const r=gTopo(G,{method:W.F('tm').value,order:'sorted'});
      if(r.err){out.innerHTML=errBox(r.err);return;}
      C.push(r.method==='kahn'?'Kahn: repeatedly output a vertex of in-degree 0 and delete its edges. When several are ready, the smallest (alphabetical / numeric) is taken first.':'DFS method: run DFS over all vertices (in order) and list the vertices by decreasing finish time. A back edge means a cycle.','A graph has a topological order only if it is a DAG; many valid orders may exist, this is one of them.');
      html=r.cycle?`<div class="dsa-err">The graph has a cycle, so no topological order exists${r.left?' (stuck with '+E(r.left.join(', '))+' still having incoming edges)':''}.</div>`:`<div class="dsa-ans">${kpi('Topological order',r.order.join(' → '),1)}</div>`;
      steps=r.steps;
      if(r.method==='kahn'){work=T(['#','Step','Ready (in-degree 0)','Output so far'],steps.map((s,i)=>[i,E(s.title),E(s.ready.join(' '))||'—',E(s.out.join(' '))||'—']));
        renderStep=s=>({g:{cur:s.cur,done:s.done,noW:true,dimE:G.E.filter(e=>s.done.includes(e.u)).map(e=>e.id),lab:Object.fromEntries(V.filter(v=>!s.done.includes(v)).map(v=>[v,'in '+s.indeg[v]]))},side:`<div class="dsa-lbl2">Ready</div><div>${E(s.ready.join(' '))||'—'}</div><div class="dsa-lbl2">Output</div><div><b>${E(s.out.join(' → '))||'—'}</b></div>`});}
      else{const d=r.dfs;work=T(['Vertex','d','f'],V.map(v=>[E(v),d.d[v],d.f[v]]),{rowId:()=>'x'});
        renderStep=s=>({g:{cur:s.cur,done:s.done,seen:s.seen,on:s.tree,noW:true,lab:Object.fromEntries(V.filter(v=>s.d[v]!=null).map(v=>[v,s.d[v]+'/'+(s.f[v]!=null?s.f[v]:'·')]))},side:`<div class="dsa-lbl2">Finished so far (latest first)</div><div>${E(G.V.filter(v=>s.f[v]!=null).sort((a,b)=>s.f[b]-s.f[a]).join(' → '))||'—'}</div>`});}
    }
    out.innerHTML=html+`<div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div><div class="dsa-lbl">Full working</div><div class="dsa-work">${work}</div>`;
    sp=stepper(out.querySelector('.dsa-stp'),steps.length,(i,body)=>{
      const s=steps[i],o=renderStep(s,i);const g=Object.assign({noW:alg==='bfs'||alg==='dfs'},o.g);
      body.innerHTML=`<div class="graphalgo-grid"><div class="graphalgo-fig">${drawGraph(o.G||G,g)}</div><div class="graphalgo-side"><div class="dsa-st">${E(s.title)}</div>${s.note?`<p class="dsa-note">${E(s.note)}</p>`:''}${o.side||''}</div></div>`;
      markRow(out,i);
    });
  }
  run();
 }});

/* ---------------- hashprobe ---------------- */
ANIM.register('hashprobe',{title:'Hashing and probing solver',steps:false,
 caption:'Set the table size, the collision strategy and your keys. Every probe is shown with the formula filled in.',
 build(stage){
  stage.style.padding='0';
  const DEF={m:'11',keys:'10 22 31 4 15 28 17 88 59'};
  stage.innerHTML=`<div class="dsa-wrap">
   <div class="dsa-ctrls">
    ${field('Table size m',inp('m',DEF.m,{type:'number',min:1,max:61}),'dsa-num')}
    ${field('Keys (in insertion order)',inp('keys',DEF.keys),'dsa-grow')}
    ${field('Collision strategy',sel('st',[['linear','Linear probing'],['quad','Quadratic probing'],['double','Double hashing'],['chain','Separate chaining']],'linear'))}
    ${field('c₁',inp('c1','0',{type:'number'}),'dsa-num','quad')}
    ${field('c₂',inp('c2','1',{type:'number'}),'dsa-num','quad')}
    ${field('h₂(k)',sel('h2k',[['rmk','R − (k mod R)'],['one','1 + (k mod R)']],'rmk'),'','double')}
    ${field('R',inp('R','7',{type:'number',min:1}),'dsa-num','double')}
    ${field('New key goes to',sel('ch',[['tail','End of the chain'],['head','Front of the chain']],'tail'),'','chain')}
    ${field('Count collisions as',sel('cc',[['probe','Every probe that hits an occupied slot'],['key','Keys whose home slot is taken']],'probe'))}
   </div>
   <div class="dsa-btns"><button type="button" class="btn sm" data-b="rand">Random example</button><button type="button" class="btn sm" data-b="reset">Default example</button></div>
   <div class="dsa-out"></div></div>`;
  const out=stage.querySelector('.dsa-out');let sp=null;
  const W=wire(stage,()=>run());
  stage.querySelector('[data-b=rand]').onclick=()=>{const m=pick([7,10,11,13]);W.F('m').value=m;const n=rnd(5,Math.min(9,m-1));const s=new Set();while(s.size<n)s.add(rnd(1,99));W.F('keys').value=[...s].join(' ');run();};
  stage.querySelector('[data-b=reset]').onclick=()=>{W.F('m').value=DEF.m;W.F('keys').value=DEF.keys;run();};
  function run(){
    if(sp)sp.stop();
    const st=W.F('st').value;W.showOnly(st);
    const mS=W.F('m').value.trim();if(!/^\d+$/.test(mS)){out.innerHTML=errBox('Table size m must be a whole number from 1 to 61.');return;}
    const m=+mS;
    const p=parseInts(W.F('keys').value,{min:1,max:40,name:'keys'});if(p.err){out.innerHTML=errBox(p.err);return;}
    const num=(n,d)=>{const s=W.F(n).value.trim();return /^-?\d+$/.test(s)?+s:(s===''?d:NaN);};
    const c1=num('c1',0),c2=num('c2',1),R=num('R',7);
    if(st==='quad'&&(isNaN(c1)||isNaN(c2))){out.innerHTML=errBox('c₁ and c₂ must be whole numbers.');return;}
    if(st==='double'&&(isNaN(R)||R<1)){out.innerHTML=errBox('R must be a whole number ≥ 1.');return;}
    const o={strategy:st,c1,c2,R,h2kind:W.F('h2k').value,head:W.F('ch').value==='head'};
    const r=hashRun(m,p.vals,o);
    if(r.err){out.innerHTML=errBox(r.err);return;}
    const cc=W.F('cc').value;const coll=cc==='probe'?r.probeColl:r.keyColl;
    const h2txt=o.h2kind==='one'?`1 + (k mod ${R})`:`${R} − (k mod ${R})`;
    const FORM={linear:`h(k, i) = (h(k) + i) mod ${m}`,quad:`h(k, i) = (h(k) + ${c1}·i + ${c2}·i²) mod ${m}`,double:`h(k, i) = (h(k) + i·h₂(k)) mod ${m}, h₂(k) = ${h2txt}`,chain:'Every key goes into the list at slot h(k).'};
    const C=[`Home slot h(k) = k mod ${m} (for a negative k the result is taken in 0..${m-1}).`,`Probe number i starts at 0. ${FORM[st]}`,st==='chain'?`Load factor α = n / m can exceed 1. A key “collides” when its slot already holds a key; new keys go to the ${o.head?'front':'end'} of the chain.`:`Open addressing tries at most m probes; if all are occupied the key is not inserted.`,cc==='probe'?'Collisions = every probe that lands on an occupied slot (a key that needs 3 extra probes adds 3).':'Collisions = number of keys whose home slot was already occupied (each such key counts once).','Duplicate keys are skipped.'];
    const other=cc==='probe'?`${r.keyColl} key${r.keyColl===1?'':'s'} collided`:`${r.probeColl} occupied probe${r.probeColl===1?'':'s'}`;
    const probeTxt=(row)=>{if(row.dup)return 'duplicate: skipped';if(st==='chain')return `slot ${row.h}`+(row.coll?` (holds ${row.probes[0].occ})`:' (empty)');return row.probes.map(q=>q.slot).join(' → ');};
    const tableHTML=(t,hl)=>`<div class="hashprobe-tab">${t.map((x,i)=>{const h=hl&&hl[i];const probed=h&&h.length?`<em>${h.map(n=>'i='+n).join(' ')}</em>`:'';const val=Array.isArray(x)?(x.length?x.map(k=>`<span class="hashprobe-k">${E(f(k))}</span>`).join('<span class="hashprobe-arr">→</span>'):'<span class="dsa-muted">—</span>'):x==null?'<span class="dsa-muted">—</span>':E(f(x));return `<div class="hashprobe-s${h?' '+h.cls:''}"><span class="hashprobe-i">${i}</span><span class="hashprobe-v">${val}</span>${probed}</div>`;}).join('')}</div>`;
    out.innerHTML=`<div class="dsa-ans">${kpi('Collisions',coll)}${kpi('Keys stored',`${r.n} of ${p.vals.length}`)}${kpi('Load factor n/m',`${r.n}/${m} = ${f(r.load)}`)}${r.failed.length?kpi('Not inserted',r.failed.map(f).join(', ')):''}</div><p class="dsa-note">Other count: ${other}.</p>
     <div class="dsa-lbl2">Final table</div>${tableHTML(r.table)}
     <div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through (one key per step)</div><div class="dsa-stp"></div>
     <div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Key k',`h(k) = k mod ${m}`,...(st==='double'?['h₂(k)']:[]),st==='chain'?'Bucket':'Probe sequence','Slot','Collisions'],r.rows.map((row,i)=>[i+1,E(f(row.k)),row.h,...(st==='double'?[row.h2==null?'—':row.h2]:[]),E(probeTxt(row)),row.dup?'—':row.slot==null?'<span class="graphalgo-chg">none</span>':row.slot,row.dup?'—':(cc==='probe'?row.coll:(row.coll?1:0))]),{rowId:i=>i+1})}</div>`;
    sp=stepper(out.querySelector('.dsa-stp'),r.steps.length+1,(i,body)=>{
      if(i===0){body.innerHTML=`<div class="dsa-st">Empty table</div>${tableHTML(Array.from({length:m},()=>st==='chain'?[]:null))}<p class="dsa-note">${m} empty slots, numbered 0 to ${m-1}. ${E(FORM[st])}</p>`;markRow(out,0);return;}
      const s=r.steps[i-1];const hl={};
      const lines=[];
      if(s.dup)lines.push(`${f(s.k)} is already in the table: skipped.`);
      else{
        lines.push(`h(${f(s.k)}) = ${f(s.k)} mod ${m} = ${s.h}.`);
        if(st==='double'&&s.h2!=null)lines.push(`h₂(${f(s.k)}) = ${o.h2kind==='one'?`1 + (${f(s.k)} mod ${R})`:`${R} − (${f(s.k)} mod ${R})`} = ${s.h2}.`);
        if(st==='chain'){hl[s.h]={cls:'fin',length:0};lines.push(s.coll?`Slot ${s.h} already holds ${s.probes[0].occ}: collision; add ${f(s.k)} to the ${o.head?'front':'end'} of the chain.`:`Slot ${s.h} is empty: start a chain there.`);}
        else{
          s.probes.forEach(q=>{const expr=st==='linear'?`(${s.h} + ${q.i}) mod ${m}`:st==='quad'?`(${s.h} + ${c1}·${q.i} + ${c2}·${q.i}²) mod ${m}`:`(${s.h} + ${q.i}·${s.h2}) mod ${m}`;
            lines.push(`i = ${q.i}: ${expr} = ${q.slot} → ${q.occ==null?'empty, place '+f(s.k)+' here.':'occupied by '+f(q.occ)+(q.i===0?' (collision).':'.')}`);
            const e=hl[q.slot]||(hl[q.slot]=Object.assign([],{cls:''}));e.push(q.i);e.cls=q.occ==null?'fin':'hit';});
          if(s.fail)lines.push(s.fail);
        }
      }
      body.innerHTML=`<div class="dsa-st">Insert ${E(f(s.k))}</div>${tableHTML(s.table,hl)}<ol class="hashprobe-log">${lines.map(l=>`<li>${E(l)}</li>`).join('')}</ol>`;
      markRow(out,i);
    },{label:'Step'});
  }
  run();
 }});

/* ---------------- infix ---------------- */
ANIM.register('infix',{title:'Infix, postfix and prefix solver',steps:false,
 caption:'Convert an infix expression with the operator-stack method, or evaluate a postfix expression, and follow the stack token by token.',
 build(stage){
  stage.style.padding='0';
  const DEF={ex:'A+B*(C^D-E)^(F+G*H)-I',pf:'6 2 3 + - 3 8 2 / + * 2 ^ 3 +'};
  stage.innerHTML=`<div class="dsa-wrap">
   <div class="dsa-ctrls">
    <div class="dsa-f"><span>Task</span>${segH('task',[['post','To postfix'],['pre','To prefix'],['eval','Evaluate postfix']],'post')}</div>
    ${field('Infix expression',inp('ex',DEF.ex),'dsa-grow','post pre')}
    ${field('^ associativity',sel('pa',[['right','Right (a^b^c = a^(b^c))'],['left','Left']],'right'),'','post pre')}
    ${field('Postfix expression (spaces between tokens)',inp('pf',DEF.pf),'dsa-grow','eval')}
    ${field('Division',sel('dv',[['real','Exact (decimals)'],['int','Integer (truncate)']],'real'),'','eval')}
   </div>
   <div class="dsa-btns"><button type="button" class="btn sm" data-b="rand">Random example</button><button type="button" class="btn sm" data-b="reset">Default example</button></div>
   <div class="dsa-out"></div></div>`;
  const out=stage.querySelector('.dsa-out');let sp=null;
  const W=wire(stage,()=>run());
  const randExpr=(d)=>{const ops=['+','-','*','/','^'];if(d<=0||Math.random()<0.3)return String.fromCharCode(65+rnd(0,7));const e=randExpr(d-1)+pick(ops)+randExpr(d-1);return Math.random()<0.35?'('+e+')':e;};
  stage.querySelector('[data-b=rand]').onclick=()=>{
    if(W.segV('task')==='eval'){const e=Array.from({length:rnd(3,5)},()=>String(rnd(1,9)));let s=[e[0]];for(let i=1;i<e.length;i++){s.push(e[i]);s.push(pick(['+','-','*','+']));}if(Math.random()<0.5){s.push(String(rnd(2,3)));s.push('^');}W.F('pf').value=s.join(' ');}
    else{let e='';for(let t=0;t<20;t++){e=randExpr(3);if(e.length>=7&&e.length<=19)break;}W.F('ex').value=e;}
    run();};
  stage.querySelector('[data-b=reset]').onclick=()=>{W.F('ex').value=DEF.ex;W.F('pf').value=DEF.pf;run();};
  const stackHTML=s=>`<div class="infix-stack">${s.length?s.map((x,i)=>`<span class="infix-sx${i===s.length-1?' top':''}">${E(typeof x==='number'?f(x):x)}</span>`).join(''):'<span class="dsa-muted">empty</span>'}</div>`;
  function run(){
    if(sp)sp.stop();
    const task=W.segV('task');W.showOnly(task);
    if(task==='eval'){
      const tk=postTok(W.F('pf').value);const div=W.F('dv').value;const r=evalPostfix(tk,{div});
      const C=['Scan left to right. An operand is pushed. An operator pops the top (right operand) and then the next (left operand), and pushes left op right.','Operators: + − * / % and ^ (power). '+(div==='int'?'Division truncates toward zero.':'Division is exact.'),'Without spaces every character is one token (so “231*+9-” means 2 3 1 * + 9 −).'];
      if(r.err&&!(r.rows&&r.rows.length)){out.innerHTML=errBox(r.err);return;}
      const rows=r.rows;
      out.innerHTML=(r.err?errBox(r.err):`<div class="dsa-ans">${kpi('Value',f(r.value))}${kpi('Tokens',tk.length)}</div>`)+`<div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div><div class="dsa-lbl">Full working</div><div class="dsa-work">${T(['#','Token','Action','Stack (bottom → top)'],rows.map((s,i)=>[i+1,`<b>${E(s.tok)}</b>`,E(s.act),E(s.stack.map(f).join(' '))||'empty']),{rowId:i=>i+1,wrap:[2]})}</div>`;
      sp=stepper(out.querySelector('.dsa-stp'),rows.length+1,(i,body)=>{
        const s=rows[i-1];
        body.innerHTML=`<div class="infix-toks">${tk.map((t,k)=>`<span class="${k===i-1?'cur':k<i-1?'done':''}">${E(t)}</span>`).join('')}</div><div class="dsa-lbl2">Stack (bottom → top)</div>${stackHTML(s?s.stack:[])}<p class="dsa-note">${s?`<b>${E(s.tok)}</b>: ${E(s.act)}`:'Start with an empty stack.'}</p>`;
        markRow(out,i);
      },{label:'Step'});
      return;
    }
    const r=infixConvert(W.F('ex').value,{powAssoc:W.F('pa').value});
    if(r.err){out.innerHTML=errBox(r.err);return;}
    const pre=task==='pre';const tr=pre?r.preTrace:r.postTrace;
    const joinT=a=>r.tokens.every(t=>t.length===1)?a.join(''):a.join(' ');
    const C=['Precedence: ^ highest, then * / %, then + −. + − * / % are left-associative; ^ is '+(r.rightPow?'right-associative (a^b^c = a^(b^c)).':'treated as left-associative here.'),'Operands (letters or numbers) go straight to the output; “(” is pushed and “)” pops back to its “(”.'];
    if(pre)C.push('Prefix method: scan the infix from right to left with the roles of “(” and “)” swapped, pop an operator only if its precedence is higher than the incoming one (or equal, for a right-associative incoming operator), then reverse the output.');
    else C.push('Postfix: before pushing an operator, pop every operator on top with higher precedence, or equal precedence when the incoming operator is left-associative.');
    let val='';
    if(r.numeric){const e=evalPostfix(r.postfix,{});if(!e.err)val=kpi('Value',f(e.value));}
    out.innerHTML=`<div class="dsa-ans">${kpi('Postfix',E(joinT(r.postfix)),1)}${kpi('Prefix',E(joinT(r.prefix)),1)}${val}</div><div class="dsa-lbl">Conventions</div>${conv(C)}<div class="dsa-lbl">Step through</div><div class="dsa-stp"></div>
     <div class="dsa-lbl">Full working${pre?' (scanning right to left)':''}</div><div class="dsa-work">${T(['#','Token','Action','Stack (bottom → top)',pre?'Output (reversed at the end)':'Postfix output'],tr.map((s,i)=>[i+1,`<b>${E(s.tok)}</b>`,E(s.act),E(s.stack.join(' '))||'empty',E(s.out.join(' '))||'—']),{rowId:i=>i+1,wrap:[2]})}</div>`;
    const order=pre?r.tokens.map((_,k)=>r.tokens.length-1-k):r.tokens.map((_,k)=>k);
    sp=stepper(out.querySelector('.dsa-stp'),tr.length+1,(i,body)=>{
      const s=tr[i-1];const ti=s&&i-1<order.length?order[i-1]:-1;const doneSet=new Set(order.slice(0,Math.min(i,order.length)));
      body.innerHTML=`<div class="infix-toks">${r.tokens.map((t,k)=>`<span class="${k===ti?'cur':doneSet.has(k)?'done':''}">${E(t)}</span>`).join('')}</div><div class="infix-grid"><div><div class="dsa-lbl2">Operator stack (bottom → top)</div>${stackHTML(s?s.stack:[])}</div><div><div class="dsa-lbl2">${s&&s.final?'Prefix':'Output'}</div><div class="infix-out">${s&&s.out.length?E(s.out.join(' ')):'<span class="dsa-muted">empty</span>'}</div></div></div><p class="dsa-note">${s?(s.tok==='end'||s.tok==='reverse'?'':`<b>${E(s.tok)}</b>: `)+E(s.act):pre?'Start at the right end of the expression with an empty stack.':'Start at the left end with an empty stack.'}</p>`;
      markRow(out,i);
    },{label:'Step'});
  }
  run();
 }});
})();

/* ================= UGC NET solvers: group mix (raster, transform2d, seest, gamesearch) =================
   Pure algorithms live on NETSOLVE.raster / NETSOLVE.transform2d / NETSOLVE.seest / NETSOLVE.gamesearch
   so they can be tested in Node (global.window = {}). Everything is wrapped in an IIFE so no global
   names are declared (several net-*.js files are concatenated into one script). */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;
/* number formatting: round to d decimals, drop trailing zeros, never print -0 */
const fmt=(v,d)=>{if(v===Infinity)return '∞';if(v===-Infinity)return '−∞';if(typeof v!=='number'||isNaN(v))return String(v);d=d==null?3:d;const p=Math.pow(10,d);let s=Math.round(v*p)/p;if(Math.abs(s)<1e-12)s=0;return String(s).replace('-','−');};
const snap=v=>{const r=Math.round(v);return Math.abs(v-r)<1e-9?r:Math.round(v*1e12)/1e12;};
const isInt=v=>typeof v==='number'&&isFinite(v)&&Math.floor(v)===v;
const num=s=>{s=String(s==null?'':s).trim().replace(/−/g,'-');if(!/^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(s))return NaN;return +s;};

/* ======================================================================
   RASTER core: DDA, Bresenham (all octants), midpoint circle, Cohen–Sutherland
   ====================================================================== */
const RA={};
/* round(p/q) with the convention round(v) = floor(v + 0.5), exact for integers p, q (q > 0) */
RA.rnd=(p,q)=>Math.floor((2*p+q)/(2*q));
RA.checkPts=function(a,lim){lim=lim||200;for(const v of a){if(!isInt(v))return 'Coordinates must be whole numbers (pixel positions).';if(Math.abs(v)>lim)return `Keep coordinates between −${lim} and ${lim}.`;}return null;};
RA.dda=function(x0,y0,x1,y1){
  const e=RA.checkPts([x0,y0,x1,y1]);if(e)return {err:e};
  const dx=x1-x0,dy=y1-y0,steps=Math.max(Math.abs(dx),Math.abs(dy));
  if(steps===0)return {dx,dy,steps:0,xinc:0,yinc:0,rows:[{k:0,x:x0,y:y0,px:x0,py:y0}],pixels:[[x0,y0]]};
  const rows=[];
  for(let k=0;k<=steps;k++){const xn=x0*steps+k*dx,yn=y0*steps+k*dy;rows.push({k,x:xn/steps,y:yn/steps,px:RA.rnd(xn,steps),py:RA.rnd(yn,steps)});}
  return {dx,dy,steps,xinc:dx/steps,yinc:dy/steps,rows,pixels:rows.map(r=>[r.px,r.py])};
};
/* Generalised Bresenham. Drives along the axis with the larger change; p < 0 → step on the driving axis only,
   p ≥ 0 → step diagonally (so a tie p = 0 steps diagonally, as in Hearn & Baker). */
RA.bresenham=function(x0,y0,x1,y1){
  const e=RA.checkPts([x0,y0,x1,y1]);if(e)return {err:e};
  const dx=Math.abs(x1-x0),dy=Math.abs(y1-y0),sx=x1>=x0?1:-1,sy=y1>=y0?1:-1,steep=dy>dx;
  const D=steep?dy:dx,d=steep?dx:dy;
  let x=x0,y=y0,p=2*d-D;const p0=p;const rows=[],pixels=[[x0,y0]];
  for(let k=0;k<D;k++){
    const pk=p;let diag=false;
    if(p<0){p+=2*d;}else{diag=true;p+=2*d-2*D;}
    if(steep){y+=sy;if(diag)x+=sx;}else{x+=sx;if(diag)y+=sy;}
    rows.push({k,p:pk,diag,x,y,pn:p});pixels.push([x,y]);
  }
  const oct=dx===0&&dy===0?0:(()=>{const a=Math.atan2(y1-y0,x1-x0);let o=Math.floor(((a<0?a+2*Math.PI:a))/(Math.PI/4))+1;return Math.min(8,o);})();
  return {dx,dy,sx,sy,steep,D,d,p0,inc1:2*d,inc2:2*d-2*D,rows,pixels,octant:oct};
};
/* Midpoint circle (Hearn & Baker): start (0, r), p0 = 1 − r (or 5/4 − r), step x until x ≥ y. */
RA.circle=function(cx,cy,r,frac){
  const e=RA.checkPts([cx,cy],200);if(e)return {err:e};
  if(!isInt(r)||r<1)return {err:'The radius must be a whole number ≥ 1.'};
  if(r>40)return {err:'Keep the radius at most 40 so the grid stays readable.'};
  let x=0,y=r,p=frac?1.25-r:1-r;const p0=p;const rows=[];
  while(x<y){const pk=p;let dec=false;x++;if(p<0)p+=2*x+1;else{y--;dec=true;p+=2*x+1-2*y;}rows.push({k:rows.length,p:pk,x,y,dec,pn:p});}
  const oct=[[0,r],...rows.map(q=>[q.x,q.y])];
  const sym=(a,b)=>{const s=[[a,b],[b,a],[b,-a],[a,-b],[-a,-b],[-b,-a],[-b,a],[-a,b]];const out=[];const seen=new Set();for(const [u,v] of s){const k=u+','+v;if(!seen.has(k)){seen.add(k);out.push([cx+u,cy+v]);}}return out;};
  const all=[];const seen=new Set();oct.forEach(([a,b])=>sym(a,b).forEach(q=>{const k=q.join();if(!seen.has(k)){seen.add(k);all.push(q);}}));
  return {cx,cy,r,p0,rows,octant:oct,sym,pixels:all};
};
/* Cohen–Sutherland: region code bits T B R L (8 4 2 1) */
RA.code=(x,y,W)=>(y>W.ymax?8:0)|(y<W.ymin?4:0)|(x>W.xmax?2:0)|(x<W.xmin?1:0);
RA.bits=c=>((c>>3)&1)+''+((c>>2)&1)+''+((c>>1)&1)+''+(c&1);
RA.ORDERS={LRBT:[1,2,4,8],TBRL:[8,4,2,1]};
RA.BNAME={1:'Left',2:'Right',4:'Bottom',8:'Top'};
RA.cohen=function(W,P,Q,order){
  for(const v of [W.xmin,W.ymin,W.xmax,W.ymax,P[0],P[1],Q[0],Q[1]])if(typeof v!=='number'||!isFinite(v))return {err:'Every coordinate must be a number.'};
  if(!(W.xmin<W.xmax&&W.ymin<W.ymax))return {err:'The window needs xmin < xmax and ymin < ymax.'};
  const ord=RA.ORDERS[order]||RA.ORDERS.LRBT;
  let p=P.slice(),q=Q.slice();const steps=[];
  for(let it=0;it<10;it++){
    const c1=RA.code(p[0],p[1],W),c2=RA.code(q[0],q[1],W);
    const st={p:p.slice(),q:q.slice(),c1,c2,or:c1|c2,and:c1&c2};
    if(!(c1|c2)){st.act='accept';steps.push(st);return {W,steps,result:'accept',seg:[p,q],P,Q};}
    if(c1&c2){st.act='reject';steps.push(st);return {W,steps,result:'reject',seg:null,P,Q};}
    const which=c1?1:2,c=which===1?c1:c2,b=ord.find(bit=>c&bit);
    const [x1,y1]=p,[x2,y2]=q;let x,y;
    if(b===8){y=W.ymax;x=x1+(x2-x1)*(W.ymax-y1)/(y2-y1);}
    else if(b===4){y=W.ymin;x=x1+(x2-x1)*(W.ymin-y1)/(y2-y1);}
    else if(b===2){x=W.xmax;y=y1+(y2-y1)*(W.xmax-x1)/(x2-x1);}
    else {x=W.xmin;y=y1+(y2-y1)*(W.xmin-x1)/(x2-x1);}
    x=snap(x);y=snap(y);
    Object.assign(st,{act:'clip',which,bound:b,pt:[x,y],slope:x2!==x1?(y2-y1)/(x2-x1):Infinity});steps.push(st);
    if(which===1)p=[x,y];else q=[x,y];
  }
  return {err:'Clipping did not converge.'};
};
NETSOLVE.raster=RA;

/* ======================================================================
   TRANSFORM2D core: 3×3 homogeneous matrices, column-vector convention P' = M·P
   ====================================================================== */
const TF={};
const I3=()=>[[1,0,0],[0,1,0],[0,0,1]];
TF.mul=(A,B)=>A.map((r,i)=>[0,1,2].map(j=>snap(r[0]*B[0][j]+r[1]*B[1][j]+r[2]*B[2][j])));
TF.T=(tx,ty)=>[[1,0,tx],[0,1,ty],[0,0,1]];
TF.R=deg=>{const t=deg*Math.PI/180;let c=Math.cos(t),s=Math.sin(t);c=snap(c);s=snap(s);if(Math.abs(c)<1e-12)c=0;if(Math.abs(s)<1e-12)s=0;return [[c,-s,0],[s,c,0],[0,0,1]];};
TF.S=(sx,sy)=>[[sx,0,0],[0,sy,0],[0,0,1]];
TF.F={x:[[1,0,0],[0,-1,0],[0,0,1]],y:[[-1,0,0],[0,1,0],[0,0,1]],o:[[-1,0,0],[0,-1,0],[0,0,1]],yx:[[0,1,0],[1,0,0],[0,0,1]],ynx:[[0,-1,0],[-1,0,0],[0,0,1]]};
TF.FNAME={x:'the x-axis (y = 0)',y:'the y-axis (x = 0)',o:'the origin',yx:'the line y = x',ynx:'the line y = −x'};
TF.H=(shx,shy)=>[[1,shx,0],[shy,1,0],[0,0,1]];
TF.apply=(M,pt)=>[snap(M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]),snap(M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2])];
TF.transpose=M=>[0,1,2].map(i=>[0,1,2].map(j=>M[j][i]));
/* expand one user operation into elementary matrices, in application order */
TF.expand=function(op){
  const out=[];const px=+op.px||0,py=+op.py||0,piv=(px!==0||py!==0)&&op.t!=='T';
  const wrap=(m,name)=>{if(piv){out.push({M:TF.T(-px,-py),name:`T(${fmt(-px)}, ${fmt(-py)})`,why:`move the fixed point (${fmt(px)}, ${fmt(py)}) to the origin`});out.push({M:m,name});out.push({M:TF.T(px,py),name:`T(${fmt(px)}, ${fmt(py)})`,why:'move it back'});}else out.push({M:m,name});};
  if(op.t==='T')out.push({M:TF.T(op.a,op.b),name:`T(${fmt(op.a)}, ${fmt(op.b)})`});
  else if(op.t==='R')wrap(TF.R(op.a),`R(${fmt(op.a)}°)`);
  else if(op.t==='S')wrap(TF.S(op.a,op.b),`S(${fmt(op.a)}, ${fmt(op.b)})`);
  else if(op.t==='H')wrap(TF.H(op.a,op.b),`Sh(${fmt(op.a)}, ${fmt(op.b)})`);
  else if(op.t==='F'){
    if(op.axis==='line'){const m=op.a,c=op.b,th=Math.atan(m)*180/Math.PI;
      out.push({M:TF.T(0,-c),name:`T(0, ${fmt(-c)})`,why:`move the line y = ${fmt(m)}x + ${fmt(c)} down to pass through the origin`});
      out.push({M:TF.R(-th),name:`R(${fmt(-th,2)}°)`,why:`rotate by −θ, θ = tan⁻¹(${fmt(m)}) = ${fmt(th,2)}°, so the line lies on the x-axis`});
      out.push({M:TF.F.x,name:'Fx',why:'reflect about the x-axis'});
      out.push({M:TF.R(th),name:`R(${fmt(th,2)}°)`,why:'rotate back'});
      out.push({M:TF.T(0,c),name:`T(0, ${fmt(c)})`,why:'move back up'});}
    else wrap(TF.F[op.axis],'F'+({x:'x',y:'y',o:'o',yx:'(y=x)',ynx:'(y=−x)'}[op.axis]));
  }
  return out;
};
TF.validate=function(ops,poly){
  if(!ops.length)return 'Add at least one transformation.';
  for(let i=0;i<ops.length;i++){const o=ops[i];const need=o.t==='F'?(o.axis==='line'?['a','b']:[]):o.t==='R'?['a']:['a','b'];
    for(const k of need.concat(o.t==='T'||(o.t==='F'&&o.axis==='line')?[]:['px','py']))if(typeof o[k]!=='number'||!isFinite(o[k]))return `Row ${i+1}: every value must be a number.`;
    if(o.t==='S'&&(o.a===0||o.b===0))return `Row ${i+1}: a scale factor of 0 flattens the shape; use a non-zero factor.`;}
  if(!poly||poly.length<1)return 'Enter at least one vertex, e.g. (0,0) (4,0) (4,3).';
  if(poly.length>12)return 'At most 12 vertices, please.';
  return null;
};
TF.parsePoly=function(s){
  s=String(s||'').replace(/−/g,'-');const pts=[];const re=/\(?\s*([-+]?\d*\.?\d+)\s*[, ]\s*([-+]?\d*\.?\d+)\s*\)?/g;let m;let rest=s;
  while((m=re.exec(s)))pts.push([+m[1],+m[2]]);
  rest=s.replace(re,'').replace(/[\s,;]/g,'');
  if(rest)return {err:'Write vertices as (x, y) pairs, e.g. (0,0) (4,0) (4,3).'};
  if(!pts.length)return {err:'Enter at least one vertex, e.g. (0,0) (4,0) (4,3).'};
  return {pts};
};
TF.compose=function(ops,poly){
  const e=TF.validate(ops,poly);if(e)return {err:e};
  const els=[];ops.forEach((o,i)=>TF.expand(o).forEach(x=>{x.op=i;els.push(x);}));
  let C=I3();const partial=[];let P=poly.map(p=>p.slice());const polys=[P];
  for(const x of els){C=TF.mul(x.M,C);partial.push(C);P=P.map(p=>TF.apply(x.M,p));polys.push(P);}
  const out=poly.map(p=>TF.apply(C,p));
  return {els,M:C,partial,polys,out,poly};
};
NETSOLVE.transform2d=TF;

/* ======================================================================
   SEEST core: COCOMO, function points, cyclomatic complexity, PERT/CPM
   ====================================================================== */
const SE={};
SE.BASIC={organic:{a:2.4,b:1.05,c:2.5,d:0.38},semi:{a:3.0,b:1.12,c:2.5,d:0.35},embedded:{a:3.6,b:1.20,c:2.5,d:0.32}};
SE.INTER={organic:{a:3.2,b:1.05,c:2.5,d:0.38},semi:{a:3.0,b:1.12,c:2.5,d:0.35},embedded:{a:2.8,b:1.20,c:2.5,d:0.32}};
SE.MODENAME={organic:'Organic',semi:'Semi-detached',embedded:'Embedded'};
SE.RATINGS=['VL','L','N','H','VH','XH'];
SE.RATENAME={VL:'Very low',L:'Low',N:'Nominal',H:'High',VH:'Very high',XH:'Extra high'};
SE.DRIVERS=[
 ['RELY','Required software reliability','Product',[.75,.88,1,1.15,1.40,null]],
 ['DATA','Database size','Product',[null,.94,1,1.08,1.16,null]],
 ['CPLX','Product complexity','Product',[.70,.85,1,1.15,1.30,1.65]],
 ['TIME','Execution time constraint','Computer',[null,null,1,1.11,1.30,1.66]],
 ['STOR','Main storage constraint','Computer',[null,null,1,1.06,1.21,1.56]],
 ['VIRT','Virtual machine volatility','Computer',[null,.87,1,1.15,1.30,null]],
 ['TURN','Computer turnaround time','Computer',[null,.87,1,1.07,1.15,null]],
 ['ACAP','Analyst capability','Personnel',[1.46,1.19,1,.86,.71,null]],
 ['AEXP','Applications experience','Personnel',[1.29,1.13,1,.91,.82,null]],
 ['PCAP','Programmer capability','Personnel',[1.42,1.17,1,.86,.70,null]],
 ['VEXP','Virtual machine experience','Personnel',[1.21,1.10,1,.90,null,null]],
 ['LEXP','Programming language experience','Personnel',[1.14,1.07,1,.95,null,null]],
 ['MODP','Modern programming practices','Project',[1.24,1.10,1,.91,.82,null]],
 ['TOOL','Use of software tools','Project',[1.24,1.10,1,.91,.83,null]],
 ['SCED','Required development schedule','Project',[1.23,1.08,1,1.04,1.10,null]]];
/* ratings: {RELY:'H', ...}; missing = nominal */
SE.cocomo=function(kloc,mode,model,ratings){
  if(typeof kloc!=='number'||!isFinite(kloc)||kloc<=0)return {err:'Size must be a positive number of KLOC.'};
  if(kloc>100000)return {err:'Size is too large (max 100 000 KLOC).'};
  const tbl=model==='inter'?SE.INTER:SE.BASIC,k=tbl[mode];if(!k)return {err:'Choose a mode.'};
  let eaf=1;const used=[];
  if(model==='inter'){for(const [id,,,m] of SE.DRIVERS){const r=(ratings&&ratings[id])||'N';const i=SE.RATINGS.indexOf(r);const v=m[i];if(v==null)return {err:`${id} has no "${SE.RATENAME[r]||r}" rating.`};if(v!==1)used.push({id,r,v});eaf*=v;}}
  const nominal=k.a*Math.pow(kloc,k.b),E=nominal*eaf,D=k.c*Math.pow(E,k.d);
  return {kloc,mode,model,k,eaf,used,nominal,E,D,staff:E/D,prod:kloc*1000/E};
};
SE.FP={EI:['External inputs (EI)',[3,4,6]],EO:['External outputs (EO)',[4,5,7]],EQ:['External inquiries (EQ)',[3,4,6]],ILF:['Internal logical files (ILF)',[7,10,15]],EIF:['External interface files (EIF)',[5,7,10]]};
SE.FPKEYS=['EI','EO','EQ','ILF','EIF'];
SE.GSC=['Data communications','Distributed data processing','Performance','Heavily used configuration','Transaction rate','Online data entry','End-user efficiency','Online update','Complex processing','Reusability','Installation ease','Operational ease','Multiple sites','Facilitate change'];
/* counts: {EI:[low,avg,high], ...}; f: 14 values 0..5 */
SE.fp=function(counts,f){
  const rows=[];let ufp=0;
  for(const k of SE.FPKEYS){const c=counts[k]||[0,0,0];for(const v of c)if(!isInt(v)||v<0)return {err:`${k}: counts must be whole numbers ≥ 0.`};
    const w=SE.FP[k][1],sub=c[0]*w[0]+c[1]*w[1]+c[2]*w[2];rows.push({k,c,w,sub});ufp+=sub;}
  if(!f||f.length!==14)return {err:'Give all 14 adjustment factors.'};
  for(const v of f)if(!isInt(v)||v<0||v>5)return {err:'Each adjustment factor is a whole number from 0 to 5.'};
  const tdi=f.reduce((a,b)=>a+b,0),vaf=0.65+0.01*tdi;
  return {rows,ufp,tdi,vaf,fp:ufp*vaf};
};
/* directed edge list "1-2, 2-3" or "1->2" */
SE.parseEdges=function(s){
  const txt=String(s||'').replace(/→|->|—|–/g,'-');const parts=txt.split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
  if(!parts.length)return {err:'Enter the flow-graph edges, e.g. 1-2, 2-3, 2-4.'};
  const E=[],nodes=[];
  for(const p of parts){const m=p.match(/^([A-Za-z0-9_]+)\s*-\s*([A-Za-z0-9_]+)$/);if(!m)return {err:`"${p}" is not an edge. Write edges like 1-2 (from node 1 to node 2).`};
    E.push([m[1],m[2]]);for(const n of [m[1],m[2]])if(!nodes.includes(n))nodes.push(n);}
  if(E.length>80)return {err:'At most 80 edges, please.'};
  return {E,nodes};
};
SE.cyclo=function(s){
  const g=SE.parseEdges(s);if(g.err)return g;const {E,nodes}=g;const N=nodes.length;
  const par={};nodes.forEach(n=>par[n]=n);const find=x=>par[x]===x?x:(par[x]=find(par[x]));E.forEach(([a,b])=>{par[find(a)]=find(b);});
  const P=new Set(nodes.map(find)).size;
  const out={};nodes.forEach(n=>out[n]=0);E.forEach(([a])=>out[a]++);
  const dec=nodes.filter(n=>out[n]>=2).map(n=>({n,out:out[n]}));
  const predSum=dec.reduce((a,d)=>a+d.out-1,0);
  const exits=nodes.filter(n=>out[n]===0);
  const V=E.length-N+2*P;
  return {E,nodes,N,e:E.length,P,V,dec,binary:dec.every(d=>d.out===2),predV:predSum+P,regions:P===1?E.length-N+2:null,exits};
};
/* PERT / CPM.  acts: [{id, pred:[ids], t}] (AON)  or  [{i, j, t}] (AOA). three-estimate: a, m, b instead of t. */
SE.te=(a,m,b)=>(a+4*m+b)/6;SE.var=(a,b)=>Math.pow((b-a)/6,2);
SE.normCdf=function(z){const t=1/(1+0.3275911*Math.abs(z)/Math.SQRT2);const y=1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-0.284496736)*t+0.254829592)*t*Math.exp(-z*z/2);return 0.5*(1+(z<0?-y:y));};
SE.cpm=function(acts,opt){
  opt=opt||{};const three=!!opt.three,aoa=!!opt.aoa;
  if(!acts.length)return {err:'Add at least one activity.'};
  if(acts.length>40)return {err:'At most 40 activities, please.'};
  const A=[];
  for(let r=0;r<acts.length;r++){const x=acts[r];let t,v=0;
    if(three){for(const k of ['a','m','b'])if(typeof x[k]!=='number'||!isFinite(x[k])||x[k]<0)return {err:`Row ${r+1}: a, m and b must be numbers ≥ 0.`};
      if(!(x.a<=x.m&&x.m<=x.b))return {err:`Row ${r+1}: estimates must satisfy a ≤ m ≤ b.`};t=SE.te(x.a,x.m,x.b);v=SE.var(x.a,x.b);}
    else{if(typeof x.t!=='number'||!isFinite(x.t)||x.t<0)return {err:`Row ${r+1}: the duration must be a number ≥ 0.`};t=x.t;}
    if(aoa){const i=String(x.i||'').trim(),j=String(x.j||'').trim();if(!i||!j)return {err:`Row ${r+1}: give both events i and j.`};if(i===j)return {err:`Row ${r+1}: an activity cannot start and end at the same event.`};
      if(A.some(y=>y.i===i&&y.j===j))return {err:`Activity ${i}–${j} is listed twice (use a dummy event for parallel activities).`};
      A.push({id:i+'-'+j,i,j,t,v,a:x.a,m:x.m,b:x.b});}
    else{const id=String(x.id||'').trim();if(!id)return {err:`Row ${r+1}: give the activity a name.`};if(!/^[A-Za-z0-9_]+$/.test(id))return {err:`Row ${r+1}: use letters and digits for the activity name.`};if(A.some(y=>y.id===id))return {err:`Activity ${id} is listed twice.`};
      A.push({id,pred:(x.pred||[]).slice(),t,v,a:x.a,m:x.m,b:x.b});}
  }
  const byId={};A.forEach(a=>byId[a.id]=a);
  if(aoa){A.forEach(a=>{a.pred=A.filter(b=>b.j===a.i).map(b=>b.id);});}
  else for(const a of A)for(const p of a.pred){if(!byId[p])return {err:`Activity ${a.id}: unknown predecessor "${p}".`};if(p===a.id)return {err:`Activity ${a.id} cannot precede itself.`};}
  A.forEach(a=>a.succ=A.filter(b=>b.pred.includes(a.id)).map(b=>b.id));
  /* topological order (Kahn, ties in input order) */
  const indeg={};A.forEach(a=>indeg[a.id]=a.pred.length);const order=[];const q=A.filter(a=>!indeg[a.id]).map(a=>a.id);
  while(q.length){const id=q.shift();order.push(id);for(const s of byId[id].succ){if(--indeg[s]===0)q.push(s);}}
  if(order.length!==A.length)return {err:'The network has a cycle, so it has no critical path. Check the predecessors.'};
  const trace=[];
  for(const id of order){const a=byId[id];a.ES=a.pred.length?Math.max(...a.pred.map(p=>byId[p].EF)):0;a.EF=a.ES+a.t;trace.push({pass:'f',id,from:a.pred.map(p=>[p,byId[p].EF])});}
  const T=Math.max(...A.map(a=>a.EF));
  for(const id of order.slice().reverse()){const a=byId[id];a.LF=a.succ.length?Math.min(...a.succ.map(s=>byId[s].LS)):T;a.LS=a.LF-a.t;trace.push({pass:'b',id,from:a.succ.map(s=>[s,byId[s].LS])});}
  const eps=1e-9;
  A.forEach(a=>{a.slack=snap(a.LS-a.ES);a.ff=snap((a.succ.length?Math.min(...a.succ.map(s=>byId[s].ES)):T)-a.EF);a.crit=Math.abs(a.slack)<eps;});
  /* critical paths: chains of critical activities with EF(a) = ES(b), from ES = 0 to EF = T */
  const paths=[];const walk=(id,path)=>{if(paths.length>=20)return;const a=byId[id];const nx=a.succ.map(s=>byId[s]).filter(b=>b.crit&&Math.abs(b.ES-a.EF)<eps);
    if(Math.abs(a.EF-T)<eps&&!a.succ.some(s=>byId[s].crit&&Math.abs(byId[s].ES-a.EF)<eps))paths.push(path);else nx.forEach(b=>walk(b.id,path.concat(b.id)));};
  A.filter(a=>a.crit&&a.ES<eps).forEach(a=>walk(a.id,[a.id]));
  const pinfo=paths.map(p=>({p,var:p.reduce((s,id)=>s+byId[id].v,0)}));
  let events=null;
  if(aoa){const ev={};A.forEach(a=>{for(const n of [a.i,a.j])if(!ev[n])ev[n]={n,TE:0,TL:T};});
    Object.values(ev).forEach(e=>{const inn=A.filter(a=>a.j===e.n),out=A.filter(a=>a.i===e.n);e.TE=inn.length?Math.max(...inn.map(a=>a.EF)):0;e.TL=out.length?Math.min(...out.map(a=>a.LS)):T;e.slack=snap(e.TL-e.TE);});
    events=Object.values(ev);}
  const maxVar=pinfo.length?Math.max(...pinfo.map(x=>x.var)):0;
  let prob=null;
  if(three&&typeof opt.deadline==='number'&&isFinite(opt.deadline)){const sd=Math.sqrt(maxVar);prob=sd>0?{D:opt.deadline,z:(opt.deadline-T)/sd,p:SE.normCdf((opt.deadline-T)/sd)}:{D:opt.deadline,z:null,p:opt.deadline>=T?1:0};}
  return {A,byId,order,T,paths:pinfo,crit:A.filter(a=>a.crit).map(a=>a.id),trace,events,three,aoa,variance:maxVar,sd:Math.sqrt(maxVar),prob};
};
NETSOLVE.seest=SE;

/* ======================================================================
   GAMESEARCH core: minimax, alpha–beta (left to right), A*
   ====================================================================== */
const GS={};
GS.parseTree=function(s){
  s=String(s||'').replace(/−/g,'-').trim();if(!s)return {err:'Enter a game tree as nested lists, e.g. [[3,5],[6,[9,1]],[2]].'};
  let i=0;const toks=[];
  while(i<s.length){const c=s[i];if(/\s/.test(c)){i++;continue;}if(c==='['||c===']'||c===','){toks.push(c);i++;continue;}
    const m=s.slice(i).match(/^[-+]?(\d+\.?\d*|\.\d+)/);if(!m)return {err:`Unexpected "${c}" at position ${i+1}. Use only numbers, [ ] and commas.`};toks.push(+m[0]);i+=m[0].length;}
  let k=0,id=0,leaves=0,depth=0;
  const parse=d=>{const t=toks[k];
    if(typeof t==='number'){k++;leaves++;depth=Math.max(depth,d);return {id:id++,leaf:true,v:t,d};}
    if(t!=='[')throw new Error(t===undefined?'The tree ends too early: a "]" is missing.':`Expected a number or "[" but found "${t}".`);
    k++;const node={id:id++,leaf:false,kids:[],d};
    if(toks[k]===']')throw new Error('Empty list "[]": every internal node needs at least one child.');
    for(;;){node.kids.push(parse(d+1));if(toks[k]===','){k++;continue;}if(toks[k]===']'){k++;break;}throw new Error(toks[k]===undefined?'A "]" is missing.':`Expected "," or "]" but found "${toks[k]}".`);}
    return node;};
  let root;try{root=parse(0);}catch(e){return {err:e.message};}
  if(k<toks.length)return {err:`Extra input after the tree: "${toks.slice(k).join('')}". Wrap everything in one outer [ ].`};
  if(root.leaf)return {err:'The root must be a list of moves, e.g. [3, 5, 2].'};
  if(leaves>64)return {err:'At most 64 leaves, please.'};if(depth>8)return {err:'At most 8 levels deep, please.'};
  const nodes=[];const walk=(n,p)=>{n.parent=p;nodes[n.id]=n;if(!n.leaf)n.kids.forEach(c=>walk(c,n.id));};walk(root,null);
  return {root,nodes,leaves,depth};
};
GS.minimax=function(root,maxRoot){
  const val={};const go=(n,mx)=>{if(n.leaf)return val[n.id]=n.v;const vs=n.kids.map(c=>go(c,!mx));return val[n.id]=mx?Math.max(...vs):Math.min(...vs);};
  go(root,maxRoot);const best=root.kids.findIndex(c=>val[c.id]===val[root.id]);return {val,value:val[root.id],best};
};
/* Alpha–beta, children left to right. strict=false: cut when α ≥ β (standard); strict=true: cut only when α > β. */
GS.alphabeta=function(tree,maxRoot,strict){
  const {root,nodes}=tree;const ev=[];const st=nodes.map(()=>({s:'u',v:null,a:null,b:null,bound:''}));
  const snapS=()=>st.map(x=>({...x}));
  const cut=(a,b)=>strict?a>b:a>=b;
  const pruned=[];let evald=0,cutoffs=0;
  const leavesUnder=n=>n.leaf?[n.id]:n.kids.flatMap(leavesUnder);
  const markPruned=n=>{st[n.id].s='p';if(!n.leaf)n.kids.forEach(markPruned);};
  const go=(n,mx,a,b)=>{
    if(n.leaf){evald++;st[n.id]={s:'d',v:n.v,a,b,bound:''};ev.push({k:'leaf',id:n.id,v:n.v,S:snapS()});return n.v;}
    let v=mx?-Infinity:Infinity;st[n.id]={s:'a',v:null,a,b,bound:''};ev.push({k:'enter',id:n.id,a,b,mx,S:snapS()});
    for(let i=0;i<n.kids.length;i++){const c=n.kids[i];const cv=go(c,!mx,a,b);
      if(mx){if(cv>v)v=cv;if(v>a)a=v;}else{if(cv<v)v=cv;if(v<b)b=v;}
      st[n.id]={s:'a',v,a,b,bound:''};
      if(i<n.kids.length-1&&cut(a,b)){const rest=n.kids.slice(i+1);const lv=rest.flatMap(leavesUnder);cutoffs++;
        rest.forEach(markPruned);pruned.push({at:n.id,kids:rest.map(r=>r.id),leaves:lv});
        st[n.id]={s:'d',v,a,b,bound:mx?'≥':'≤'};
        ev.push({k:'cut',id:n.id,v,a,b,mx,rest:rest.map(r=>r.id),leaves:lv,S:snapS()});return v;}
      ev.push({k:'upd',id:n.id,from:c.id,cv,v,a,b,mx,S:snapS()});
    }
    st[n.id]={s:'d',v,a,b,bound:''};ev.push({k:'ret',id:n.id,v,mx,S:snapS()});return v;};
  const value=go(root,maxRoot,-Infinity,Infinity);
  const prunedLeaves=pruned.reduce((s,p)=>s+p.leaves.length,0);
  return {value,events:ev,pruned,prunedLeaves,evaluated:evald,cutoffs,final:ev[ev.length-1].S};
};
/* A* graph search. edges "S A 1" / "S-A 1" / "S-A:1"; h "S=7, A=6" */
GS.parseGraph=function(eTxt,hTxt,directed){
  const lines=String(eTxt||'').replace(/−/g,'-').split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
  if(!lines.length)return {err:'Enter the edges, e.g. S-A 1, S-B 4, A-G 5.'};
  const adj={},nodes=[],E=[];const add=n=>{if(!adj[n]){adj[n]=[];nodes.push(n);}};
  for(const l of lines){const m=l.match(/^([A-Za-z0-9_]+)\s*(?:-|\s)\s*([A-Za-z0-9_]+)\s*[:=\s]\s*(\d*\.?\d+)$/);
    if(!m)return {err:`"${l}" is not an edge. Write it as A-B 4 (from A to B, cost 4).`};
    const [,u,v,cs]=m,c=+cs;if(u===v)return {err:`"${l}": a node cannot connect to itself.`};add(u);add(v);
    E.push({u,v,c});adj[u].push({to:v,c});if(!directed)adj[v].push({to:u,c});}
  if(nodes.length>30)return {err:'At most 30 nodes, please.'};
  const h={};const hs=String(hTxt||'').replace(/−/g,'-').split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
  for(const x of hs){const m=x.match(/^([A-Za-z0-9_]+)\s*[:=\s]\s*(\d*\.?\d+)$/);if(!m)return {err:`"${x}" is not a heuristic value. Write it as A=5.`};if(!adj[m[1]])return {err:`h(${m[1]}) is given, but ${m[1]} is not in the graph.`};h[m[1]]=+m[2];}
  const miss=nodes.filter(n=>h[n]===undefined);if(miss.length)return {err:`Give h for every node (missing: ${miss.join(', ')}).`};
  return {adj,nodes,E,h,directed};
};
/* Ties on f are broken by the smaller h, then alphabetically. Goal test when a node is taken off OPEN. */
GS.astar=function(G,start,goal){
  if(!G.adj[start])return {err:`Start node "${start}" is not in the graph.`};if(!G.adj[goal])return {err:`Goal node "${goal}" is not in the graph.`};
  const h=G.h,g={},par={},open=new Set([start]),closed=new Set();g[start]=0;par[start]=null;const it=[];
  const cmp=(a,b)=>(g[a]+h[a])-(g[b]+h[b])||h[a]-h[b]||(a<b?-1:a>b?1:0);
  const snapO=()=>[...open].sort(cmp).map(n=>({n,g:g[n],h:h[n],f:g[n]+h[n],par:par[n]}));
  const pathTo=n=>{const p=[];while(n!=null){p.unshift(n);n=par[n];}return p;};
  it.push({k:'init',open:snapO(),closed:[]});
  let found=null;
  for(let guard=0;open.size&&guard<500;guard++){
    const n=[...open].sort(cmp)[0];open.delete(n);
    if(n===goal){closed.add(n);found=n;it.push({k:'goal',n,g:g[n],f:g[n]+h[n],open:snapO(),closed:[...closed],path:pathTo(n)});break;}
    closed.add(n);const gen=[];
    for(const {to,c} of G.adj[n]){const ng=g[n]+c;
      if(open.has(to)){if(ng<g[to]){gen.push({n:to,g:ng,f:ng+h[to],note:`better path (old g ${fmt(g[to])}), updated`,cls:'upd'});g[to]=ng;par[to]=n;}else gen.push({n:to,g:ng,f:ng+h[to],note:`already on OPEN with g ${fmt(g[to])} ≤ ${fmt(ng)}, ignored`,cls:'skip'});}
      else if(closed.has(to)){if(ng<g[to]){gen.push({n:to,g:ng,f:ng+h[to],note:`on CLOSED but cheaper (old g ${fmt(g[to])}): reopened`,cls:'reopen'});closed.delete(to);open.add(to);g[to]=ng;par[to]=n;}else gen.push({n:to,g:ng,f:ng+h[to],note:'on CLOSED, ignored',cls:'skip'});}
      else{g[to]=ng;par[to]=n;open.add(to);gen.push({n:to,g:ng,f:ng+h[to],note:'new, added to OPEN',cls:'new'});}}
    it.push({k:'exp',n,g:g[n],f:g[n]+h[n],gen,open:snapO(),closed:[...closed],path:pathTo(n)});
  }
  /* h* by Dijkstra from the goal on reversed edges, for the admissibility check */
  const rev={};G.nodes.forEach(x=>rev[x]=[]);G.E.forEach(e=>{rev[e.v].push({to:e.u,c:e.c});if(!G.directed)rev[e.u].push({to:e.v,c:e.c});});
  const hs={};G.nodes.forEach(x=>hs[x]=Infinity);hs[goal]=0;const done=new Set();
  for(;;){let u=null;for(const x of G.nodes)if(!done.has(x)&&hs[x]<Infinity&&(u===null||hs[x]<hs[u]))u=x;if(u===null)break;done.add(u);for(const {to,c} of rev[u])if(hs[u]+c<hs[to])hs[to]=hs[u]+c;}
  const inadm=G.nodes.filter(x=>h[x]>hs[x]+1e-9);
  const incons=[];G.E.forEach(e=>{if(h[e.u]>e.c+h[e.v]+1e-9)incons.push([e.u,e.v,e.c]);if(!G.directed&&h[e.v]>e.c+h[e.u]+1e-9)incons.push([e.v,e.u,e.c]);});
  return {iters:it,found:!!found,path:found?pathTo(found):null,cost:found?g[found]:null,expanded:it.filter(x=>x.k==='exp').length+(found?1:0),hstar:hs,inadm,incons,optimal:hs[start]};
};
NETSOLVE.gamesearch=GS;

/* ======================================================================
   UI (browser only)
   ====================================================================== */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const pick=a=>a[Math.floor(Math.random()*a.length)];
function debounce(fn,ms){let t;return (...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms);};}
const M='netmix';
/* generic step-through: render(i) sets the whole state for step i (idempotent) */
function stepper(host,n,render,start){
  let i=0,timer=null;
  host.innerHTML=`<div class="${M}-stp"><button type="button" class="btn sm" data-a="rs" aria-label="Back to the first step">↺</button><button type="button" class="btn sm" data-a="pv">◀ Prev</button><button type="button" class="btn sm primary" data-a="pl">▶ Play</button><button type="button" class="btn sm" data-a="nx">Next ▶</button><input type="range" min="0" max="${Math.max(0,n-1)}" value="0" aria-label="Jump to step"><span class="${M}-stpc" aria-live="polite"></span></div>`;
  const pl=host.querySelector('[data-a=pl]'),rg=host.querySelector('input'),ct=host.querySelector(`.${M}-stpc`);
  const stop=()=>{clearTimeout(timer);timer=null;pl.textContent='▶ Play';};
  const go=k=>{i=Math.max(0,Math.min(n-1,k));rg.value=i;ct.textContent=`Step ${i+1} of ${n}`;render(i);};
  const tick=()=>{if(!document.body.contains(host)){stop();return;}if(i>=n-1){stop();return;}go(i+1);timer=setTimeout(tick,1400);};
  host.querySelector('[data-a=rs]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-a=pv]').onclick=()=>{stop();go(i-1);};
  host.querySelector('[data-a=nx]').onclick=()=>{stop();go(i+1);};
  pl.onclick=()=>{if(timer){stop();return;}if(i>=n-1)go(0);pl.textContent='❚❚ Pause';timer=setTimeout(tick,800);};
  rg.oninput=()=>{stop();go(+rg.value);};
  go(start==null?n-1:start);return {go,stop,get i(){return i;}};
}
function tabs(host,names,cur,onPick){
  host.innerHTML=names.map((nm,k)=>`<button type="button" aria-pressed="${k===cur}" data-k="${k}">${nm}</button>`).join('');
  host.querySelectorAll('button').forEach(b=>b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(+b.dataset.k);});
}
function seg(host,cur,onPick){host.querySelectorAll('button').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.v===cur));b.onclick=()=>{host.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));onPick(b.dataset.v);};});}
const segH=(id,opts)=>`<div class="${M}-seg" id="${id}">${opts.map(([v,l])=>`<button type="button" data-v="${v}">${l}</button>`).join('')}</div>`;
const card=(k,big,sub,cls)=>`<div class="${M}-card ${cls||''}"><span class="${M}-k">${k}</span><b class="${M}-big">${big}</b>${sub?`<span>${sub}</span>`:''}</div>`;
const table=(head,rows,cls)=>`<div class="${M}-scroll"><table class="${M}-tbl ${cls||''}"><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
const inp=(k,label,v,w)=>`<label class="${M}-lab ${w||''}">${label}<input type="text" inputmode="decimal" data-k="${k}" value="${E(v)}" spellcheck="false" autocomplete="off"></label>`;
const pt=(x,y)=>`(${fmt(x)}, ${fmt(y)})`;
function setErr(el,msg){if(msg){el.hidden=false;el.textContent=msg;}else el.hidden=true;}
/* arrowhead polygon at (x,y) pointing along (dx,dy) */
function arrow(x,y,dx,dy,cls,sz){sz=sz||8;const L=Math.hypot(dx,dy)||1,ux=dx/L,uy=dy/L;const bx=x-ux*sz,by=y-uy*sz;return `<polygon class="${cls}" points="${x},${y} ${bx-uy*sz*.5},${by+ux*sz*.5} ${bx+uy*sz*.5},${by-ux*sz*.5}"/>`;}
/* layered graph drawing. nodes:[{id,lines:[main,sub],cls}] edges:[{u,v,label,cls}] layer:{id:n} */
function graphSvg(nodes,edges,layer,o){
  o=Object.assign({dir:'LR',nw:60,nh:34,gapL:120,gapA:62,pad:14,round:8},o||{});
  const ids=nodes.map(n=>n.id),L={};ids.forEach(id=>{(L[layer[id]]=L[layer[id]]||[]).push(id);});
  const ks=Object.keys(L).map(Number).sort((a,b)=>a-b),pos={};ks.forEach(k=>L[k].forEach((id,i)=>pos[id]=i));
  for(let sw=0;sw<3;sw++)for(const k of ks){const bc=id=>{const ps=edges.filter(e=>(e.v===id&&layer[e.u]<k)).map(e=>pos[e.u]);return ps.length?ps.reduce((a,b)=>a+b,0)/ps.length:pos[id];};
    const b={};L[k].forEach(id=>b[id]=bc(id));L[k].sort((x,y)=>b[x]-b[y]||pos[x]-pos[y]);L[k].forEach((id,i)=>pos[id]=i);}
  const maxN=Math.max(...ks.map(k=>L[k].length)),xy={};
  ks.forEach((k,ki)=>{const n=L[k].length;L[k].forEach((id,i)=>{const al=ki*o.gapL,ac=(i-(n-1)/2+(maxN-1)/2)*o.gapA;xy[id]=o.dir==='TB'?[ac,al]:[al,ac];});});
  const offX=o.pad+o.nw/2,offY=o.pad+o.nh/2+(o.dir==='LR'?8:0);ids.forEach(id=>{xy[id]=[xy[id][0]+offX,xy[id][1]+offY];});
  const W=Math.max(...ids.map(id=>xy[id][0]))+o.nw/2+o.pad,H=Math.max(...ids.map(id=>xy[id][1]))+o.nh/2+o.pad+8;
  const trim=(cx,cy,dx,dy)=>{const hw=o.nw/2+2,hh=o.nh/2+2;const t=Math.min(dx?hw/Math.abs(dx):Infinity,dy?hh/Math.abs(dy):Infinity);return [cx+dx*t,cy+dy*t];};
  let es='',ls='';
  const pair={};
  edges.forEach(e=>{const [x1,y1]=xy[e.u],[x2,y2]=xy[e.v];const key=[e.u,e.v].sort().join('|');pair[key]=(pair[key]||0)+1;
    const adj=layer[e.v]-layer[e.u]===1,twin=edges.some(f=>f.u===e.v&&f.v===e.u);
    let d,lx,ly,ax,ay,adx,ady;
    if(adj&&!twin){const [sx,sy]=trim(x1,y1,x2-x1,y2-y1),[tx,ty]=trim(x2,y2,x1-x2,y1-y2);d=`M${sx},${sy}L${tx},${ty}`;lx=(sx+tx)/2;ly=(sy+ty)/2;ax=tx;ay=ty;adx=tx-sx;ady=ty-sy;}
    else{const dx=x2-x1,dy=y2-y1,Ln=Math.hypot(dx,dy)||1;let off=Math.min(60,18+Ln*.18)*(twin?1:(layer[e.v]<=layer[e.u]?1.2:0.7));const nx=-dy/Ln,ny=dx/Ln;
      const cx=(x1+x2)/2+nx*off,cy=(y1+y2)/2+ny*off;const [sx,sy]=trim(x1,y1,cx-x1,cy-y1),[tx,ty]=trim(x2,y2,cx-x2,cy-y2);
      d=`M${sx},${sy}Q${cx},${cy} ${tx},${ty}`;lx=.25*sx+.5*cx+.25*tx;ly=.25*sy+.5*cy+.25*ty;ax=tx;ay=ty;adx=tx-cx;ady=ty-cy;}
    es+=`<path class="${M}-e ${e.cls||''}" d="${d}"/>`+(o.arrows===false?'':arrow(ax,ay,adx,ady,`${M}-ah ${e.cls||''}`));
    if(e.label!=null&&e.label!=='')ls+=`<text class="${M}-el ${e.cls||''}" x="${lx}" y="${ly+4}" text-anchor="middle">${E(e.label)}</text>`;});
  let ns='';
  nodes.forEach(n=>{const [x,y]=xy[n.id];const l=n.lines||[n.id];
    ns+=`<g class="${M}-nd ${n.cls||''}"><rect x="${x-o.nw/2}" y="${y-o.nh/2}" width="${o.nw}" height="${o.nh}" rx="${o.round}"/>`+
      (l.length===1?`<text class="${M}-nt" x="${x}" y="${y+4.5}" text-anchor="middle">${E(l[0])}</text>`:`<text class="${M}-nt" x="${x}" y="${y-3}" text-anchor="middle">${E(l[0])}</text><text class="${M}-ns" x="${x}" y="${y+12}" text-anchor="middle">${E(l[1])}</text>`)+
      (n.tag?`<text class="${M}-tag" x="${x}" y="${y-o.nh/2-5}" text-anchor="middle">${E(n.tag)}</text>`:'')+`</g>`;});
  return `<svg class="${M}-svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${E(o.label||'Graph')}">${es}${ls}${ns}</svg>`;
}
const longest=(ids,edges)=>{/* longest-path layering of a DAG (edges given as {u,v}) */const L={};ids.forEach(i=>L[i]=0);for(let r=0;r<ids.length;r++){let ch=false;edges.forEach(e=>{if(L[e.v]<L[e.u]+1){L[e.v]=L[e.u]+1;ch=true;}});if(!ch)break;}return L;};
const mat=(Mx,d)=>`<span class="${M}-mat">${Mx.map(r=>r.map(v=>`<span>${fmt(v,d==null?4:d)}</span>`).join('')).join('')}</span>`;

/* ---------------------------------------------------------------- raster UI */
ANIM.register('raster',{title:'Line, circle and clipping solver',steps:false,
 caption:'Enter the end points, the circle or the clip window. The solver plots every pixel, shows the decision parameter at each step and walks through Cohen–Sutherland clipping.',
 build(stage){
  const P='raster';
  const DEF={line:{x0:'20',y0:'10',x1:'30',y1:'18',algo:'bres',swap:false},circ:{cx:'0',cy:'0',r:'10',frac:'0'},clip:{xmin:'10',ymin:'10',xmax:'40',ymax:'30',x1:'5',y1:'5',x2:'50',y2:'35',order:'LRBT'}};
  const st={tab:0,line:{...DEF.line},circ:{...DEF.circ},clip:{...DEF.clip}};
  const PRE={line:[['Hearn & Baker: (20,10) → (30,18)',{x0:'20',y0:'10',x1:'30',y1:'18'}],['Gentle: (2,3) → (12,8)',{x0:'2',y0:'3',x1:'12',y1:'8'}],['Steep: (1,1) → (3,6)',{x0:'1',y0:'1',x1:'3',y1:'6'}],['Negative slope: (0,0) → (8,−5)',{x0:'0',y0:'0',x1:'8',y1:'-5'}],['Right to left: (10,4) → (0,0)',{x0:'10',y0:'4',x1:'0',y1:'0'}]],
    circ:[['Hearn & Baker: r = 10',{cx:'0',cy:'0',r:'10'}],['r = 8',{cx:'0',cy:'0',r:'8'}],['Centre (4,3), r = 6',{cx:'4',cy:'3',r:'6'}]],
    clip:[['Two clips per end',{xmin:'10',ymin:'10',xmax:'40',ymax:'30',x1:'5',y1:'5',x2:'50',y2:'35'}],['Trivially accepted',{xmin:'10',ymin:'10',xmax:'40',ymax:'30',x1:'15',y1:'12',x2:'35',y2:'28'}],['Trivially rejected',{xmin:'10',ymin:'10',xmax:'40',ymax:'30',x1:'0',y1:'35',x2:'50',y2:'40'}],['Outside, but not trivially',{xmin:'10',ymin:'10',xmax:'40',ymax:'30',x1:'0',y1:'25',x2:'20',y2:'45'}],['Window (2,2)–(8,8), diagonal',{xmin:'2',ymin:'2',xmax:'8',ymax:'8',x1:'0',y1:'0',x2:'10',y2:'10'}]]};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${M} ${P}"><div class="${M}-tabs" role="group" aria-label="Algorithm"></div><div class="${M}-in"></div><div class="${M}-err" role="alert" hidden></div><div class="${M}-ans"></div><div class="${M}-conv"></div><div class="${M}-sth"></div><p class="${M}-cap" aria-live="polite"></p><div class="${M}-two"><div class="${M}-work"></div><div class="${M}-fig"></div></div></div>`;
  const $=s=>stage.querySelector(s),root=$(`.${M}`),inBox=$(`.${M}-in`),err=$(`.${M}-err`),ans=$(`.${M}-ans`),conv=$(`.${M}-conv`),sth=$(`.${M}-sth`),cap=$(`.${M}-cap`),work=$(`.${M}-work`),fig=$(`.${M}-fig`);
  const key=()=>['line','circ','clip'][st.tab];
  tabs($(`.${M}-tabs`),['Line: DDA / Bresenham','Circle: midpoint','Clipping: Cohen–Sutherland'],0,k=>{st.tab=k;drawInputs();compute();});
  function drawInputs(){
    const k=key(),s=st[k];let h='';
    if(k==='line')h=inp('x0','x₀',s.x0)+inp('y0','y₀',s.y0)+inp('x1','x₁',s.x1)+inp('y1','y₁',s.y1)+`<label class="${M}-lab">Algorithm<select data-k="algo"><option value="bres">Bresenham</option><option value="dda">DDA</option></select></label><label class="${M}-chk ${M}-wide"><input type="checkbox" data-k="swap"> Swap the end points so that we always start from the left end (x₀ ≤ x₁), as Hearn &amp; Baker do</label>`;
    else if(k==='circ')h=inp('cx','Centre x',s.cx)+inp('cy','Centre y',s.cy)+inp('r','Radius r',s.r)+`<label class="${M}-lab ${M}-w2">Initial decision parameter<select data-k="frac"><option value="0">p₀ = 1 − r (integer)</option><option value="1">p₀ = 5/4 − r</option></select></label>`;
    else h=inp('xmin','x<sub>min</sub>',s.xmin)+inp('ymin','y<sub>min</sub>',s.ymin)+inp('xmax','x<sub>max</sub>',s.xmax)+inp('ymax','y<sub>max</sub>',s.ymax)+inp('x1','P₁ x',s.x1)+inp('y1','P₁ y',s.y1)+inp('x2','P₂ x',s.x2)+inp('y2','P₂ y',s.y2)+`<label class="${M}-lab ${M}-wide">Order of boundary tests<select data-k="order"><option value="LRBT">Left, Right, Bottom, Top (Hearn &amp; Baker)</option><option value="TBRL">Top, Bottom, Right, Left (Foley et al.)</option></select></label>`;
    h+=`<div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option>${PRE[k].map((p,i)=>`<option value="${i}">${E(p[0])}</option>`).join('')}</select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`;
    inBox.innerHTML=h;
    inBox.querySelectorAll('[data-k]').forEach(el=>{const f=el.dataset.k;if(el.type==='checkbox')el.checked=!!s[f];else el.value=s[f];
      const upd=()=>{s[f]=el.type==='checkbox'?el.checked:el.value;compute();};el.addEventListener(el.tagName==='SELECT'||el.type==='checkbox'?'change':'input',el.tagName==='INPUT'&&el.type==='text'?debounce(upd,250):upd);});
    inBox.querySelector('[data-x=pre]').onchange=e=>{const p=PRE[k][+e.target.value];if(!p)return;Object.assign(s,p[1]);drawInputs();compute();};
    inBox.querySelector('[data-b=rnd]').onclick=()=>{
      if(k==='line'){const x0=rnd(0,12),y0=rnd(0,12);let x1,y1;do{x1=rnd(0,24);y1=rnd(0,24);}while(Math.max(Math.abs(x1-x0),Math.abs(y1-y0))<5);Object.assign(s,{x0:''+x0,y0:''+y0,x1:''+x1,y1:''+y1});}
      else if(k==='circ')Object.assign(s,{cx:''+rnd(-3,3),cy:''+rnd(-3,3),r:''+rnd(5,14)});
      else{const a=rnd(0,4)*5,b=rnd(0,4)*5;Object.assign(s,{xmin:''+a,ymin:''+b,xmax:''+(a+rnd(3,6)*5),ymax:''+(b+rnd(2,5)*5),x1:''+rnd(a-15,a+45),y1:''+rnd(b-15,b+40),x2:''+rnd(a-15,a+45),y2:''+rnd(b-15,b+40)});}
      drawInputs();compute();};
  }
  /* pixel grid */
  function pixSvg(bx,pix,extra){
    const [x0,y0,x1,y1]=bx,nx=x1-x0+1,ny=y1-y0+1;const cs=Math.max(7,Math.min(26,Math.floor(520/Math.max(nx,ny))));const lab=cs>=16?1:cs>=10?2:5;
    const pad=26,W=nx*cs+pad+6,H=ny*cs+pad+6;const X=x=>pad+(x-x0)*cs,Y=y=>6+(y1-y)*cs;
    let g='';for(let i=0;i<=nx;i++)g+=`<line class="${M}-gl" x1="${pad+i*cs}" y1="6" x2="${pad+i*cs}" y2="${6+ny*cs}"/>`;for(let j=0;j<=ny;j++)g+=`<line class="${M}-gl" x1="${pad}" y1="${6+j*cs}" x2="${pad+nx*cs}" y2="${6+j*cs}"/>`;
    for(let x=x0;x<=x1;x++)if(x%lab===0)g+=`<text class="${M}-ax" x="${X(x)+cs/2}" y="${H-8}" text-anchor="middle">${fmt(x)}</text>`;
    for(let y=y0;y<=y1;y++)if(y%lab===0)g+=`<text class="${M}-ax" x="${pad-4}" y="${Y(y)+cs/2+4}" text-anchor="end">${fmt(y)}</text>`;
    let p='';pix.forEach(([x,y,c])=>{p+=`<rect class="${P}-px ${c}" x="${X(x)+1}" y="${Y(y)+1}" width="${cs-2}" height="${cs-2}" rx="2"/>`;});
    const C=(x,y)=>[X(x)+cs/2,Y(y)+cs/2];
    return `<svg class="${M}-svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Pixel grid">${g}${p}${extra?extra(C,cs):''}</svg>`;
  }
  let S=null,stp=null;
  function compute(){
    const k=key(),s=st[k];const n={};for(const f in s)n[f]=typeof s[f]==='string'&&/^[xyr]|^c[xy]$/.test(f)?num(s[f]):s[f];
    let r;
    if(k==='line'){let a=[n.x0,n.y0,n.x1,n.y1];if(a.some(v=>isNaN(v)))r={err:'Every coordinate must be a whole number.'};else{if(s.swap&&a[0]>a[2])a=[a[2],a[3],a[0],a[1]];r=s.algo==='dda'?RA.dda(...a):RA.bresenham(...a);if(!r.err){r.pts=a;const len=Math.max(Math.abs(a[2]-a[0]),Math.abs(a[3]-a[1]));if(len>60)r={err:'Keep the line to at most 60 steps so the grid and table stay readable.'};}}}
    else if(k==='circ'){if([n.cx,n.cy,n.r].some(v=>isNaN(v)))r={err:'Centre and radius must be whole numbers.'};else r=RA.circle(n.cx,n.cy,n.r,s.frac==='1');}
    else{const v=[n.xmin,n.ymin,n.xmax,n.ymax,n.x1,n.y1,n.x2,n.y2];if(v.some(x=>isNaN(x)))r={err:'Every coordinate must be a number.'};else if(n.x1===n.x2&&n.y1===n.y2)r={err:'P₁ and P₂ are the same point; enter a line.'};else if(v.some(x=>Math.abs(x)>1000))r={err:'Keep coordinates between −1000 and 1000.'};else r=RA.cohen({xmin:n.xmin,ymin:n.ymin,xmax:n.xmax,ymax:n.ymax},[n.x1,n.y1],[n.x2,n.y2],s.order);}
    if(r.err){setErr(err,r.err);root.classList.add(`${M}-stale`);return;}
    setErr(err,null);root.classList.remove(`${M}-stale`);S=r;
    if(k==='line')(s.algo==='dda'?showDDA:showBres)(r);else if(k==='circ')showCirc(r);else showClip(r);
  }
  const lineExtra=pts=>(C)=>{const [a,b]=C(pts[0],pts[1]),[c,d]=C(pts[2],pts[3]);return `<line class="${P}-true" x1="${a}" y1="${b}" x2="${c}" y2="${d}"/>`;};
  const bounds=(pix,m)=>{const xs=pix.map(p=>p[0]),ys=pix.map(p=>p[1]);return [Math.min(...xs)-m,Math.min(...ys)-m,Math.max(...xs)+m,Math.max(...ys)+m];};
  function showDDA(r){
    const [x0,y0,x1,y1]=r.pts;const m=r.dx?r.dy/r.dx:Infinity;
    ans.innerHTML=card('Pixels plotted',r.pixels.length,`steps + 1 = ${r.steps} + 1`)+card('Steps',r.steps,`max(|Δx|, |Δy|) = max(${Math.abs(r.dx)}, ${Math.abs(r.dy)})`)+card('x increment',fmt(r.xinc,4),`Δx / steps = ${r.dx}/${r.steps||1}`)+card('y increment',fmt(r.yinc,4),`Δy / steps = ${r.dy}/${r.steps||1}`)+card('Slope m',r.dx?fmt(m,4):'∞ (vertical)',`Δy/Δx = ${r.dy}/${r.dx}`);
    conv.innerHTML=`<p class="${M}-note"><b>DDA:</b> steps = max(|Δx|, |Δy|); each step adds x<sub>inc</sub> = Δx/steps and y<sub>inc</sub> = Δy/steps. <b>Convention:</b> the plotted pixel is round(v) = ⌊v + 0.5⌋, so 2.5 → 3 and −2.5 → −2. The values are computed exactly (x₀ + k·x<sub>inc</sub>), so no floating-point drift. Start: ${pt(x0,y0)}.</p>`;
    const bx=bounds(r.pixels.concat([[x1,y1]]),1);
    const rows=i=>r.rows.map((q,j)=>`<tr class="${j===i?M+'-cur':j>i?M+'-fut':''}"><td>${q.k}</td><td>${fmt(q.x,3)}</td><td>${fmt(q.y,3)}</td><td><b>${pt(q.px,q.py)}</b></td></tr>`);
    work.innerHTML=`<h4 class="${M}-h">Step table</h4><div class="${P}-tb"></div><p class="${M}-note">Pixels: ${r.pixels.map(p=>pt(p[0],p[1])).join(' ')}</p>`;
    const tb=work.querySelector(`.${P}-tb`);
    stp=stepper(sth,r.rows.length,i=>{tb.innerHTML=table(['k','x<sub>k</sub>','y<sub>k</sub>','Pixel (round)'],rows(i));
      fig.innerHTML=pixSvg(bx,r.pixels.map((p,j)=>[p[0],p[1],j<i?'on':j===i?'now':'fut']),lineExtra(r.pts));
      const q=r.rows[i];cap.innerHTML=i===0?`k = 0: start at ${pt(x0,y0)} and plot it.`:`k = ${i}: x = ${fmt(r.rows[i-1].x,3)} + ${fmt(r.xinc,4)} = ${fmt(q.x,3)}, y = ${fmt(r.rows[i-1].y,3)} + ${fmt(r.yinc,4)} = ${fmt(q.y,3)} → plot <b>${pt(q.px,q.py)}</b>.`;});
  }
  function showBres(r){
    const [x0,y0,x1,y1]=r.pts,maj=r.steep?'y':'x',mn=r.steep?'x':'y';
    const D=r.D,d=r.d;
    ans.innerHTML=card('Pixels plotted',r.pixels.length,`Δ${maj} + 1 = ${D} + 1`)+card('Driving axis',maj,r.steep?'|m| > 1: step y every time':'|m| ≤ 1: step x every time')+card('p₀',r.p0,`2Δ${mn} − Δ${maj} = 2·${d} − ${D}`)+card('If p < 0 add',r.inc1,`2Δ${mn} = 2·${d}`)+card('If p ≥ 0 add',r.inc2,`2Δ${mn} − 2Δ${maj} = ${2*d} − ${2*D}`)+card('Octant',r.octant||'—',`Δx = ${x1-x0}, Δy = ${y1-y0}`);
    conv.innerHTML=`<p class="${M}-note"><b>Bresenham (all octants):</b> step along the axis with the larger change (${maj}); the other coordinate (${mn}) moves by ${r.steep?(r.sx>0?'+1':'−1'):(r.sy>0?'+1':'−1')} only when p<sub>k</sub> ≥ 0. <b>Convention:</b> p<sub>k</sub> = 0 steps diagonally (Hearn &amp; Baker's “otherwise” branch). We start from the first end point you entered, ${pt(x0,y0)}${r.sx<0||r.sy<0?`, moving ${r.sx<0?'left':'right'} and ${r.sy<0?'down':'up'}`:''}.</p>`;
    const bx=bounds(r.pixels,1);
    const rows=i=>[`<tr class="${i===0?M+'-cur':''}"><td>start</td><td>—</td><td>—</td><td><b>${pt(x0,y0)}</b></td><td>${r.p0}</td></tr>`].concat(r.rows.map((q,j)=>`<tr class="${j+1===i?M+'-cur':j+1>i?M+'-fut':''}"><td>${q.k}</td><td>${q.p}</td><td>${q.diag?'p ≥ 0: diagonal':'p < 0: '+maj+' only'}</td><td><b>${pt(q.x,q.y)}</b></td><td>${q.p} ${q.diag?(r.inc2<0?'− '+(-r.inc2):'+ '+r.inc2):'+ '+r.inc1} = ${q.pn}</td></tr>`));
    work.innerHTML=`<h4 class="${M}-h">Step table</h4><div class="${P}-tb"></div><p class="${M}-note">Pixels: ${r.pixels.map(p=>pt(p[0],p[1])).join(' ')}</p>`;
    const tb=work.querySelector(`.${P}-tb`);
    stp=stepper(sth,r.pixels.length,i=>{tb.innerHTML=table(['k','p<sub>k</sub>','Decision','Next pixel','p<sub>k+1</sub>'],rows(i));
      fig.innerHTML=pixSvg(bx,r.pixels.map((p,j)=>[p[0],p[1],j<i?'on':j===i?'now':'fut']),lineExtra(r.pts));
      if(i===0)cap.innerHTML=`Start: plot ${pt(x0,y0)}. p₀ = 2Δ${mn} − Δ${maj} = ${2*d} − ${D} = <b>${r.p0}</b>.`;
      else{const q=r.rows[i-1];cap.innerHTML=`k = ${q.k}: p<sub>${q.k}</sub> = ${q.p} ${q.diag?'≥ 0, so both x and y change':'< 0, so only '+maj+' changes'} → plot <b>${pt(q.x,q.y)}</b>; p<sub>${q.k+1}</sub> = ${q.pn}.`;}});
  }
  function showCirc(r){
    const n=r.rows.length;
    ans.innerHTML=card('p₀',fmt(r.p0),r.p0%1?`5/4 − ${r.r}`:`1 − ${r.r}`)+card('Octant points',r.octant.length,'from (0, r) until x ≥ y')+card('Total pixels',r.pixels.length,'8-way symmetry, duplicates removed')+card('Centre',pt(r.cx,r.cy),`radius ${r.r}`);
    conv.innerHTML=`<p class="${M}-note"><b>Midpoint circle (Hearn &amp; Baker):</b> compute the octant from (0, r) for a circle at the origin. If p<sub>k</sub> &lt; 0, the next point is (x+1, y) and p<sub>k+1</sub> = p<sub>k</sub> + 2x<sub>k+1</sub> + 1; otherwise it is (x+1, y−1) and p<sub>k+1</sub> = p<sub>k</sub> + 2x<sub>k+1</sub> + 1 − 2y<sub>k+1</sub>. Stop when x ≥ y. Each point (x, y) gives 8 pixels (±x, ±y), (±y, ±x), shifted by the centre (${fmt(r.cx)}, ${fmt(r.cy)}). Both p₀ = 1 − r and 5/4 − r give the same pixels for a whole-number r.</p>`;
    const bx=[r.cx-r.r-1,r.cy-r.r-1,r.cx+r.r+1,r.cy+r.r+1];
    const rows=i=>[`<tr class="${i===0?M+'-cur':''}"><td>start</td><td>—</td><td><b>(0, ${r.r})</b></td><td>—</td><td>—</td><td>${fmt(r.p0)}</td></tr>`].concat(r.rows.map((q,j)=>`<tr class="${j+1===i?M+'-cur':j+1>i?M+'-fut':''}"><td>${q.k}</td><td>${fmt(q.p)}</td><td><b>(${q.x}, ${q.y})</b></td><td>${2*q.x}</td><td>${2*q.y}</td><td>${fmt(q.pn)}</td></tr>`));
    work.innerHTML=`<h4 class="${M}-h">Step table (octant from (0, r))</h4><div class="${P}-tb"></div><p class="${M}-note ${P}-sym"></p>`;
    const tb=work.querySelector(`.${P}-tb`),sym=work.querySelector(`.${P}-sym`);
    const circ=(C,cs)=>{const [x,y]=C(r.cx,r.cy);return `<circle class="${P}-true" cx="${x}" cy="${y}" r="${r.r*cs}" fill="none"/>`;};
    stp=stepper(sth,n+1,i=>{tb.innerHTML=table(['k','p<sub>k</sub>','(x<sub>k+1</sub>, y<sub>k+1</sub>)','2x<sub>k+1</sub>','2y<sub>k+1</sub>','p<sub>k+1</sub>'],rows(i));
      const done=new Set(),now=new Set();r.octant.forEach(([a,b],j)=>{if(j<=i)r.sym(a,b).forEach(q=>(j===i?now:done).add(q.join()));});
      fig.innerHTML=pixSvg(bx,r.pixels.map(p=>{const k2=p.join();return [p[0],p[1],now.has(k2)?'now':done.has(k2)?'on':'fut'];}),circ);
      const [a,b]=r.octant[i];sym.innerHTML=`8 symmetric pixels of (${a}, ${b}): ${r.sym(a,b).map(q=>pt(q[0],q[1])).join(' ')}`;
      if(i===0)cap.innerHTML=`Start at (0, ${r.r}); p₀ = <b>${fmt(r.p0)}</b>. Its symmetric pixels are highlighted.`;
      else{const q=r.rows[i-1];cap.innerHTML=`k = ${q.k}: p<sub>${q.k}</sub> = ${fmt(q.p)} ${q.dec?'≥ 0, so y decreases':'< 0, so y stays'} → <b>(${q.x}, ${q.y})</b>; p<sub>${q.k+1}</sub> = ${fmt(q.p)} + ${2*q.x} + 1${q.dec?' − '+2*q.y:''} = ${fmt(q.pn)}.`;}});
  }
  function showClip(r){
    const W=r.W,last=r.steps[r.steps.length-1],B=RA.bits;
    ans.innerHTML=card('Result',r.result==='accept'?(r.steps.length===1?'Trivially accepted':'Accepted after clipping'):(r.steps.length===1?'Trivially rejected':'Rejected'),r.result==='accept'?'':'no part is inside',r.result==='accept'?M+'-okc':M+'-badc')+
      card('Region codes',`${B(r.steps[0].c1)}, ${B(r.steps[0].c2)}`,'P₁, P₂ (bits T B R L)')+(r.seg?card('Clipped line',`${pt(...r.seg[0])} – ${pt(...r.seg[1])}`,''):'')+card('Intersections',r.steps.filter(s=>s.act==='clip').length,'computed');
    conv.innerHTML=`<p class="${M}-note"><b>Region code</b> bits, left to right: <b>T</b>op (y &gt; y<sub>max</sub>), <b>B</b>ottom (y &lt; y<sub>min</sub>), <b>R</b>ight (x &gt; x<sub>max</sub>), <b>L</b>eft (x &lt; x<sub>min</sub>). Accept when code₁ OR code₂ = 0000; reject when code₁ AND code₂ ≠ 0000. Otherwise take an outside end point (P₁ first), clip it at the first boundary whose bit is set in the order ${s2o(st.clip.order)}, and repeat. Points on the boundary count as inside. Intersections: x = x₁ + (y<sub>b</sub> − y₁)/m, y = y₁ + m(x<sub>b</sub> − x₁).</p>`;
    const act=s=>s.act==='accept'?`OR = 0000 → <b>accept</b>`:s.act==='reject'?`AND = ${B(s.and)} ≠ 0000 → <b>reject</b>`:`clip P${s.which} (code ${B(s.which===1?s.c1:s.c2)}) at <b>${RA.BNAME[s.bound]}</b> ${s.bound>2?'y = '+fmt(s.bound===8?W.ymax:W.ymin):'x = '+fmt(s.bound===2?W.xmax:W.xmin)} → ${pt(...s.pt)}`;
    const rows=i=>r.steps.map((s,j)=>`<tr class="${j===i?M+'-cur':j>i?M+'-fut':''}"><td>${j+1}</td><td>${pt(...s.p)} <code>${B(s.c1)}</code></td><td>${pt(...s.q)} <code>${B(s.c2)}</code></td><td><code>${B(s.or)}</code></td><td><code>${B(s.and)}</code></td><td>${act(s)}</td></tr>`);
    work.innerHTML=`<h4 class="${M}-h">Clipping steps</h4><div class="${P}-tb"></div>`;const tb=work.querySelector(`.${P}-tb`);
    const xs=[W.xmin,W.xmax,r.P[0],r.Q[0]],ys=[W.ymin,W.ymax,r.P[1],r.Q[1]];const mx=(Math.max(...xs)-Math.min(...xs))*.12+1,my=(Math.max(...ys)-Math.min(...ys))*.12+1;
    const X0=Math.min(...xs)-mx,X1=Math.max(...xs)+mx,Y0=Math.min(...ys)-my,Y1=Math.max(...ys)+my;const sc=Math.min(460/(X1-X0),340/(Y1-Y0));const Wd=(X1-X0)*sc+20,Hd=(Y1-Y0)*sc+20;
    const X=x=>10+(x-X0)*sc,Y=y=>10+(Y1-y)*sc;
    stp=stepper(sth,r.steps.length,i=>{tb.innerHTML=table(['Step','P₁ (code)','P₂ (code)','OR','AND','Action'],rows(i));
      const s=r.steps[i];let g=`<rect class="${P}-win" x="${X(W.xmin)}" y="${Y(W.ymax)}" width="${(W.xmax-W.xmin)*sc}" height="${(W.ymax-W.ymin)*sc}"/>`;
      [[W.xmin,'x'],[W.xmax,'x'],[W.ymin,'y'],[W.ymax,'y']].forEach(([v,a])=>{g+=a==='x'?`<line class="${P}-ext" x1="${X(v)}" y1="0" x2="${X(v)}" y2="${Hd}"/>`:`<line class="${P}-ext" x1="0" y1="${Y(v)}" x2="${Wd}" y2="${Y(v)}"/>`;});
      const cx=[(X0+W.xmin)/2,(W.xmin+W.xmax)/2,(W.xmax+X1)/2],cy=[(Y0+W.ymin)/2,(W.ymin+W.ymax)/2,(W.ymax+Y1)/2];
      cx.forEach(a=>cy.forEach(b=>{g+=`<text class="${P}-rc" x="${X(a)}" y="${Y(b)+4}" text-anchor="middle">${B(RA.code(a,b,W))}</text>`;}));
      g+=`<line class="${P}-orig" x1="${X(r.P[0])}" y1="${Y(r.P[1])}" x2="${X(r.Q[0])}" y2="${Y(r.Q[1])}"/>`;
      const end=i===r.steps.length-1;const seg=end&&r.result==='reject'?null:[s.p,s.q];
      if(seg)g+=`<line class="${P}-seg ${end&&r.result==='accept'?'ok':''}" x1="${X(seg[0][0])}" y1="${Y(seg[0][1])}" x2="${X(seg[1][0])}" y2="${Y(seg[1][1])}"/>`;
      [[s.p,'P₁'],[s.q,'P₂']].forEach(([p,l])=>{g+=`<circle class="${P}-pt" cx="${X(p[0])}" cy="${Y(p[1])}" r="4"/><text class="${P}-pl" x="${X(p[0])+6}" y="${Y(p[1])-6}">${l}${pt(...p)}</text>`;});
      if(s.act==='clip')g+=`<circle class="${P}-ip" cx="${X(s.pt[0])}" cy="${Y(s.pt[1])}" r="5"/>`;
      fig.innerHTML=`<svg class="${M}-svg" viewBox="0 0 ${Wd} ${Hd}" width="${Wd}" height="${Hd}" role="img" aria-label="Clip window and line">${g}</svg>`;
      cap.innerHTML=`Step ${i+1}: P₁ ${pt(...s.p)} has code ${B(s.c1)}, P₂ ${pt(...s.q)} has code ${B(s.c2)}. `+(s.act==='clip'?`Neither test decides, so clip P${s.which} against the <b>${RA.BNAME[s.bound]}</b> edge: ${s.bound>2?`x = ${fmt(s.which===1?s.p[0]:s.q[0],3)} + (${fmt(s.bound===8?W.ymax:W.ymin)} − ${fmt(s.which===1?s.p[1]:s.q[1],3)})/m`:`y = ${fmt(s.which===1?s.p[1]:s.q[1],3)} + m·(${fmt(s.bound===2?W.xmax:W.xmin)} − ${fmt(s.which===1?s.p[0]:s.q[0],3)})`} with m = ${fmt(s.slope,4)} → <b>${pt(...s.pt)}</b>.`:act(s)+'.');});
  }
  const s2o=o=>o==='LRBT'?'Left, Right, Bottom, Top':'Top, Bottom, Right, Left';
  drawInputs();compute();
 }});

/* ---------------------------------------------------------------- transform2d UI */
ANIM.register('transform2d',{title:'2D transformation composer',steps:false,
 caption:'List the transformations in the order they are applied. The solver builds each 3 × 3 homogeneous matrix (including the translate–transform–translate back sandwich for a fixed point), multiplies them and draws the polygon after every step.',
 build(stage){
  const P='transform2d';
  const TYPES=[['T','Translate'],['R','Rotate'],['S','Scale'],['F','Reflect'],['H','Shear']];
  const AX=[['x','about x-axis'],['y','about y-axis'],['o','about origin'],['yx','about y = x'],['ynx','about y = −x'],['line','about y = mx + c']];
  const op=(t,a,b,px,py,axis)=>({t,a:a==null?'':''+a,b:b==null?'':''+b,px:''+(px||0),py:''+(py||0),axis:axis||'x'});
  const PRE=[
    ['Rotate 45° about the origin (Hearn & Baker triangle)','(0,0) (1,1) (5,2)',[op('R',45)]],
    ['Rotate 90° about the point (2,2)','(2,2) (4,2) (4,3)',[op('R',90,null,2,2)]],
    ['Scale ×2 about the fixed point (2,2)','(2,2) (4,2) (4,4) (2,4)',[op('S',2,2,2,2)]],
    ['Reflect about the line y = x + 2','(4,1) (6,1) (6,3)',[op('F',1,2,0,0,'line')]],
    ['Translate (3,0) then rotate 90°','(1,0) (2,0) (2,1)',[op('T',3,0),op('R',90)]],
    ['Shear x by 2, then reflect about y = x','(0,0) (1,0) (1,1) (0,1)',[op('H',2,0),op('F',null,null,0,0,'yx')]]];
  const st={poly:PRE[0][1],ops:PRE[0][2].map(o=>({...o})),conv:'col'};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${M} ${P}"><div class="${M}-in">
     <label class="${M}-lab ${M}-wide">Polygon vertices<input type="text" id="${P}Poly" spellcheck="false" autocomplete="off"></label>
     <div class="${M}-wide"><span class="${M}-lab">Transformations, in the order applied</span><div class="${P}-ops"></div><button type="button" class="btn sm" id="${P}Add">+ Add transformation</button></div>
     <label class="${M}-lab ${M}-wide">Matrix convention<select id="${P}Conv"><option value="col">Column vectors: P′ = M · P, composite M = Mₙ ⋯ M₂ · M₁ (Hearn &amp; Baker)</option><option value="row">Row vectors: P′ = P · M, composite M = M₁ · M₂ ⋯ Mₙ (transposed matrices)</option></select></label>
     <div class="${M}-btns"><label class="${M}-lab">Example<select id="${P}Pre"><option value="">Choose…</option>${PRE.map((p,i)=>`<option value="${i}">${E(p[0])}</option>`).join('')}</select></label><button type="button" class="btn sm" id="${P}Rnd">🎲 Random example</button></div>
   </div><div class="${M}-err" role="alert" hidden></div><div class="${M}-ans"></div><div class="${M}-conv"></div><div class="${M}-sth"></div><p class="${M}-cap" aria-live="polite"></p><div class="${M}-two"><div class="${M}-work"></div><div class="${M}-fig"></div></div></div>`;
  const $=s=>stage.querySelector(s),root=$(`.${M}`),opsBox=$(`.${P}-ops`),err=$(`.${M}-err`),ans=$(`.${M}-ans`),conv=$(`.${M}-conv`),sth=$(`.${M}-sth`),cap=$(`.${M}-cap`),work=$(`.${M}-work`),fig=$(`.${M}-fig`);
  $(`#${P}Poly`).value=st.poly;$(`#${P}Conv`).value=st.conv;
  function opRow(o,i){
    const f=(k,l)=>`<label class="${P}-f">${l}<input type="text" inputmode="decimal" data-i="${i}" data-f="${k}" value="${E(o[k])}" spellcheck="false"></label>`;
    let h=`<span class="${P}-n">${i+1}</span><select data-i="${i}" data-f="t" aria-label="Transformation ${i+1}">${TYPES.map(([v,l])=>`<option value="${v}"${o.t===v?' selected':''}>${l}</option>`).join('')}</select>`;
    if(o.t==='T')h+=f('a','t<sub>x</sub>')+f('b','t<sub>y</sub>');
    else if(o.t==='R')h+=f('a','θ°');
    else if(o.t==='S')h+=f('a','s<sub>x</sub>')+f('b','s<sub>y</sub>');
    else if(o.t==='H')h+=f('a','sh<sub>x</sub>')+f('b','sh<sub>y</sub>');
    else{h+=`<select data-i="${i}" data-f="axis" aria-label="Reflection line">${AX.map(([v,l])=>`<option value="${v}"${o.axis===v?' selected':''}>${l}</option>`).join('')}</select>`;if(o.axis==='line')h+=f('a','m')+f('b','c');}
    if(o.t!=='T'&&!(o.t==='F'&&o.axis==='line'))h+=`<span class="${P}-about">${o.t==='F'?'shifted to pass through':'about'}</span>`+f('px','x')+f('py','y');
    h+=`<button type="button" class="btn sm ${P}-del" data-del="${i}" aria-label="Remove transformation ${i+1}"${st.ops.length<2?' disabled':''}>✕</button>`;
    return `<div class="${P}-op">${h}</div>`;
  }
  function drawOps(){
    opsBox.innerHTML=st.ops.map(opRow).join('');
    opsBox.querySelectorAll('input').forEach(el=>el.oninput=debounce(()=>{st.ops[+el.dataset.i][el.dataset.f]=el.value;compute();},250));
    opsBox.querySelectorAll('select').forEach(el=>el.onchange=()=>{const o=st.ops[+el.dataset.i];o[el.dataset.f]=el.value;if(el.dataset.f==='t'){const d={T:['2','1'],R:['90',''],S:['2','2'],H:['1','0'],F:['1','0']}[o.t];o.a=d[0];o.b=d[1];}else if(o.axis==='line'&&o.a===''){o.a='1';o.b='0';}drawOps();compute();});
    opsBox.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{st.ops.splice(+b.dataset.del,1);drawOps();compute();});
  }
  $(`#${P}Add`).onclick=()=>{if(st.ops.length>=8){setErr(err,'At most 8 transformations, please.');return;}st.ops.push(op('T',1,1));drawOps();compute();};
  $(`#${P}Poly`).oninput=debounce(e=>{st.poly=e.target.value;compute();},250);
  $(`#${P}Conv`).onchange=e=>{st.conv=e.target.value;compute();};
  $(`#${P}Pre`).onchange=e=>{const p=PRE[+e.target.value];if(!p)return;st.poly=p[1];st.ops=p[2].map(o=>({...o}));$(`#${P}Poly`).value=st.poly;drawOps();compute();};
  $(`#${P}Rnd`).onclick=()=>{const n=rnd(1,3);st.ops=[];for(let k=0;k<n;k++){const t=pick(['T','R','S','F','H']);
      if(t==='T')st.ops.push(op('T',rnd(-4,4),rnd(-4,4)));else if(t==='R')st.ops.push(op('R',pick([30,45,60,90,180,-90]),null,pick([0,0,rnd(1,3)]),pick([0,0,rnd(1,3)])));
      else if(t==='S')st.ops.push(op('S',pick([2,0.5,3,1]),pick([2,1,0.5]),pick([0,rnd(1,3)]),pick([0,rnd(1,3)])));else if(t==='H')st.ops.push(op('H',pick([1,2,0.5]),0));
      else st.ops.push(pick([op('F',null,null,0,0,pick(['x','y','o','yx','ynx'])),op('F',pick([1,-1,2]),rnd(-2,2),0,0,'line')]));}
    const tri=pick([[[0,0],[3,0],[3,2]],[[1,1],[4,1],[4,3],[1,3]],[[0,0],[2,0],[1,3]],[[2,1],[5,2],[3,4]]]);st.poly=tri.map(p=>`(${p[0]},${p[1]})`).join(' ');$(`#${P}Poly`).value=st.poly;drawOps();compute();};
  const nm=o=>({T:'Translate',R:'Rotate',S:'Scale',F:'Reflect',H:'Shear'}[o.t]);
  function compute(){
    const pp=TF.parsePoly(st.poly);if(pp.err){setErr(err,pp.err);root.classList.add(`${M}-stale`);return;}
    const ops=st.ops.map(o=>({t:o.t,axis:o.axis,a:num(o.a),b:o.t==='R'?0:num(o.b),px:num(o.px||'0'),py:num(o.py||'0')}));
    const r=TF.compose(ops,pp.pts);
    if(r.err){setErr(err,r.err);root.classList.add(`${M}-stale`);return;}
    setErr(err,null);root.classList.remove(`${M}-stale`);show(r);
  }
  function show(r){
    const row=st.conv==='row',TT=m=>row?TF.transpose(m):m,n=r.els.length;
    const names=r.els.map(x=>x.name);
    const chain=row?names.join(' · '):names.slice().reverse().join(' · ');
    ans.innerHTML=`<div class="${M}-card ${P}-cm"><span class="${M}-k">Composite matrix${row?' (row-vector form)':''}</span>${mat(TT(r.M))}<span>M = ${E(chain)}</span></div>`+card('Transformed vertices',r.out.map(p=>pt(p[0],p[1])).join(' '),`from ${r.poly.map(p=>pt(p[0],p[1])).join(' ')}`)+card('Elementary matrices',n,`from ${st.ops.length} transformation${st.ops.length>1?'s':''}`);
    conv.innerHTML=`<p class="${M}-note"><b>Conventions:</b> homogeneous coordinates (x, y, 1). Positive angles rotate <b>anticlockwise</b>. ${row?'Row vectors: P′ = P · M, so each matrix is the transpose of the column form and the composite is M₁ · M₂ ⋯ M<sub>n</sub> (first applied on the <b>left</b>).':'Column vectors: P′ = M · P, so the composite is M<sub>n</sub> ⋯ M₂ · M₁ (the first transformation applied is on the <b>right</b>).'} A fixed point (x<sub>f</sub>, y<sub>f</sub>) ≠ (0, 0) expands to T(x<sub>f</sub>, y<sub>f</sub>) · M · T(−x<sub>f</sub>, −y<sub>f</sub>). Matrix multiplication is not commutative, so order matters.</p>`;
    const partial=i=>i===0?[[1,0,0],[0,1,0],[0,0,1]]:r.partial[i-1];
    let w=`<h4 class="${M}-h">Elementary matrices, in the order applied</h4><div class="${P}-list">`;
    r.els.forEach((x,k)=>{w+=`<div class="${P}-el" data-k="${k+1}"><div class="${P}-elh"><b>M<sub>${k+1}</sub> = ${E(x.name)}</b><span>${E(nm(st.ops[x.op]))} #${x.op+1}${x.why?' · '+E(x.why):''}</span></div>${mat(TT(x.M))}</div>`;});
    w+=`</div><h4 class="${M}-h">Composite</h4><div class="${P}-prod">${row?r.els.map((x,k)=>`<span class="${P}-fac">${mat(TT(x.M))}<small>M<sub>${k+1}</sub></small></span>`).join('<span class="'+P+'-op2">·</span>'):r.els.map((x,k)=>`<span class="${P}-fac">${mat(TT(x.M))}<small>M<sub>${k+1}</sub></small></span>`).reverse().join('<span class="'+P+'-op2">·</span>')}<span class="${P}-op2">=</span><span class="${P}-fac">${mat(TT(r.M))}<small>M</small></span></div>`;
    w+=`<h4 class="${M}-h">Vertices</h4>`+`<div class="${P}-vt">`+table(['Vertex','(x, y, 1)',row?'P · M':'M · P','Image'],r.poly.map((p,k)=>{const o=r.out[k];const Mx=r.M;return `<tr><td>${String.fromCharCode(65+k)}</td><td>${pt(p[0],p[1])}</td><td>x′ = ${fmt(Mx[0][0],4)}·${fmt(p[0])} + ${fmt(Mx[0][1],4)}·${fmt(p[1])} + ${fmt(Mx[0][2],4)}<br>y′ = ${fmt(Mx[1][0],4)}·${fmt(p[0])} + ${fmt(Mx[1][1],4)}·${fmt(p[1])} + ${fmt(Mx[1][2],4)}</td><td><b>${String.fromCharCode(65+k)}′${pt(o[0],o[1])}</b></td></tr>`;}))+'</div>';
    w+=`<h4 class="${M}-h">Running product</h4><div class="${P}-run"></div>`;
    work.innerHTML=w;const run=work.querySelector(`.${P}-run`);
    /* grid bounds over every intermediate polygon */
    const allP=r.polys.flat().concat(st.ops.filter(o=>o.t!=='T').map(o=>[num(o.px)||0,num(o.py)||0]));
    let x0=Math.floor(Math.min(0,...allP.map(p=>p[0])))-1,x1=Math.ceil(Math.max(0,...allP.map(p=>p[0])))+1,y0=Math.floor(Math.min(0,...allP.map(p=>p[1])))-1,y1=Math.ceil(Math.max(0,...allP.map(p=>p[1])))+1;
    const span=Math.max(x1-x0,y1-y0);const cs=Math.max(8,Math.min(34,Math.floor(440/span)));const step=span>40?10:span>16?5:span>8?2:1;
    const Wd=(x1-x0)*cs+36,Hd=(y1-y0)*cs+30,X=x=>28+(x-x0)*cs,Y=y=>8+(y1-y)*cs;
    let grid='';for(let x=x0;x<=x1;x++)grid+=`<line class="${M}-gl${x===0?' '+M+'-axl':''}" x1="${X(x)}" y1="${Y(y1)}" x2="${X(x)}" y2="${Y(y0)}"/>`+(x%step===0?`<text class="${M}-ax" x="${X(x)}" y="${Hd-6}" text-anchor="middle">${fmt(x)}</text>`:'');
    for(let y=y0;y<=y1;y++)grid+=`<line class="${M}-gl${y===0?' '+M+'-axl':''}" x1="${X(x0)}" y1="${Y(y)}" x2="${X(x1)}" y2="${Y(y)}"/>`+(y%step===0?`<text class="${M}-ax" x="22" y="${Y(y)+4}" text-anchor="end">${fmt(y)}</text>`:'');
    const poly=(ps,cls,lab)=>`<polygon class="${P}-poly ${cls}" points="${ps.map(p=>X(p[0])+','+Y(p[1])).join(' ')}"/>`+(lab?ps.map((p,k)=>`<circle class="${P}-v ${cls}" cx="${X(p[0])}" cy="${Y(p[1])}" r="3"/><text class="${P}-vl ${cls}" x="${X(p[0])+5}" y="${Y(p[1])-5}">${String.fromCharCode(65+k)}${lab}</text>`).join(''):'');
    const lineRef=()=>{let g='';st.ops.forEach(o=>{if(o.t==='F'&&o.axis==='line'){const m=num(o.a),c=num(o.b);const ya=m*x0+c,yb=m*x1+c;g+=`<line class="${P}-ref" x1="${X(x0)}" y1="${Y(ya)}" x2="${X(x1)}" y2="${Y(yb)}"/>`;}
      else if(o.t!=='T'){const px=num(o.px)||0,py=num(o.py)||0;if(px||py)g+=`<circle class="${P}-piv" cx="${X(px)}" cy="${Y(py)}" r="5"/><text class="${P}-vl" x="${X(px)+7}" y="${Y(py)+14}">(${fmt(px)}, ${fmt(py)})</text>`;}});return g;};
    const clip=`<clipPath id="${P}clip"><rect x="${X(x0)}" y="${Y(y1)}" width="${(x1-x0)*cs}" height="${(y1-y0)*cs}"/></clipPath>`;
    stp=stepper(sth,n+1,i=>{
      fig.innerHTML=`<svg class="${M}-svg" viewBox="0 0 ${Wd} ${Hd}" width="${Wd}" height="${Hd}" role="img" aria-label="Polygon before and after">${clip}${grid}<g clip-path="url(#${P}clip)">${lineRef()}</g>${poly(r.polys[0],'orig',i===0?'':'')}${i>0&&i<n?poly(r.out,'ghost',''):''}${poly(r.polys[i],i===n?'fin':'cur',i===0?'':'′')}</svg><p class="${M}-legend"><span class="${P}-k0"></span> original <span class="${P}-k1"></span> ${i===n?'final image':'after step '+i}${i>0&&i<n?` <span class="${P}-k2"></span> final`:''}</p>`;
      work.querySelectorAll(`.${P}-el`).forEach(el=>{const k=+el.dataset.k;el.classList.toggle('on',k===i);el.classList.toggle('fut',k>i);});
      const C=partial(i);run.innerHTML=i===0?`<p class="${M}-note">Start with the identity matrix.</p>${mat(C)}`:`<p class="${M}-note">${row?`C<sub>${i}</sub> = C<sub>${i-1}</sub> · M<sub>${i}</sub>`:`C<sub>${i}</sub> = M<sub>${i}</sub> · C<sub>${i-1}</sub>`}</p><div class="${P}-prod">${row?`${mat(TT(partial(i-1)))}<span class="${P}-op2">·</span>${mat(TT(r.els[i-1].M))}`:`${mat(r.els[i-1].M)}<span class="${P}-op2">·</span>${mat(partial(i-1))}`}<span class="${P}-op2">=</span>${mat(TT(C))}</div>`;
      cap.innerHTML=i===0?`The original polygon ${r.poly.map(p=>pt(p[0],p[1])).join(' ')}. Press Next to apply M₁.`:`Apply M<sub>${i}</sub> = <b>${E(r.els[i-1].name)}</b>${r.els[i-1].why?' ('+E(r.els[i-1].why)+')':''}: the vertices become ${r.polys[i].map(p=>pt(p[0],p[1])).join(' ')}.`;},n);
  }
  let stp=null;drawOps();compute();
 }});

/* editable table: cols [{k,label,w}], rows = array of objects with string values (mutated in place) */
function edTable(host,cols,rows,onChange,blank){
  const fire=debounce(onChange,250);
  const draw=()=>{
    host.innerHTML=`<div class="${M}-scroll"><table class="${M}-tbl ${M}-ed"><thead><tr><th>#</th>${cols.map(c=>`<th>${c.label}</th>`).join('')}<th></th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td>${cols.map(c=>`<td><input type="text" data-i="${i}" data-k="${c.k}" value="${E(r[c.k])}" style="width:${c.w||3.6}em" spellcheck="false" autocomplete="off" aria-label="${E(c.aria||c.k)} row ${i+1}"></td>`).join('')}<td><button type="button" class="btn sm ${M}-x" data-del="${i}" aria-label="Remove row ${i+1}"${rows.length<2?' disabled':''}>✕</button></td></tr>`).join('')}</tbody></table></div><button type="button" class="btn sm ${M}-addrow" data-add="1">+ Add row</button>`;
    host.querySelectorAll('input').forEach(el=>el.oninput=()=>{rows[+el.dataset.i][el.dataset.k]=el.value;fire();});
    host.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{rows.splice(+b.dataset.del,1);draw();onChange();});
    host.querySelector('[data-add]').onclick=()=>{if(rows.length>=40)return;rows.push(blank(rows));draw();onChange();};
  };
  draw();return {draw};
}

/* ---------------------------------------------------------------- seest UI */
ANIM.register('seest',{title:'Software estimation and scheduling solver',steps:false,
 caption:'COCOMO effort and schedule, function points, cyclomatic complexity and PERT/CPM critical paths, with every formula shown with your numbers substituted.',
 build(stage){
  const P='seest';
  const st={tab:0,
    co:{model:'basic',mode:'organic',kloc:'32',r:{}},
    fp:{c:{EI:['0','50','0'],EO:['0','40','0'],EQ:['0','35','0'],ILF:['0','6','0'],EIF:['0','4','0']},f:Array(14).fill(3)},
    g:{sub:'cc',edges:'1-2, 2-3, 2-6, 3-4, 3-5, 4-7, 5-7, 7-8, 6-8, 8-2, 8-9',form:'aon',three:false,deadline:'',
       aon:[['A','','3'],['B','','4'],['C','A','2'],['D','A','5'],['E','B, C','1'],['F','D, E','2']].map(([id,pred,t])=>({id,pred,t,a:'',m:'',b:''})),
       aoa:[['1','2','4'],['1','3','6'],['2','3','3'],['2','4','5'],['3','4','2']].map(([i,j,t])=>({i,j,t,a:'',m:'',b:''}))}};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${M} ${P}"><div class="${M}-tabs" role="group" aria-label="Topic"></div><div class="${P}-pane"></div></div>`;
  const $=s=>stage.querySelector(s),pane=$(`.${P}-pane`);
  tabs($(`.${M}-tabs`),['COCOMO','Function points','Cyclomatic complexity &amp; PERT/CPM'],0,k=>{st.tab=k;render();});
  const shell=inner=>`<div class="${M}-in">${inner}</div><div class="${M}-err" role="alert" hidden></div><div class="${M}-ans"></div><div class="${M}-conv"></div><div class="${P}-out"></div>`;
  function render(){[drawCo,drawFp,drawG][st.tab]();}

  /* ---------- COCOMO ---------- */
  function drawCo(){
    const s=st.co;
    pane.innerHTML=shell(`<div class="${M}-w2"><span class="${M}-lab">Model</span>${segH(P+'Mdl',[['basic','Basic'],['inter','Intermediate']])}</div>
      <label class="${M}-lab ${M}-w2">Mode<select data-k="mode"><option value="organic">Organic</option><option value="semi">Semi-detached</option><option value="embedded">Embedded</option></select></label>
      ${inp('kloc','Size (KLOC)',s.kloc)}
      <div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option><option value="0">32 KLOC organic (≈ 91 PM)</option><option value="1">400 KLOC, all three modes (Aggarwal)</option><option value="2">Intermediate: 10 KLOC embedded, RELY VH, ACAP H</option></select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>
      <div class="${M}-wide ${P}-drv"></div>`);
    const q=s2=>pane.querySelector(s2),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),out=q(`.${P}-out`),drv=q(`.${P}-drv`);
    seg(q('#'+P+'Mdl'),s.model,v=>{s.model=v;drawDrv();calc();});
    q('[data-k=mode]').value=s.mode;q('[data-k=mode]').onchange=e=>{s.mode=e.target.value;calc();};
    q('[data-k=kloc]').oninput=debounce(e=>{s.kloc=e.target.value;calc();},250);
    q('[data-x=pre]').onchange=e=>{const v=e.target.value;if(v==='0')Object.assign(s,{model:'basic',mode:'organic',kloc:'32',r:{}});else if(v==='1')Object.assign(s,{model:'basic',mode:'organic',kloc:'400',r:{}});else if(v==='2')Object.assign(s,{model:'inter',mode:'embedded',kloc:'10',r:{RELY:'VH',ACAP:'H'}});else return;drawCo();};
    q('[data-b=rnd]').onclick=()=>{s.kloc=''+pick([8,12,20,32,45,60,90,150,250,400]);s.mode=pick(['organic','semi','embedded']);s.r={};if(s.model==='inter')SE.DRIVERS.forEach(([id,,,m])=>{if(Math.random()<.3){const ok=SE.RATINGS.filter((r,i)=>m[i]!=null);s.r[id]=pick(ok);}});drawCo();};
    function drawDrv(){
      if(s.model!=='inter'){drv.innerHTML='';return;}
      drv.innerHTML=`<span class="${M}-lab">Cost drivers (effort multipliers)</span><div class="${P}-grid">${SE.DRIVERS.map(([id,name,grp,m])=>`<label class="${P}-dl"><span><b>${id}</b> ${E(name)}</span><select data-d="${id}">${SE.RATINGS.map((r,i)=>m[i]==null?'':`<option value="${r}">${SE.RATENAME[r]} (${m[i].toFixed(2)})</option>`).join('')}</select></label>`).join('')}</div><button type="button" class="btn sm" data-b="nom">Reset all to nominal</button>`;
      drv.querySelectorAll('[data-d]').forEach(el=>{el.value=s.r[el.dataset.d]||'N';el.onchange=()=>{s.r[el.dataset.d]=el.value;calc();};});
      drv.querySelector('[data-b=nom]').onclick=()=>{s.r={};drawDrv();calc();};
    }
    function calc(){
      const r=SE.cocomo(num(s.kloc),s.mode,s.model,s.r);
      if(r.err){setErr(err,r.err);pane.classList.add(`${M}-stale`);return;}setErr(err,null);pane.classList.remove(`${M}-stale`);
      const k=r.k,inter=s.model==='inter';
      ans.innerHTML=card('Effort E',fmt(r.E,2)+' PM','person-months')+card('Duration D',fmt(r.D,2)+' months','development time')+card('Average staff',fmt(r.staff,2),'E / D persons')+card('Productivity',fmt(r.prod,1)+' LOC/PM','KLOC × 1000 / E')+(inter?card('EAF',fmt(r.eaf,4),r.used.length?r.used.map(u=>u.id).join(' × '):'all nominal'):'');
      conv.innerHTML=`<p class="${M}-note"><b>${inter?'Intermediate':'Basic'} COCOMO (Boehm 1981).</b> E = a · (KLOC)<sup>b</sup>${inter?' · EAF':''} person-months; D = c · E<sup>d</sup> months. ${inter?'Intermediate uses a = 3.2 / 3.0 / 2.8 with the same b, c, d as Basic; EAF is the product of the 15 cost-driver multipliers (nominal = 1.00).':''} Rule of thumb for the mode: organic for small, familiar in-house projects (up to about 50 KLOC), semi-detached for mixed teams (about 50–300 KLOC), embedded for tight hardware or regulatory constraints. Answers are not rounded until the end; NET options are usually rounded to the nearest whole number.</p>`;
      const lnK=Math.pow(r.kloc,k.b);
      let h=`<h4 class="${M}-h">Working</h4><div class="${M}-formula">`;
      if(inter)h+=`<p>EAF = ${r.used.length?r.used.map(u=>`${u.id} (${SE.RATENAME[u.r]}) ${u.v.toFixed(2)}`).join(' × ')+' = <b>'+fmt(r.eaf,4)+'</b>':'1.00 (every driver nominal)'}</p>`;
      h+=`<p>E = a · (KLOC)<sup>b</sup>${inter?' · EAF':''} = ${k.a} × ${fmt(r.kloc)}<sup>${k.b}</sup>${inter?' × '+fmt(r.eaf,4):''} = ${k.a} × ${fmt(lnK,3)}${inter?' × '+fmt(r.eaf,4):''} = <b>${fmt(r.E,2)} PM</b></p>`;
      h+=`<p>D = c · E<sup>d</sup> = ${k.c} × ${fmt(r.E,2)}<sup>${k.d}</sup> = ${k.c} × ${fmt(Math.pow(r.E,k.d),3)} = <b>${fmt(r.D,2)} months</b></p>`;
      h+=`<p>Staff = E / D = ${fmt(r.E,2)} / ${fmt(r.D,2)} = <b>${fmt(r.staff,2)} persons</b>; productivity = ${fmt(r.kloc*1000)} / ${fmt(r.E,2)} = <b>${fmt(r.prod,1)} LOC/PM</b></p></div>`;
      h+=`<h4 class="${M}-h">Coefficients</h4>`+table(['Mode','a (basic)','a (intermediate)','b','c','d'],['organic','semi','embedded'].map(m=>`<tr class="${m===s.mode?M+'-cur':''}"><td>${SE.MODENAME[m]}</td><td>${SE.BASIC[m].a}</td><td>${SE.INTER[m].a}</td><td>${SE.BASIC[m].b}</td><td>${SE.BASIC[m].c}</td><td>${SE.BASIC[m].d}</td></tr>`));
      h+=`<h4 class="${M}-h">Same size in every mode (${inter?'intermediate':'basic'})</h4>`+table(['Mode','E (PM)','D (months)','Staff'],['organic','semi','embedded'].map(m=>{const x=SE.cocomo(r.kloc,m,s.model,s.r);return `<tr class="${m===s.mode?M+'-cur':''}"><td>${SE.MODENAME[m]}</td><td>${fmt(x.E,2)}</td><td>${fmt(x.D,2)}</td><td>${fmt(x.staff,2)}</td></tr>`;}));
      out.innerHTML=`<div class="${P}-body">${h}</div>`;
    }
    drawDrv();calc();
  }

  /* ---------- Function points ---------- */
  function drawFp(){
    const s=st.fp;
    pane.innerHTML=shell(`<div class="${M}-wide"><span class="${M}-lab">Counts by complexity (weights in brackets)</span>${table(['Component','Low','Average','High'],SE.FPKEYS.map(k=>`<tr><td>${SE.FP[k][0]}</td>${[0,1,2].map(j=>`<td><input type="text" inputmode="numeric" data-c="${k}" data-j="${j}" value="${E(s.c[k][j])}" style="width:3.6em" aria-label="${k} ${['low','average','high'][j]} count"> <small>×${SE.FP[k][1][j]}</small></td>`).join('')}</tr>`),P+'-cnt')}</div>
      <div class="${M}-wide"><span class="${M}-lab">14 general system characteristics F<sub>i</sub> (0 = no influence … 5 = essential)</span><div class="${P}-grid">${SE.GSC.map((g,i)=>`<label class="${P}-dl"><span>F<sub>${i+1}</sub> ${E(g)}</span><select data-f="${i}">${[0,1,2,3,4,5].map(v=>`<option value="${v}">${v}</option>`).join('')}</select></label>`).join('')}</div></div>
      <div class="${M}-btns"><label class="${M}-lab">Set all 14 factors to<select data-x="all"><option value="">Choose…</option>${[0,1,2,3,4,5].map(v=>`<option value="${v}">${v}${v===3?' (average)':''}</option>`).join('')}</select></label><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option><option value="0">Aggarwal: 50/40/35/6/4, all average</option><option value="1">Mixed complexities, factors 0</option></select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`);
    const q=x=>pane.querySelector(x),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),out=q(`.${P}-out`);
    pane.querySelectorAll('[data-c]').forEach(el=>el.oninput=debounce(()=>{s.c[el.dataset.c][+el.dataset.j]=el.value;calc();},250));
    pane.querySelectorAll('[data-f]').forEach(el=>{el.value=s.f[+el.dataset.f];el.onchange=()=>{s.f[+el.dataset.f]=+el.value;calc();};});
    q('[data-x=all]').onchange=e=>{if(e.target.value==='')return;s.f=Array(14).fill(+e.target.value);drawFp();};
    q('[data-x=pre]').onchange=e=>{const v=e.target.value;if(v==='0'){s.c={EI:['0','50','0'],EO:['0','40','0'],EQ:['0','35','0'],ILF:['0','6','0'],EIF:['0','4','0']};s.f=Array(14).fill(3);}else if(v==='1'){s.c={EI:['2','0','0'],EO:['0','0','1'],EQ:['0','3','0'],ILF:['0','0','1'],EIF:['2','0','0']};s.f=Array(14).fill(0);}else return;drawFp();};
    q('[data-b=rnd]').onclick=()=>{SE.FPKEYS.forEach(k=>{s.c[k]=Math.random()<.5?['0',''+rnd(2,30),'0']:[''+rnd(0,12),''+rnd(0,12),''+rnd(0,6)];});s.f=Math.random()<.4?Array(14).fill(rnd(1,4)):s.f.map(()=>rnd(0,5));drawFp();};
    function calc(){
      const c={};for(const k of SE.FPKEYS)c[k]=s.c[k].map(v=>v.trim()===''?0:num(v));
      const r=SE.fp(c,s.f);
      if(r.err){setErr(err,r.err);pane.classList.add(`${M}-stale`);return;}setErr(err,null);pane.classList.remove(`${M}-stale`);
      ans.innerHTML=card('UFP',fmt(r.ufp),'unadjusted function points')+card('ΣF<sub>i</sub>',r.tdi,'total degree of influence')+card('VAF (CAF)',fmt(r.vaf,2),'0.65 + 0.01 × ΣF<sub>i</sub>')+card('FP',fmt(r.fp,2),'UFP × VAF');
      conv.innerHTML=`<p class="${M}-note"><b>IFPUG / Albrecht weights.</b> UFP = Σ count × weight over the five components and three complexities. The value adjustment factor (also called CAF) is 0.65 + 0.01 × ΣF<sub>i</sub>, so it ranges from 0.65 (all 0) to 1.35 (all 5). “All factors average” means every F<sub>i</sub> = 3, ΣF<sub>i</sub> = 42 and VAF = 1.07.</p>`;
      out.innerHTML=`<div class="${P}-body"><h4 class="${M}-h">UFP</h4>`+table(['Component','Low','Average','High','Subtotal'],r.rows.map(x=>`<tr><td>${x.k}</td>${[0,1,2].map(j=>`<td>${x.c[j]} × ${x.w[j]} = ${x.c[j]*x.w[j]}</td>`).join('')}<td><b>${x.sub}</b></td></tr>`).concat([`<tr class="${M}-cur"><td colspan="4">UFP</td><td><b>${r.ufp}</b></td></tr>`]))+
        `<div class="${M}-formula"><p>ΣF<sub>i</sub> = ${s.f.join(' + ')} = <b>${r.tdi}</b></p><p>VAF = 0.65 + 0.01 × ${r.tdi} = <b>${fmt(r.vaf,2)}</b></p><p>FP = UFP × VAF = ${r.ufp} × ${fmt(r.vaf,2)} = <b>${fmt(r.fp,2)}</b></p></div></div>`;
    }
    calc();
  }

  /* ---------- Cyclomatic complexity and PERT/CPM ---------- */
  function drawG(){
    const s=st.g;
    pane.innerHTML=`<div class="${P}-sub">${segH(P+'Sub',[['cc','Cyclomatic complexity'],['pert','PERT / CPM']])}</div><div class="${P}-gp"></div>`;
    seg(pane.querySelector('#'+P+'Sub'),s.sub,v=>{s.sub=v;inner();});
    const gp=pane.querySelector(`.${P}-gp`);
    function inner(){(s.sub==='cc'?drawCC:drawPert)(gp);}
    inner();
  }
  function randFlow(){let n=1,cur=1;const Ed=[];const cnt=rnd(2,3);
    for(let i=0;i<cnt;i++){const t=pick(['if','ifelse','while','switch']);
      if(t==='if'){const a=++n,j=++n;Ed.push([cur,a],[a,j],[cur,j]);cur=j;}
      else if(t==='ifelse'){const a=++n,b=++n,j=++n;Ed.push([cur,a],[cur,b],[a,j],[b,j]);cur=j;}
      else if(t==='while'){const d=++n,b=++n,x=++n;Ed.push([cur,d],[d,b],[b,d],[d,x]);cur=x;}
      else{const a=++n,b=++n,c=++n,j=++n;Ed.push([cur,a],[cur,b],[cur,c],[a,j],[b,j],[c,j]);cur=j;}}
    return Ed.map(e=>e.join('-')).join(', ');}
  function drawCC(host){
    const s=st.g;
    host.innerHTML=shell(`<label class="${M}-lab ${M}-wide">Flow-graph edges (directed, from-to)<textarea data-k="edges" rows="2" spellcheck="false"></textarea></label>
      <div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option><option value="1-2, 2-3, 2-6, 3-4, 3-5, 4-7, 5-7, 7-8, 6-8, 8-2, 8-9">Loop with nested if (V = 4)</option><option value="1-2, 1-3, 2-4, 3-4">if–else (V = 2)</option><option value="1-2, 2-3, 3-2, 2-4">while loop (V = 2)</option><option value="1-2, 1-3, 1-4, 2-5, 3-5, 4-5">switch with 3 cases (V = 3)</option><option value="1-2, 1-3, 2-4, 3-4, 5-6, 5-7, 6-8, 7-8">Two separate modules (P = 2)</option></select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`)+`<div class="${M}-two"><div class="${M}-work"></div><div class="${M}-fig"></div></div>`;
    const q=x=>host.querySelector(x),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),work=q(`.${M}-work`),fig=q(`.${M}-fig`),ta=q('[data-k=edges]');
    ta.value=s.edges;ta.oninput=debounce(()=>{s.edges=ta.value;calc();},300);
    q('[data-x=pre]').onchange=e=>{if(!e.target.value)return;s.edges=e.target.value;ta.value=s.edges;calc();};
    q('[data-b=rnd]').onclick=()=>{s.edges=randFlow();ta.value=s.edges;calc();};
    function calc(){
      const r=SE.cyclo(s.edges);
      if(r.err){setErr(err,r.err);host.classList.add(`${M}-stale`);return;}setErr(err,null);host.classList.remove(`${M}-stale`);
      ans.innerHTML=card('V(G)',r.V,`E − N + 2P = ${r.e} − ${r.N} + ${2*r.P}`)+card('Nodes N',r.N,'')+card('Edges E',r.e,'')+card('Components P',r.P,r.P===1?'connected':'separate modules')+card('Decision nodes',r.dec.length,r.dec.map(d=>d.n).join(', ')||'none');
      conv.innerHTML=`<p class="${M}-note"><b>Three ways to get V(G)</b> (McCabe). All three agree for a connected flow graph with one entry and one exit. V(G) is also the number of independent paths (the basis set) and so the minimum number of test cases for basis-path testing.</p>`;
      const agree=r.V===r.predV&&(r.regions==null||r.regions===r.V);
      let h=`<h4 class="${M}-h">Working</h4><div class="${M}-formula">`+
        `<p><b>1. Edges and nodes:</b> V(G) = E − N + 2P = ${r.e} − ${r.N} + 2 × ${r.P} = <b>${r.V}</b></p>`+
        `<p><b>2. Decision (predicate) nodes:</b> V(G) = Σ(out-degree − 1) + ${r.P===1?'1':'P'} = ${r.dec.length?r.dec.map(d=>`(${d.out} − 1)`).join(' + '):'0'} + ${r.P} = <b>${r.predV}</b>${r.binary&&r.dec.length?` (all decisions are binary, so this is simply D + 1 with D = ${r.dec.length})`:r.dec.length?' (a node with k exits counts as k − 1 decisions)':''}</p>`+
        (r.regions!=null?`<p><b>3. Regions:</b> R = E − N + 2 = ${r.e} − ${r.N} + 2 = <b>${r.regions}</b> (Euler's formula for a planar graph; count the outer region too)</p>`:`<p><b>3. Regions:</b> counted per connected component; for P = ${r.P} use V(G) = Σ (regions of each part).</p>`)+`</div>`;
      if(r.exits.length!==r.P)h+=`<p class="${M}-warn">This graph has ${r.exits.length} exit node${r.exits.length===1?'':'s'} (${r.exits.join(', ')||'none'}); a well-formed flow graph has one per module, which is why the formulas can disagree.</p>`;
      else if(!agree)h+=`<p class="${M}-warn">The formulas disagree for this graph; check for unreachable nodes.</p>`;
      h+=table(['Node','Out-degree','Role'],r.nodes.map(n=>{const o=r.E.filter(e=>e[0]===n).length;return `<tr class="${o>=2?M+'-cur':''}"><td>${E(n)}</td><td>${o}</td><td>${o>=2?'decision':o===0?'exit':'process'}</td></tr>`;}));
      work.innerHTML=h;
      /* draw: layer by longest path after removing back edges found by DFS */
      const adj={};r.nodes.forEach(n=>adj[n]=[]);r.E.forEach(([a,b])=>adj[a].push(b));
      const state={},back=new Set();const dfs=u=>{state[u]=1;for(const v of adj[u]){if(state[v]===1)back.add(u+'>'+v);else if(!state[v])dfs(v);}state[u]=2;};
      const inDeg={};r.nodes.forEach(n=>inDeg[n]=0);r.E.forEach(([,b])=>inDeg[b]++);
      r.nodes.filter(n=>!inDeg[n]).concat(r.nodes).forEach(n=>{if(!state[n])dfs(n);});
      const fwd=r.E.filter(([a,b])=>!back.has(a+'>'+b)).map(([u,v])=>({u,v}));const lay=longest(r.nodes,fwd);
      const decs=new Set(r.dec.map(d=>d.n));
      fig.innerHTML=`<div class="${M}-scroll">${graphSvg(r.nodes.map(n=>({id:n,lines:[n],cls:decs.has(n)?'dec':r.exits.includes(n)?'exit':''})),r.E.map(([u,v])=>({u,v})),lay,{dir:'TB',nw:32,nh:32,round:16,gapL:58,gapA:56,label:'Flow graph'})}</div><p class="${M}-legend"><span class="${P}-kd"></span> decision node <span class="${P}-kx"></span> exit node</p>`;
    }
    calc();
  }
  function drawPert(host){
    const s=st.g;
    host.innerHTML=shell(`<div class="${M}-w2"><span class="${M}-lab">Network form</span>${segH(P+'Form',[['aon','Activity on node'],['aoa','Activity on arrow (i–j)']])}</div>
      <div class="${M}-w2"><span class="${M}-lab">Durations</span>${segH(P+'Three',[['1','One time (CPM)'],['3','a, m, b (PERT)']])}</div>
      ${s.three?inp('deadline','Deadline D for P(T ≤ D), optional',s.deadline,M+'-w2'):''}
      <div class="${M}-wide ${P}-acts"></div>
      <div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option><option value="0">CPM, activity on node (T = 10)</option><option value="1">PERT, activity on node (T = 9)</option><option value="2">CPM, activity on arrow (two critical paths)</option><option value="3">PERT, activity on arrow</option></select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`)+`<div class="${M}-sth"></div><p class="${M}-cap" aria-live="polite"></p><div class="${P}-net"></div><div class="${P}-tbl"></div>`;
    const q=x=>host.querySelector(x),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),sth=q(`.${M}-sth`),cap=q(`.${M}-cap`),net=q(`.${P}-net`),tb=q(`.${P}-tbl`);
    seg(q('#'+P+'Form'),s.form,v=>{s.form=v;drawPert(host);});
    seg(q('#'+P+'Three'),s.three?'3':'1',v=>{s.three=v==='3';fillThree();drawPert(host);});
    if(s.three)q('[data-k=deadline]').oninput=debounce(e=>{s.deadline=e.target.value;calc();},250);
    function fillThree(){for(const r of s[s.form]){if(s.three&&r.a===''&&r.t!==''){r.a=r.t;r.m=r.t;r.b=r.t;}if(!s.three&&r.t===''&&r.m!=='')r.t=r.m;}}
    const cols=(s.form==='aon'?[{k:'id',label:'Activity',w:4.5},{k:'pred',label:'Predecessors',w:7}]:[{k:'i',label:'i',w:3},{k:'j',label:'j',w:3}]).concat(s.three?[{k:'a',label:'a',w:3},{k:'m',label:'m',w:3},{k:'b',label:'b',w:3}]:[{k:'t',label:'Duration',w:4}]);
    edTable(q(`.${P}-acts`),cols,s[s.form],calc,rows=>s.form==='aon'?{id:String.fromCharCode(65+rows.length%26),pred:rows.length?rows[rows.length-1].id:'',t:'1',a:'1',m:'2',b:'3'}:{i:rows.length?rows[rows.length-1].j:'1',j:String(+(rows.length?rows[rows.length-1].j:1)+1),t:'1',a:'1',m:'2',b:'3'});
    q('[data-x=pre]').onchange=e=>{const v=e.target.value;if(v==='')return;
      if(v==='0'){s.form='aon';s.three=false;s.aon=[['A','','3'],['B','','4'],['C','A','2'],['D','A','5'],['E','B, C','1'],['F','D, E','2']].map(([id,pred,t])=>({id,pred,t,a:'',m:'',b:''}));}
      else if(v==='1'){s.form='aon';s.three=true;s.deadline='10';s.aon=[['A','',1,2,3],['B','',2,3,4],['C','A',1,3,11],['D','B',2,4,6],['E','C, D',1,2,3]].map(([id,pred,a,m,b])=>({id,pred,t:'',a:''+a,m:''+m,b:''+b}));}
      else if(v==='2'){s.form='aoa';s.three=false;s.aoa=[['1','2','4'],['1','3','6'],['2','3','3'],['2','4','5'],['3','4','2']].map(([i,j,t])=>({i,j,t,a:'',m:'',b:''}));}
      else{s.form='aoa';s.three=true;s.deadline='20';s.aoa=[['1','2',2,4,6],['1','3',3,5,9],['2','4',4,6,8],['3','4',1,2,3],['3','5',6,8,16],['4','5',2,3,4]].map(([i,j,a,m,b])=>({i,j,t:'',a:''+a,m:''+m,b:''+b}));}
      drawPert(host);};
    q('[data-b=rnd]').onclick=()=>{const n=rnd(5,8);
      if(s.form==='aon'){s.aon=[];for(let k=0;k<n;k++){const id=String.fromCharCode(65+k);const pr=k<2?[]:[...new Set([rnd(0,k-1),rnd(Math.max(0,k-3),k-1)])].slice(0,rnd(1,2)).map(x=>String.fromCharCode(65+x));const m=rnd(2,9),a=Math.max(1,m-rnd(1,3)),b=m+rnd(1,6);s.aon.push({id,pred:pr.join(', '),t:''+m,a:''+a,m:''+m,b:''+b});}}
      else{s.aoa=[];const ev=rnd(4,6);for(let j=2;j<=ev;j++){const i=rnd(Math.max(1,j-2),j-1);const m=rnd(2,9);s.aoa.push({i:''+i,j:''+j,t:''+m,a:''+Math.max(1,m-2),m:''+m,b:''+(m+rnd(1,5))});}
        for(let k=0;k<rnd(1,3);k++){const i=rnd(1,ev-2),j=rnd(i+2,ev);if(!s.aoa.some(x=>x.i===''+i&&x.j===''+j)){const m=rnd(2,9);s.aoa.push({i:''+i,j:''+j,t:''+m,a:''+Math.max(1,m-2),m:''+m,b:''+(m+rnd(1,5))});}}}
      if(s.three&&!s.deadline)s.deadline='';drawPert(host);};
    let stp=null;
    function calc(){
      const rows=s[s.form];const acts=rows.map(r=>s.form==='aon'?{id:r.id,pred:String(r.pred||'').split(/[\s,;]+/).filter(Boolean),t:num(r.t),a:num(r.a),m:num(r.m),b:num(r.b)}:{i:r.i,j:r.j,t:num(r.t),a:num(r.a),m:num(r.m),b:num(r.b)});
      const dl=s.three&&String(s.deadline).trim()!==''?num(s.deadline):undefined;
      if(dl!==undefined&&isNaN(dl)){setErr(err,'The deadline must be a number.');host.classList.add(`${M}-stale`);return;}
      const r=SE.cpm(acts,{three:s.three,aoa:s.form==='aoa',deadline:dl});
      if(r.err){setErr(err,r.err);host.classList.add(`${M}-stale`);return;}setErr(err,null);host.classList.remove(`${M}-stale`);
      const cp=r.paths.map(p=>p.p.map(id=>s.form==='aoa'?id:id).join(s.form==='aoa'?' → ':' → '));
      const cpEv=s.form==='aoa'?r.paths.map(p=>[p.p[0].split('-')[0]].concat(p.p.map(id=>id.split('-')[1])).join(' → ')):cp;
      ans.innerHTML=card('Project duration T',fmt(r.T,2),s.three?'expected (sum of t<sub>e</sub> on the critical path)':'length of the critical path')+card(`Critical path${r.paths.length>1?'s':''}`,cpEv.join('<br>'),s.form==='aoa'?'events':'activities')+(s.three?card('Variance σ²',fmt(r.variance,4),`σ = ${fmt(r.sd,4)}${r.paths.length>1?' (largest over critical paths)':''}`):'')+(r.prob?card(`P(T ≤ ${fmt(r.prob.D)})`,fmt(r.prob.p*100,2)+'%',r.prob.z==null?'σ = 0':`z = (${fmt(r.prob.D)} − ${fmt(r.T,2)}) / ${fmt(r.sd,4)} = ${fmt(r.prob.z,3)}`):'');
      conv.innerHTML=`<p class="${M}-note"><b>Conventions:</b> ${s.three?'t<sub>e</sub> = (a + 4m + b) / 6 and σ² = ((b − a) / 6)². Project variance = sum of σ² along the critical path (the largest if there are several); P(T ≤ D) uses the normal distribution with z = (D − T) / σ. ':''}Forward pass: ES = max EF of the predecessors (0 at the start), EF = ES + t. Backward pass: LF = min LS of the successors (T at the end), LS = LF − t. Total float (slack) = LS − ES; free float = min ES of the successors − EF. Critical activities have zero slack.${s.form==='aoa'?' For events: T<sub>E</sub> = earliest, T<sub>L</sub> = latest occurrence time.':''}</p>`;
      const n=r.trace.length;
      const lab=a=>s.form==='aoa'?a.id:a.id;
      const draw=f=>{
        const fin=f>=n,done=r.trace.slice(0,Math.min(f+1,n));const fw=new Set(done.filter(x=>x.pass==='f').map(x=>x.id)),bw=new Set(done.filter(x=>x.pass==='b').map(x=>x.id));const cur=fin?null:r.trace[f].id;
        const head=['Activity'].concat(s.three?['a','m','b','t<sub>e</sub>','σ²']:['t'],['ES','EF','LS','LF','Slack','Free float','Critical']);
        const rowsH=r.A.map(a=>`<tr class="${a.id===cur?M+'-cur':''}${fin&&a.crit?' '+P+'-crit':''}"><td><b>${E(lab(a))}</b>${s.form==='aon'&&a.pred.length?` <small>← ${E(a.pred.join(', '))}</small>`:''}</td>${s.three?`<td>${fmt(a.a)}</td><td>${fmt(a.m)}</td><td>${fmt(a.b)}</td><td>${fmt(a.t,3)}</td><td>${fmt(a.v,4)}</td>`:`<td>${fmt(a.t)}</td>`}<td>${fw.has(a.id)?fmt(a.ES,2):''}</td><td>${fw.has(a.id)?fmt(a.EF,2):''}</td><td>${bw.has(a.id)?fmt(a.LS,2):''}</td><td>${bw.has(a.id)?fmt(a.LF,2):''}</td><td>${fin?fmt(a.slack,2):''}</td><td>${fin?fmt(a.ff,2):''}</td><td>${fin?(a.crit?'<b>✓</b>':''):''}</td></tr>`);
        let h=`<h4 class="${M}-h">Activity table</h4>`+table(head,rowsH,P+'-at');
        if(r.events)h+=`<h4 class="${M}-h">Event times</h4>`+table(['Event','T<sub>E</sub>','T<sub>L</sub>','Slack'],r.events.map(e=>`<tr class="${fin&&e.slack===0?P+'-crit':''}"><td>${E(e.n)}</td><td>${fin||r.A.filter(a=>a.j===e.n).every(a=>fw.has(a.id))?fmt(e.TE,2):''}</td><td>${fin||r.A.filter(a=>a.i===e.n).every(a=>bw.has(a.id))&&bw.size?fmt(e.TL,2):''}</td><td>${fin?fmt(e.slack,2):''}</td></tr>`));
        tb.innerHTML=h;
        /* network */
        let svg;
        if(s.form==='aon'){const ids=r.A.map(a=>a.id),ed=[];r.A.forEach(a=>a.pred.forEach(p=>ed.push({u:p,v:a.id,cls:fin&&a.crit&&r.byId[p].crit&&Math.abs(r.byId[p].EF-a.ES)<1e-9?'crit':''})));
          const lay=longest(ids,ed);
          svg=graphSvg(r.A.map(a=>({id:a.id,lines:[`${a.id} (${fmt(a.t,2)})`,`${fw.has(a.id)?fmt(a.ES,2)+'–'+fmt(a.EF,2):'·'} | ${bw.has(a.id)?fmt(a.LS,2)+'–'+fmt(a.LF,2):'·'}`],cls:(a.id===cur?'cur ':'')+(fin&&a.crit?'crit':'')})),ed,lay,{nw:104,nh:40,gapL:140,gapA:58,label:'Activity-on-node network'});}
        else{const evs=r.events.map(e=>e.n),ed=r.A.map(a=>({u:a.i,v:a.j,label:fmt(a.t,2),cls:(a.id===cur?'cur ':'')+(fin&&a.crit?'crit':'')}));const lay=longest(evs,ed);
          svg=graphSvg(r.events.map(e=>{const te=fin||r.A.filter(a=>a.j===e.n).every(a=>fw.has(a.id)),tl=fin||(bw.size&&r.A.filter(a=>a.i===e.n).every(a=>bw.has(a.id)));return {id:e.n,lines:[e.n,`${te?fmt(e.TE,2):'·'} | ${tl?fmt(e.TL,2):'·'}`],cls:fin&&e.slack===0?'crit':''};}),ed,lay,{nw:64,nh:40,round:20,gapL:120,gapA:62,label:'Activity-on-arrow network'});}
        net.innerHTML=`<div class="${M}-scroll">${svg}</div><p class="${M}-legend">${s.form==='aon'?'Each node: name (duration), then ES–EF | LS–LF.':'Each event: number, then T<sub>E</sub> | T<sub>L</sub>; arrows carry durations.'} <span class="${P}-kc"></span> critical</p>`;
        if(fin)cap.innerHTML=`Slack = LS − ES. Activities with zero slack form the critical path${r.paths.length>1?'s':''} <b>${cpEv.join('</b> and <b>')}</b>, length T = ${fmt(r.T,2)}.`;
        else{const t=r.trace[f],a=r.byId[t.id];
          cap.innerHTML=t.pass==='f'?`Forward pass, <b>${E(a.id)}</b>: ES = ${t.from.length?`max(${t.from.map(([p,v])=>`EF<sub>${E(p)}</sub> ${fmt(v,2)}`).join(', ')})`:'0 (no predecessor)'} = ${fmt(a.ES,2)}; EF = ${fmt(a.ES,2)} + ${fmt(a.t,2)} = <b>${fmt(a.EF,2)}</b>.`:`Backward pass, <b>${E(a.id)}</b>: LF = ${t.from.length?`min(${t.from.map(([p,v])=>`LS<sub>${E(p)}</sub> ${fmt(v,2)}`).join(', ')})`:'T = '+fmt(r.T,2)+' (no successor)'} = ${fmt(a.LF,2)}; LS = ${fmt(a.LF,2)} − ${fmt(a.t,2)} = <b>${fmt(a.LS,2)}</b>.`;}
      };
      stp=stepper(sth,n+1,draw);
    }
    calc();
  }
  render();
 }});

/* ---------------------------------------------------------------- gamesearch UI */
ANIM.register('gamesearch',{title:'Minimax, alpha–beta and A* solver',steps:false,
 caption:'Type a game tree as nested lists to get minimax values and an alpha–beta trace with the pruned branches, or a weighted graph with heuristic values to get the A* OPEN/CLOSED trace.',
 build(stage){
  const P='gamesearch';
  const ROM='Arad-Zerind 75, Arad-Sibiu 140, Arad-Timisoara 118, Zerind-Oradea 71, Oradea-Sibiu 151, Timisoara-Lugoj 111, Lugoj-Mehadia 70, Mehadia-Drobeta 75, Drobeta-Craiova 120, Craiova-Rimnicu 146, Craiova-Pitesti 138, Sibiu-Fagaras 99, Sibiu-Rimnicu 80, Rimnicu-Pitesti 97, Fagaras-Bucharest 211, Pitesti-Bucharest 101, Bucharest-Giurgiu 90, Bucharest-Urziceni 85, Urziceni-Hirsova 98, Hirsova-Eforie 86, Urziceni-Vaslui 142, Vaslui-Iasi 92, Iasi-Neamt 87';
  const ROMH='Arad=366, Bucharest=0, Craiova=160, Drobeta=242, Eforie=161, Fagaras=176, Giurgiu=77, Hirsova=151, Iasi=226, Lugoj=244, Mehadia=241, Neamt=234, Oradea=380, Pitesti=100, Rimnicu=193, Sibiu=253, Timisoara=329, Urziceni=80, Vaslui=199, Zerind=374';
  const TPRE=[['Brief example','[[3,5],[6,[9,1]],[2]]'],['Russell & Norvig Fig. 5.2','[[3,12,8],[2,4,6],[14,5,2]]'],['Depth 3, binary','[[[3,5],[6,9]],[[1,2],[0,-1]]]'],['Depth 3, 8 leaves','[[[2,3],[5,9]],[[0,1],[7,5]]]'],['Depth 4, 16 leaves','[[[[10,5],[7,11]],[[12,8],[9,8]]],[[[5,12],[11,12]],[[9,8],[7,10]]]]']];
  const APRE=[['Small graph (h not consistent at D)','S-A 1, S-G 12, A-B 3, A-C 1, B-D 3, C-D 1, C-G 2, D-G 3','S=4, A=3, B=4, C=2, D=6, G=0','S','G',true],['Romania: Arad → Bucharest (Russell & Norvig)',ROM,ROMH,'Arad','Bucharest',false],['Grid-like, ties on f','S-A 2, S-B 2, A-C 2, B-C 2, A-D 3, C-G 3, D-G 1','S=5, A=4, B=4, C=3, D=1, G=0','S','G',false]];
  const st={tab:0,tree:TPRE[0][1],max:'max',strict:'0',view:'ab',g:{e:APRE[0][1],h:APRE[0][2],s:'S',t:'G',dir:true}};
  stage.style.padding='0';
  stage.innerHTML=`<div class="${M} ${P}"><div class="${M}-tabs" role="group" aria-label="Method"></div><div class="${P}-pane"></div></div>`;
  const pane=stage.querySelector(`.${P}-pane`);
  tabs(stage.querySelector(`.${M}-tabs`),['Minimax &amp; alpha–beta','A* search'],0,k=>{st.tab=k;(k?drawA:drawT)();});
  const shell=inner=>`<div class="${M}-in">${inner}</div><div class="${M}-err" role="alert" hidden></div><div class="${M}-ans"></div><div class="${M}-conv"></div>`;
  const inf=v=>v===Infinity?'+∞':v===-Infinity?'−∞':fmt(v);
  function randTree(){const d=rnd(2,3),b=()=>rnd(2,3);const g=k=>k===0?String(rnd(0,20)):'['+Array.from({length:b()},()=>g(k-1)).join(',')+']';return g(d);}

  /* ---------- minimax / alpha-beta ---------- */
  function drawT(){
    pane.innerHTML=shell(`<label class="${M}-lab ${M}-wide">Game tree (nested lists; leaves are utilities)<input type="text" data-k="tree" spellcheck="false" autocomplete="off"></label>
      <div class="${M}-w2"><span class="${M}-lab">Root player</span>${segH(P+'Root',[['max','MAX'],['min','MIN']])}</div>
      <label class="${M}-lab ${M}-w2">Pruning rule<select data-k="strict"><option value="0">Prune when α ≥ β (standard)</option><option value="1">Prune only when α &gt; β (strict)</option></select></label>
      <div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option>${TPRE.map((p,i)=>`<option value="${i}">${E(p[0])}</option>`).join('')}</select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`)+
      `<div class="${P}-vw">${segH(P+'View',[['ab','Alpha–beta trace'],['mm','Minimax values']])}</div><div class="${M}-sth"></div><p class="${M}-cap" aria-live="polite"></p><div class="${P}-tree ${M}-scroll"></div><div class="${P}-log"></div>`;
    const q=x=>pane.querySelector(x),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),sth=q(`.${M}-sth`),cap=q(`.${M}-cap`),treeEl=q(`.${P}-tree`),logEl=q(`.${P}-log`),ti=q('[data-k=tree]');
    ti.value=st.tree;ti.oninput=debounce(()=>{st.tree=ti.value;calc();},300);
    seg(q('#'+P+'Root'),st.max,v=>{st.max=v;calc();});seg(q('#'+P+'View'),st.view,v=>{st.view=v;calc();});
    q('[data-k=strict]').value=st.strict;q('[data-k=strict]').onchange=e=>{st.strict=e.target.value;calc();};
    q('[data-x=pre]').onchange=e=>{const p=TPRE[+e.target.value];if(!p)return;st.tree=p[1];ti.value=st.tree;calc();};
    q('[data-b=rnd]').onclick=()=>{st.tree=randTree();ti.value=st.tree;calc();};
    function calc(){
      const T=GS.parseTree(st.tree);
      if(T.err){setErr(err,T.err);pane.classList.add(`${M}-stale`);return;}setErr(err,null);pane.classList.remove(`${M}-stale`);
      const mx=st.max==='max',mm=GS.minimax(T.root,mx),ab=GS.alphabeta(T,mx,st.strict==='1');
      /* names: internal nodes A, B, C … in preorder */
      const name={};let c=0;T.nodes.forEach(n=>{if(!n.leaf){name[n.id]=c<26?String.fromCharCode(65+c):String.fromCharCode(65+c%26)+Math.floor(c/26);c++;}else name[n.id]=fmt(n.v);});
      const isMax=n=>(n.d%2===0)===mx;
      const bestPath=[T.root.id];let cur=T.root;while(!cur.leaf){const k=cur.kids.find(x=>mm.val[x.id]===mm.val[cur.id]);bestPath.push(k.id);cur=k;}
      ans.innerHTML=card('Minimax value',fmt(mm.value),`root ${mx?'MAX':'MIN'} node A`)+card('Best move',`child ${mm.best+1} (${T.root.kids[mm.best].leaf?'leaf':name[T.root.kids[mm.best].id]})`,'leftmost child with the root value')+card('Leaves pruned',ab.prunedLeaves,`of ${T.leaves}; ${ab.evaluated} evaluated`)+card('Cut-offs',ab.cutoffs,ab.pruned.map(p=>name[p.at]).join(', ')||'none');
      conv.innerHTML=`<p class="${M}-note"><b>Conventions:</b> levels alternate ${mx?'MAX, MIN, MAX …':'MIN, MAX, MIN …'} from the root; ▲ = MAX, ▼ = MIN. Alpha–beta visits children <b>left to right</b>, starts with α = −∞, β = +∞, and ${st.strict==='1'?'prunes only when α > β (strict)':'prunes the remaining children as soon as α ≥ β'}. A MAX node raises α, a MIN node lowers β. Pruning never changes the root value. “≥ v” / “≤ v” marks a node that was cut off, so v is only a bound.</p>`;
      /* layout */
      const leafIdx={};let li=0;const x={},y={};const place=n=>{if(n.leaf){x[n.id]=li++;}else{n.kids.forEach(place);x[n.id]=(x[n.kids[0].id]+x[n.kids[n.kids.length-1].id])/2;}y[n.id]=n.d;};place(T.root);
      const gx=44,gy=72,padL=46,W=padL+li*gx+10,H=(T.depth+1)*gy+10;const X=id=>padL+x[id]*gx+gx/2,Y=id=>26+y[id]*gy;
      const shape=(n,cls)=>{const cx=X(n.id),cy=Y(n.id);if(n.leaf)return `<rect class="${P}-n ${cls}" x="${cx-15}" y="${cy-12}" width="30" height="24" rx="4"/>`;const up=isMax(n);return `<polygon class="${P}-n ${cls}" points="${up?`${cx},${cy-17} ${cx-19},${cy+13} ${cx+19},${cy+13}`:`${cx},${cy+17} ${cx-19},${cy-13} ${cx+19},${cy-13}`}"/>`;};
      const draw=(S,nowId,cutIds)=>{
        let e='',nd='',tx='';
        T.nodes.forEach(n=>{if(n.leaf)return;n.kids.forEach(k=>{const pr=S[k.id].s==='p';const cut=cutIds&&cutIds.includes(k.id);e+=`<line class="${P}-e ${pr?'pr':''} ${st.view==='mm'&&bestPath.includes(k.id)&&bestPath.includes(n.id)?'best':''} ${cut?'cut':''}" x1="${X(n.id)}" y1="${Y(n.id)+(isMax(n)?13:17)}" x2="${X(k.id)}" y2="${Y(k.id)-(k.leaf?12:isMax(k)?17:13)}"/>`;
          if(pr&&S[n.id].s!=='p'){const mx2=(X(n.id)+X(k.id))/2,my2=(Y(n.id)+Y(k.id))/2;e+=`<text class="${P}-cutm" x="${mx2}" y="${my2+4}" text-anchor="middle">✂</text>`;}});});
        T.nodes.forEach(n=>{const s=S[n.id];const cls=(s.s==='u'?'u':s.s==='p'?'pr':s.s==='a'?'act':'done')+(n.id===nowId?' now':'')+(n.leaf?' leaf':'');
          nd+=shape(n,cls);const v=n.leaf?fmt(n.v):s.v==null?'':(s.bound?s.bound:'')+inf(s.v);
          nd+=`<text class="${P}-v ${cls}" x="${X(n.id)}" y="${Y(n.id)+(n.leaf?4.5:isMax(n)?8:0)}" text-anchor="middle">${E(v)}</text>`;
          if(!n.leaf){nd+=`<text class="${P}-nm" x="${X(n.id)+22}" y="${Y(n.id)-8}">${name[n.id]}</text>`;
            if(st.view==='ab'&&s.a!=null&&s.s!=='p')tx+=`<text class="${P}-ab" x="${X(n.id)}" y="${Y(n.id)+30}" text-anchor="middle">α ${inf(s.a)} β ${inf(s.b)}</text>`;}});
        let lv='';for(let d=0;d<=T.depth;d++)lv+=`<text class="${P}-lv" x="4" y="${26+d*gy+4}">${(d%2===0)===mx?'MAX':'MIN'}</text>`;
        treeEl.innerHTML=`<svg class="${M}-svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Game tree">${lv}${e}${nd}${tx}</svg>`;
      };
      if(st.view==='mm'){
        sth.innerHTML='';const S=T.nodes.map(n=>({s:'d',v:mm.val[n.id],a:null,b:null,bound:''}));draw(S,null);
        cap.innerHTML=`Minimax backs values up from the leaves: each ${mx?'MAX':'MIN'} level takes the ${mx?'maximum':'minimum'} of its children and the next level the ${mx?'minimum':'maximum'}. Root value <b>${fmt(mm.value)}</b>; the best line of play is highlighted.`;
        logEl.innerHTML=`<h4 class="${M}-h">Backed-up values</h4>`+table(['Node','Level','Children','Value'],T.nodes.filter(n=>!n.leaf).map(n=>`<tr><td>${name[n.id]}</td><td>${isMax(n)?'MAX':'MIN'}</td><td>${isMax(n)?'max':'min'}(${n.kids.map(k=>fmt(mm.val[k.id])).join(', ')})</td><td><b>${fmt(mm.val[n.id])}</b></td></tr>`));
        return;}
      const evT=ev=>{const n=T.nodes[ev.id],nm=name[ev.id],role=n.leaf?'':isMax(n)?'MAX':'MIN',par=n.parent!=null?name[n.parent]:'';
        if(ev.k==='enter')return `Visit ${role} node <b>${nm}</b> with α = ${inf(ev.a)}, β = ${inf(ev.b)}.`;
        if(ev.k==='leaf')return `Evaluate leaf <b>${fmt(ev.v)}</b> (child of ${par}).`;
        if(ev.k==='upd')return `${nm} (${role}) receives ${inf(ev.cv)}: v = ${inf(ev.v)}, so ${ev.mx?'α':'β'} = <b>${inf(ev.mx?ev.a:ev.b)}</b> (α ${inf(ev.a)}, β ${inf(ev.b)}).`;
        if(ev.k==='cut')return `At ${nm} (${role}): v = ${inf(ev.v)}, now α = ${inf(ev.a)} ${st.strict==='1'?'>':'≥'} β = ${inf(ev.b)}, so the remaining ${ev.rest.length} child${ev.rest.length>1?'ren are':' is'} <b>pruned</b> (${ev.leaves.length} lea${ev.leaves.length===1?'f':'ves'}: ${ev.leaves.map(l=>fmt(T.nodes[l].v)).join(', ')}). ${nm} returns ${inf(ev.v)}.`;
        return `${nm} is finished: it returns <b>${inf(ev.v)}</b>${par?' to '+par:' (root value)'}.`;};
      logEl.innerHTML=`<h4 class="${M}-h">Trace</h4><ol class="${P}-trace">${ab.events.map((ev,k)=>`<li data-k="${k}" class="${ev.k==='cut'?'cut':''}">${evT(ev)}</li>`).join('')}</ol>`+(ab.pruned.length?`<p class="${M}-note"><b>Pruned:</b> ${ab.pruned.map(p=>`below ${name[p.at]}: ${p.leaves.map(l=>fmt(T.nodes[l].v)).join(', ')}`).join('; ')} → <b>${ab.prunedLeaves}</b> lea${ab.prunedLeaves===1?'f':'ves'} never evaluated.</p>`:`<p class="${M}-note">No branch can be pruned with this ordering.</p>`);
      const items=[...logEl.querySelectorAll('li')];
      stepper(sth,ab.events.length,i=>{const ev=ab.events[i];draw(ev.S,ev.id,ev.k==='cut'?ev.rest:null);cap.innerHTML=`${i+1}. ${evT(ev)}`;items.forEach((li2,k)=>{li2.classList.toggle('on',k===i);li2.classList.toggle('fut',k>i);});const ol=items[i]&&items[i].parentNode;if(ol)ol.scrollTop=Math.max(0,items[i].offsetTop-ol.clientHeight/2);});
    }
    calc();
  }

  /* ---------- A* ---------- */
  function drawA(){
    const g=st.g;
    pane.innerHTML=shell(`<label class="${M}-lab ${M}-wide">Edges (from-to cost)<textarea data-k="e" rows="2" spellcheck="false"></textarea></label>
      <label class="${M}-lab ${M}-wide">Heuristic h(n)<textarea data-k="h" rows="1" spellcheck="false"></textarea></label>
      ${inp('s','Start',g.s)}${inp('t','Goal',g.t)}<label class="${M}-chk"><input type="checkbox" data-k="dir"> Directed edges</label>
      <div class="${M}-btns"><label class="${M}-lab">Example<select data-x="pre"><option value="">Choose…</option>${APRE.map((p,i)=>`<option value="${i}">${E(p[0])}</option>`).join('')}</select></label><button type="button" class="btn sm" data-b="rnd">🎲 Random example</button></div>`)+
      `<div class="${M}-sth"></div><p class="${M}-cap" aria-live="polite"></p><div class="${P}-graph"></div><div class="${P}-at"></div>`;
    const q=x=>pane.querySelector(x),err=q(`.${M}-err`),ans=q(`.${M}-ans`),conv=q(`.${M}-conv`),sth=q(`.${M}-sth`),cap=q(`.${M}-cap`),gEl=q(`.${P}-graph`),tEl=q(`.${P}-at`);
    q('[data-k=e]').value=g.e;q('[data-k=h]').value=g.h;q('[data-k=dir]').checked=g.dir;
    ['e','h','s','t'].forEach(k=>q(`[data-k=${k}]`).oninput=debounce(ev=>{g[k]=ev.target.value.trim();calc();},300));
    q('[data-k=dir]').onchange=ev=>{g.dir=ev.target.checked;calc();};
    q('[data-x=pre]').onchange=ev=>{const p=APRE[+ev.target.value];if(!p)return;Object.assign(g,{e:p[1],h:p[2],s:p[3],t:p[4],dir:p[5]});drawA();};
    q('[data-b=rnd]').onclick=()=>{/* random layered graph with admissible h = true distance minus a little */
      const L=[['S'],['A','B'],['C','D','E'],['F','H'],['G']];const ed=[];L.forEach((l,i)=>{if(i===L.length-1)return;l.forEach(u=>{const nx=L[i+1];const k=rnd(1,Math.min(2,nx.length));const cs=[...nx].sort(()=>Math.random()-.5).slice(0,k);cs.forEach(v=>ed.push([u,v,rnd(1,9)]));});});
      L[L.length-2].forEach(u=>{if(!ed.some(e=>e[0]===u))ed.push([u,'G',rnd(1,9)]);});L.slice(1).forEach((l,i)=>l.forEach(v=>{if(!ed.some(e=>e[1]===v))ed.push([pick(L[i]),v,rnd(1,9)]);}));
      const G=GS.parseGraph(ed.map(e=>`${e[0]}-${e[1]} ${e[2]}`).join(', '),L.flat().map(n=>n+'=0').join(', '),true);const hs=GS.astar(G,'S','G').hstar;
      Object.assign(g,{e:ed.map(e=>`${e[0]}-${e[1]} ${e[2]}`).join(', '),h:L.flat().map(n=>`${n}=${hs[n]===Infinity?rnd(3,9):Math.max(0,hs[n]-rnd(0,2))}`).join(', '),s:'S',t:'G',dir:true});drawA();};
    function calc(){
      const G=GS.parseGraph(g.e,g.h,g.dir);const r=G.err?G:GS.astar(G,g.s,g.t);
      if(r.err){setErr(err,r.err);pane.classList.add(`${M}-stale`);return;}setErr(err,null);pane.classList.remove(`${M}-stale`);
      ans.innerHTML=card('Path',r.found?r.path.join(' → '):'none','goal not reachable'.slice(0,r.found?0:99))+card('Cost',r.found?fmt(r.cost):'—',r.found&&r.optimal<r.cost-1e-9?`not optimal: the cheapest is ${fmt(r.optimal)}`:r.found?'optimal':'')+card('Nodes expanded',r.expanded,'including the goal')+card('Heuristic',r.inadm.length?'Not admissible':'Admissible',r.inadm.length?`h &gt; h* at ${r.inadm.join(', ')}`:'h(n) ≤ h*(n) everywhere',r.inadm.length?M+'-badc':M+'-okc')+card('Consistent?',r.incons.length?'No':'Yes',r.incons.length?r.incons.slice(0,3).map(([u,v,c])=>`h(${u}) &gt; ${fmt(c)} + h(${v})`).join('; '):'h(u) ≤ c(u,v) + h(v) on every edge',r.incons.length?M+'-badc':M+'-okc');
      conv.innerHTML=`<p class="${M}-note"><b>A* (graph search):</b> f(n) = g(n) + h(n). Always expand the OPEN node with the smallest f; <b>ties</b> go to the smaller h, then alphabetical order. The goal test is done when a node is taken off OPEN, not when it is generated. A cheaper path to a node on OPEN updates it; a cheaper path to a node on CLOSED reopens it. With an admissible h the first goal expanded is optimal.</p>`;
      const it=r.iters;
      const nodes=G.nodes;const und={};nodes.forEach(n=>und[n]=[]);G.E.forEach(e=>{und[e.u].push(e.v);und[e.v].push(e.u);});
      const lay={};nodes.forEach(n=>lay[n]=-1);lay[g.s]=0;const Q=[g.s];while(Q.length){const u=Q.shift();for(const v of und[u])if(lay[v]<0){lay[v]=lay[u]+1;Q.push(v);}}const mxL=Math.max(...Object.values(lay));nodes.forEach(n=>{if(lay[n]<0)lay[n]=mxL+1;});
      const nw=Math.max(58,Math.max(...nodes.map(n=>n.length))*8+18);
      const opS=o=>o.map(x=>`${E(x.n)}(${fmt(x.g)}+${fmt(x.h)}=${fmt(x.f)})`).join(', ')||'∅';
      tEl.innerHTML=`<h4 class="${M}-h">OPEN / CLOSED trace</h4>`+table(['Step','Expand n (g + h = f)','Successors','OPEN after (sorted by f)','CLOSED'],it.map((x,k)=>`<tr data-k="${k}"><td>${k}</td><td>${x.k==='init'?'—':`<b>${E(x.n)}</b> (${fmt(x.g)} + ${fmt(G.h[x.n])} = ${fmt(x.f)})${x.k==='goal'?' <b>goal ✓</b>':''}`}</td><td>${x.k==='exp'?x.gen.map(y=>`<span class="${P}-${y.cls}">${E(y.n)}: g ${fmt(y.g)}, f ${fmt(y.f)} (${E(y.note)})</span>`).join('<br>')||'none':x.k==='init'?`start: ${E(g.s)}`:'stop'}</td><td>${opS(x.open)}</td><td>${x.closed.map(E).join(', ')||'∅'}</td></tr>`),P+'-tt');
      const rowsT=[...tEl.querySelectorAll('tbody tr')];
      stepper(sth,it.length,i=>{const x=it[i],op=new Set(x.open.map(o=>o.n)),cl=new Set(x.closed);const fin=i===it.length-1&&r.found;const pathE=new Set();const pth=fin?r.path:(x.path||[]);for(let k=1;k<pth.length;k++)pathE.add(pth[k-1]+'>'+pth[k]);
        const gv={};x.open.forEach(o=>gv[o.n]=o);
        gEl.innerHTML=`<div class="${M}-scroll">${graphSvg(nodes.map(n=>({id:n,lines:[n,gv[n]?`f ${fmt(gv[n].f)}`:`h ${fmt(G.h[n])}`],cls:(n===x.n?'cur ':'')+(fin&&r.path.includes(n)?'path ':'')+(op.has(n)?'op':cl.has(n)?'cl':'')})),G.E.map(e=>({u:e.u,v:e.v,label:fmt(e.c),cls:pathE.has(e.u+'>'+e.v)||(!g.dir&&pathE.has(e.v+'>'+e.u))?(fin?'path':'cur'):''})),lay,{nw,nh:36,gapL:nw+58,gapA:52,arrows:g.dir,label:'Search graph'})}</div><p class="${M}-legend"><span class="${P}-ko"></span> OPEN <span class="${P}-kl"></span> CLOSED <span class="${P}-kn"></span> being expanded${r.found?` <span class="${P}-kp"></span> path`:''}</p>`;
        rowsT.forEach((tr,k)=>{tr.classList.toggle(`${M}-cur`,k===i);tr.classList.toggle(`${M}-fut`,k>i);});
        cap.innerHTML=x.k==='init'?`Put the start node ${E(g.s)} on OPEN with g = 0, f = h = ${fmt(G.h[g.s])}.`:x.k==='goal'?`${E(x.n)} has the smallest f = ${fmt(x.f)} and is the goal: stop. Path <b>${r.path.join(' → ')}</b>, cost <b>${fmt(r.cost)}</b>.`:`Expand <b>${E(x.n)}</b> (smallest f = ${fmt(x.g)} + ${fmt(G.h[x.n])} = ${fmt(x.f)}); ${x.gen.length?x.gen.map(y=>`${E(y.n)} ${y.cls==='new'?'added':y.cls==='upd'?'updated':y.cls==='reopen'?'reopened':'ignored'} (f ${fmt(y.f)})`).join(', '):'no successors'}.`+(i===it.length-1&&!r.found?' OPEN is empty: the goal is unreachable.':'');});
    }
    calc();
  }
  drawT();
 }});

})();

/* ================= UGC NET solvers: Operating systems (cpusched, pagerepl, banker, disksched) =================
   Pure algorithms live on window.NETSOLVE.<id> so they can be tested in Node (global.window = {}).
   UI registers ANIM playgrounds. */
const NETSOLVE = NS_ROOT.NETSOLVE;
(function(){
'use strict';
const fx=x=>{if(x==null||x===''||!isFinite(x))return String(x==null?'':x);const r=Math.round(x*1000)/1000;return String(r);};
const f2=x=>(Math.round(x*100)/100).toFixed(2);
const gcd=(a,b)=>{a=Math.abs(a);b=Math.abs(b);while(b){[a,b]=[b,a%b];}return a;};
/* "43/5 = 8.60" for integer sums, plain decimal otherwise */
const frac=(sum,n)=>{if(!n)return '0';const s=Math.round(sum*1000)/1000;if(Number.isInteger(s)){const g=gcd(s,n)||1;const a=s/g,b=n/g;return b===1?String(a):`${s}/${n}${g>1?` = ${a}/${b}`:''} = ${f2(s/n)}`;}return `${fx(s)}/${n} = ${f2(s/n)}`;};

/* ======================= CPU scheduling ======================= */
NETSOLVE.cpusched=(function(){
  const NAMES={fcfs:'FCFS',sjf:'SJF (non-preemptive)',srtf:'SRTF (preemptive SJF)','prio-np':'Priority (non-preemptive)','prio-p':'Priority (preemptive)',rr:'Round robin'};
  /* procs: [{id,at,bt,pr}] ; algo in NAMES ; o: {q, cs, csAll, lowIsHigh(default true), rrNewFirst(default true)} */
  function schedule(procs,algo,o){
    o=o||{};const cs=+o.cs||0,csAll=!!o.csAll,q=+o.q||1,low=o.lowIsHigh!==false,newFirst=o.rrNewFirst!==false;
    const P=procs.map((p,i)=>({id:String(p.id),at:+p.at,bt:+p.bt,pr:+(p.pr||0),i,rem:+p.bt,st:null,ct:null}));
    const n=P.length,G=[],log=[];let t=0,prev=null,afterIdle=false,done=0,guard=0;
    const push=(p,s,e)=>{if(e<=s+1e-9)return;const l=G[G.length-1];if(l&&l.p===p&&Math.abs(l.e-s)<1e-9)l.e=e;else G.push({p,s,e});};
    const pk=p=>algo==='fcfs'||algo==='rr'?[p.at,p.i]:(algo==='sjf'||algo==='srtf')?[p.rem,p.at,p.i]:[low?p.pr:-p.pr,p.at,p.i];
    const cmp=(a,b)=>{const x=pk(a),y=pk(b);for(let k=0;k<x.length;k++)if(x[k]!==y[k])return x[k]-y[k];return 0;};
    const needCS=p=>cs>0&&p!==prev&&(csAll||(prev!==null&&!afterIdle));
    const desc=p=>algo==='fcfs'?`${p.id}(at ${fx(p.at)})`:(algo==='sjf'||algo==='srtf')?`${p.id}(${algo==='srtf'?'rem':'bt'} ${fx(p.rem)})`:`${p.id}(pr ${fx(p.pr)})`;
    const why={fcfs:'earliest arrival',sjf:'shortest burst',srtf:'shortest remaining time','prio-np':'highest priority','prio-p':'highest priority'};
    if(!n)return {gantt:[],rows:[],log:[],end:0};
    if(algo!=='rr'){
      const pre=algo==='srtf'||algo==='prio-p';
      while(done<n&&guard++<100000){
        const ready=P.filter(p=>p.ct===null&&p.at<=t+1e-9);
        if(!ready.length){const na=Math.min(...P.filter(p=>p.ct===null).map(p=>p.at));push(null,t,na);log.push({s:t,e:na,pick:null,text:`t=${fx(t)}: nothing has arrived, so the CPU is <b>idle</b> until t=${fx(na)}.`});t=na;afterIdle=true;continue;}
        ready.sort(cmp);const p=ready[0];const s0=t;
        let text=`t=${fx(t)}: ready {${ready.map(desc).join(', ')}} → <b>${p.id}</b>`+(ready.length>1?` (${why[algo]}${ready.length>1&&cmp(ready[0],ready[1])===0?'':''}${ready.length>1&&pk(ready[0])[0]===pk(ready[1])[0]?'; tie broken by arrival, then id':''})`:' (only ready process)');
        if(prev&&prev!==p&&prev.ct===null&&pre)text+=`, pre-empting ${prev.id}`;
        if(prev===p&&pre&&s0>p.st)text=`t=${fx(t)}: ready {${ready.map(desc).join(', ')}} → <b>${p.id}</b> keeps the CPU (no pre-emption)`;
        if(needCS(p)){push('CS',t,t+cs);t+=cs;text+=`; context switch ${fx(t-cs)}–${fx(t)}`;}
        if(p.st===null)p.st=t;
        let end=t+p.rem;
        if(pre){const na=P.filter(x=>x.ct===null&&x.at>t+1e-9).map(x=>x.at);if(na.length)end=Math.min(end,Math.min(...na));}
        push(p.id,t,end);p.rem=Math.round((p.rem-(end-t))*1e6)/1e6;t=end;
        if(p.rem<=1e-9){p.rem=0;p.ct=t;done++;text+=`; runs to t=${fx(t)} and <b>completes</b>.`;}else text+=`; runs to t=${fx(t)} (new arrival: re-check).`;
        log.push({s:s0,e:t,pick:p.id,text});prev=p;afterIdle=false;
      }
    }else{
      const order=[...P].sort((a,b)=>a.at-b.at||a.i-b.i);let k=0;const Q=[];
      const admit=(upto,strict)=>{const got=[];while(k<n&&(strict?order[k].at<upto-1e-9:order[k].at<=upto+1e-9)){Q.push(order[k]);got.push(order[k].id);k++;}return got;};
      admit(0);
      while(done<n&&guard++<100000){
        if(!Q.length){const na=order[k].at;push(null,t,na);log.push({s:t,e:na,pick:null,text:`t=${fx(t)}: ready queue empty, CPU <b>idle</b> until t=${fx(na)}.`});t=na;afterIdle=true;admit(t);continue;}
        const s0=t;const qBefore=Q.map(x=>x.id);const p=Q.shift();let text=`t=${fx(t)}: queue [${qBefore.join(', ')}] → <b>${p.id}</b> from the front`;
        if(needCS(p)){push('CS',t,t+cs);t+=cs;const g=admit(t);text+=`; context switch ${fx(t-cs)}–${fx(t)}`+(g.length?` (${g.join(', ')} arrive)`:'');}
        if(p.st===null)p.st=t;
        const run=Math.min(q,p.rem);push(p.id,t,t+run);t+=run;p.rem=Math.round((p.rem-run)*1e6)/1e6;
        let arr;
        if(p.rem>1e-9){if(newFirst){arr=admit(t);Q.push(p);}else{arr=admit(t,true);Q.push(p);arr=arr.concat(admit(t));}}
        else{arr=admit(t);p.rem=0;p.ct=t;done++;}
        text+=`; runs ${fx(run)} to t=${fx(t)}`+(arr.length?`; ${arr.join(', ')} join${arr.length>1?'':'s'} the queue`:'')+(p.ct!==null?`; <b>completes</b>.`:`; quantum expires, ${p.id} goes to the back. Queue: [${Q.map(x=>x.id).join(', ')}].`);
        log.push({s:s0,e:t,pick:p.id,text});prev=p;afterIdle=false;
      }
    }
    const rows=P.map(p=>({id:p.id,at:p.at,bt:p.bt,pr:p.pr,st:p.st,ct:p.ct,tat:+(p.ct-p.at).toFixed(6),wt:+(p.ct-p.at-p.bt).toFixed(6),rt:+(p.st-p.at).toFixed(6)}));
    const sum=k=>rows.reduce((a,r)=>a+r[k],0),first=Math.min(...P.map(p=>p.at));
    const busy=sum('bt'),span=t-first;
    return {gantt:G,rows,log,end:t,first,busy,span,util:span?busy/span:1,
      sums:{tat:sum('tat'),wt:sum('wt'),rt:sum('rt'),ct:sum('ct')},
      avg:{tat:sum('tat')/n,wt:sum('wt')/n,rt:sum('rt')/n,ct:sum('ct')/n}};
  }
  function validate(procs,algo,o){
    if(!procs.length)return 'Add at least one process.';
    for(const p of procs){
      for(const [k,lab] of [['at','Arrival'],['bt','Burst']]){const v=p[k];if(v===''||v==null||!isFinite(+v))return `${p.id}: ${lab} time must be a number.`;}
      if(+p.at<0)return `${p.id}: arrival time cannot be negative.`;
      if(+p.bt<=0)return `${p.id}: burst time must be greater than 0.`;
      if((algo==='prio-np'||algo==='prio-p')&&(p.pr===''||p.pr==null||!isFinite(+p.pr)))return `${p.id}: enter a priority number.`;
    }
    if(procs.length>20)return 'Use at most 20 processes.';
    if(algo==='rr'&&!(+o.q>0))return 'The time quantum must be greater than 0.';
    if(!(+o.cs>=0))return 'Context-switch time must be 0 or more.';
    const tot=procs.reduce((a,p)=>a+ +p.bt,0)+Math.max(...procs.map(p=>+p.at));if(tot>2000)return 'Times are too large to draw (keep the total under 2000).';
    if(algo==='rr'&&tot/(+o.q)>1500)return 'The quantum is too small for these bursts.';
    return '';
  }
  return {schedule,validate,NAMES};
})();

/* ======================= Page replacement ======================= */
NETSOLVE.pagerepl=(function(){
  const NAMES={fifo:'FIFO',lru:'LRU',opt:'Optimal (OPT)',lfu:'LFU',mru:'MRU'};
  /* refs: array of page labels (strings or numbers); nf frames. Frames keep their slot: the victim's slot gets the new page. */
  function simulate(refs,nf,algo){
    const fr=new Array(nf).fill(null),load=new Array(nf).fill(-1),last=new Array(nf).fill(-1),cnt=new Array(nf).fill(0);
    const steps=[];let faults=0,hits=0;
    refs.forEach((r,i)=>{
      const slot=fr.findIndex(x=>x!==null&&String(x)===String(r));
      let st={ref:r,hit:false,victim:null,slot:-1,why:''};
      if(slot>=0){hits++;st.hit=true;st.slot=slot;last[slot]=i;cnt[slot]++;st.why=`${r} is already in frame ${slot+1}: <b>hit</b>.`;}
      else{
        faults++;let v=fr.indexOf(null);
        if(v>=0){st.why=`${r} is not in memory: <b>fault</b>. A free frame (${v+1}) is available, so no page is replaced (compulsory fault).`;}
        else{
          const idx=[...Array(nf).keys()];const byLoad=(a,b)=>load[a]-load[b];
          if(algo==='fifo'){v=idx.sort(byLoad)[0];st.why=`<b>fault</b>. FIFO replaces the page loaded earliest: ${fr[v]}.`;}
          else if(algo==='lru'){v=idx.sort((a,b)=>last[a]-last[b])[0];st.why=`<b>fault</b>. LRU replaces the page used least recently: ${fr[v]} (last used at reference ${last[v]+1}).`;}
          else if(algo==='mru'){v=idx.sort((a,b)=>last[b]-last[a])[0];st.why=`<b>fault</b>. MRU replaces the page used most recently: ${fr[v]}.`;}
          else if(algo==='lfu'){v=idx.sort((a,b)=>cnt[a]-cnt[b]||byLoad(a,b))[0];const tie=idx.filter(k=>cnt[k]===cnt[v]).length>1;st.why=`<b>fault</b>. LFU replaces the least frequently used page: ${fr[v]} (count ${cnt[v]})${tie?'; tie broken FIFO (loaded earliest)':''}.`;}
          else{const nxt=k=>{for(let j=i+1;j<refs.length;j++)if(String(refs[j])===String(fr[k]))return j;return Infinity;};
            v=idx.sort((a,b)=>(nxt(b)-nxt(a))||byLoad(a,b))[0];const nv=nxt(v);
            st.why=`<b>fault</b>. OPT replaces the page used farthest in the future: ${fr[v]} (${nv===Infinity?'never used again':'next used at reference '+(nv+1)})${idx.filter(k=>nxt(k)===nv).length>1?'; tie broken FIFO (loaded earliest)':''}.`;}
          st.victim=fr[v];
        }
        fr[v]=r;load[v]=i;last[v]=i;cnt[v]=1;st.slot=v;
      }
      st.frames=fr.slice();
      /* the algorithm's own bookkeeping, for display */
      const occ=[...Array(nf).keys()].filter(k=>fr[k]!==null);
      if(algo==='fifo')st.state='queue: '+occ.sort((a,b)=>load[a]-load[b]).map(k=>fr[k]).join(' ');
      else if(algo==='lru'||algo==='mru')st.state='old→new: '+occ.sort((a,b)=>last[a]-last[b]).map(k=>fr[k]).join(' ');
      else if(algo==='lfu')st.state=occ.map(k=>fr[k]+':'+cnt[k]).join(' ');
      else st.state='';
      steps.push(st);
    });
    return {steps,faults,hits,n:refs.length,ratio:refs.length?hits/refs.length:0};
  }
  function belady(refs,algo,maxF){
    const out=[];for(let f=1;f<=maxF;f++)out.push({frames:f,faults:simulate(refs,f,algo).faults});
    const anom=[];for(let k=1;k<out.length;k++)if(out[k].faults>out[k-1].faults)anom.push([out[k-1],out[k]]);
    return {table:out,anomalies:anom};
  }
  function parse(s){return String(s||'').trim().split(/[\s,]+/).filter(Boolean);}
  return {simulate,belady,parse,NAMES};
})();

/* ======================= Banker's algorithm ======================= */
NETSOLVE.banker=(function(){
  const le=(a,b)=>a.every((x,i)=>x<=b[i]);
  const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]);
  function need(alloc,max){return max.map((r,i)=>sub(r,alloc[i]));}
  /* mode 'cyclic' (Galvin: keep scanning from the next process, wrap around) or 'restart' (after each allocation, scan again from P0) */
  function safety(alloc,max,avail,mode){
    const n=alloc.length,N=need(alloc,max);let work=avail.slice();const fin=new Array(n).fill(false),seq=[],trace=[];
    let i=0,since=0,guard=0;
    while(seq.length<n&&since<n&&guard++<10000){
      if(!fin[i]){
        const ok=le(N[i],work);const before=work.slice();
        if(ok){work=add(work,alloc[i]);fin[i]=true;seq.push(i);since=0;}else since++;
        trace.push({p:i,need:N[i],work:before,ok,after:work.slice()});
        if(ok&&mode==='restart'){i=0;continue;}
      }
      i=(i+1)%n;
    }
    return {safe:seq.length===n,seq,trace,need:N,finish:fin,work};
  }
  /* request by process p: returns {ok, stage:'need'|'avail'|'unsafe'|'granted', ...} */
  function request(alloc,max,avail,p,req,mode){
    const N=need(alloc,max);
    if(!le(req,N[p]))return {ok:false,stage:'need',need:N[p]};
    if(!le(req,avail))return {ok:false,stage:'avail',need:N[p]};
    const a2=alloc.map((r,i)=>i===p?add(r,req):r.slice()),av2=sub(avail,req);
    const s=safety(a2,max,av2,mode);
    return {ok:s.safe,stage:s.safe?'granted':'unsafe',need:N[p],alloc:a2,avail:av2,safety:s};
  }
  function validate(alloc,max,avail){
    const bad=v=>!Number.isInteger(v)||v<0;
    for(let i=0;i<alloc.length;i++)for(let j=0;j<alloc[i].length;j++){
      if(bad(alloc[i][j])||bad(max[i][j]))return `P${i}: every Allocation and Max value must be a whole number ≥ 0.`;
      if(alloc[i][j]>max[i][j])return `P${i}: Allocation (${alloc[i][j]}) is more than Max (${max[i][j]}) for resource ${String.fromCharCode(65+j)}. A process can never hold more than its maximum claim.`;}
    for(let j=0;j<avail.length;j++)if(bad(avail[j]))return `Available ${String.fromCharCode(65+j)} must be a whole number ≥ 0.`;
    return '';
  }
  return {need,safety,request,validate};
})();

/* ======================= Disk scheduling ======================= */
NETSOLVE.disksched=(function(){
  const NAMES={fcfs:'FCFS',sstf:'SSTF',scan:'SCAN (elevator)',cscan:'C-SCAN',look:'LOOK',clook:'C-LOOK'};
  /* reqs: cylinders; head; dir 'up' (towards higher numbers) | 'down'; size = number of cylinders (0..size-1); countJump: include C-SCAN/C-LOOK return jump in the total */
  function schedule(reqs,head,dir,size,algo,countJump){
    const R=reqs.map(Number),maxC=size-1;const path=[{pos:head,type:'start'}];let pos=head;
    const go=(to,type)=>{path.push({pos:to,type:type||'serve'});pos=to;};
    const up=dir!=='down';
    if(algo==='fcfs')R.forEach(r=>go(r));
    else if(algo==='sstf'){
      const left=R.slice();let d=up;
      while(left.length){let bi=0;for(let k=1;k<left.length;k++){const a=Math.abs(left[k]-pos),b=Math.abs(left[bi]-pos);
          if(a<b||(a===b&&((d&&left[k]>pos)||(!d&&left[k]<pos))))bi=k;}
        const r=left.splice(bi,1)[0];if(r!==pos)d=r>pos;go(r);}
    }else{
      const at=R.filter(r=>r===head);const hi=R.filter(r=>r>head).sort((a,b)=>a-b),lo=R.filter(r=>r<head).sort((a,b)=>b-a);
      at.forEach(r=>go(r));
      const first=up?hi:lo,second=up?lo:hi,end=up?maxC:0,other=up?0:maxC;
      if(algo==='scan'||algo==='look'){
        first.forEach(r=>go(r));
        if(second.length){if(algo==='scan'&&pos!==end)go(end,'end');second.forEach(r=>go(r));}
      }else{ /* cscan / clook: second group served in the same direction after the jump */
        first.forEach(r=>go(r));
        if(second.length){const sec=second.slice().reverse();
          if(algo==='cscan'){if(pos!==end)go(end,'end');go(other,'jump');}
          else go(sec[0],'jump');
          sec.forEach((r,k)=>{if(!(algo==='clook'&&k===0))go(r);});}
      }
    }
    let total=0;const moves=[];
    for(let k=1;k<path.length;k++){const d=Math.abs(path[k].pos-path[k-1].pos);const jump=path[k].type==='jump';const counted=!jump||countJump;if(counted)total+=d;moves.push({from:path[k-1].pos,to:path[k].pos,d,type:path[k].type,counted});}
    const order=path.filter(p=>p.type==='serve'||(p.type==='jump'&&algo==='clook')).map(p=>p.pos);
    return {path,moves,total,order,avg:R.length?total/R.length:0};
  }
  function validate(reqs,head,size){
    if(!(Number.isInteger(size)&&size>=2&&size<=100000))return 'Disk size must be a whole number of cylinders (at least 2).';
    if(!Number.isInteger(head)||head<0||head>=size)return `Head position must be a whole number from 0 to ${size-1}.`;
    if(!reqs.length)return 'Enter at least one request.';
    if(reqs.length>60)return 'Use at most 60 requests.';
    for(const r of reqs){const v=Number(r);if(!Number.isInteger(v))return `“${r}” is not a whole cylinder number.`;if(v<0||v>=size)return `Request ${v} is outside the disk (0 to ${size-1}).`;}
    return '';
  }
  return {schedule,validate,NAMES};
})();

if(typeof ANIM==='undefined')return;
const esc=ANIM.esc;

/* ---------- shared UI helpers ---------- */
/* stepper bar: calls render(k) with k in 1..n; k=n shows everything */
function stepBar(el,getN,render){
  let k=0,timer=null;
  el.innerHTML=`<div class="netos-step"><span class="netos-sl">Step through</span><button class="btn sm" data-a="first" aria-label="First step">⏮</button><button class="btn sm" data-a="prev" aria-label="Previous step">◀</button><button class="btn sm primary" data-a="play">▶ Play</button><button class="btn sm" data-a="next" aria-label="Next step">▶|</button><button class="btn sm" data-a="all">Show all</button><span class="netos-cnt" aria-live="polite"></span></div>`;
  const cnt=el.querySelector('.netos-cnt'),pl=el.querySelector('[data-a=play]');
  const stop=()=>{clearTimeout(timer);timer=null;pl.textContent='▶ Play';};
  const set=v=>{const n=getN();k=Math.max(1,Math.min(n,v));cnt.textContent=k>=n?`All ${n} steps`:`Step ${k} of ${n}`;render(k);};
  const tick=()=>{if(!document.body.contains(el)){stop();return;}if(k>=getN()){stop();return;}set(k+1);timer=setTimeout(tick,1100);};
  el.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const a=b.dataset.a;
    if(a==='play'){if(timer){stop();return;}if(k>=getN())set(1);pl.textContent='❚❚ Pause';timer=setTimeout(tick,900);return;}
    stop();if(a==='first')set(1);if(a==='prev')set(k-1);if(a==='next')set(k+1);if(a==='all')set(getN());});
  return {reset(){stop();set(getN());},stop};
}
const chip=(label,val,main)=>`<div class="netos-chip${main?' main':''}"><span>${label}</span><b>${val}</b></div>`;
const rnd=(a,b)=>a+Math.floor(Math.random()*(b-a+1));
const PAL=['#AFC8F0','#A8D5BA','#F3C98B','#E8B4B8','#C9B8E8','#9ED8DB','#E6D39A','#F0B8D8','#B8D8A0','#D6C3AE'];

/* ======================= cpusched UI ======================= */
ANIM.register('cpusched',{title:'CPU scheduling solver',steps:false,
 caption:'Enter your own processes. The solver draws the Gantt chart and works out CT, TAT, WT and RT for each process, with the averages.',
 build(stage){
  const S=NETSOLVE.cpusched;
  const DEF=[['0','5','3'],['1','3','1'],['2','8','4'],['3','6','2']];
  let rows=DEF.map(r=>r.slice());
  stage.classList.add('netos-stage');
  stage.innerHTML=`<div class="netos cpusched">
   <div class="netos-in">
    <div class="netos-ctl">
     <label>Algorithm<select data-k="algo">${Object.entries(S.NAMES).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label>
     <label data-show="rr">Time quantum<input type="number" data-k="q" value="2" min="0.5" step="0.5"></label>
     <label data-show="prio">Priority rule<select data-k="low"><option value="1">Lower number = higher priority</option><option value="0">Higher number = higher priority</option></select></label>
     <label>Context switch time<input type="number" data-k="cs" value="0" min="0" step="0.5"></label>
     <label data-show="rr">RR: at a quantum expiry<select data-k="rro"><option value="1">New arrival queued first (standard)</option><option value="0">Pre-empted process queued first</option></select></label>
     <label class="chk" data-show="cs"><input type="checkbox" data-k="csAll"> Also charge a switch at the first dispatch and after idle time</label>
    </div>
    <div class="netos-scroll"><table class="netos-tbl netos-edit"><thead><tr><th>Process</th><th>Arrival</th><th>Burst</th><th data-col="pr">Priority</th><th></th></tr></thead><tbody></tbody></table></div>
    <div class="netos-btns"><button class="btn sm" data-b="add">+ Add process</button><button class="btn sm" data-b="rand">Random example</button><button class="btn sm" data-b="def">Default example</button></div>
    <p class="netos-err" role="alert" hidden></p>
   </div>
   <div class="netos-out">
    <div class="netos-chips"></div>
    <div class="netos-h">Gantt chart</div>
    <div class="netos-scroll cpusched-gw"><div class="cpusched-g"></div></div>
    <div class="netos-sb"></div>
    <p class="netos-note" aria-live="polite"></p>
    <div class="netos-h">Per-process table</div>
    <div class="netos-scroll"><table class="netos-tbl cpusched-res"></table></div>
    <div class="netos-work"></div>
    <details class="netos-conv"><summary>Conventions used</summary><ul class="cpusched-conv"></ul></details>
   </div></div>`;
  const $=s=>stage.querySelector(s),tb=$('tbody'),err=$('.netos-err'),out=$('.netos-out');
  const ctl=k=>stage.querySelector(`[data-k="${k}"]`);
  let R=null;
  function drawInputs(){
    tb.innerHTML=rows.map((r,i)=>`<tr><th>P${i+1}</th>${r.map((v,j)=>`<td${j===2?' data-col="pr"':''}><input inputmode="decimal" aria-label="P${i+1} ${['arrival','burst','priority'][j]}" data-r="${i}" data-c="${j}" value="${esc(v)}"></td>`).join('')}<td><button class="netos-x" data-del="${i}" aria-label="Remove P${i+1}" ${rows.length<2?'disabled':''}>×</button></td></tr>`).join('');
  }
  function opts(){return {algo:ctl('algo').value,q:+ctl('q').value,cs:+ctl('cs').value||0,csAll:ctl('csAll').checked,lowIsHigh:ctl('low').value==='1',rrNewFirst:ctl('rro').value==='1'};}
  function vis(){const a=ctl('algo').value,pr=a.startsWith('prio');
    stage.querySelectorAll('[data-show]').forEach(el=>{const s=el.dataset.show;el.hidden=s==='rr'?a!=='rr':s==='prio'?!pr:s==='cs'?!(+ctl('cs').value>0):false;});
    stage.querySelectorAll('[data-col="pr"]').forEach(el=>el.classList.toggle('netos-dim',!pr));}
  const color=id=>{const i=+String(id).replace(/\D/g,'')-1;return PAL[((i%PAL.length)+PAL.length)%PAL.length];};
  function gantt(T){
    const g=R.gantt,tot=R.end,unit=Math.max(10,Math.min(46,620/Math.max(tot,1)));
    let html='';
    g.forEach((s,idx)=>{
      const parts=T>=s.e?[[s.s,s.e,true]]:T<=s.s?[[s.s,s.e,false]]:[[s.s,T,true],[T,s.e,false]];
      parts.forEach(([a,b,on])=>{const d=b-a;const cls=s.p===null?'idle':s.p==='CS'?'cs':'';
        html+=`<div class="cpusched-b ${cls} ${on?'':'fut'}" style="flex:${d} 0 ${Math.max(26,d*unit)}px;${on&&cls===''?`background:${color(s.p)}`:''}" title="${esc((s.p===null?'Idle':s.p==='CS'?'Context switch':s.p)+' '+fx(a)+'–'+fx(b))}">${on?`<span>${s.p===null?'idle':s.p==='CS'?'CS':esc(s.p)}</span>`:''}${idx===0&&a===s.s&&on?`<i class="l">${fx(a)}</i>`:''}${on?`<i>${fx(b)}</i>`:''}</div>`;});
    });
    $('.cpusched-g').innerHTML=html;
  }
  function table(T){
    const pr=ctl('algo').value.startsWith('prio');
    const done=r=>r.ct<=T+1e-9;
    $('.cpusched-res').innerHTML=`<thead><tr><th>Process</th><th>AT</th><th>BT</th>${pr?'<th>Pr</th>':''}<th>Start</th><th>CT</th><th>TAT<small>= CT − AT</small></th><th>WT<small>= TAT − BT</small></th><th>RT<small>= start − AT</small></th></tr></thead><tbody>${R.rows.map(r=>{const d=done(r),st=r.st<T+1e-9||d;return `<tr class="${d?'':'netos-pend'}"><th><span class="cpusched-sw" style="background:${color(r.id)}"></span>${esc(r.id)}</th><td>${fx(r.at)}</td><td>${fx(r.bt)}</td>${pr?`<td>${fx(r.pr)}</td>`:''}<td>${st?fx(r.st):'–'}</td><td>${d?fx(r.ct):'–'}</td><td>${d?`${fx(r.ct)} − ${fx(r.at)} = <b>${fx(r.tat)}</b>`:'–'}</td><td>${d?`${fx(r.tat)} − ${fx(r.bt)} = <b>${fx(r.wt)}</b>`:'–'}</td><td>${st?`${fx(r.st)} − ${fx(r.at)} = <b>${fx(r.rt)}</b>`:'–'}</td></tr>`;}).join('')}</tbody>
     ${T>=R.end?`<tfoot><tr><th>Total</th><td></td><td>${fx(R.busy)}</td>${pr?'<td></td>':''}<td></td><td>${fx(R.sums.ct)}</td><td><b>${fx(R.sums.tat)}</b></td><td><b>${fx(R.sums.wt)}</b></td><td><b>${fx(R.sums.rt)}</b></td></tr></tfoot>`:''}`;
  }
  const sb=stepBar($('.netos-sb'),()=>R?R.log.length:1,k=>{if(!R)return;const T=k>=R.log.length?Infinity:R.log[k-1].e;gantt(T);table(T);$('.netos-note').innerHTML=R.log[k-1].text;});
  function run(){
    vis();const o=opts();
    const procs=rows.map((r,i)=>({id:'P'+(i+1),at:r[0].trim(),bt:r[1].trim(),pr:r[2].trim()}));
    const e=S.validate(procs,o.algo,o);
    err.hidden=!e;err.textContent=e;out.classList.toggle('netos-stale',!!e);if(e)return;
    R=S.schedule(procs,o.algo,o);const n=procs.length;
    $('.netos-chips').innerHTML=chip('Average WT',f2(R.avg.wt),1)+chip('Average TAT',f2(R.avg.tat),1)+chip('Average RT',f2(R.avg.rt))+chip('Schedule length',fx(R.end))+chip('CPU utilisation',f2(R.util*100)+'%')+chip('Throughput',`${n}/${fx(R.span)} = ${f2(n/R.span)}`);
    $('.netos-work').innerHTML=`<div class="netos-h">Working</div><div class="netos-f">
      <p>Average TAT = ΣTAT / n = (${R.rows.map(r=>fx(r.tat)).join(' + ')}) / ${n} = <b>${frac(R.sums.tat,n)}</b></p>
      <p>Average WT = ΣWT / n = (${R.rows.map(r=>fx(r.wt)).join(' + ')}) / ${n} = <b>${frac(R.sums.wt,n)}</b></p>
      <p>Average RT = ΣRT / n = (${R.rows.map(r=>fx(r.rt)).join(' + ')}) / ${n} = <b>${frac(R.sums.rt,n)}</b></p>
      <p>CPU utilisation = total burst / (last completion − first arrival) = ${fx(R.busy)} / (${fx(R.end)} − ${fx(R.first)}) = <b>${f2(R.util*100)}%</b></p></div>`;
    const a=o.algo;
    $('.cpusched-conv').innerHTML=[
      'TAT = CT − AT; WT = TAT − BT; RT (response time) = first time on the CPU − AT.',
      'Ties are broken by <b>arrival time, then process id</b> (P1 before P2)'+(a==='sjf'||a==='srtf'?', after comparing '+(a==='srtf'?'remaining':'burst')+' time':a.startsWith('prio')?', after comparing priority':'')+'.',
      a==='srtf'||a==='prio-p'?'Pre-emption is checked only when a new process arrives or the running one finishes. On an exact tie the running process (earlier arrival) keeps the CPU.':'',
      a.startsWith('prio')?(o.lowIsHigh?'Lower priority number = higher priority.':'Higher priority number = higher priority.'):'',
      a==='rr'?(o.rrNewFirst?'A process that arrives at the same instant a quantum expires joins the ready queue <b>before</b> the pre-empted process (standard convention).':'A process that arrives at the same instant a quantum expires joins the queue <b>after</b> the pre-empted process.')+' If a process is alone, it simply continues with no switch.':'',
      o.cs>0?`A context switch of ${fx(o.cs)} is charged whenever the CPU moves to a different process${o.csAll?', including the first dispatch and after an idle gap':' (not before the first process and not after an idle gap)'}. It counts in WT and TAT, not in CPU utilisation.`:'Context-switch time is 0.',
      'If nothing has arrived, the CPU sits idle until the next arrival (shown hatched).'].filter(Boolean).map(s=>`<li>${s}</li>`).join('');
    sb.reset();
  }
  stage.addEventListener('input',e=>{const t=e.target;if(t.dataset.r!=null){rows[+t.dataset.r][+t.dataset.c]=t.value;}run();});
  stage.addEventListener('change',e=>{if(e.target.dataset.k)run();});
  stage.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
    if(b.dataset.del!=null){rows.splice(+b.dataset.del,1);drawInputs();run();}
    else if(b.dataset.b==='add'){if(rows.length>=20)return;const last=rows[rows.length-1];rows.push([String((+last?.[0]||0)+1),'4','2']);drawInputs();run();}
    else if(b.dataset.b==='rand'){const n=rnd(4,6);rows=[];let at=0;for(let i=0;i<n;i++){rows.push([String(at),String(rnd(1,9)),String(rnd(1,5))]);at+=rnd(0,3);}
      if(Math.random()<.3)rows[n-1][0]=String(+rows[n-2][0]+12);drawInputs();run();}
    else if(b.dataset.b==='def'){rows=DEF.map(r=>r.slice());drawInputs();run();}});
  drawInputs();run();
 }});

/* ======================= pagerepl UI ======================= */
ANIM.register('pagerepl',{title:'Page replacement solver',steps:false,
 caption:'Type a reference string and a frame count. Each column is one reference; F marks a page fault and H a hit.',
 build(stage){
  const S=NETSOLVE.pagerepl;
  const DEF='7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1',BEL='1 2 3 4 1 2 5 1 2 3 4 5';
  stage.classList.add('netos-stage');
  stage.innerHTML=`<div class="netos pagerepl">
   <div class="netos-in"><div class="netos-ctl">
    <label class="netos-wide">Reference string<input data-k="refs" value="${DEF}" spellcheck="false"></label>
    <label>Frames<input type="number" data-k="nf" value="3" min="1" max="12"></label>
    <label>Algorithm<select data-k="algo">${Object.entries(S.NAMES).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label>
   </div>
   <div class="netos-btns"><button class="btn sm" data-b="rand">Random example</button><button class="btn sm" data-b="def">Default example</button><button class="btn sm" data-b="bel">Load Belady string</button><button class="btn sm" data-b="cmp">Compare all algorithms</button></div>
   <p class="netos-err" role="alert" hidden></p></div>
   <div class="netos-out">
    <div class="netos-chips"></div>
    <div class="netos-h">Frame-by-frame table</div>
    <div class="netos-scroll"><table class="netos-tbl pagerepl-t"></table></div>
    <div class="netos-sb"></div>
    <p class="netos-note" aria-live="polite"></p>
    <div class="netos-work"></div>
    <div class="pagerepl-cmp"></div>
    <div class="netos-h">Belady's anomaly</div>
    <p class="pagerepl-bt"><button class="btn sm primary" data-b="belady">Check Belady's anomaly</button> <span class="netos-mut">Runs the chosen algorithm for 1 to N frames on this string.</span></p>
    <div class="pagerepl-bel"></div>
    <details class="netos-conv"><summary>Conventions used</summary><ul>
     <li>Frames start empty. <b>Page faults include the initial compulsory faults</b> that fill empty frames.</li>
     <li>A replaced page's frame receives the new page, so each row is one physical frame.</li>
     <li>Hit ratio = hits / references; fault ratio = faults / references.</li>
     <li>Optimal and LFU ties are broken FIFO (the page loaded earliest leaves). LFU counts restart at 1 when a page is loaded again.</li>
     <li>LRU and Optimal are stack algorithms, so they can never show Belady's anomaly; FIFO can.</li></ul></details>
   </div></div>`;
  const $=s=>stage.querySelector(s),ctl=k=>stage.querySelector(`[data-k="${k}"]`),err=$('.netos-err');
  let R=null,refs=[],nf=3;
  function draw(K){
    const st=R.steps;
    let h=`<thead><tr><th>Ref</th>${st.map((s,i)=>`<th class="${i===K-1&&K<st.length?'cur':''}${i>=K?' fut':''}">${esc(s.ref)}</th>`).join('')}</tr></thead><tbody>`;
    for(let f=0;f<nf;f++)h+=`<tr><th>Frame ${f+1}</th>${st.map((s,i)=>{if(i>=K)return '<td class="fut"></td>';const v=s.frames[f];const cls=s.slot===f?(s.hit?'hit':'new'):'';return `<td class="${cls}">${v===null?'':esc(v)}</td>`;}).join('')}</tr>`;
    h+=`<tr class="pagerepl-m"><th>Result</th>${st.map((s,i)=>i>=K?'<td class="fut"></td>':`<td class="${s.hit?'h':'f'}">${s.hit?'H':'F'}</td>`).join('')}</tr>`;
    h+=`<tr class="pagerepl-v"><th>Out</th>${st.map((s,i)=>i>=K?'<td class="fut"></td>':`<td>${s.victim!=null?esc(s.victim):''}</td>`).join('')}</tr>`;
    if(st[0]&&st[0].state!=='')h+=`<tr class="pagerepl-s"><th>${ctl('algo').value==='lfu'?'Counts':ctl('algo').value==='fifo'?'Queue':'Recency'}</th>${st.map((s,i)=>i>=K?'<td class="fut"></td>':`<td>${esc(s.state.replace(/^[^:]*: /,'')).replace(/ /g,'<br>')}</td>`).join('')}</tr>`;
    $('.pagerepl-t').innerHTML=h+'</tbody>';
    const f=st.slice(0,K).filter(s=>!s.hit).length;
    $('.netos-note').innerHTML=K>=st.length?`All ${st.length} references done: <b>${R.faults} faults</b>, ${R.hits} hits.`:`Reference ${K} (page ${esc(st[K-1].ref)}): ${st[K-1].why} Faults so far: ${f}.`;
  }
  const sb=stepBar($('.netos-sb'),()=>R?R.steps.length:1,k=>{if(R)draw(k);});
  function read(){refs=S.parse(ctl('refs').value);nf=+ctl('nf').value;
    if(!refs.length)return 'Enter a reference string, e.g. 7 0 1 2 0 3.';
    if(refs.length>60)return 'Use at most 60 references.';
    if(refs.some(r=>r.length>4))return 'Each page should be a short label such as 7 or 12 (separate pages with spaces or commas).';
    if(!Number.isInteger(nf)||nf<1||nf>12)return 'Frames must be a whole number from 1 to 12.';return '';}
  function run(){
    const e=read();err.hidden=!e;err.textContent=e;$('.netos-out').classList.toggle('netos-stale',!!e);$('.pagerepl-bel').innerHTML='';$('.pagerepl-cmp').innerHTML='';if(e)return;
    const algo=ctl('algo').value;R=S.simulate(refs,nf,algo);const n=refs.length,distinct=new Set(refs).size;
    $('.netos-chips').innerHTML=chip('Page faults',R.faults,1)+chip('Hits',R.hits)+chip('Hit ratio',`${R.hits}/${n} = ${f2(R.ratio*100)}%`,1)+chip('Fault ratio',`${R.faults}/${n} = ${f2(R.faults/n*100)}%`)+chip('Compulsory faults',Math.min(distinct,R.steps.filter((s,i)=>!s.hit&&!refs.slice(0,i).includes(s.ref)).length));
    $('.netos-work').innerHTML=`<div class="netos-f"><p>Page faults = <b>${R.faults}</b> (out of ${n} references, ${distinct} distinct pages, ${nf} frames)</p><p>Hit ratio = hits / references = ${R.hits} / ${n} = <b>${f2(R.ratio)}</b> (${f2(R.ratio*100)}%)</p><p>Miss ratio = ${R.faults} / ${n} = ${f2(R.faults/n)}</p></div>`;
    sb.reset();
  }
  function belady(){
    if(read())return;const algo=ctl('algo').value;const maxF=Math.min(12,Math.max(nf+3,new Set(refs).size+1,5));
    const B=S.belady(refs,algo,maxF),mx=Math.max(...B.table.map(r=>r.faults),1);
    const bad=new Set(B.anomalies.map(a=>a[1].frames));
    $('.pagerepl-bel').innerHTML=`<div class="pagerepl-bars">${B.table.map(r=>`<div class="${bad.has(r.frames)?'bad':''}${r.frames===nf?' cur':''}"><span>${r.frames} frame${r.frames>1?'s':''}</span><i style="width:${r.faults/mx*100}%"></i><b>${r.faults}</b></div>`).join('')}</div>
      <p class="netos-verdict ${B.anomalies.length?'bad':'ok'}">${B.anomalies.length?`<b>Belady's anomaly found</b> for ${S.NAMES[algo]}: `+B.anomalies.map(([a,b])=>`${a.frames} frames → ${a.faults} faults, but ${b.frames} frames → ${b.faults} faults`).join('; ')+'. More frames gave more faults.':`No anomaly: with ${S.NAMES[algo]} the fault count never rises as frames increase on this string.${algo==='lru'||algo==='opt'?' (It cannot: this is a stack algorithm.)':algo==='fifo'?' Try “Load Belady string”.':''}`}</p>`;
  }
  function compare(){
    if(read())return;const n=refs.length;
    $('.pagerepl-cmp').innerHTML=`<div class="netos-h">All algorithms, ${nf} frames</div><div class="netos-scroll"><table class="netos-tbl"><thead><tr><th>Algorithm</th><th>Faults</th><th>Hits</th><th>Hit ratio</th></tr></thead><tbody>${Object.keys(S.NAMES).map(a=>{const r=S.simulate(refs,nf,a);return `<tr><th>${S.NAMES[a]}</th><td><b>${r.faults}</b></td><td>${r.hits}</td><td>${r.hits}/${n} = ${f2(r.ratio*100)}%</td></tr>`;}).join('')}</tbody></table></div>`;
  }
  stage.addEventListener('input',e=>{if(e.target.dataset.k)run();});
  stage.addEventListener('change',e=>{if(e.target.dataset.k==='algo')run();});
  stage.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||!b.dataset.b)return;const a=b.dataset.b;
    if(a==='rand'){const L=rnd(12,18),P=rnd(5,7);const arr=[];for(let i=0;i<L;i++)arr.push(i>2&&Math.random()<.35?arr[rnd(Math.max(0,i-4),i-1)]:rnd(0,P));ctl('refs').value=arr.join(' ');ctl('nf').value=rnd(3,4);run();}
    else if(a==='def'){ctl('refs').value=DEF;ctl('nf').value=3;ctl('algo').value='fifo';run();}
    else if(a==='bel'){ctl('refs').value=BEL;ctl('nf').value=3;ctl('algo').value='fifo';run();belady();}
    else if(a==='belady')belady();else if(a==='cmp')compare();});
  run();
 }});

/* ======================= banker UI ======================= */
ANIM.register('banker',{title:"Banker's algorithm solver",steps:false,
 caption:"Enter Allocation, Max and Available. The solver builds the Need matrix, traces the safety algorithm and checks resource requests.",
 build(stage){
  const S=NETSOLVE.banker,L=j=>String.fromCharCode(65+j);
  const DEF={alloc:[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]],max:[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]],avail:[3,3,2]};
  let st=JSON.parse(JSON.stringify(DEF));
  stage.classList.add('netos-stage');
  stage.innerHTML=`<div class="netos banker">
   <div class="netos-in"><div class="netos-ctl">
    <label>Processes (n)<input type="number" data-k="n" value="5" min="1" max="10"></label>
    <label>Resource types (m)<input type="number" data-k="m" value="3" min="1" max="6"></label>
    <label>Safety scan order<select data-k="mode"><option value="cyclic">Continue from the next process (textbook)</option><option value="restart">Restart from P0 after each finish</option></select></label>
   </div>
   <div class="netos-scroll"><table class="netos-tbl netos-edit banker-in"></table></div>
   <div class="netos-btns"><button class="btn sm" data-b="rand">Random example</button><button class="btn sm" data-b="def">Default example</button></div>
   <p class="netos-err" role="alert" hidden></p></div>
   <div class="netos-out">
    <div class="netos-chips"></div>
    <div class="netos-h">Need = Max − Allocation</div>
    <div class="netos-scroll"><table class="netos-tbl banker-need"></table></div>
    <div class="netos-h">Safety algorithm trace</div>
    <div class="netos-scroll"><table class="netos-tbl banker-tr"></table></div>
    <div class="netos-sb"></div>
    <p class="netos-note" aria-live="polite"></p>
    <div class="netos-h">Resource request</div>
    <div class="netos-ctl banker-rq"><label>Process<select data-q="p"></select></label><label>Request vector<input data-q="v" value="1 0 2" spellcheck="false"></label><button class="btn sm primary" data-b="req">Check request</button></div>
    <div class="banker-rr"></div>
    <details class="netos-conv"><summary>Conventions used</summary><ul>
     <li>Need[i] = Max[i] − Allocation[i]. Work starts as Available.</li>
     <li>A process can finish if Need[i] ≤ Work (every resource). It then releases its Allocation: Work = Work + Allocation[i].</li>
     <li>Scan order: <i>continue</i> keeps going from the next process and wraps round (this gives the textbook answer &lt;P1, P3, P4, P0, P2&gt;); <i>restart</i> goes back to P0 after each finish. Both give a valid safe sequence when one exists; NET options may list either.</li>
     <li>Request: grant only if Request ≤ Need, Request ≤ Available and the resulting state is safe.</li></ul></details>
   </div></div>`;
  const $=s=>stage.querySelector(s),ctl=k=>stage.querySelector(`[data-k="${k}"]`),err=$('.netos-err');
  let R=null;const n=()=>st.alloc.length,m=()=>st.avail.length;
  const vec=v=>`(${v.join(', ')})`;
  function drawInputs(){
    const hd=[...Array(m()).keys()].map(L).map(x=>`<th>${x}</th>`).join('');
    $('.banker-in').innerHTML=`<thead><tr><th rowspan="2"></th><th colspan="${m()}" class="grp">Allocation</th><th colspan="${m()}" class="grp">Max</th></tr><tr>${hd}${hd}</tr></thead><tbody>${st.alloc.map((r,i)=>`<tr><th>P${i}</th>${r.map((v,j)=>`<td><input inputmode="numeric" aria-label="P${i} allocation ${L(j)}" data-t="alloc" data-i="${i}" data-j="${j}" value="${v}"></td>`).join('')}${st.max[i].map((v,j)=>`<td class="${j===0?'sep':''}"><input inputmode="numeric" aria-label="P${i} max ${L(j)}" data-t="max" data-i="${i}" data-j="${j}" value="${v}"></td>`).join('')}</tr>`).join('')}
      <tr class="banker-av"><th>Available</th>${st.avail.map((v,j)=>`<td><input inputmode="numeric" aria-label="Available ${L(j)}" data-t="avail" data-j="${j}" value="${v}"></td>`).join('')}<td colspan="${m()}"></td></tr></tbody>`;
    $('[data-q=p]').innerHTML=st.alloc.map((_,i)=>`<option value="${i}">P${i}</option>`).join('');
  }
  function resize(){const N=Math.max(1,Math.min(10,+ctl('n').value||1)),M=Math.max(1,Math.min(6,+ctl('m').value||1));
    const fit=(a,r,c)=>Array.from({length:r},(_,i)=>Array.from({length:c},(_,j)=>(a[i]&&a[i][j]!=null)?a[i][j]:0));
    st.alloc=fit(st.alloc,N,M);st.max=fit(st.max,N,M);st.avail=Array.from({length:M},(_,j)=>st.avail[j]!=null?st.avail[j]:0);drawInputs();run();}
  function showTrace(K){
    const tr=R.trace;
    $('.banker-tr').innerHTML=`<thead><tr><th>#</th><th>Process</th><th>Need</th><th>Work</th><th>Need ≤ Work?</th><th>New Work = Work + Alloc</th></tr></thead><tbody>${tr.slice(0,K).map((t,k)=>`<tr class="${t.ok?'ok':'no'}${k===K-1&&K<tr.length?' cur':''}"><td>${k+1}</td><th>P${t.p}</th><td>${vec(t.need)}</td><td>${vec(t.work)}</td><td>${t.ok?'✓ yes, P'+t.p+' finishes':'✗ no, P'+t.p+' waits'}</td><td>${t.ok?`${vec(t.work)} + ${vec(st.alloc[t.p])} = <b>${vec(t.after)}</b>`:'–'}</td></tr>`).join('')}</tbody>`;
    const done=tr.slice(0,K).filter(t=>t.ok).map(t=>'P'+t.p);
    $('.netos-note').innerHTML=K>=tr.length?(R.safe?`Every process can finish, so the state is <b>safe</b>. Safe sequence: &lt;${R.seq.map(i=>'P'+i).join(', ')}&gt;.`:`No remaining process has Need ≤ Work ${vec(R.work)}. The state is <b>unsafe</b> (${R.finish.map((f,i)=>f?null:'P'+i).filter(Boolean).join(', ')} cannot finish).`):`Check ${K}: ${tr[K-1].ok?`P${tr[K-1].p} can finish.`:`P${tr[K-1].p} must wait.`} Finished so far: &lt;${done.join(', ')}&gt;.`;
  }
  const sb=stepBar($('.netos-sb'),()=>R?Math.max(1,R.trace.length):1,k=>{if(R)showTrace(k);});
  function run(){
    const e=S.validate(st.alloc,st.max,st.avail);err.hidden=!e;err.textContent=e;$('.netos-out').classList.toggle('netos-stale',!!e);$('.banker-rr').innerHTML='';if(e)return;
    R=S.safety(st.alloc,st.max,st.avail,ctl('mode').value);
    const tot=st.avail.map((a,j)=>a+st.alloc.reduce((s,r)=>s+r[j],0));
    $('.netos-chips').innerHTML=chip('State',R.safe?'SAFE':'UNSAFE',1).replace('netos-chip main',`netos-chip main ${R.safe?'ok':'bad'}`)+chip('Safe sequence',R.safe?'&lt;'+R.seq.map(i=>'P'+i).join(', ')+'&gt;':'none',1)+chip('Total instances',vec(tot));
    const hd=[...Array(m()).keys()].map(L).map(x=>`<th>${x}</th>`).join('');
    $('.banker-need').innerHTML=`<thead><tr><th></th>${hd}<th>Working</th></tr></thead><tbody>${R.need.map((r,i)=>`<tr><th>P${i}</th>${r.map(v=>`<td><b>${v}</b></td>`).join('')}<td class="netos-mut">${vec(st.max[i])} − ${vec(st.alloc[i])}</td></tr>`).join('')}</tbody>`;
    sb.reset();
  }
  function request(){
    const p=+$('[data-q=p]').value;const raw=$('[data-q=v]').value.trim().split(/[\s,()]+/).filter(Boolean);const box=$('.banker-rr');
    if(raw.length!==m()||raw.some(x=>!/^\d+$/.test(x))){box.innerHTML=`<p class="netos-err">Enter ${m()} whole numbers for the request, e.g. ${Array(m()).fill(0).map((_,j)=>j%2).join(' ')}.</p>`;return;}
    const req=raw.map(Number);const r=S.request(st.alloc,st.max,st.avail,p,req,ctl('mode').value);
    const c1=req.every((x,j)=>x<=r.need[j]),c2=req.every((x,j)=>x<=st.avail[j]);
    let h=`<ol class="banker-ck"><li class="${c1?'ok':'no'}">Request ${vec(req)} ≤ Need[P${p}] ${vec(r.need)}? <b>${c1?'Yes':'No: the process has exceeded its maximum claim (error).'}</b></li>`;
    if(c1)h+=`<li class="${c2?'ok':'no'}">Request ≤ Available ${vec(st.avail)}? <b>${c2?'Yes':'No: P'+p+' must wait.'}</b></li>`;
    if(c1&&c2){h+=`<li class="${r.ok?'ok':'no'}">Pretend to allocate: Available = ${vec(r.avail)}, Allocation[P${p}] = ${vec(r.alloc[p])}, Need[P${p}] = ${vec(r.need.map((x,j)=>x-req[j]))}. Run safety: <b>${r.ok?'safe, sequence &lt;'+r.safety.seq.map(i=>'P'+i).join(', ')+'&gt;':'unsafe'}</b>.</li>`;}
    h+=`</ol><p class="netos-verdict ${r.ok?'ok':'bad'}">${r.ok?`<b>Grant</b> the request of P${p}.`:r.stage==='need'?'<b>Error</b>: request exceeds the declared need.':r.stage==='avail'?`<b>Wait</b>: not enough resources available now.`:`<b>Deny</b> (P${p} waits): granting would leave the system unsafe.`}${r.ok?' <button class="btn sm" data-b="apply">Apply to the state above</button>':''}</p>`;
    if(r.stage==='unsafe'||r.ok)h+=`<details><summary>Safety trace after the pretend allocation</summary><div class="netos-scroll"><table class="netos-tbl"><thead><tr><th>Process</th><th>Need</th><th>Work</th><th>OK?</th><th>New Work</th></tr></thead><tbody>${r.safety.trace.map(t=>`<tr class="${t.ok?'ok':'no'}"><th>P${t.p}</th><td>${vec(t.need)}</td><td>${vec(t.work)}</td><td>${t.ok?'✓':'✗'}</td><td>${t.ok?vec(t.after):'–'}</td></tr>`).join('')}</tbody></table></div></details>`;
    box.innerHTML=h;box._apply=r.ok?()=>{st.alloc=r.alloc;st.avail=r.avail;drawInputs();run();}:null;
  }
  stage.addEventListener('input',e=>{const t=e.target;if(t.dataset.t){const v=t.value.trim()===''?NaN:Number(t.value);if(t.dataset.t==='avail')st.avail[+t.dataset.j]=v;else st[t.dataset.t][+t.dataset.i][+t.dataset.j]=v;run();}
    else if(t.dataset.k==='n'||t.dataset.k==='m')resize();});
  stage.addEventListener('change',e=>{if(e.target.dataset.k==='mode')run();});
  stage.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||!b.dataset.b)return;const a=b.dataset.b;
    if(a==='req')request();
    else if(a==='apply'){const f=$('.banker-rr')._apply;if(f)f();}
    else if(a==='def'){st=JSON.parse(JSON.stringify(DEF));ctl('n').value=5;ctl('m').value=3;drawInputs();run();}
    else if(a==='rand'){const N=5,M=3;st.max=Array.from({length:N},()=>Array.from({length:M},()=>rnd(1,9)));st.alloc=st.max.map(r=>r.map(x=>rnd(0,Math.min(x,4))));st.avail=Array.from({length:M},()=>rnd(1,5));ctl('n').value=N;ctl('m').value=M;drawInputs();run();}});
  drawInputs();run();
 }});

/* ======================= disksched UI ======================= */
ANIM.register('disksched',{title:'Disk scheduling solver',steps:false,
 caption:'Enter the request queue, the head position and the disk size. The chart plots cylinder (across) against service order (down).',
 build(stage){
  const S=NETSOLVE.disksched;
  const DEF={q:'98 183 37 122 14 124 65 67',head:53,size:200};
  stage.classList.add('netos-stage');
  stage.innerHTML=`<div class="netos disksched">
   <div class="netos-in"><div class="netos-ctl">
    <label class="netos-wide">Request queue (cylinders)<input data-k="q" value="${DEF.q}" spellcheck="false"></label>
    <label>Head at<input type="number" data-k="head" value="${DEF.head}" min="0"></label>
    <label>Disk size N (cylinders 0 to N−1)<input type="number" data-k="size" value="${DEF.size}" min="2"></label>
    <label>Algorithm<select data-k="algo">${Object.entries(S.NAMES).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label>
    <label>Direction<select data-k="dir"><option value="up">Towards higher cylinders</option><option value="down">Towards 0</option></select></label>
    <label class="chk" data-show="c"><input type="checkbox" data-k="jump" checked> Count the return jump in the total</label>
   </div>
   <div class="netos-btns"><button class="btn sm" data-b="rand">Random example</button><button class="btn sm" data-b="def">Default example</button><button class="btn sm" data-b="cmp">Compare all algorithms</button></div>
   <p class="netos-err" role="alert" hidden></p></div>
   <div class="netos-out">
    <div class="netos-chips"></div>
    <div class="netos-h">Head movement</div>
    <div class="netos-scroll disksched-cw"><svg class="disksched-c" role="img" aria-label="Head movement chart"></svg></div>
    <div class="netos-sb"></div>
    <p class="netos-note" aria-live="polite"></p>
    <div class="netos-h">Seek working</div>
    <div class="netos-scroll"><table class="netos-tbl disksched-t"></table></div>
    <div class="netos-work"></div>
    <div class="disksched-cmp"></div>
    <details class="netos-conv"><summary>Conventions used</summary><ul class="disksched-conv"></ul></details>
   </div></div>`;
  const $=s=>stage.querySelector(s),ctl=k=>stage.querySelector(`[data-k="${k}"]`),err=$('.netos-err');
  let R=null,cfg=null;
  function chart(K){
    const P=R.path,W=640,x0=34,x1=W-20,y0=40,dy=30,H=y0+(P.length-1)*dy+24,sz=cfg.size-1;
    const X=c=>x0+(x1-x0)*c/sz;
    const svg=$('.disksched-c');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('width',W);svg.setAttribute('height',H);
    let g=`<line class="ax" x1="${x0}" y1="24" x2="${x1}" y2="24"/>`;
    const ticks=[...new Set([0,sz,cfg.head,...cfg.reqs])].sort((a,b)=>a-b);
    let lastX=-99;ticks.forEach(c=>{const x=X(c);g+=`<line class="tk" x1="${x}" y1="20" x2="${x}" y2="${H-10}"/>`;if(x-lastX>=20||c===sz){g+=`<text x="${x}" y="14" text-anchor="middle">${c}</text>`;lastX=x;}});
    for(let k=1;k<P.length;k++){const a=P[k-1],b=P[k],on=k<=K;const mv=R.moves[k-1];
      g+=`<line class="mv ${b.type==='jump'?'jump':''} ${on?'':'fut'} ${k===K&&K<P.length-1?'cur':''}" x1="${X(a.pos)}" y1="${y0+(k-1)*dy}" x2="${X(b.pos)}" y2="${y0+k*dy}"/>`;
      if(on)g+=`<text class="d" x="${(X(a.pos)+X(b.pos))/2+(b.pos>=a.pos?6:-6)}" y="${y0+(k-.5)*dy+4}" text-anchor="${b.pos>=a.pos?'start':'end'}">${mv.counted?mv.d:'('+mv.d+')'}</text>`;}
    P.forEach((p,k)=>{if(k>K)return;const x=X(p.pos),y=y0+k*dy;g+=`<circle class="pt ${p.type}" cx="${x}" cy="${y}" r="${p.type==='start'?6:4.5}"/><text class="pl" x="${x+(p.pos>sz*0.85?-9:9)}" y="${y-7}" text-anchor="${p.pos>sz*0.85?'end':'start'}">${p.pos}</text>`;});
    svg.innerHTML=g;
  }
  function table(K){
    let run=0;
    $('.disksched-t').innerHTML=`<thead><tr><th>#</th><th>Move</th><th>Seek |to − from|</th><th>Running total</th></tr></thead><tbody>${R.moves.map((m,k)=>{if(m.counted)run+=m.d;if(k>=K)return '';const tag=m.type==='jump'?' <span class="netos-tag">return jump'+(m.counted?'':', not counted')+'</span>':m.type==='end'?' <span class="netos-tag">disk end</span>':'';return `<tr class="${k===K-1&&K<R.moves.length?'cur':''}${m.counted?'':' netos-dim'}"><td>${k+1}</td><td>${m.from} → ${m.to}${tag}</td><td>|${m.to} − ${m.from}| = <b>${m.d}</b></td><td>${run}</td></tr>`;}).join('')}</tbody>`;
    const m=R.moves[K-1];
    $('.netos-note').innerHTML=!m?'':K>=R.moves.length?`Done. Total head movement = <b>${R.total}</b> cylinders.`:`Move ${K}: head goes ${m.from} → ${m.to}${m.type==='jump'?' (return jump)':m.type==='end'?' (to the end of the disk)':''}, seek ${m.d}.`;
  }
  const sb=stepBar($('.netos-sb'),()=>R?Math.max(1,R.moves.length):1,k=>{if(R){chart(k);table(k);}});
  function read(){const reqs=String(ctl('q').value).trim().split(/[\s,]+/).filter(Boolean);const head=Number(ctl('head').value),size=Number(ctl('size').value);
    const e=S.validate(reqs,head,size);cfg={reqs:reqs.map(Number),head,size,algo:ctl('algo').value,dir:ctl('dir').value,jump:ctl('jump').checked};return e;}
  function run(){
    const a=ctl('algo').value;stage.querySelector('[data-show=c]').hidden=!(a==='cscan'||a==='clook');
    const e=read();err.hidden=!e;err.textContent=e;$('.netos-out').classList.toggle('netos-stale',!!e);$('.disksched-cmp').innerHTML='';if(e)return;
    R=S.schedule(cfg.reqs,cfg.head,cfg.dir,cfg.size,cfg.algo,cfg.jump);
    const jm=R.moves.find(m=>m.type==='jump');
    $('.netos-chips').innerHTML=chip('Total head movement',R.total+' cylinders',1)+chip('Average seek',`${R.total}/${cfg.reqs.length} = ${f2(R.avg)}`)+(jm?chip('Return jump',jm.counted?`${jm.d} (counted)`:`${jm.d} (not counted)`):'');
    $('.netos-work').innerHTML=`<div class="netos-f"><p>Service order: ${cfg.head} → ${R.path.slice(1).map(p=>p.type==='serve'||(p.type==='jump'&&cfg.algo==='clook')?p.pos:`<span class="netos-mut">${p.pos}</span>`).join(' → ')}</p><p>Total = ${R.moves.filter(m=>m.counted).map(m=>m.d).join(' + ')||0} = <b>${R.total}</b>${jm&&!jm.counted?` <span class="netos-mut">(return jump of ${jm.d} excluded; with it: ${R.total+jm.d})</span>`:jm?` <span class="netos-mut">(without the return jump: ${R.total-jm.d})</span>`:''}</p></div>`;
    $('.disksched-conv').innerHTML=[
      'Seek distance = |new cylinder − old cylinder|; total head movement = the sum of all seeks.',
      `Cylinders run from 0 to ${cfg.size-1}. The head starts at ${cfg.head}, moving ${cfg.dir==='up'?'towards higher numbers':'towards 0'}.`,
      'SSTF picks the closest request; on an equal-distance tie it keeps moving in the current direction.',
      'SCAN and C-SCAN travel all the way to the disk end before reversing or jumping; LOOK and C-LOOK turn at the last request. If nothing is left on the other side, the arm stops at the last request.',
      'C-SCAN jumps from one end to the other (e.g. 199 → 0); C-LOOK jumps to the farthest request on the other side. '+(cfg.jump?'<b>The jump is counted</b> in the total (the arm really travels). Many textbooks do this.':'<b>The jump is not counted</b> (treated as a fast return with no servicing). Some keys use this; check the question wording.'),
      'A request at the current head position is served first with seek 0.'].map(s=>`<li>${s}</li>`).join('');
    sb.reset();
  }
  function compare(){if(read())return;$('.disksched-cmp').innerHTML=`<div class="netos-h">All algorithms (same input)</div><div class="netos-scroll"><table class="netos-tbl"><thead><tr><th>Algorithm</th><th>Total movement</th><th>Order</th></tr></thead><tbody>${Object.keys(S.NAMES).map(a=>{const r=S.schedule(cfg.reqs,cfg.head,cfg.dir,cfg.size,a,cfg.jump);return `<tr><th>${S.NAMES[a]}</th><td><b>${r.total}</b></td><td class="netos-mut">${r.order.join(' ')}</td></tr>`;}).join('')}</tbody></table></div>`;}
  stage.addEventListener('input',e=>{if(e.target.dataset.k)run();});
  stage.addEventListener('change',e=>{if(e.target.dataset.k)run();});
  stage.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||!b.dataset.b)return;const a=b.dataset.b;
    if(a==='def'){ctl('q').value=DEF.q;ctl('head').value=DEF.head;ctl('size').value=DEF.size;run();}
    else if(a==='rand'){const N=200,arr=[];for(let i=0;i<8;i++)arr.push(rnd(0,N-1));ctl('q').value=arr.join(' ');ctl('head').value=rnd(20,180);ctl('size').value=N;run();}
    else if(a==='cmp')compare();});
  run();
 }});
})();

/* ================= UGC NET solvers: Theory of computation & compilers (dfa, ll1, lr) =================
   Pure algorithms live on window.NETSOLVE.dfa / .ll1 / .lr so they can be tested in Node
   (global.window = {}). The UI registers three ANIM playgrounds.
   Wrapped in an IIFE so the NETSOLVE binding does not collide with other net-*.js files
   when the harness concatenates every script into one <script>. */
(function(){
'use strict';
const NETSOLVE = NS_ROOT.NETSOLVE;
const EPS='ε';
const EPS_WORDS=new Set(['ε','eps','epsilon','λ','lambda','#','∈','Є']);
const NONE=new Set(['-','∅','φ','Φ','phi','{}','—','–','_']);
const byNum=(a,b)=>a-b;
const LETTERS='ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const letterName=i=>i<26?LETTERS[i]:'S'+i;

/* ============================================================
   CORE 1: finite automata
   A = {n, names[], alpha[], start, acc[bool], d[state][sym] = [targets], e[state] = [targets], eps}
   ============================================================ */
function parseAutomaton(spec){
  const alpha=String(spec.alpha||'').split(/[\s,]+/).filter(Boolean);
  if(!alpha.length)return {error:'Enter at least one input symbol in Σ, e.g. “a b”.'};
  if(new Set(alpha).size!==alpha.length)return {error:'Σ has a repeated symbol.'};
  if(alpha.some(a=>EPS_WORDS.has(a)))return {error:'Don’t put ε in Σ: tick “ε-moves” to get an ε column.'};
  if(alpha.length>6)return {error:'Use at most 6 input symbols.'};
  const rows=spec.rows||[];
  if(!rows.length)return {error:'Add at least one state.'};
  if(rows.length>12)return {error:'Use at most 12 states.'};
  const names=rows.map(r=>String(r.name==null?'':r.name).trim());
  for(let i=0;i<names.length;i++){
    if(!names[i])return {error:`The state in row ${i+1} has no name.`};
    if(/[\s,{}]/.test(names[i]))return {error:`State name “${names[i]}” must not contain spaces, commas or braces.`};
    if(names.indexOf(names[i])!==i)return {error:`Two states are both called “${names[i]}”.`};
  }
  const idx=new Map(names.map((n,i)=>[n,i]));
  const starts=rows.map((r,i)=>r.start?i:-1).filter(i=>i>=0);
  if(starts.length!==1)return {error:'Mark exactly one start state (→).'};
  const cols=alpha.concat(spec.eps?[EPS]:[]);
  const d=rows.map(()=>alpha.map(()=>[])),e=rows.map(()=>[]);
  for(let i=0;i<rows.length;i++)for(let c=0;c<cols.length;c++){
    const txt=String(((rows[i].cells||{})[cols[c]])||'');
    const toks=txt.replace(/[{}]/g,' ').split(/[\s,]+/).filter(t=>t&&!NONE.has(t));
    const out=c<alpha.length?d[i][c]:e[i];
    for(const t of toks){
      if(!idx.has(t))return {error:`Row ${names[i]}, column ${cols[c]}: “${t}” is not a state name.`};
      if(!out.includes(idx.get(t)))out.push(idx.get(t));
    }
    out.sort(byNum);
  }
  return {A:{n:rows.length,names,alpha,start:starts[0],acc:rows.map(r=>!!r.accept),d,e,eps:!!spec.eps}};
}
function kindOf(A){
  const hasE=A.e.some(x=>x.length),multi=A.d.some(r=>r.some(c=>c.length>1)),miss=A.d.some(r=>r.some(c=>!c.length));
  return {hasE,multi,miss,det:!hasE&&!multi,label:hasE?'ε-NFA':multi?'NFA':miss?'DFA (partial)':'DFA'};
}
function closure(A,set){
  const seen=new Set(set),st=[...set];
  while(st.length){const s=st.pop();for(const t of A.e[s])if(!seen.has(t)){seen.add(t);st.push(t);}}
  return [...seen].sort(byNum);
}
function move(A,set,c){const o=new Set();for(const s of set)for(const t of A.d[s][c])o.add(t);return [...o].sort(byNum);}
/* split a string into symbols: whitespace-separated if it has spaces, else greedy longest match */
function tokenize(syms,str){
  str=String(str==null?'':str).trim();
  if(!str||EPS_WORDS.has(str))return {toks:[]};
  if(/\s/.test(str)){
    const toks=str.split(/\s+/);const bad=toks.find(t=>!syms.includes(t));
    return bad!==undefined?{error:`“${bad}” is not a symbol of the ${syms.length?'alphabet':'grammar'} (${syms.join(' ')}).`}:{toks};
  }
  const sorted=[...syms].sort((a,b)=>b.length-a.length),toks=[];let i=0;
  while(i<str.length){const m=sorted.find(s=>s&&str.startsWith(s,i));if(!m)return {error:`“${str[i]}” at position ${i+1} is not a symbol (${syms.join(' ')}).`};toks.push(m);i+=m.length;}
  return {toks};
}
function simulate(A,toks){
  const steps=[{sym:null,moved:null,set:closure(A,[A.start])}];
  for(const t of toks){
    const c=A.alpha.indexOf(t);const moved=move(A,steps[steps.length-1].set,c);
    steps.push({sym:t,moved,set:closure(A,moved)});
  }
  const last=steps[steps.length-1].set;
  return {steps,accepted:last.some(s=>A.acc[s])};
}
/* subset construction; the ∅ set becomes an ordinary (trap) state if it is reached */
function subset(A,max){
  max=max||200;
  const key=s=>s.join(','),sets=[closure(A,[A.start])],map=new Map([[key(sets[0]),0]]),rows=[];
  for(let i=0;i<sets.length;i++){
    if(sets.length>max)return {error:`The subset construction passed ${max} DFA states; use a smaller NFA.`};
    const row=[];
    for(let c=0;c<A.alpha.length;c++){
      const moved=move(A,sets[i],c),cl=closure(A,moved),k=key(cl),isNew=!map.has(k);
      if(isNew){map.set(k,sets.length);sets.push(cl);}
      row.push({moved,cl,to:map.get(k),isNew});
    }
    rows.push(row);
  }
  const names=sets.map((s,i)=>letterName(i));
  const D={n:sets.length,names,alpha:A.alpha.slice(),start:0,acc:sets.map(s=>s.some(x=>A.acc[x])),d:rows.map(r=>r.map(x=>[x.to])),e:sets.map(()=>[]),eps:false};
  return {sets,rows,D,dead:sets.findIndex(s=>!s.length)};
}
/* minimisation by partition refinement (Moore). Input must be deterministic (may be partial). */
function minimize(A){
  const k=kindOf(A);if(!k.det)return {error:'Minimisation needs a DFA.'};
  const seen=new Set([A.start]),q=[A.start];
  while(q.length){const s=q.shift();for(const c of A.d[s])for(const t of c)if(!seen.has(t)){seen.add(t);q.push(t);}}
  const order=[...seen].sort(byNum),unreachable=A.names.filter((n,i)=>!seen.has(i));
  const pos=new Map(order.map((s,i)=>[s,i]));
  const names=order.map(i=>A.names[i]),acc=order.map(i=>A.acc[i]);
  const needTrap=order.some(s=>A.d[s].some(t=>!t.length));
  let trap=-1;
  const delta=order.map(s=>A.d[s].map(t=>t.length?pos.get(t[0]):-1));
  if(needTrap){
    trap=names.length;let tn='∅';while(names.includes(tn))tn+="'";
    names.push(tn);acc.push(false);delta.push(A.alpha.map(()=>trap));
    delta.forEach(r=>r.forEach((t,c)=>{if(t<0)r[c]=trap;}));
  }
  const N=names.length,all=[...Array(N).keys()];
  let blocks=[all.filter(s=>!acc[s]),all.filter(s=>acc[s])].filter(b=>b.length);
  const P0=blocks.map(b=>b.slice());
  const rounds=[];
  for(let guard=0;guard<N+2;guard++){
    const blockOf=[];blocks.forEach((b,i)=>b.forEach(s=>blockOf[s]=i));
    const sig=all.map(s=>delta[s].map(t=>blockOf[t]));
    const next=[],from=[];
    blocks.forEach((b,bi)=>{const m=new Map();b.forEach(s=>{const k2=sig[s].join(',');if(!m.has(k2)){m.set(k2,[]);next.push(m.get(k2));from.push(bi);}m.get(k2).push(s);});});
    const split=next.map((nb,i)=>blocks[from[i]].length!==nb.length);
    rounds.push({blocks:blocks.map(b=>b.slice()),blockOf,sig,next:next.map(b=>b.slice()),split,changed:next.length!==blocks.length});
    if(next.length===blocks.length)break;
    blocks=next;
  }
  blocks=blocks.slice().sort((a,b)=>Math.min(...a)-Math.min(...b));
  const bOf=[];blocks.forEach((b,i)=>b.forEach(s=>bOf[s]=i));
  const mnames=blocks.map(b=>b.length===1?names[b[0]]:'{'+b.map(s=>names[s]).join(',')+'}');
  const macc=blocks.map(b=>acc[b[0]]);
  const md=blocks.map(b=>A.alpha.map((_,c)=>[bOf[delta[b[0]][c]]]));
  const minD={n:blocks.length,names:mnames,alpha:A.alpha.slice(),start:bOf[0],acc:macc,d:md,e:blocks.map(()=>[]),eps:false};
  const deadBlocks=blocks.map((b,i)=>i).filter(i=>!macc[i]&&md[i].every(t=>t[0]===i));
  return {names,acc,delta,trap,unreachable,P0,rounds,blocks,minD,count:blocks.length,deadCount:deadBlocks.length,deadBlocks};
}
/* strings of length <= n accepted, via the subset DFA: exact counts + a capped list (lexicographic by Σ order) */
function acceptedStrings(A,n,cap){
  cap=cap||300;
  const S=subset(A);if(S.error)return S;
  const D=S.D,N=D.n,m=D.alpha.length;
  const counts=[],lists=[];let listed=0,truncated=false;
  /* canAcc[r][s]: an accepting state is reachable from s in exactly r steps */
  const canAcc=[D.acc.slice()];
  for(let r=1;r<=n;r++)canAcc.push(D.d.map(row=>row.some(t=>canAcc[r-1][t[0]])));
  let ways=D.d.map((_,s)=>s===D.start?1:0);
  for(let L=0;L<=n;L++){
    counts.push(ways.reduce((a,w,s)=>a+(D.acc[s]?w:0),0));
    const nw=Array(N).fill(0);ways.forEach((w,s)=>{if(w)D.d[s].forEach(t=>nw[t[0]]+=w);});ways=nw;
    const list=[];
    (function rec(s,pre,left){
      if(truncated)return;
      if(!left){if(D.acc[s]){if(listed>=cap){truncated=true;return;}list.push(pre.slice());listed++;}return;}
      if(!canAcc[left][s])return;
      for(let c=0;c<m;c++){pre.push(D.alpha[c]);rec(D.d[s][c][0],pre,left-1);pre.pop();}
    })(D.start,[],L);
    lists.push(list);
  }
  return {counts,lists,truncated,total:counts.reduce((a,b)=>a+b,0)};
}
NETSOLVE.dfa={parseAutomaton,kindOf,closure,move,tokenize,simulate,subset,minimize,acceptedStrings};

/* ============================================================
   CORE 2: grammars, FIRST/FOLLOW, LL(1)
   G = {start, nts[], terms[], prods:[{lhs, rhs[]}]}   (ε = empty rhs)
   ============================================================ */
function parseGrammar(text){
  const lines=String(text||'').split(/\n/).map(l=>l.replace(/\/\/.*$/,'').trim()).filter(Boolean);
  if(!lines.length)return {error:'Enter at least one production, e.g. S -> a S b | ε'};
  const raw=[];let last=null;
  for(let i=0;i<lines.length;i++){
    const L=lines[i];
    if(/^\|/.test(L)){if(!last)return {error:`Line ${i+1}: “|” continues the previous rule, but there is none.`};last.alts.push(...L.slice(1).split('|'));continue;}
    const m=L.match(/^(.*?)(->|→|::=)(.*)$/);
    if(!m)return {error:`Line ${i+1}: write a rule as “A -> α | β” (no arrow found).`};
    const lhs=m[1].trim();
    if(!lhs)return {error:`Line ${i+1}: the left side is empty.`};
    if(/\s/.test(lhs))return {error:`Line ${i+1}: the left side must be one nonterminal, not “${lhs}”.`};
    if(lhs==='$'||EPS_WORDS.has(lhs))return {error:`Line ${i+1}: “${lhs}” can’t be a nonterminal.`};
    last={lhs,alts:m[3].split('|')};raw.push(last);
  }
  const nts=[];raw.forEach(r=>{if(!nts.includes(r.lhs))nts.push(r.lhs);});
  const byLen=[...nts].sort((a,b)=>b.length-a.length);
  const prods=[],warn=[];let squashed=false;
  /* spaced mode if any alternative has spaces inside it; otherwise every character is a symbol */
  const spaced=raw.some(r=>r.alts.some(a=>/\S\s+\S/.test(a.trim())));
  for(const r of raw)for(let alt of r.alts){
    alt=alt.trim();let rhs;
    if(!alt||EPS_WORDS.has(alt))rhs=[];
    else if(spaced)rhs=alt.split(/\s+/).filter(t=>!EPS_WORDS.has(t));
    else{rhs=[];let i=0;squashed=squashed||alt.length>1;
      while(i<alt.length){const nt=byLen.find(n=>alt.startsWith(n,i));if(nt){rhs.push(nt);i+=nt.length;continue;}
        let t=alt[i++];while(i<alt.length&&alt[i]==="'")t+=alt[i++];rhs.push(t);}
    }
    if(rhs.includes('$'))return {error:'“$” is the end marker; don’t use it in the grammar.'};
    if(!prods.some(p=>p.lhs===r.lhs&&p.rhs.join('\u0001')===rhs.join('\u0001')))prods.push({lhs:r.lhs,rhs});
  }
  if(prods.length>60)return {error:'Use at most 60 productions.'};
  const G={start:nts[0],nts,terms:[],prods};recomputeTerms(G);
  const odd=G.terms.filter(t=>/^[A-Z]/.test(t)&&t.length<=3);
  if(odd.length)warn.push(`${odd.join(', ')} ${odd.length>1?'have':'has'} no productions, so ${odd.length>1?'they are':'it is'} treated as terminal${odd.length>1?'s':''}.`);
  if(squashed)warn.push('No alternative has spaces, so each character is read as one symbol (nonterminal names like E\' are matched whole). Separate symbols with spaces, e.g. “F -> ( E ) | id”, for multi-letter terminals.');
  return {G,warn};
}
function recomputeTerms(G){
  const t=[];G.prods.forEach(p=>p.rhs.forEach(x=>{if(!G.nts.includes(x)&&!t.includes(x))t.push(x);}));G.terms=t;return G;
}
function cloneG(G){return {start:G.start,nts:G.nts.slice(),terms:G.terms.slice(),prods:G.prods.map(p=>({lhs:p.lhs,rhs:p.rhs.slice()}))};}
const prodStr=p=>`${p.lhs} → ${p.rhs.length?p.rhs.join(' '):EPS}`;
function grammarLines(G){return G.nts.filter(A=>G.prods.some(p=>p.lhs===A)).map(A=>`${A} → ${G.prods.filter(p=>p.lhs===A).map(p=>p.rhs.length?p.rhs.join(' '):EPS).join(' | ')}`);}
function freshName(G,A){let n=A+"'";while(G.nts.includes(n)||G.terms.includes(n))n+="'";return n;}
function setProds(G,A,list){
  let at=G.prods.findIndex(p=>p.lhs===A);if(at<0)at=G.prods.length;
  const rest=G.prods.filter(p=>p.lhs!==A);const before=G.prods.slice(0,at).filter(p=>p.lhs!==A).length;
  rest.splice(before,0,...list.map(r=>({lhs:A,rhs:r})));G.prods=rest;
}
function insertNT(G,after,B,list){
  G.nts.splice(G.nts.indexOf(after)+1,0,B);
  let at=-1;G.prods.forEach((p,i)=>{if(p.lhs===after)at=i;});
  G.prods.splice(at+1,0,...list.map(r=>({lhs:B,rhs:r})));
}
function leftCornerReach(G,from,to){
  const seen=new Set(),st=[from];
  while(st.length){const A=st.pop();for(const p of G.prods)if(p.lhs===A&&p.rhs.length&&G.nts.includes(p.rhs[0])){const B=p.rhs[0];if(B===to)return true;if(!seen.has(B)){seen.add(B);st.push(B);}}}
  return false;
}
function elimLeftRecursion(G0){
  const G=cloneG(G0),steps=[];
  const lr=G.nts.filter(A=>leftCornerReach(G,A,A));
  if(!lr.length)return {G,steps:[{text:'No left recursion: no nonterminal A has A ⇒⁺ A α.',lines:grammarLines(G)}],changed:false};
  steps.push({text:`Left-recursive nonterminals: ${lr.join(', ')}. Order the nonterminals ${G.nts.join(', ')} and process them in that order.`});
  const order=G.nts.slice();
  for(let i=0;i<order.length;i++){
    const Ai=order[i];
    for(let j=0;j<i;j++){
      const Aj=order[j];
      const mine=G.prods.filter(p=>p.lhs===Ai);
      if(!mine.some(p=>p.rhs[0]===Aj)||!leftCornerReach(G,Aj,Ai))continue;
      const ajp=G.prods.filter(p=>p.lhs===Aj).map(p=>p.rhs);
      const out=[];mine.forEach(p=>{if(p.rhs[0]===Aj)ajp.forEach(dl=>out.push(dl.concat(p.rhs.slice(1))));else out.push(p.rhs);});
      const ded=[];out.forEach(r=>{if(!ded.some(x=>x.join('\u0001')===r.join('\u0001')))ded.push(r);});
      setProds(G,Ai,ded);
      steps.push({text:`Indirect recursion: substitute the ${Aj}-productions into ${Ai} → ${Aj} γ.`,lines:grammarLines(G)});
    }
    const mine=G.prods.filter(p=>p.lhs===Ai);
    const rec=mine.filter(p=>p.rhs[0]===Ai),non=mine.filter(p=>p.rhs[0]!==Ai);
    if(!rec.length)continue;
    const cyc=rec.filter(p=>p.rhs.length===1);
    const alphas=rec.filter(p=>p.rhs.length>1).map(p=>p.rhs.slice(1));
    const B=freshName(G,Ai);
    let note='';
    if(cyc.length)note+=` The useless rule ${Ai} → ${Ai} is dropped.`;
    if(!non.length)note+=` ${Ai} has no non-recursive alternative, so it derives no terminal string.`;
    if(!alphas.length){setProds(G,Ai,non.map(p=>p.rhs));steps.push({text:`${Ai} → ${Ai} only: dropped.`+note,lines:grammarLines(G)});continue;}
    setProds(G,Ai,non.map(p=>p.rhs.concat([B])));
    insertNT(G,Ai,B,alphas.map(a=>a.concat([B])).concat([[]]));
    steps.push({text:`Immediate left recursion in ${Ai}: ${Ai} → ${Ai} α | β becomes ${Ai} → β ${B} and ${B} → α ${B} | ε, with α ∈ {${alphas.map(a=>a.join(' ')).join(', ')}} and β ∈ {${non.map(p=>p.rhs.length?p.rhs.join(' '):EPS).join(', ')||'none'}}.`+note,lines:grammarLines(G)});
    order.splice(i+1,0,B);i++;
  }
  recomputeTerms(G);
  return {G,steps,changed:true};
}
function leftFactor(G0){
  const G=cloneG(G0),steps=[];let changed=false;
  for(let guard=0;guard<60;guard++){
    let did=false;
    for(const A of G.nts.slice()){
      const alts=G.prods.filter(p=>p.lhs===A).map(p=>p.rhs);
      const groups=new Map();alts.forEach(r=>{if(!r.length)return;if(!groups.has(r[0]))groups.set(r[0],[]);groups.get(r[0]).push(r);});
      const grp=[...groups.values()].find(g=>g.length>1);if(!grp)continue;
      let L=0;while(grp.every(r=>r.length>L&&r[L]===grp[0][L]))L++;
      const pre=grp[0].slice(0,L),B=freshName(G,A);
      const out=[];let placed=false;
      alts.forEach(r=>{if(grp.includes(r)){if(!placed){out.push(pre.concat([B]));placed=true;}}else out.push(r);});
      const tails=[];grp.forEach(r=>{const t=r.slice(L);if(!tails.some(x=>x.join('\u0001')===t.join('\u0001')))tails.push(t);});
      tails.sort((x,y)=>(x.length?0:1)-(y.length?0:1)); /* ε tail listed last, as in textbooks */
      setProds(G,A,out);insertNT(G,A,B,tails);
      steps.push({text:`${A}: the alternatives ${grp.map(r=>r.join(' ')).join(' | ')} share the prefix “${pre.join(' ')}”. Factor it out: ${A} → ${pre.join(' ')} ${B}, ${B} → ${tails.map(t=>t.length?t.join(' '):EPS).join(' | ')}.`,lines:grammarLines(G)});
      did=changed=true;break;
    }
    if(!did)break;
  }
  if(!changed)steps.push({text:'No left factoring needed: no two alternatives of a nonterminal start with the same symbol.',lines:grammarLines(G)});
  recomputeTerms(G);
  return {G,steps,changed};
}
function firstSets(G){
  const isNT=new Set(G.nts),F={};G.nts.forEach(A=>F[A]=new Set());
  const fs=X=>isNT.has(X)?F[X]:new Set([X]);
  const seq=arr=>{const o=new Set();for(const X of arr){const f=fs(X);for(const t of f)if(t!==EPS)o.add(t);if(!f.has(EPS))return o;}o.add(EPS);return o;};
  const passes=[];let changed=true;
  while(changed&&passes.length<100){
    changed=false;const adds=[];
    G.prods.forEach((p,pi)=>{const f=seq(p.rhs);const nw=[...f].filter(t=>!F[p.lhs].has(t));if(nw.length){nw.forEach(t=>F[p.lhs].add(t));adds.push({A:p.lhs,p:pi,add:nw});changed=true;}});
    passes.push({adds,snap:snap(F)});
  }
  return {F,passes,seq};
}
function snap(F){const o={};for(const k in F)o[k]=[...F[k]];return o;}
function followSets(G,FI){
  const isNT=new Set(G.nts),Fo={};G.nts.forEach(A=>Fo[A]=new Set());
  Fo[G.start].add('$');
  const passes=[{adds:[{A:G.start,add:['$'],why:`${G.start} is the start symbol`}],snap:snap(Fo)}];
  let changed=true;
  while(changed&&passes.length<100){
    changed=false;const adds=[];
    G.prods.forEach(p=>p.rhs.forEach((X,i)=>{
      if(!isNT.has(X))return;
      const beta=p.rhs.slice(i+1),f=FI.seq(beta);
      const a1=[...f].filter(t=>t!==EPS&&!Fo[X].has(t));
      if(a1.length){a1.forEach(t=>Fo[X].add(t));adds.push({A:X,add:a1,why:`FIRST(${beta.join(' ')}) − {ε}, from ${prodStr(p)}`});changed=true;}
      if(f.has(EPS)&&X!==p.lhs){
        const a2=[...Fo[p.lhs]].filter(t=>!Fo[X].has(t));
        if(a2.length){a2.forEach(t=>Fo[X].add(t));adds.push({A:X,add:a2,why:beta.length?`FOLLOW(${p.lhs}), since ${beta.join(' ')} ⇒* ε in ${prodStr(p)}`:`FOLLOW(${p.lhs}), since ${X} ends ${prodStr(p)}`});changed=true;}
      }
    }));
    passes.push({adds,snap:snap(Fo)});
  }
  return {Fo,passes};
}
function ll1Table(G,FI,FO){
  const cols=G.terms.concat(['$']),M={};
  G.nts.forEach(A=>{M[A]={};cols.forEach(t=>M[A][t]=[]);});
  const why=[];
  G.prods.forEach((p,pi)=>{
    const f=FI.seq(p.rhs),viaF=[...f].filter(t=>t!==EPS),viaFo=f.has(EPS)?[...FO.Fo[p.lhs]]:[];
    viaF.forEach(t=>{if(!M[p.lhs][t].includes(pi))M[p.lhs][t].push(pi);});
    viaFo.forEach(t=>{if(!M[p.lhs][t].includes(pi))M[p.lhs][t].push(pi);});
    why.push({p:pi,first:[...f],viaF,viaFo});
  });
  const conflicts=[];G.nts.forEach(A=>cols.forEach(t=>{if(M[A][t].length>1)conflicts.push({A,t,prods:M[A][t].slice()});}));
  return {M,cols,conflicts,why,isLL1:!conflicts.length};
}
function ll1Parse(G,T,toks,maxSteps){
  maxSteps=maxSteps||400;
  const isNT=new Set(G.nts),stack=['$',G.start],inp=toks.concat(['$']);let i=0;const steps=[];
  for(let g=0;g<maxSteps;g++){
    const X=stack[stack.length-1],a=inp[i],row={stack:stack.slice(),input:inp.slice(i)};
    if(X==='$'&&a==='$'){row.action='accept';row.ok=true;steps.push(row);return {steps,accepted:true};}
    if(!isNT.has(X)){
      if(X===a){stack.pop();i++;row.action=`match ${a}`;steps.push(row);continue;}
      row.action=`error: top of stack is ${X} but the input has ${a}`;row.err=true;steps.push(row);return {steps,accepted:false};
    }
    const cell=T.M[X][a]||[];
    if(!cell.length){row.action=`error: M[${X}, ${a}] is empty`;row.err=true;steps.push(row);return {steps,accepted:false};}
    const p=G.prods[cell[0]];stack.pop();for(let k=p.rhs.length-1;k>=0;k--)stack.push(p.rhs[k]);
    row.action=`output ${prodStr(p)}`+(cell.length>1?' (conflict: first entry used)':'');row.p=cell[0];steps.push(row);
  }
  steps.push({stack:stack.slice(),input:inp.slice(i),action:`stopped after ${maxSteps} steps`,err:true});
  return {steps,accepted:false};
}
function ll1Analyze(G0,opt){
  opt=opt||{};let G=cloneG(G0);const lr=opt.leftRec?elimLeftRecursion(G):null;if(lr)G=lr.G;
  const lf=opt.leftFactor?leftFactor(G):null;if(lf)G=lf.G;
  const FI=firstSets(G),FO=followSets(G,FI),T=ll1Table(G,FI,FO);
  return {G,lr,lf,FI,FO,T};
}
/* shortest-derivation heights, used to generate random sentences */
function heights(G){
  const H={};G.nts.forEach(A=>H[A]=Infinity);let ch=true;
  while(ch){ch=false;G.prods.forEach(p=>{const h=1+Math.max(0,...p.rhs.map(x=>G.nts.includes(x)?H[x]:0));if(h<H[p.lhs]){H[p.lhs]=h;ch=true;}});}
  return H;
}
function randomSentence(G,rand,maxLen){
  rand=rand||Math.random;maxLen=maxLen||12;const H=heights(G);
  if(!isFinite(H[G.start]))return null;
  const ph=p=>1+Math.max(0,...p.rhs.map(x=>G.nts.includes(x)?H[x]:0));
  for(let tries=0;tries<20;tries++){
    let form=[G.start],steps=0,ok=true;
    while(form.some(x=>G.nts.includes(x))){
      if(++steps>200||form.length>maxLen*2){ok=false;break;}
      const i=form.findIndex(x=>G.nts.includes(x)),A=form[i];
      let ps=G.prods.filter(p=>p.lhs===A&&isFinite(ph(p)));
      if(steps>6||form.length>maxLen){const m=Math.min(...ps.map(ph));ps=ps.filter(p=>ph(p)===m);}
      const p=ps[Math.floor(rand()*ps.length)];form.splice(i,1,...p.rhs);
    }
    if(ok&&form.length<=maxLen&&(form.length||tries>8))return form;
  }
  return null;
}
NETSOLVE.ll1={parseGrammar,grammarLines,prodStr,elimLeftRecursion,leftFactor,firstSets,followSets,ll1Table,ll1Parse,analyze:ll1Analyze,randomSentence,tokenize};

/* ============================================================
   CORE 3: LR(0) items, SLR(1), CLR(1) = canonical LR(1), LALR(1)
   ============================================================ */
function augment(G){
  let S=G.start+"'";while(G.nts.includes(S)||G.terms.includes(S))S+="'";
  return {start:S,nts:[S].concat(G.nts),terms:G.terms.slice(),prods:[{lhs:S,rhs:[G.start]}].concat(G.prods.map(p=>({lhs:p.lhs,rhs:p.rhs.slice()})))};
}
function lrCollection(A,withLA,FI,max){
  max=max||400;
  const isNT=new Set(A.nts),byLhs={};A.nts.forEach(n=>byLhs[n]=[]);A.prods.forEach((p,i)=>byLhs[p.lhs].push(i));
  const ik=it=>withLA?it[0]+'.'+it[1]+'.'+it[2]:it[0]+'.'+it[1];
  function clos(kernel){
    const items=kernel.map(x=>x.slice()),seen=new Set(items.map(ik));
    for(let k=0;k<items.length;k++){
      const [p,d,la]=items[k],X=A.prods[p].rhs[d];
      if(X===undefined||!isNT.has(X))continue;
      let las=[null];
      if(withLA){const f=FI.seq(A.prods[p].rhs.slice(d+1));las=[...f].filter(t=>t!==EPS);if(f.has(EPS)&&!las.includes(la))las.push(la);}
      for(const q of byLhs[X])for(const b of las){const it=withLA?[q,0,b]:[q,0];const key=ik(it);if(!seen.has(key)){seen.add(key);items.push(it);}}
    }
    return items;
  }
  const states=[],keys=new Map(),trans=[];
  function add(kernel){
    const key=kernel.map(ik).sort().join('|');
    if(keys.has(key))return keys.get(key);
    const id=states.length;keys.set(key,id);states.push({kernel,items:clos(kernel)});trans.push({});return id;
  }
  add(withLA?[[0,0,'$']]:[[0,0]]);
  for(let i=0;i<states.length;i++){
    if(states.length>max)return {error:`More than ${max} item sets; use a smaller grammar.`};
    const syms=[];states[i].items.forEach(([p,d])=>{const X=A.prods[p].rhs[d];if(X!==undefined&&!syms.includes(X))syms.push(X);});
    for(const X of syms){
      const kernel=states[i].items.filter(([p,d])=>A.prods[p].rhs[d]===X).map(it=>withLA?[it[0],it[1]+1,it[2]]:[it[0],it[1]+1]);
      trans[i][X]=add(kernel);
    }
  }
  return {states,trans};
}
function lrTable(A,nStates,trans,completes){
  /* completes(i) -> [{p, las[]}] */
  const isNT=new Set(A.nts),cols=A.terms.concat(['$']),action=[],go=[];
  for(let i=0;i<nStates;i++){
    const row={},g={};
    const put=(t,v)=>{(row[t]=row[t]||[]);if(!row[t].includes(v))row[t].push(v);};
    for(const X in trans[i]){if(isNT.has(X))g[X]=trans[i][X];else put(X,'s'+trans[i][X]);}
    for(const c of completes(i)){if(c.p===0)put('$','acc');else c.las.forEach(t=>put(t,'r'+c.p));}
    action.push(row);go.push(g);
  }
  const conflicts=[];let sr=0,rr=0;
  action.forEach((row,i)=>cols.forEach(t=>{const cell=row[t];if(!cell||cell.length<2)return;
    const s=cell.filter(v=>v[0]==='s'||v==='acc').length,r=cell.filter(v=>v[0]==='r').length;
    const type=[];if(s&&r){sr++;type.push('shift–reduce');}if(r>1){rr++;type.push('reduce–reduce');}
    conflicts.push({state:i,t,cell:cell.slice(),type:type.join(' + ')});}));
  return {action,go,cols,conflicts,sr,rr,ok:!conflicts.length,n:nStates};
}
function lrAnalyze(G){
  const A=augment(G),FI=firstSets(A),FO=followSets(A,FI);
  const L0=lrCollection(A,false);if(L0.error)return L0;
  const L1=lrCollection(A,true,FI);if(L1.error)return L1;
  const all=A.terms.concat(['$']);
  const compl0=i=>L0.states[i].items.filter(([p,d])=>d===A.prods[p].rhs.length);
  const tLR0=lrTable(A,L0.states.length,L0.trans,i=>compl0(i).map(([p])=>({p,las:all})));
  const tSLR=lrTable(A,L0.states.length,L0.trans,i=>compl0(i).map(([p])=>({p,las:A.terms.concat(['$']).filter(t=>FO.Fo[A.prods[p].lhs].has(t))})));
  const tCLR=lrTable(A,L1.states.length,L1.trans,i=>{
    const m=new Map();L1.states[i].items.forEach(([p,d,la])=>{if(d===A.prods[p].rhs.length){if(!m.has(p))m.set(p,[]);m.get(p).push(la);}});
    return [...m].map(([p,las])=>({p,las}));});
  /* LALR: merge LR(1) states with the same core; number them like the LR(0) states */
  const coreKey=k=>[...new Set(k.map(it=>it[0]+'.'+it[1]))].sort().join('|');
  const l0key=new Map(L0.states.map((s,i)=>[s.kernel.map(it=>it[0]+'.'+it[1]).sort().join('|'),i]));
  const members=L0.states.map(()=>[]),la=L0.states.map(()=>new Map());
  L1.states.forEach((s,i)=>{const j=l0key.get(coreKey(s.kernel));members[j].push(i);
    s.items.forEach(([p,d,t])=>{const k=p+'.'+d;if(!la[j].has(k))la[j].set(k,new Set());la[j].get(k).add(t);});});
  const tLALR=lrTable(A,L0.states.length,L0.trans,i=>compl0(i).map(([p,d])=>({p,las:all.filter(t=>(la[i].get(p+'.'+d)||new Set()).has(t))})));
  const lalrCount=new Set(L1.states.map(s=>coreKey(s.kernel))).size;
  return {A,FI,FO,L0,L1,lalr:{members,la,count:lalrCount},tables:{lr0:tLR0,slr:tSLR,lalr:tLALR,clr:tCLR}};
}
function lrParse(A,T,toks,maxSteps){
  maxSteps=maxSteps||600;
  const st=[0],sy=[],inp=toks.concat(['$']);let i=0;const steps=[];
  const stackStr=()=>{let s=String(st[0]);for(let k=0;k<sy.length;k++)s+=' '+sy[k]+' '+st[k+1];return s;};
  for(let g=0;g<maxSteps;g++){
    const s=st[st.length-1],a=inp[i],cell=(T.action[s]||{})[a],row={stack:stackStr(),input:inp.slice(i)};
    if(!cell||!cell.length){row.action=`error: ACTION[${s}, ${a}] is empty`;row.err=true;steps.push(row);return {steps,accepted:false};}
    const rs=cell.filter(v=>v[0]==='r').sort((x,y)=>+x.slice(1)-+y.slice(1));
    const v=cell.find(x=>x[0]==='s')||cell.find(x=>x==='acc')||rs[0];
    const note=cell.length>1?` (conflict ${cell.join('/')}: ${v[0]==='s'?'shift preferred':'first production preferred'})`:'';
    if(v==='acc'){row.action='accept';row.ok=true;steps.push(row);return {steps,accepted:true};}
    if(v[0]==='s'){const j=+v.slice(1);st.push(j);sy.push(a);i++;row.action=`shift ${a}, go to ${j}`+note;steps.push(row);continue;}
    const p=+v.slice(1),P=A.prods[p],n=P.rhs.length;
    st.splice(st.length-n,n);sy.splice(sy.length-n,n);
    const top=st[st.length-1],j=T.go[top][P.lhs];
    if(j===undefined){row.action=`reduce by ${prodStr(P)}, but GOTO[${top}, ${P.lhs}] is empty`;row.err=true;steps.push(row);return {steps,accepted:false};}
    st.push(j);sy.push(P.lhs);row.action=`reduce by ${prodStr(P)} (r${p}); GOTO[${top}, ${P.lhs}] = ${j}`+note;row.p=p;steps.push(row);
  }
  steps.push({stack:stackStr(),input:inp.slice(i),action:`stopped after ${maxSteps} steps`,err:true});
  return {steps,accepted:false};
}
function itemStr(A,p,d){const r=A.prods[p].rhs;return `${A.prods[p].lhs} → ${r.slice(0,d).concat(['·']).concat(r.slice(d)).join(' ')}`;}
NETSOLVE.lr={augment,lrCollection,lrTable,analyze:lrAnalyze,parse:lrParse,itemStr,parseGrammar,tokenize};

/* ============================================================
   UI (browser only)
   ============================================================ */
if(typeof ANIM==='undefined'||typeof document==='undefined')return;
const E=ANIM.esc;
let UIDN=0;const uid=()=>'toc'+(++UIDN)+Math.random().toString(36).slice(2,6);
const rnd=n=>Math.floor(Math.random()*n);
function debounce(fn,ms){let t;return ()=>{clearTimeout(t);t=setTimeout(fn,ms);};}

/* step-through control: render(k) returns HTML. Works without animation (discrete steps). */
function stepper(P,host,n,render,opt){
  opt=opt||{};let k=opt.start==null?n-1:Math.max(0,Math.min(n-1,opt.start)),timer=null;
  host.innerHTML=`<div class="${P}-stp" role="group" aria-label="Step through"><button class="btn sm" data-a="first" aria-label="First step">⏮</button><button class="btn sm" data-a="prev" aria-label="Previous step">◀</button><button class="btn sm" data-a="play">▶ Play</button><button class="btn sm" data-a="next" aria-label="Next step">▶|</button><button class="btn sm" data-a="last" aria-label="Last step">⏭</button><span class="${P}-stpk" aria-live="polite"></span></div><div class="${P}-stpb"></div>`;
  const body=host.querySelector(`.${P}-stpb`),lab=host.querySelector(`.${P}-stpk`),pl=host.querySelector('[data-a=play]');
  function go(i){k=Math.max(0,Math.min(n-1,i));lab.textContent=opt.label?opt.label(k):`Step ${k+1} of ${n}`;body.innerHTML=render(k);}
  function stop(){clearInterval(timer);timer=null;pl.textContent='▶ Play';}
  pl.onclick=()=>{if(timer){stop();return;}if(k>=n-1)go(0);pl.textContent='❚❚ Pause';
    timer=setInterval(()=>{if(!host.isConnected||k>=n-1){stop();return;}go(k+1);},opt.ms||1100);};
  host.querySelector('[data-a=first]').onclick=()=>{stop();go(0);};
  host.querySelector('[data-a=prev]').onclick=()=>{stop();go(k-1);};
  host.querySelector('[data-a=next]').onclick=()=>{stop();go(k+1);};
  host.querySelector('[data-a=last]').onclick=()=>{stop();go(n-1);};
  go(k);
  return {go,get k(){return k;}};
}
function tabsHTML(P,tabs,cur){return `<div class="${P}-tabs" role="tablist">${tabs.map(([k,l])=>`<button role="tab" data-tab="${k}" aria-selected="${k===cur}">${l}</button>`).join('')}</div>`;}
function card(P,label,val,cls){return `<div class="${P}-card ${cls||''}"><span>${label}</span><b>${val}</b></div>`;}
const setOf=(A,arr)=>arr.length?'{'+arr.map(i=>E(A.names[i])).join(',')+'}':'∅';

/* ---------- automaton diagram (≤ 6 states), inline SVG ---------- */
function diagram(P,A,hi){
  const n=A.n;
  if(n>6)return `<p class="${P}-note">The diagram is drawn for up to 6 states; this automaton has ${n}. Use the table.</p>`;
  const id=uid(),R=19;
  const abbrev=A.names.some(s=>s.length>3);
  const lab=i=>abbrev?String(i+1):A.names[i];
  /* order: start first */
  const ord=[A.start].concat([...Array(n).keys()].filter(i=>i!==A.start));
  const pos=[];let W=400,H;
  if(n<=3){H=150;ord.forEach((s,k)=>pos[s]={x:n===1?200:70+k*(260/(n-1)),y:92,ang:-Math.PI/2});}
  else{H=320;const cx=200,cy=160,rx=130,ry=90;ord.forEach((s,k)=>{const a=Math.PI+2*Math.PI*k/n;pos[s]={x:cx+rx*Math.cos(a),y:cy+ry*Math.sin(a),ang:a};});}
  const edges=new Map();
  for(let s=0;s<n;s++){
    A.d[s].forEach((ts,c)=>ts.forEach(t=>{const k=s+'>'+t;if(!edges.has(k))edges.set(k,[]);edges.get(k).push(A.alpha[c]);}));
    A.e[s].forEach(t=>{const k=s+'>'+t;if(!edges.has(k))edges.set(k,[]);edges.get(k).push(EPS);});
  }
  let paths='',labels='';
  const f=v=>v.toFixed(1);
  for(const [k,ls] of edges){
    const [s,t]=k.split('>').map(Number),txt=E(ls.join(','));const a=pos[s],b=pos[t];
    if(s===t){
      let ang=a.ang;if(s===A.start)ang=n<=3?-Math.PI/2:-Math.PI*0.62;
      const u=x=>({x:a.x+Math.cos(x)*R,y:a.y+Math.sin(x)*R});
      const p1=u(ang-0.45),p2=u(ang+0.45),c1={x:a.x+Math.cos(ang-0.75)*(R+44),y:a.y+Math.sin(ang-0.75)*(R+44)},c2={x:a.x+Math.cos(ang+0.75)*(R+44),y:a.y+Math.sin(ang+0.75)*(R+44)};
      paths+=`<path class="${P}-e" d="M${f(p1.x)},${f(p1.y)} C${f(c1.x)},${f(c1.y)} ${f(c2.x)},${f(c2.y)} ${f(p2.x)},${f(p2.y)}" marker-end="url(#${id})"/>`;
      const lx=a.x+Math.cos(ang)*(R+42),ly=a.y+Math.sin(ang)*(R+42);
      labels+=`<text class="${P}-el" x="${f(lx)}" y="${f(ly+4)}">${txt}</text>`;
      continue;
    }
    const dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy)||1,nx=-dy/L,ny=dx/L;
    let off=edges.has(t+'>'+s)?24:0;
    if(n<=3){const gap=Math.abs(ord.indexOf(s)-ord.indexOf(t));if(gap>1)off=Math.max(off,48);}
    const mx=(a.x+b.x)/2,my=(a.y+b.y)/2,cx=mx+nx*off,cy=my+ny*off;
    const us=(px,py,qx,qy,r)=>{const vx=qx-px,vy=qy-py,l=Math.hypot(vx,vy)||1;return {x:px+vx/l*r,y:py+vy/l*r};};
    const p1=us(a.x,a.y,cx,cy,R),p2=us(b.x,b.y,cx,cy,R+1);
    paths+=`<path class="${P}-e" d="M${f(p1.x)},${f(p1.y)} Q${f(cx)},${f(cy)} ${f(p2.x)},${f(p2.y)}" marker-end="url(#${id})"/>`;
    const qx=.25*p1.x+.5*cx+.25*p2.x+nx*(off?9:8),qy=.25*p1.y+.5*cy+.25*p2.y+ny*(off?9:8);
    labels+=`<text class="${P}-el" x="${f(qx)}" y="${f(qy+4)}">${txt}</text>`;
  }
  const sp=pos[A.start];const sa=n<=3?Math.PI:Math.PI*0.86;
  const s1={x:sp.x+Math.cos(sa)*(R+30),y:sp.y+Math.sin(sa)*(R+30)},s2={x:sp.x+Math.cos(sa)*(R+1),y:sp.y+Math.sin(sa)*(R+1)};
  paths+=`<path class="${P}-e ${P}-st" d="M${f(s1.x)},${f(s1.y)} L${f(s2.x)},${f(s2.y)}" marker-end="url(#${id})"/>`;
  let nodes='';
  for(let s=0;s<n;s++){const p=pos[s],h=hi&&hi.includes(s);
    nodes+=`<g class="${P}-n${h?' hi':''}${A.acc[s]?' acc':''}"><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${R}"/>${A.acc[s]?`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${R-4}"/>`:''}<text x="${f(p.x)}" y="${f(p.y+4)}">${E(lab(s))}</text></g>`;}
  const legend=abbrev?`<p class="${P}-note">${A.names.map((nm,i)=>`<b>${i+1}</b> = ${E(nm)}`).join(' · ')}</p>`:'';
  return `<div class="${P}-dia"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="State diagram"><defs><marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="${P}-ah" d="M0,0 L10,5 L0,10 z"/></marker></defs>${paths}${nodes}${labels}</svg></div>${legend}`;
}
/* transition table of an automaton; hi = highlighted states */
function autoTable(P,A,hi,opt){
  opt=opt||{};const cols=A.alpha.map((a,c)=>({h:E(a),get:s=>A.d[s][c]}));
  if(A.eps&&A.e.some(x=>x.length))cols.push({h:EPS,get:s=>A.e[s]});
  const cell=ts=>!ts.length?'<span class="'+P+'-mut">—</span>':ts.length===1&&!opt.sets?E(A.names[ts[0]]):setOf(A,ts);
  return `<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th></th><th>State</th>${opt.extraHead||''}${cols.map(c=>`<th>${c.h}</th>`).join('')}</tr></thead><tbody>${
    [...Array(A.n).keys()].map(s=>`<tr class="${hi&&hi.includes(s)?'hi':''}"><td class="${P}-mk">${s===A.start?'→':''}${A.acc[s]?'*':''}</td><th>${E(A.names[s])}</th>${opt.extra?opt.extra(s):''}${cols.map(c=>`<td>${cell(c.get(s))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

/* ================= dfa playground ================= */
const DFA_DEF={alpha:'a b',eps:false,rows:[
  {name:'q0',start:true,accept:false,cells:{a:'q0,q1',b:'q0'}},
  {name:'q1',start:false,accept:false,cells:{a:'',b:'q2'}},
  {name:'q2',start:false,accept:false,cells:{a:'',b:'q3'}},
  {name:'q3',start:false,accept:true,cells:{a:'',b:''}}],str:'aabb',n:4};
function dfaRandom(){
  const nfa=Math.random()<.5,n=nfa?(Math.random()<.7?3:4):4+rnd(3),names=[...Array(n).keys()].map(i=>'q'+i),alpha=['a','b'];
  const eps=nfa&&Math.random()<.4;
  const rows=names.map((nm,i)=>({name:nm,start:i===0,accept:Math.random()<.35,cells:{}}));
  if(!rows.some(r=>r.accept))rows[n-1].accept=true;
  if(rows.every(r=>r.accept))rows[0].accept=false;
  rows.forEach((r,i)=>{alpha.forEach(a=>{
    if(!nfa){r.cells[a]=names[rnd(n)];return;}
    const k=Math.random()<.3?0:Math.random()<.6?1:2;const ts=new Set();while(ts.size<k)ts.add(names[rnd(n)]);r.cells[a]=[...ts].join(',');});
    if(eps)r.cells[EPS]=Math.random()<.3?names[(i+1+rnd(n-1))%n]:'';});
  const str=[...Array(3+rnd(4))].map(()=>alpha[rnd(2)]).join('');
  return {alpha:'a b',eps,rows,str,n:4};
}
ANIM.register('dfa',{title:'Finite automaton solver: simulate, subset construction, minimise',steps:false,
 caption:'Edit the transition table (blank or ∅ = no move, several targets = NFA). Every result updates as you type.',
 build(stage){
  const P='dfa',U=uid();let M=JSON.parse(JSON.stringify(DFA_DEF)),tab='sim',R=null;
  stage.classList.add('toc-stage');
  stage.innerHTML=`<div class="${P}-wrap">
   <div class="${P}-bar"><label class="${P}-f">Alphabet Σ<input data-k="alpha" spellcheck="false" autocomplete="off" style="width:7em"></label>
    <label class="${P}-chk"><input type="checkbox" data-k="eps"> ε-moves</label>
    <button class="btn sm" data-k="add">+ State</button><button class="btn sm" data-k="def">Default</button><button class="btn sm primary" data-k="rnd">Random example</button></div>
   <div class="${P}-scroll" data-k="ed"></div>
   <p class="${P}-note">→ start state, * accepting. A cell holds the target state, or several comma-separated targets for an NFA.</p>
   <div class="${P}-bar"><label class="${P}-f">Input string<input data-k="str" spellcheck="false" autocomplete="off" style="width:9em"></label>
    <label class="${P}-f">List accepted strings up to length<input type="number" min="0" max="10" data-k="n" style="width:4.5em"></label></div>
   <div class="${P}-msg" role="alert" data-k="msg"></div>
   <div class="${P}-sum" data-k="sum"></div>
   <div data-k="tabs"></div><div class="${P}-out" data-k="out"></div></div>`;
  const q=k=>stage.querySelector(`[data-k=${k}]`);
  const ed=q('ed'),msg=q('msg'),sum=q('sum'),out=q('out'),tabsEl=q('tabs');
  const cols=()=>String(M.alpha).split(/[\s,]+/).filter(Boolean).concat(M.eps?[EPS]:[]);
  function renderEd(){
    const cs=cols();
    ed.innerHTML=`<table class="${P}-tbl ${P}-edt"><thead><tr><th title="Start state">→</th><th title="Accepting state">*</th><th>State</th>${cs.map(c=>`<th>${E(c)}</th>`).join('')}<th></th></tr></thead><tbody>${M.rows.map((r,i)=>`<tr data-i="${i}">
      <td><input type="radio" name="${U}" data-f="start" ${r.start?'checked':''} aria-label="Start state ${E(r.name)}"></td>
      <td><input type="checkbox" data-f="accept" ${r.accept?'checked':''} aria-label="Accepting ${E(r.name)}"></td>
      <td><input class="${P}-nm" data-f="name" value="${E(r.name)}" aria-label="State name" spellcheck="false" autocomplete="off"></td>
      ${cs.map(c=>`<td><input class="${P}-cell" data-c="${E(c)}" value="${E((r.cells||{})[c]||'')}" aria-label="δ(${E(r.name)}, ${E(c)})" spellcheck="false" autocomplete="off"></td>`).join('')}
      <td><button class="${P}-x" data-f="del" aria-label="Remove state ${E(r.name)}" ${M.rows.length<2?'disabled':''}>×</button></td></tr>`).join('')}</tbody></table>`;
  }
  function loadInputs(){q('alpha').value=M.alpha;q('eps').checked=!!M.eps;q('str').value=M.str;q('n').value=M.n;renderEd();}
  const later=debounce(solve,200);
  ed.addEventListener('input',e=>{
    const tr=e.target.closest('tr[data-i]');if(!tr)return;const r=M.rows[+tr.dataset.i];const f=e.target.dataset.f;
    if(f==='start'){M.rows.forEach(x=>x.start=false);r.start=true;}
    else if(f==='accept')r.accept=e.target.checked;
    else if(f==='name')r.name=e.target.value;
    else if(e.target.dataset.c!=null){r.cells=r.cells||{};r.cells[e.target.dataset.c]=e.target.value;}
    later();
  });
  ed.addEventListener('change',e=>{if(e.target.dataset.f==='start'||e.target.dataset.f==='accept')solve();});
  /* renaming a state renames its uses in the cells */
  ed.addEventListener('focusin',e=>{if(e.target.dataset.f==='name')e.target.dataset.old=e.target.value;});
  ed.addEventListener('focusout',e=>{
    if(e.target.dataset.f!=='name')return;const o=(e.target.dataset.old||'').trim(),nw=e.target.value.trim();
    if(!o||!nw||o===nw||M.rows.filter(r=>r.name.trim()===nw).length>1)return;
    let hit=false;M.rows.forEach(r=>{for(const c in r.cells){const parts=String(r.cells[c]).split(/(\s*,\s*|\s+)/);const np=parts.map(t=>t===o?(hit=true,nw):t);r.cells[c]=np.join('');}});
    if(hit){/* update cell inputs in place so focus moving to the next field is not lost */
      ed.querySelectorAll('tr[data-i]').forEach(tr=>{const r=M.rows[+tr.dataset.i];tr.querySelectorAll('[data-c]').forEach(inp=>{const v=(r.cells||{})[inp.dataset.c]||'';if(inp.value!==v)inp.value=v;});});
      solve();}
  });
  ed.addEventListener('click',e=>{
    if(e.target.dataset.f!=='del')return;const i=+e.target.closest('tr').dataset.i;const wasStart=M.rows[i].start;
    M.rows.splice(i,1);if(wasStart&&M.rows.length)M.rows[0].start=true;renderEd();solve();
  });
  q('alpha').addEventListener('input',e=>{M.alpha=e.target.value;renderEd();later();});
  q('eps').addEventListener('change',e=>{M.eps=e.target.checked;renderEd();solve();});
  q('str').addEventListener('input',e=>{M.str=e.target.value;later();});
  q('n').addEventListener('input',e=>{M.n=e.target.value;later();});
  q('add').onclick=()=>{let k=M.rows.length;const has=nm=>M.rows.some(r=>r.name===nm);while(has('q'+k))k++;M.rows.push({name:'q'+k,start:!M.rows.length,accept:false,cells:{}});renderEd();solve();};
  q('def').onclick=()=>{M=JSON.parse(JSON.stringify(DFA_DEF));loadInputs();solve();};
  q('rnd').onclick=()=>{M=dfaRandom();loadInputs();solve();};
  tabsEl.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;renderTabs();renderOut();});
  function renderTabs(){tabsEl.innerHTML=tabsHTML(P,[['sim','Simulate'],['sub','NFA → DFA'],['min','Minimise'],['acc','Accepted strings']],tab);}
  function solve(){
    const C=NETSOLVE.dfa;const pr=C.parseAutomaton({alpha:M.alpha,eps:M.eps,rows:M.rows});
    if(pr.error){R=null;msg.textContent=pr.error;msg.hidden=false;sum.innerHTML='';out.innerHTML='';return;}
    const A=pr.A,K=C.kindOf(A),notes=[];
    const tk=C.tokenize(A.alpha,M.str);
    let n=parseInt(M.n,10);if(!(n>=0))n=0;if(n>10){n=10;notes.push('Strings are listed up to length 10.');}
    if(tk.error)notes.push('Input string: '+tk.error);
    const sim=tk.error?null:C.simulate(A,tk.toks);
    const sub=C.subset(A);if(sub.error){R=null;msg.textContent=sub.error;msg.hidden=false;return;}
    const minIn=K.det?A:sub.D,mn=C.minimize(minIn),acc=C.acceptedStrings(A,n);
    R={A,K,tk,sim,sub,mn,acc,n,minFromSub:!K.det};
    msg.textContent=notes.join(' ');msg.hidden=!notes.length;
    const dN=sub.D.n,dead=sub.dead>=0;
    sum.innerHTML=card(P,'Type',K.label)+
      (sim?card(P,`“${E(tk.toks.join('')||EPS)}”`,sim.accepted?'Accepted':'Rejected',sim.accepted?'ok':'bad'):'')+
      (K.det?card(P,'Reachable states',`${A.n-mn.unreachable.length} <small>of ${A.n}</small>`):card(P,'Subset DFA states',`${dN}${dead?` <small>(${dN-1} + ∅ trap)</small>`:''}`))+
      card(P,'Minimal DFA states',`${mn.count}${mn.deadCount?` <small>(${mn.count-mn.deadCount} without trap)</small>`:''}`,'key')+
      card(P,`Accepted, length ≤ ${n}`,acc.total);
    renderTabs();renderOut();
  }
  function renderOut(){
    if(!R){out.innerHTML='';return;}
    const {A,K}=R;
    if(tab==='sim'){
      if(!R.sim){out.innerHTML=`<p class="${P}-note">Fix the input string to simulate.</p>`;return;}
      const st=R.sim.steps,toks=R.tk.toks;
      out.innerHTML=`<p class="${P}-conv">${K.det?'DFA: one current state; a missing entry sends the machine to a dead (trap) state and the string is rejected.':'NFA: the machine is in a <b>set</b> of states'+(K.hasE?'; after every move we take the <b>ε-closure</b>':'')+'. Accept if the final set contains an accepting state.'}</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),st.length,k=>{
        const cur=st[k].set,last=k===st.length-1;
        const status=last?`<p class="${P}-verdict ${R.sim.accepted?'ok':'bad'}">“${E(toks.join('')||EPS)}” is <b>${R.sim.accepted?'accepted':'rejected'}</b>: the final ${K.det?'state':'set'} ${setOf(A,cur)} ${R.sim.accepted?'contains an':'has no'} accepting state.</p>`
          :`<p class="${P}-verdict">Read “${E(toks.slice(0,k).join('')||EPS)}”, next symbol <b>${E(toks[k])}</b>. Current: ${setOf(A,cur)}</p>`;
        const tape=`<div class="${P}-tape">${toks.length?toks.map((t,i)=>`<span class="${i<k?'done':i===k&&!last?'cur':''}">${E(t)}</span>`).join(''):`<span class="cur">${EPS}</span>`}</div>`;
        const trace=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Step</th><th>Read</th>${K.hasE?'<th>move</th><th>ε-closure = current</th>':'<th>Current</th>'}</tr></thead><tbody>${st.map((s,i)=>`<tr class="${i===k?'hi':''}${i>k?' dim':''}"><td>${i}</td><td>${s.sym==null?'start':E(s.sym)}</td>${K.hasE?`<td>${s.moved?setOf(A,s.moved):`{${E(A.names[A.start])}}`}</td>`:''}<td>${setOf(A,s.set)}</td></tr>`).join('')}</tbody></table></div>`;
        return tape+status+`<div class="${P}-two"><div>${diagram(P,A,cur)}</div><div>${autoTable(P,A,cur)}</div></div>`+trace;
      },{label:k=>`Symbol ${k} of ${st.length-1}`});
      return;
    }
    if(tab==='sub'){
      const S=R.sub,D=S.D;
      const detail=k=>{const lines=[];
        if(k===0)lines.push(`Start state A = ${K.hasE?`ε-closure({${E(A.names[A.start])}})`:`{${E(A.names[A.start])}}`} = ${setOf(A,S.sets[0])}`);
        S.rows[k].forEach((c,j)=>lines.push(`${K.hasE?`ε-closure(move(${D.names[k]}, ${E(A.alpha[j])})) = ε-closure(${setOf(A,c.moved)})`:`δ(${D.names[k]}, ${E(A.alpha[j])}) = ${setOf(A,c.moved)}`} = ${setOf(A,c.cl)} = <b>${D.names[c.to]}</b>${c.isNew?` <span class="${P}-tag new">new</span>`:''}${!c.cl.length?` <span class="${P}-tag">trap</span>`:''}`));
        return `<ul class="${P}-work">${lines.map(l=>`<li>${l}</li>`).join('')}</ul>`;};
      out.innerHTML=`<p class="${P}-conv">${K.det?'The input is already a DFA; the construction just renames its reachable states (shown for practice). ':''}Each DFA state is a set of NFA states. Process states in the order they are discovered (A, B, C, …). ∅ is kept as a trap state when it appears.</p><div data-k="stp"></div><h4 class="${P}-h">Resulting DFA: ${D.n} state${D.n>1?'s':''}${S.dead>=0?` (${D.n-1} if the ∅ trap state is not counted)`:''}</h4><div class="${P}-two"><div>${diagram(P,D)}</div><div></div></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),S.rows.length,k=>{
        const rows=S.rows.slice(0,k+1);
        const tbl=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th></th><th>DFA</th><th>NFA states</th>${A.alpha.map(a=>`<th>${E(a)}</th>`).join('')}</tr></thead><tbody>${rows.map((r,i)=>`<tr class="${i===k?'hi':''}"><td class="${P}-mk">${i===0?'→':''}${D.acc[i]?'*':''}</td><th>${D.names[i]}</th><td>${setOf(A,S.sets[i])}</td>${r.map(c=>`<td>${D.names[c.to]}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
        return detail(k)+tbl+(k===S.rows.length-1?`<p class="${P}-note">Accepting DFA states (*) are those containing an NFA accepting state.</p>`:'');
      },{label:k=>`DFA state ${D.names[k]} (${k+1} of ${S.rows.length})`});
      return;
    }
    if(tab==='min'){
      const mn=R.mn,src=R.minFromSub?R.sub.D:A,nm=mn.names;
      const blk=(bs,split)=>bs.map((b,i)=>`<span class="${P}-blk${split&&split[i]?' new':''}">{${b.map(s=>E(nm[s])).join(', ')}}</span>`).join(' ');
      const steps=[];
      steps.push(()=>{const l=[];
        if(R.minFromSub)l.push('The input is an NFA, so minimise the subset-construction DFA (states A, B, …).');
        l.push(mn.unreachable.length?`Remove unreachable states: <b>${mn.unreachable.map(E).join(', ')}</b>.`:'All states are reachable from the start state.');
        l.push(mn.trap>=0?`Some moves are missing, so add a trap state <b>${E(nm[mn.trap])}</b> (non-accepting, loops on every symbol).`:'Every state has a move on every symbol (complete DFA).');
        l.push(`P<sub>0</sub> splits non-accepting from accepting states: ${blk(mn.P0)}`);
        return `<ul class="${P}-work">${l.map(x=>`<li>${x}</li>`).join('')}</ul>`+autoTable(P,src,[]);});
      mn.rounds.forEach((r,ri)=>steps.push(()=>{
        const bl=s=>r.blockOf[s]+1;
        const tbl=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>State</th><th>Group in P<sub>${ri}</sub></th>${src.alpha.map(a=>`<th>on ${E(a)} → group</th>`).join('')}</tr></thead><tbody>${r.blocks.map((b,bi)=>b.map((s,j)=>`<tr class="${j===0?'grp':''}"><th>${E(nm[s])}</th><td>${bi+1}</td>${r.sig[s].map((g,c)=>`<td>${E(nm[mn.delta[s][c]])} (${g+1})</td>`).join('')}</tr>`).join('')).join('')}</tbody></table></div>`;
        return `<p class="${P}-verdict">Round ${ri+1}: two states stay together only if, on every symbol, they go to the same group of P<sub>${ri}</sub>. Groups are numbered 1, 2, … in the order ${blk(r.blocks)}.</p>`+tbl+
          `<p class="${P}-verdict">${r.changed?`P<sub>${ri+1}</sub> = ${blk(r.next,r.split)} (split groups highlighted)`:`P<sub>${ri+1}</sub> = P<sub>${ri}</sub>: no group splits, so stop.`}</p>`;}));
      steps.push(()=>{const D=mn.minD;
        return `<p class="${P}-verdict ok">Minimal DFA: <b>${mn.count} state${mn.count>1?'s':''}</b>${mn.deadCount?` (${mn.count-mn.deadCount} if the trap state is not drawn)`:''}. Each final group becomes one state.</p><div class="${P}-two"><div>${diagram(P,D)}</div><div>${autoTable(P,D,[])}</div></div>`;});
      out.innerHTML=`<p class="${P}-conv">Partition refinement (Moore / table-filling equivalent): start from {non-accepting}, {accepting} and split groups until stable. Unreachable states are removed first; missing moves go to a trap state, which is counted.</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),steps.length,k=>steps[k](),{label:k=>k===0?'Set-up':k===steps.length-1?'Result':`Round ${k} of ${mn.rounds.length}`});
      return;
    }
    if(tab==='acc'){
      const a=R.acc;
      out.innerHTML=`<p class="${P}-conv">All strings of length 0 to ${R.n} accepted by the automaton, in order of length, then alphabetical by Σ order. Counts are exact; the list shows at most 300 strings.</p><div class="${P}-scroll"><table class="${P}-tbl ${P}-acc"><thead><tr><th>Length</th><th>Count</th><th>Strings</th></tr></thead><tbody>${a.counts.map((c,L)=>`<tr><td>${L}</td><td>${c}</td><td class="${P}-strs">${a.lists[L].map(s=>`<code>${E(s.join('')||EPS)}</code>`).join(' ')}${a.lists[L].length<c?` <span class="${P}-mut">… ${c-a.lists[L].length} more</span>`:''}</td></tr>`).join('')}</tbody></table></div><p class="${P}-verdict ok">Total accepted strings of length ≤ ${R.n}: <b>${a.total}</b></p>`;
    }
  }
  loadInputs();solve();
 }});

/* ================= shared grammar UI bits ================= */
function symSet(set,order){const o=order.concat(['$',EPS]);return '{ '+[...set].sort((a,b)=>o.indexOf(a)-o.indexOf(b)).map(E).join(', ')+' }';}
function grammarPre(P,G,numbered){return `<pre class="${P}-g">${G.prods.map((p,i)=>(numbered?`(${numbered==='from0'?i:i+1}) `:'')+E(prodStr(p))).join('\n')}</pre>`;}
const LL1_POOL=[
  ['E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id',true,false],
  ["E -> T E'\nE' -> + T E' | ε\nT -> F T'\nT' -> * F T' | ε\nF -> ( E ) | id",false,false],
  ['S -> i E t S | i E t S e S | a\nE -> b',false,true],
  ['S -> A a | b\nA -> A c | S d | ε',true,false],
  ['S -> a S b S | b S a S | ε',false,false],
  ['S -> ( L ) | a\nL -> L , S | S',true,false],
  ['S -> A B\nA -> a A | ε\nB -> b B | c',false,false],
  ['S -> a B D h\nB -> c C\nC -> b C | ε\nD -> E F\nE -> g | ε\nF -> f | ε',false,false],
  ['bexpr -> bexpr or bterm | bterm\nbterm -> bterm and bfactor | bfactor\nbfactor -> not bfactor | ( bexpr ) | true | false',true,false],
  ['S -> a b c | a b d | a e\nA -> S f | g',false,true],
];

/* ================= ll1 playground ================= */
ANIM.register('ll1',{title:'LL(1) solver: FIRST, FOLLOW, parsing table and parse trace',steps:false,
 caption:'One rule per line: A -> α | β. Separate symbols with spaces; write ε (or eps, #) for the empty string. The first rule’s left side is the start symbol.',
 build(stage){
  const P='ll1';let tab='g',R=null;
  stage.classList.add('toc-stage');
  stage.innerHTML=`<div class="${P}-wrap">
   <label class="${P}-f ${P}-ta">Grammar<textarea data-k="g" rows="5" spellcheck="false" autocomplete="off"></textarea></label>
   <div class="${P}-bar"><label class="${P}-chk"><input type="checkbox" data-k="lr"> Eliminate left recursion</label><label class="${P}-chk"><input type="checkbox" data-k="lf"> Left factor</label></div>
   <div class="${P}-bar"><label class="${P}-f">Input to parse<input data-k="s" spellcheck="false" autocomplete="off" style="width:12em"></label>
    <button class="btn sm" data-k="def">Default</button><button class="btn sm primary" data-k="rnd">Random example</button></div>
   <div class="${P}-msg" role="alert" data-k="msg"></div><div class="${P}-sum" data-k="sum"></div>
   <div data-k="tabs"></div><div class="${P}-out" data-k="out"></div></div>`;
  const q=k=>stage.querySelector(`[data-k=${k}]`);const msg=q('msg'),sum=q('sum'),out=q('out'),tabsEl=q('tabs');
  function load(g,lr,lf,s){q('g').value=g;q('lr').checked=lr;q('lf').checked=lf;q('s').value=s;}
  const later=debounce(solve,250);
  ['g','s'].forEach(k=>q(k).addEventListener('input',later));
  ['lr','lf'].forEach(k=>q(k).addEventListener('change',solve));
  q('def').onclick=()=>{load(LL1_POOL[0][0],true,true,'id + id * id');solve();};
  q('rnd').onclick=()=>{
    const cur=q('g').value;let e;do{e=LL1_POOL[rnd(LL1_POOL.length)];}while(e[0]===cur&&LL1_POOL.length>1);
    const pg=NETSOLVE.ll1.parseGrammar(e[0]);const s=pg.G?NETSOLVE.ll1.randomSentence(pg.G):null;
    load(e[0],e[1]||Math.random()<.5,e[2]||Math.random()<.5,s?s.join(' '):'');solve();};
  tabsEl.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;renderTabs();renderOut();});
  function renderTabs(){tabsEl.innerHTML=tabsHTML(P,[['g','Grammar'],['ff','FIRST & FOLLOW'],['tbl','LL(1) table'],['parse','Parse']],tab);}
  function solve(){
    const C=NETSOLVE.ll1,pg=C.parseGrammar(q('g').value);
    if(pg.error){R=null;msg.textContent=pg.error;msg.hidden=false;sum.innerHTML='';out.innerHTML='';tabsEl.innerHTML='';return;}
    const an=C.analyze(pg.G,{leftRec:q('lr').checked,leftFactor:q('lf').checked});
    const notes=pg.warn.slice();
    const tk=C.tokenize(an.G.terms,q('s').value.replace(/\s*\$\s*$/,''));
    if(tk.error)notes.push('Input: '+tk.error);
    const pr=tk.error?null:C.ll1Parse(an.G,an.T,tk.toks);
    const leftRecLeft=an.G.nts.filter(A=>leftCornerReach(an.G,A,A));
    if(leftRecLeft.length)notes.push(`The grammar is still left-recursive (${leftRecLeft.join(', ')}), so it can’t be LL(1). Tick “Eliminate left recursion”.`);
    R={pg,an,tk,pr};msg.textContent=notes.join(' ');msg.hidden=!notes.length;
    const nc=an.T.conflicts.length;
    sum.innerHTML=card(P,'LL(1)?',an.T.isLL1?'Yes':'No',an.T.isLL1?'ok':'bad')+card(P,'Conflicting cells',nc,nc?'bad':'')+
      card(P,'Table size',`${an.G.nts.length} × ${an.T.cols.length}`)+
      (pr?card(P,'Parse of input',pr.accepted?'Accepted':'Error',pr.accepted?'ok':'bad'):'');
    renderTabs();renderOut();
  }
  function renderOut(){
    if(!R){out.innerHTML='';return;}
    const {an,pg}=R,G=an.G,order=G.terms;
    if(tab==='g'){
      let h=`<h4 class="${P}-h">Grammar as entered</h4><pre class="${P}-g">${grammarLines(pg.G).map(E).join('\n')}</pre>`;
      const block=(title,res)=>res?`<h4 class="${P}-h">${title}</h4><ol class="${P}-work">${res.steps.map(s=>`<li>${E(s.text)}${s.lines?`<pre class="${P}-g">${s.lines.map(E).join('\n')}</pre>`:''}</li>`).join('')}</ol>`:'';
      h+=block('Eliminating left recursion',an.lr)+block('Left factoring',an.lf);
      if(!an.lr&&!an.lf)h+=`<p class="${P}-note">No transformation selected: the grammar is used as entered.</p>`;
      h+=`<h4 class="${P}-h">Grammar used for LL(1): productions numbered</h4>`+grammarPre(P,G,true)+
        `<p class="${P}-note">Nonterminals: ${G.nts.map(E).join(', ')} · Terminals: ${order.map(E).join(', ')} · Start: ${E(G.start)}</p>`;
      out.innerHTML=h;return;
    }
    if(tab==='ff'){
      const fp=an.FI.passes,op=an.FO.passes,n=fp.length+op.length;
      out.innerHTML=`<p class="${P}-conv">Both sets are computed by passes over the productions until a pass adds nothing (fixed point). FIRST(X Y…) takes FIRST(X) − ε, and moves on to Y only if X ⇒* ε. $ is the end marker: FOLLOW(start) ∋ $. FOLLOW never contains ε.</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),n,k=>{
        const inF=k<fp.length,fs=inF?fp[k].snap:fp[fp.length-1].snap,fo=inF?null:op[k-fp.length].snap;
        const adds=inF?fp[k].adds:op[k-fp.length].adds;
        const addTxt=adds.length?`<ul class="${P}-work">${adds.map(a=>inF?`<li>${E(a.A)} → ${E(G.prods[a.p].rhs.join(' ')||EPS)} adds ${symSet(a.add,order)} to FIRST(${E(a.A)})</li>`:`<li>FOLLOW(${E(a.A)}) += ${symSet(a.add,order)} : ${E(a.why)}</li>`).join('')}</ul>`:`<p class="${P}-verdict">Nothing changed in this pass, so ${inF?'FIRST':'FOLLOW'} is complete.</p>`;
        const newF=new Set(inF?adds.map(a=>a.A):[]),newO=new Set(!inF?adds.map(a=>a.A):[]);
        const tbl=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>Nonterminal</th><th>FIRST</th><th>FOLLOW</th></tr></thead><tbody>${G.nts.map(A=>`<tr><th>${E(A)}</th><td class="${newF.has(A)?'new':''}">${symSet(fs[A],order)}</td><td class="${newO.has(A)?'new':''}">${fo?symSet(fo[A],order):'<span class="'+P+'-mut">later</span>'}</td></tr>`).join('')}</tbody></table></div>`;
        return `<p class="${P}-verdict"><b>${inF?`FIRST, pass ${k+1}`:k===fp.length?'FOLLOW, rule 1':`FOLLOW, pass ${k-fp.length}`}</b></p>`+addTxt+tbl;
      },{label:k=>k<fp.length?`FIRST pass ${k+1}/${fp.length}`:`FOLLOW step ${k-fp.length+1}/${op.length}`});
      return;
    }
    if(tab==='tbl'){
      const T=an.T,conf=new Set(T.conflicts.map(c=>c.A+'\u0001'+c.t));
      const tbl=`<div class="${P}-scroll"><table class="${P}-tbl ${P}-pt"><thead><tr><th>M</th>${T.cols.map(t=>`<th>${E(t)}</th>`).join('')}</tr></thead><tbody>${G.nts.map(A=>`<tr><th>${E(A)}</th>${T.cols.map(t=>{const c=T.M[A][t];return `<td class="${conf.has(A+'\u0001'+t)?'bad':''}">${c.map(pi=>E(prodStr(G.prods[pi]))).join('<br>')}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
      const why=`<div class="${P}-scroll"><table class="${P}-tbl"><thead><tr><th>#</th><th>Production</th><th>FIRST(α)</th><th>Placed under</th></tr></thead><tbody>${T.why.map(w=>`<tr><td>${w.p+1}</td><td>${E(prodStr(G.prods[w.p]))}</td><td>${symSet(w.first,order)}</td><td>${w.viaF.map(E).join(', ')}${w.viaFo.length?`${w.viaF.length?', ':''}${w.viaFo.map(E).join(', ')} <span class="${P}-mut">(FOLLOW(${E(G.prods[w.p].lhs)}), as ε ∈ FIRST(α))</span>`:''}</td></tr>`).join('')}</tbody></table></div>`;
      const cl=T.conflicts.length?`<p class="${P}-verdict bad"><b>Not LL(1)</b>: ${T.conflicts.length} cell${T.conflicts.length>1?'s have':' has'} more than one production: ${T.conflicts.map(c=>`M[${E(c.A)}, ${E(c.t)}] = {${c.prods.map(pi=>E(prodStr(G.prods[pi]))).join(' ; ')}}`).join(' · ')}.</p>`:`<p class="${P}-verdict ok"><b>LL(1)</b>: every cell has at most one production.</p>`;
      out.innerHTML=`<p class="${P}-conv">For each A → α: put it in M[A, a] for every terminal a ∈ FIRST(α); if ε ∈ FIRST(α), also in M[A, b] for every b ∈ FOLLOW(A) (including $). Blank cells are errors.</p>`+cl+tbl+`<h4 class="${P}-h">Why each entry is there</h4>`+why;
      return;
    }
    if(tab==='parse'){
      if(!R.pr){out.innerHTML=`<p class="${P}-note">Enter a valid input string to parse.</p>`;return;}
      const st=R.pr.steps;
      out.innerHTML=`<p class="${P}-conv">Predictive parsing: stack starts as $ ${E(G.start)} (top on the right). If the top is a terminal it must match the input; if it is a nonterminal A, replace it by the production in M[A, a], pushed right-to-left.${an.T.isLL1?'':' The table has conflicts, so the first entry of a cell is used.'}</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),st.length,k=>`<div class="${P}-scroll"><table class="${P}-tbl ${P}-trace"><thead><tr><th>#</th><th>Stack</th><th>Input</th><th>Action</th></tr></thead><tbody>${st.map((r,i)=>`<tr class="${i===k?'hi':''}${i>k?' dim':''}${r.err?' bad':''}${r.ok?' ok':''}"><td>${i+1}</td><td class="${P}-stk">${r.stack.map(E).join(' ')}</td><td class="${P}-inp">${r.input.map(E).join(' ')}</td><td>${E(r.action)}</td></tr>`).join('')}</tbody></table></div>`+
        (k===st.length-1?`<p class="${P}-verdict ${R.pr.accepted?'ok':'bad'}">${R.pr.accepted?'Accepted: the stack and the input both reached $.':'Rejected: '+E(st[st.length-1].action)}</p>`:''),{label:k=>`Move ${k+1} of ${st.length}`,ms:800});
    }
  }
  load(LL1_POOL[0][0],true,true,'id + id * id');solve();
 }});

/* ================= lr playground ================= */
const LR_POOL=[
  ['E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id','id * id + id'],
  ['S -> C C\nC -> c C | d','c d d'],
  ['S -> L = R | R\nL -> * R | id\nR -> L','* id = id'],
  ['S -> A a | b A c | d c | b d a\nA -> d','b d c'],
  ['S -> A a | b A c | B c | b B a\nA -> d\nB -> d','b d a'],
  ['E -> E + E | E * E | ( E ) | id','id + id * id'],
  ['S -> ( L ) | x\nL -> S | L , S','( x , ( x ) )'],
  ['S -> a A d | b B d | a B e | b A e\nA -> c\nB -> c','a c e'],
  ['S -> A B\nA -> a A | ε\nB -> b B | b','a a b'],
];
const METHODS=[['lr0','LR(0)'],['slr','SLR(1)'],['lalr','LALR(1)'],['clr','CLR(1)']];
ANIM.register('lr',{title:'LR solver: item sets, SLR(1) / LALR(1) / CLR(1) tables, conflicts',steps:false,
 caption:'One rule per line: A -> α | β, symbols separated by spaces, ε for empty. The grammar is augmented with S′ → S; productions are numbered from 1 (rN = reduce by production N).',
 build(stage){
  const P='lr';let tab='items',R=null;
  stage.classList.add('toc-stage');
  stage.innerHTML=`<div class="${P}-wrap">
   <label class="${P}-f ${P}-ta">Grammar<textarea data-k="g" rows="4" spellcheck="false" autocomplete="off"></textarea></label>
   <div class="${P}-bar"><label class="${P}-f">Method<select data-k="m">${METHODS.map(([k,l])=>`<option value="${k}"${k==='slr'?' selected':''}>${l}</option>`).join('')}</select></label>
    <label class="${P}-f">Input to parse<input data-k="s" spellcheck="false" autocomplete="off" style="width:11em"></label>
    <button class="btn sm" data-k="def">Default</button><button class="btn sm primary" data-k="rnd">Random example</button></div>
   <div class="${P}-msg" role="alert" data-k="msg"></div><div data-k="sum"></div>
   <div data-k="tabs"></div><div class="${P}-out" data-k="out"></div></div>`;
  const q=k=>stage.querySelector(`[data-k=${k}]`);const msg=q('msg'),sum=q('sum'),out=q('out'),tabsEl=q('tabs');
  const later=debounce(solve,300);
  q('g').addEventListener('input',later);q('s').addEventListener('input',later);q('m').addEventListener('change',solve);
  q('def').onclick=()=>{q('g').value=LR_POOL[0][0];q('s').value=LR_POOL[0][1];q('m').value='slr';solve();};
  q('rnd').onclick=()=>{const cur=q('g').value;let e;do{e=LR_POOL[rnd(LR_POOL.length)];}while(e[0]===cur);
    q('g').value=e[0];const pg=NETSOLVE.ll1.parseGrammar(e[0]);const s=pg.G&&Math.random()<.6?NETSOLVE.ll1.randomSentence(pg.G):null;q('s').value=s?s.join(' '):e[1];solve();};
  tabsEl.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;renderTabs();renderOut();});
  function renderTabs(){tabsEl.innerHTML=tabsHTML(P,[['items','Item sets'],['tbl','Parsing table'],['parse','Parse trace']],tab);}
  function solve(){
    const pg=NETSOLVE.ll1.parseGrammar(q('g').value);
    if(pg.error){R=null;msg.textContent=pg.error;msg.hidden=false;sum.innerHTML='';out.innerHTML='';tabsEl.innerHTML='';return;}
    const an=NETSOLVE.lr.analyze(pg.G);
    if(an.error){R=null;msg.textContent=an.error;msg.hidden=false;sum.innerHTML='';out.innerHTML='';return;}
    const m=q('m').value,T=an.tables[m],notes=pg.warn.slice();
    const tk=NETSOLVE.lr.tokenize(pg.G.terms,q('s').value.replace(/\s*\$\s*$/,''));
    if(tk.error)notes.push('Input: '+tk.error);
    const pr=tk.error?null:NETSOLVE.lr.parse(an.A,T,tk.toks);
    R={pg,an,m,T,tk,pr};msg.textContent=notes.join(' ');msg.hidden=!notes.length;
    const cnt={lr0:an.L0.states.length,slr:an.L0.states.length,lalr:an.lalr.count,clr:an.L1.states.length};
    sum.innerHTML=`<div class="${P}-scroll"><table class="${P}-tbl ${P}-cmp"><thead><tr><th>Method</th><th>States</th><th>S/R conflicts</th><th>R/R conflicts</th><th>Grammar is</th></tr></thead><tbody>${METHODS.map(([k,l])=>{const t=an.tables[k];return `<tr class="${k===m?'hi':''}"><th>${l}</th><td>${cnt[k]}</td><td class="${t.sr?'bad':''}">${t.sr}</td><td class="${t.rr?'bad':''}">${t.rr}</td><td class="${t.ok?'ok':'bad'}">${t.ok?l:'not '+l}</td></tr>`;}).join('')}</tbody></table></div>`+
      `<div class="${P}-sum">${card(P,'LR(0) item sets',an.L0.states.length,'key')}${card(P,'LR(1) item sets',an.L1.states.length)}${card(P,METHODS.find(x=>x[0]===m)[1]+' conflicts',T.conflicts.length,T.conflicts.length?'bad':'ok')}${pr?card(P,'Parse of input',pr.accepted?'Accepted':'Error',pr.accepted?'ok':'bad'):''}</div>`;
    renderTabs();renderOut();
  }
  function itemsFor(i){
    const {an,m}=R,A=an.A;
    if(m==='clr'){
      const s=an.L1.states[i],grp=new Map();s.items.forEach(([p,d,la])=>{const k=p+'.'+d;if(!grp.has(k))grp.set(k,{p,d,las:[]});grp.get(k).las.push(la);});
      return [...grp.values()].map(g=>({t:itemStr(A,g.p,g.d)+' , '+g.las.join(' / '),done:g.d===A.prods[g.p].rhs.length,k:s.kernel.some(x=>x[0]===g.p&&x[1]===g.d)}));
    }
    const s=an.L0.states[i];
    return s.items.map(([p,d])=>{let t=itemStr(A,p,d);if(m==='lalr'){const la=[...(an.lalr.la[i].get(p+'.'+d)||[])];const o=A.terms.concat(['$']);la.sort((x,y)=>o.indexOf(x)-o.indexOf(y));t+=' , '+la.join(' / ');}
      return {t,done:d===A.prods[p].rhs.length,k:s.kernel.some(x=>x[0]===p&&x[1]===d)};});
  }
  function renderOut(){
    if(!R){out.innerHTML='';return;}
    const {an,m,T}=R,A=an.A,isNT=new Set(A.nts);
    const coll=m==='clr'?an.L1:an.L0,n=coll.states.length;
    if(tab==='items'){
      const conv={lr0:'LR(0) items (canonical collection). The same sets are used for SLR(1).',slr:'LR(0) items (canonical collection); SLR(1) uses them with FOLLOW sets for reduces.',
        lalr:'LALR(1): LR(1) sets with the same core (items without lookaheads) are merged; they are numbered like the LR(0) sets. Lookaheads follow the comma.',
        clr:'Canonical LR(1) items [A → α · β , a]. Closure adds [B → · γ , b] for every b ∈ FIRST(β a).'}[m];
      const cardH=i=>{const its=itemsFor(i),tr=coll.trans[i];
        const mem=m==='lalr'&&an.lalr.members[i].length>1?`<span class="${P}-mut"> merged LR(1) ${an.lalr.members[i].join(', ')}</span>`:'';
        return `<div class="${P}-set" data-i="${i}"><div class="${P}-sh">I<sub>${i}</sub>${mem}</div><ul>${its.map(x=>`<li class="${x.k?'k':''}${x.done?' done':''}">${E(x.t)}</li>`).join('')}</ul>${Object.keys(tr).length?`<div class="${P}-go">${Object.entries(tr).map(([X,j])=>`${E(X)}: I<sub>${j}</sub>`).join(' · ')}</div>`:''}</div>`;};
      out.innerHTML=`<p class="${P}-conv">${conv} Kernel items are in bold, closure items in grey; complete items (dot at the end, a reduce) are marked ✓. Sets are created in breadth-first order, taking the symbols after the dot in item order.</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),n,k=>{
        const via=[];for(let i=0;i<n;i++)for(const X in coll.trans[i])if(coll.trans[i][X]===k&&i<k)via.push(`goto(I${i}, ${X})`);
        const head=k===0?`<p class="${P}-verdict">I<sub>0</sub> = closure({ ${E(itemStr(A,0,0))}${m==='lr0'||m==='slr'?'':' , $'} })</p>`:`<p class="${P}-verdict">I<sub>${k}</sub> = ${E(via[0]||'')}${via.length>1?` <span class="${P}-mut">(also ${E(via.slice(1).join(', '))})</span>`:''}</p>`;
        return head+`<div class="${P}-sets">${[...Array(k+1).keys()].map(i=>cardH(i).replace(`class="${P}-set"`,`class="${P}-set${i===k?' hi':''}"`)).join('')}</div>`+(k===n-1?`<p class="${P}-verdict ok"><b>${n}</b> ${m==='clr'?'LR(1)':m==='lalr'?'LALR(1)':'LR(0)'} item sets.</p>`:'');
      },{label:k=>`I${k} (${k+1} of ${n})`,ms:900});
      return;
    }
    if(tab==='tbl'){
      const conf=new Set(T.conflicts.map(c=>c.state+'\u0001'+c.t));
      const nts=A.nts.slice(1);
      const tbl=`<div class="${P}-scroll"><table class="${P}-tbl ${P}-pt"><thead><tr><th rowspan="2">State</th><th colspan="${T.cols.length}">ACTION</th><th colspan="${nts.length}">GOTO</th></tr><tr>${T.cols.map(t=>`<th>${E(t)}</th>`).join('')}${nts.map(X=>`<th>${E(X)}</th>`).join('')}</tr></thead><tbody>${T.action.map((row,i)=>`<tr><th>${i}</th>${T.cols.map(t=>`<td class="${conf.has(i+'\u0001'+t)?'bad':''}">${(row[t]||[]).join(' / ')}</td>`).join('')}${nts.map(X=>`<td class="${P}-gt">${T.go[i][X]!==undefined?T.go[i][X]:''}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
      const conv={lr0:'LR(0): a complete item A → α · reduces on <b>every</b> terminal and $.',slr:'SLR(1): a complete item A → α · reduces only on terminals in <b>FOLLOW(A)</b>.',lalr:'LALR(1): reduce on the merged lookaheads of the item.',clr:'CLR(1): reduce only on the item’s own lookahead.'}[m];
      const fo=m==='slr'||m==='lr0'?`<h4 class="${P}-h">FOLLOW sets</h4><p class="${P}-note">${A.nts.slice(1).map(X=>`FOLLOW(${E(X)}) = ${symSet(an.FO.Fo[X],A.terms)}`).join(' · ')}</p>`:'';
      const cl=T.conflicts.length?`<p class="${P}-verdict bad"><b>${T.conflicts.length} conflict${T.conflicts.length>1?'s':''}</b> (${T.sr} shift–reduce, ${T.rr} reduce–reduce), so the grammar is not ${METHODS.find(x=>x[0]===m)[1]}:</p><ul class="${P}-work">${T.conflicts.map(c=>`<li>State ${c.state} on <code>${E(c.t)}</code>: ${c.cell.map(v=>v[0]==='r'?`${v} (${E(prodStr(A.prods[+v.slice(1)]))})`:v).join(' vs ')}: ${c.type}</li>`).join('')}</ul>`:`<p class="${P}-verdict ok">No conflicts: the grammar is ${METHODS.find(x=>x[0]===m)[1]}.</p>`;
      out.innerHTML=`<p class="${P}-conv">sN = shift and go to state N; rN = reduce by production N; acc = accept on $ in the state with S′ → S ·. ${conv}</p>`+cl+`<h4 class="${P}-h">Productions</h4>`+grammarPre(P,A,'from0')+tbl+fo;
      return;
    }
    if(tab==='parse'){
      if(!R.pr){out.innerHTML=`<p class="${P}-note">Enter a valid input string to parse.</p>`;return;}
      const st=R.pr.steps;
      out.innerHTML=`<p class="${P}-conv">The stack holds states and grammar symbols (bottom on the left). Shift pushes the token and the new state; reduce by A → α pops 2|α| entries and pushes A and GOTO[top, A].${T.ok?'':' This table has conflicts; the trace resolves them as YACC does: shift over reduce, and the earlier production in a reduce–reduce conflict.'}</p><div data-k="stp"></div>`;
      stepper(P,out.querySelector('[data-k=stp]'),st.length,k=>`<div class="${P}-scroll"><table class="${P}-tbl ${P}-trace"><thead><tr><th>#</th><th>Stack</th><th>Input</th><th>Action</th></tr></thead><tbody>${st.map((r,i)=>`<tr class="${i===k?'hi':''}${i>k?' dim':''}${r.err?' bad':''}${r.ok?' ok':''}"><td>${i+1}</td><td class="${P}-stk">${E(r.stack)}</td><td class="${P}-inp">${r.input.map(E).join(' ')}</td><td>${E(r.action)}</td></tr>`).join('')}</tbody></table></div>`+
        (k===st.length-1?`<p class="${P}-verdict ${R.pr.accepted?'ok':'bad'}">${R.pr.accepted?'Accepted.':'Rejected: '+E(st[st.length-1].action)}</p>`:''),{label:k=>`Move ${k+1} of ${st.length}`,ms:800});
    }
  }
  q('g').value=LR_POOL[0][0];q('s').value=LR_POOL[0][1];solve();
 }});
})();

/* ================= Academy slot mounting ================= */
const EXPECTED=["kmap", "amat", "bptree", "truthtable", "lpp", "transport", "assign", "ieee754", "pipeline", "cachemap", "raster", "transform2d", "fdtool", "serial", "cpusched", "banker", "pagerepl", "disksched", "seest", "infix", "treeops", "sorttrace", "hashprobe", "graphalgo", "dfa", "ll1", "lr", "crc", "slidewin", "subnet", "tcpcong", "gamesearch"];
function mountSlot(slot,name){
  if(!name||!Object.prototype.hasOwnProperty.call(ANIM.REG,name)){
    try{console.warn('[UGCSolvers] unknown solver "'+name+'" for slot',slot);}catch(e){}
    return false;
  }
  if(slot.dataset.solverMounted===name)return true;
  const fallback=slot.innerHTML;
  try{ANIM.mount(slot,name);slot.dataset.solverMounted=name;slot.classList.add('is-mounted');return true;}
  catch(err){slot.innerHTML=fallback;try{console.error('[UGCSolvers] "'+name+'" failed to mount',err);}catch(e){}return false;}
}
function readList(doc){
  const el=doc.getElementById('lessonSolvers');if(!el)return [];
  try{const v=JSON.parse(el.textContent||'[]');return Array.isArray(v)?v.map(x=>String(x==null?'':x)):[];}
  catch(err){try{console.warn('[UGCSolvers] #lessonSolvers is not valid JSON',err);}catch(e){}return [];}
}
function mountAll(root){
  const doc=(root&&root.ownerDocument)||document,scope=root||document;
  const list=readList(doc);
  scope.querySelectorAll('.solver-slot[data-solver]').forEach(slot=>{
    const i=parseInt(slot.getAttribute('data-solver'),10);
    const name=Number.isInteger(i)&&i>=0?list[i]:undefined;
    if(name===undefined){try{console.warn('[UGCSolvers] no solver name at index '+slot.getAttribute('data-solver'));}catch(e){}return;}
    mountSlot(slot,name);
  });
}
window.UGCSolvers={names:Object.keys(ANIM.REG),expected:EXPECTED.slice(),mount:mountSlot,mountAll:mountAll,NETSOLVE:NS_ROOT.NETSOLVE};
if(typeof document!=='undefined'){
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>mountAll(document));
  else mountAll(document);
}
})();
