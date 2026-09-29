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
  const img = document.createElement('img');
  img.className = 'thumb';
  // TODO(1): set alt, width (300), height (300), loading 'lazy' and decoding 'async'
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

function addCards(products) {
  const cards = products.map(card);
  grid.append(...cards);
  // TODO(5): add the class 'reveal' to each card and observe it with revealObserver
}

async function loadMore() {
  // TODO(3): return early if loading is true or skip >= total
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
    // TODO(4): when skip >= total, disconnect feedObserver and show the end message
  } catch (err) {
    skeletons.forEach((s) => s.remove());
    sentinel.textContent = 'Could not load products (' + err.message + ').';
  } finally {
    loading = false;
  }
  // TODO(3): re-observe the sentinel here so a still-visible sentinel fires again
}

// TODO(2): const feedObserver = new IntersectionObserver(...) watching #sentinel
// TODO(5): const revealObserver = new IntersectionObserver(...) with threshold 0.15
// TODO(6): a ResizeObserver on grid that sets grid.dataset.size and #width

loadMore();
