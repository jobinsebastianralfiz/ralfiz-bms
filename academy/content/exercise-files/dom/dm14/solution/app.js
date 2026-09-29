const grid = document.querySelector('#grid');
const sentinel = document.querySelector('#sentinel');
const status = document.querySelector('#status');
const widthBadge = document.querySelector('#width');
const PAGE = 12;
let skip = 0;
let total = Infinity;
let loading = false;
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

function card(p) {
  const li = document.createElement('li');
  li.className = 'card';
  const img = Object.assign(document.createElement('img'), {
    className: 'thumb', alt: p.title, width: 300, height: 300,
    loading: 'lazy', decoding: 'async',
  });
  img.addEventListener('error', () => {         // broken image → tidy placeholder
    const ph = Object.assign(document.createElement('div'), { className: 'thumb ph', textContent: '🛍️' });
    ph.setAttribute('role', 'img');
    ph.setAttribute('aria-label', p.title);
    img.replaceWith(ph);
  }, { once: true });
  img.src = p.thumbnail;
  const body = document.createElement('div');
  body.className = 'body';
  body.innerHTML = '<h3></h3><p><b></b><span></span></p>';
  body.querySelector('h3').textContent = p.title;
  body.querySelector('b').textContent = usd.format(p.price);
  body.querySelector('span').textContent = '★ ' + p.rating.toFixed(1);
  li.append(img, body);
  return li;
}

const revealObserver = new IntersectionObserver((entries, obs) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    entry.target.classList.add('in');
    obs.unobserve(entry.target);
  }
}, { threshold: 0.15 });

function addCards(products) {
  const cards = products.map(card);
  grid.append(...cards);
  cards.forEach((c) => {
    c.classList.add('reveal');
    revealObserver.observe(c);
  });
}

async function loadMore() {
  if (loading || skip >= total) return;
  loading = true;
  const skeletons = Array.from({ length: 4 }, () =>
    Object.assign(document.createElement('li'), { className: 'card skeleton' }));
  grid.append(...skeletons);
  try {
    const url = new URL('https://dummyjson.com/products');
    url.search = new URLSearchParams({ limit: PAGE, skip,
      select: 'title,price,rating,thumbnail' });
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    total = data.total;
    skip += data.products.length;
    skeletons.forEach((s) => s.remove());
    addCards(data.products);
    status.textContent = skip + ' of ' + total;
    if (skip >= total) {
      feedObserver.disconnect();
      sentinel.textContent = 'You have seen all ' + total + ' products';
    }
  } catch (err) {
    skeletons.forEach((s) => s.remove());
    sentinel.textContent = 'Could not load products (' + err.message + '). ';
    const retry = Object.assign(document.createElement('button'), { textContent: 'Try again' });
    retry.addEventListener('click', () => { sentinel.textContent = ''; loadMore(); });
    sentinel.append(retry);
  } finally {
    loading = false;
  }
  if (skip < total) {                         // fresh callback if still visible
    feedObserver.unobserve(sentinel);
    feedObserver.observe(sentinel);
  }
}

const feedObserver = new IntersectionObserver(([entry]) => {
  if (entry.isIntersecting) loadMore();
}, { rootMargin: '0px 0px 400px 0px' });
feedObserver.observe(sentinel);

new ResizeObserver(([entry]) => {
  const width = Math.round(entry.contentBoxSize[0].inlineSize);
  grid.dataset.size = width < 520 ? 'compact' : 'regular';
  widthBadge.textContent = width + 'px · ' + grid.dataset.size;
}).observe(grid);
