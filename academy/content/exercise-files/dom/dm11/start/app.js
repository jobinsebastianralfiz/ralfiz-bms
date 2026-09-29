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
  // TODO(1): build the URL with URLSearchParams (limit, skip, select).
  //   With a query use `${API}/search?...&q=...`, otherwise `${API}?...`.
  return `${API}?limit=${PAGE_SIZE}`;
}

async function fetchPage(url, signal) {
  // TODO(2): return cache.get(url) when cached. Otherwise fetch with the
  //   signal, throw an Error when !res.ok, parse JSON, store it in the
  //   cache and return it.
  return { products: [], total: 0, skip: 0, limit: 0 };
}

function productCard(product) {
  const card = cardTemplate.content.firstElementChild.cloneNode(true);
  // TODO(3): fill the clone: img.src and img.alt (the product title),
  //   remove the img on its error event, and set textContent of .title,
  //   .brandline, .price ($12.99) and .rating (★ 4.5).
  return card;
}

function showSkeletons(n) {
  for (let i = 0; i < n; i++) {
    grid.append(skeletonTemplate.content.firstElementChild.cloneNode(true));
  }
}

function renderStatus() {
  // TODO(4): from state, update aria-busy on the grid, #error.hidden,
  //   #error-detail, #more.hidden (show only on success with more to load)
  //   and the #status text: "Loading products…", "No products match …"
  //   or "Showing 12 of 194".
}

async function load({ reset = false } = {}) {
  // TODO(5): abort the previous controller and create a new one.
  if (reset) {
    state.skip = 0;
    grid.replaceChildren();
  }
  state.status = 'loading';
  renderStatus();
  showSkeletons(reset ? PAGE_SIZE : 4);

  try {
    const data = await fetchPage(pageUrl(state.query, state.skip));
    grid.querySelectorAll('.skeleton').forEach((s) => s.remove());
    grid.append(...data.products.map(productCard));
    Object.assign(state, { skip: state.skip + data.products.length, total: data.total, status: 'success' });
  } catch (err) {
    // TODO(6): ignore AbortError; otherwise remove skeletons and set
    //   status 'error' with err.message.
    console.error(err);
  }
  renderStatus();
}

// TODO(7): write debounce(fn, ms) and use it (300 ms) on #search input:
//   trim the value, skip if unchanged, store it in state.query and
//   call load({ reset: true }).

// TODO(8): #more loads the next page; #retry calls load again.

load({ reset: true });
