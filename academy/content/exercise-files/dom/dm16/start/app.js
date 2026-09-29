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
let shown = [];     // bar values as currently drawn
let bars = [];      // hit boxes from the last draw
let hover = -1;
let frame = 0;

function setupCanvas() {
  // TODO(1): read the CSS size with getBoundingClientRect(), set canvas.width
  // and canvas.height to that size × devicePixelRatio, get the 2d context and
  // call ctx.setTransform(dpr, 0, 0, dpr, 0, 0). Store the CSS size in W and H.
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
  // TODO(2): clearRect, draw 4 grid lines with lakh() labels, then one
  // roundRect bar per month (radius [6, 6, 0, 0]) with its month label.
  // Push { x, w, top, mid } for each column into bars. Use color('--accent')
  // and color('--accent-strong') for the hovered bar.
}

// TODO(3): pointermove → find the column under the pointer, redraw with
// hover set, and show #tip with the amount and month; pointerleave → hide it.

function animateBars(target) {
  // TODO(4): requestAnimationFrame loop over 700ms with an ease-out curve,
  // updating shown and calling drawBars(shown) each frame. Skip it when
  // reduce.matches is true.
  shown = target.slice();
  drawBars(shown);
}

function svg(tag, attrs = {}, ...children) {
  // TODO(5): create the element with document.createElementNS(NS, tag),
  // set each attribute with setAttribute, append the children and return it.
  return document.createElement('span');
}

function buildDonut(categories) {
  // TODO(5): an <svg viewBox="0 0 200 200" role="img"> with a <title>, a grey
  // track circle (r = 70, stroke-width 24) and, inside a <g> rotated -90deg
  // around (100, 100), one circle per category. Set stroke-dasharray to
  // "share × C  C" and stroke-dashoffset to minus the length so far.
  // TODO(6): add a <title> and tabindex="0" to each segment, fill #legend with
  // createElement + textContent, and highlight on pointerenter and focus.
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
  shown = data.revenue.map(() => 0);
  setupCanvas();
  animateBars(data.revenue);
  buildDonut(data.categories);
  // TODO(7): observe the canvas with a ResizeObserver: setupCanvas() then drawBars(shown).
}

main().catch((err) => {
  document.querySelector('#barsTitle').textContent = err.message;
});
