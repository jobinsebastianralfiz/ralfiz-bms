const NS = 'http://www.w3.org/2000/svg';
const canvas = document.querySelector('#bars');
const tip = document.querySelector('#tip');
const css = getComputedStyle(document.documentElement);
const color = (name) => css.getPropertyValue(name).trim();
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const lakh = (v) => '₹' + +(v / 1e5).toFixed(1) + 'L';
const reduce = matchMedia('(prefers-reduced-motion: reduce)');

let data = null;
let ctx = null;
let W = 0;
let H = 0;
let shown = [];
let bars = [];
let hover = -1;
let frame = 0;

function setupCanvas() {
  const dpr = window.devicePixelRatio || 1;
  ({ width: W, height: H } = canvas.getBoundingClientRect());
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

// A round maximum that splits into 4 steps of 1, 2, 2.5 or 5 × 10ⁿ
function niceMax(v) {
  const raw = v / 4;
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = [1, 2, 2.5, 5, 10].find((n) => n * p >= raw);
  return 4 * m * p;
}

function drawBars(values) {
  if (!ctx) return;
  ctx.clearRect(0, 0, W, H);
  const pad = { top: 12, right: 4, bottom: 24, left: 44 };
  const plotH = H - pad.top - pad.bottom;
  const base = pad.top + plotH;
  const max = niceMax(Math.max(...data.revenue));
  const y = (v) => base - (v / max) * plotH;
  ctx.font = '11px system-ui, sans-serif';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const gy = Math.round(y((max / 4) * i)) + 0.5;
    ctx.strokeStyle = color(i ? '--grid' : '--axis');
    ctx.beginPath(); ctx.moveTo(pad.left, gy); ctx.lineTo(W - pad.right, gy); ctx.stroke();
    ctx.fillStyle = color('--muted');
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(i ? lakh((max / 4) * i) : '₹0', pad.left - 8, gy);
  }
  const slot = (W - pad.left - pad.right) / values.length;
  const bw = Math.min(34, slot * 0.62);
  bars = values.map((v, i) => {
    const x = pad.left + slot * i + (slot - bw) / 2;
    const top = y(v);
    ctx.fillStyle = color(i === hover ? '--accent-strong' : '--accent');
    ctx.globalAlpha = hover === -1 || i === hover ? 1 : 0.45;
    ctx.beginPath();
    ctx.roundRect(x, top, bw, base - top, [6, 6, 0, 0]);
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.fillStyle = color('--muted');
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(slot < 34 ? data.months[i][0] : data.months[i], x + bw / 2, base + 8);
    return { x: pad.left + slot * i, w: slot, top, mid: x + bw / 2 };
  });
}

canvas.addEventListener('pointermove', (e) => {
  const x = e.clientX - canvas.getBoundingClientRect().left;
  const i = bars.findIndex((b) => x >= b.x && x < b.x + b.w);
  if (i !== hover) { hover = i; drawBars(shown); }
  tip.hidden = i < 0;
  if (i < 0) return;
  tip.textContent = data.months[i] + ' · ' + inr.format(data.revenue[i]);
  tip.style.left = Math.min(W - 70, Math.max(70, bars[i].mid)) + 'px';
  tip.style.top = bars[i].top + 'px';
});
canvas.addEventListener('pointerleave', () => { hover = -1; tip.hidden = true; drawBars(shown); });

function animateBars(target) {
  cancelAnimationFrame(frame);
  if (reduce.matches) { shown = target.slice(); drawBars(shown); return; }
  const from = shown.slice();
  let start = null;
  const step = (now) => {
    start ??= now;
    const t = Math.min(1, (now - start) / 700);
    const e = 1 - (1 - t) ** 3;
    shown = from.map((f, i) => f + (target[i] - f) * e);
    drawBars(shown);
    if (t < 1) frame = requestAnimationFrame(step);
  };
  frame = requestAnimationFrame(step);
}

function svg(tag, attrs = {}, ...children) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  el.append(...children);
  return el;
}

function buildDonut(categories) {
  const R = 70;
  const C = 2 * Math.PI * R;
  const total = categories.reduce((s, c) => s + c.revenue, 0);
  const chart = svg('svg', { viewBox: '0 0 200 200', role: 'img', 'aria-labelledby': 'donutTitle' },
    svg('title', { id: 'donutTitle' }, 'Revenue by category'),
    svg('circle', { cx: 100, cy: 100, r: R, fill: 'none', stroke: '#eef2f7', 'stroke-width': 24 }));
  const ring = svg('g', { transform: 'rotate(-90 100 100)' });
  const big = svg('text', { x: 100, y: 104, 'text-anchor': 'middle', class: 'big' }, lakh(total));
  const small = svg('text', { x: 100, y: 124, 'text-anchor': 'middle', class: 'small' }, 'total revenue');
  let offset = 0;
  const rows = [];
  const segs = categories.map((c) => {
    const len = (c.revenue / total) * C;
    const pct = Math.round((c.revenue / total) * 100) + '%';
    const seg = svg('circle', { cx: 100, cy: 100, r: R, stroke: c.color, class: 'seg-arc', tabindex: 0,
      'stroke-dasharray': Math.max(0, len - 2) + ' ' + C, 'stroke-dashoffset': -offset },
      svg('title', {}, c.name + ': ' + inr.format(c.revenue) + ' (' + pct + ')'));
    offset += len;
    const li = document.createElement('li');
    const dot = document.createElement('span');
    dot.className = 'dot';
    dot.style.background = c.color;
    const name = document.createElement('span');
    name.textContent = c.name;
    const val = document.createElement('b');
    val.textContent = lakh(c.revenue) + ' · ' + pct;
    li.append(dot, name, val);
    rows.push(li);
    return seg;
  });
  ring.append(...segs);
  chart.append(ring, big, small);
  document.querySelector('#donut').append(chart);
  document.querySelector('#legend').append(...rows);

  const highlight = (i) => {
    chart.classList.toggle('dim', i >= 0);
    segs.forEach((s, k) => s.classList.toggle('on', k === i));
    rows.forEach((r, k) => r.classList.toggle('on', k === i));
    big.textContent = lakh(i >= 0 ? categories[i].revenue : total);
    small.textContent = i >= 0 ? categories[i].name : 'total revenue';
  };
  [segs, rows].forEach((list) => list.forEach((el, i) => {
    el.addEventListener('pointerenter', () => highlight(i));
    el.addEventListener('pointerleave', () => highlight(-1));
    el.addEventListener('focus', () => highlight(i));
    el.addEventListener('blur', () => highlight(-1));
  }));
}

async function main() {
  const res = await fetch('sales.json');
  if (!res.ok) throw new Error('Could not load sales.json: HTTP ' + res.status);
  data = await res.json();
  const total = data.revenue.reduce((a, b) => a + b, 0);
  const best = data.revenue.indexOf(Math.max(...data.revenue));
  document.querySelector('#total').textContent = inr.format(total);
  document.querySelector('#best').textContent = data.months[best] + ' · ' + lakh(data.revenue[best]);
  document.querySelector('#barsTitle').textContent = 'Monthly revenue · ' + data.year;
  canvas.setAttribute('aria-label', 'Monthly revenue ' + data.year + ': ' +
    data.months.map((m, i) => m + ' ' + lakh(data.revenue[i])).join(', '));
  shown = data.revenue.map(() => 0);
  setupCanvas();
  animateBars(data.revenue);
  buildDonut(data.categories);
  new ResizeObserver(() => { setupCanvas(); drawBars(shown); }).observe(canvas);
}

main().catch((err) => {
  document.querySelector('#barsTitle').textContent = err.message;
});
