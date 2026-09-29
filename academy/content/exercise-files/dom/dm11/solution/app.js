// Ralfiz Store product browser: states, skeletons, load more,
// debounced search, cancelled stale requests and a response cache.
const API = 'https://dummyjson.com/products';
const PAGE_SIZE = 12;
const FIELDS = 'title,brand,price,rating,thumbnail';

const $ = (selector) => document.querySelector(selector);
const grid = $('#grid');
const cardTemplate = $('#card-template');
const skeletonTemplate = $('#skeleton-template');

const state = { query: '', skip: 0, total: 0, status: 'idle', error: '' };
const cache = new Map();
let controller = null;

function pageUrl(query, skip) {
  const params = new URLSearchParams({ limit: PAGE_SIZE, skip, select: FIELDS });
  if (query) params.set('q', query);
  return query ? `${API}/search?${params}` : `${API}?${params}`;
}

async function fetchPage(url, signal) {
  if (cache.has(url)) return cache.get(url);
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`The server answered ${res.status}.`);
  const data = await res.json();
  cache.set(url, data);
  return data;
}

function productCard(product) {
  const card = cardTemplate.content.firstElementChild.cloneNode(true);
  const img = card.querySelector('img');
  img.src = product.thumbnail;
  img.alt = product.title;
  img.addEventListener('error', () => img.remove(), { once: true }); // keep the gradient
  card.querySelector('.title').textContent = product.title;
  card.querySelector('.brandline').textContent = product.brand ?? 'Ralfiz Select';
  card.querySelector('.price').textContent = `$${product.price.toFixed(2)}`;
  card.querySelector('.rating').textContent = `★ ${product.rating.toFixed(1)}`;
  return card;
}

function showSkeletons(n) {
  for (let i = 0; i < n; i++) {
    grid.append(skeletonTemplate.content.firstElementChild.cloneNode(true));
  }
}

function renderStatus() {
  const { status, total, skip, query, error } = state;
  grid.setAttribute('aria-busy', String(status === 'loading'));
  $('#error').hidden = status !== 'error';
  $('#error-detail').textContent = error;
  $('#more').hidden = status !== 'success' || skip >= total;
  if (status === 'loading') $('#status').textContent = 'Loading products…';
  else if (status === 'success' && total === 0) {
    $('#status').textContent = `No products match “${query}”. Try a shorter word.`;
  } else if (status === 'success') {
    $('#status').textContent = `Showing ${skip} of ${total}${query ? ` for “${query}”` : ''}`;
  }
}

async function load({ reset = false } = {}) {
  controller?.abort();
  const ctrl = (controller = new AbortController());
  if (reset) {
    state.skip = 0;
    grid.replaceChildren();
  }
  state.status = 'loading';
  renderStatus();
  showSkeletons(reset ? PAGE_SIZE : 4);

  try {
    const data = await fetchPage(pageUrl(state.query, state.skip), ctrl.signal);
    grid.querySelectorAll('.skeleton').forEach((s) => s.remove());
    grid.append(...data.products.map(productCard));
    Object.assign(state, { skip: state.skip + data.products.length, total: data.total, status: 'success' });
  } catch (err) {
    if (err.name === 'AbortError') return; // a newer request replaced this one
    grid.querySelectorAll('.skeleton').forEach((s) => s.remove());
    Object.assign(state, { status: 'error', error: err.message });
  }
  renderStatus();
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

$('#search').addEventListener('input', debounce((event) => {
  const query = event.target.value.trim();
  if (query === state.query) return;
  state.query = query;
  load({ reset: true });
}, 300));

$('#more').addEventListener('click', () => load());
$('#retry').addEventListener('click', () => load({ reset: state.skip === 0 }));

load({ reset: true });
