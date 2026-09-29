const ROW_H = 44;
const OVERSCAN = 5;
const cities = ['Kochi', 'Kozhikode', 'Thrissur', 'Bengaluru', 'Dubai', 'Toronto'];
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const weights = [0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 4, 4, 5]; // busier cities
const orders = Array.from({ length: 5000 }, (_, i) => ({
  id: 20001 + i,
  customer: 'Customer ' + (i + 1),
  city: cities[weights[(i * 7) % weights.length]],
  total: 199 + ((i * 7919) % 9800),
}));

function rowFor(o) {
  const row = document.createElement('div');
  row.className = 'row';
  for (const [cls, text] of [['', '#' + o.id], ['', o.customer], ['', o.city], ['amt', inr.format(o.total)]]) {
    const span = document.createElement('span');
    span.className = cls;
    span.textContent = text;
    row.append(span);
  }
  return row;
}

// 3. Virtual list
const viewport = document.querySelector('#viewport');
const rowsEl = document.querySelector('#rows');
document.querySelector('#spacer').style.height = orders.length * ROW_H + 'px';
let lastFirst = -1;
function renderVisibleRows() {
  const first = Math.max(0, Math.floor(viewport.scrollTop / ROW_H) - OVERSCAN);
  if (first === lastFirst) return;
  lastFirst = first;
  const count = Math.ceil(viewport.clientHeight / ROW_H) + OVERSCAN * 2;
  rowsEl.replaceChildren(...orders.slice(first, first + count).map(rowFor));
  rowsEl.style.transform = 'translateY(' + first * ROW_H + 'px)';
}

// Revenue per city
const revenue = Object.entries(Object.groupBy(orders, (o) => o.city))
  .map(([city, list]) => ({ city, sum: list.reduce((s, o) => s + o.total, 0) }));
const max = Math.max(...revenue.map((r) => r.sum));
document.querySelector('#bars').replaceChildren(...revenue.map((r) => {
  const li = document.createElement('li');
  const name = document.createElement('span');
  name.textContent = r.city;
  const track = document.createElement('span');
  track.className = 'track';
  const bar = document.createElement('span');
  bar.className = 'bar';
  track.append(bar);
  const amt = document.createElement('span');
  amt.className = 'amt';
  amt.textContent = inr.format(r.sum);
  li.append(name, track, amt);
  return li;
}));

// 2. All reads, then all writes
function updateBars() {
  const bars = [...document.querySelectorAll('.bar')];
  const widths = bars.map((bar) => bar.parentElement.clientWidth);
  bars.forEach((bar, i) => {
    bar.style.width = (revenue[i].sum / max) * widths[i] + 'px';
  });
}

// 1. Measure the first render
performance.mark('render-start');
renderVisibleRows();
updateBars();
performance.mark('render-end');
const m = performance.measure('render', 'render-start', 'render-end');
console.log('render: ' + m.duration.toFixed(1) + ' ms');
document.querySelector('#summary').textContent = orders.length.toLocaleString('en-IN') + ' orders';

// 4. At most one render per frame; passive so scrolling never waits
let queued = false;
viewport.addEventListener('scroll', () => {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; renderVisibleRows(); });
}, { passive: true });

// 5. Debounced resize
function debounce(fn, ms = 150) {
  let id;
  return (...args) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...args), ms);
  };
}
addEventListener('resize', debounce(() => {
  updateBars();
  lastFirst = -1;
  renderVisibleRows();
}));

// 6. Toast animated by CSS transform/opacity
function showToast() {
  const toast = document.querySelector('#toast');
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}
setTimeout(showToast, 800);
