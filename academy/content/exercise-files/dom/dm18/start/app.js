const ROW_H = 44;
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

// TODO(3): this renders every row. Replace it with a virtual list.
function renderAllRows() {
  const rows = document.querySelector('#rows');
  rows.style.position = 'static';
  for (const o of orders) rows.append(rowFor(o)); // 5,000 live appends
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
  track.innerHTML = '<span class="bar"></span>'; // static markup
  const amt = document.createElement('span');
  amt.className = 'amt';
  amt.textContent = inr.format(r.sum);
  li.append(name, track, amt);
  return li;
}));

// TODO(2): read/write/read/write thrashing. Batch it.
function updateBars() {
  document.querySelectorAll('.bar').forEach((bar, i) => {
    const width = bar.parentElement.clientWidth;
    bar.style.width = (revenue[i].sum / max) * width + 'px';
  });
}

// TODO(1): mark and measure this first render
renderAllRows();
updateBars();
document.querySelector('#summary').textContent = orders.length + ' orders';

// TODO(5): this runs dozens of times per second while resizing
addEventListener('resize', () => updateBars());

// TODO(4): heavy scroll handler with no throttling (use it for the virtual list)
document.querySelector('#viewport').addEventListener('scroll', () => {});

// TODO(6): animating bottom with setInterval runs layout every step
function showToast() {
  const toast = document.querySelector('#toast');
  let bottom = -60;
  const id = setInterval(() => {
    bottom += 4;
    toast.style.bottom = bottom + 'px';
    if (bottom >= 16) clearInterval(id);
  }, 16);
  setTimeout(() => { toast.style.bottom = '-60px'; }, 3000);
}
setTimeout(showToast, 800);
