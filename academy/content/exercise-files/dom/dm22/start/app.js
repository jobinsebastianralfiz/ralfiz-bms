// Ralfiz Store · starter. Work through TODO(1) to TODO(6).
const API = 'https://dummyjson.com';
const PAGE = 12;
const FIELDS = 'title,price,rating,thumbnail,category,discountPercentage,stock,brand';
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, className, text = '') => Object.assign(document.createElement(tag), { className, textContent: text });
const state = readUrl();
const cache = new Map();
const seen = new Map();
let cart = {};
let controller;
let current;

function readUrl() {
  // TODO(1): read q, cat, sort and page from new URLSearchParams(location.search).
  // page must be a number >= 1.
  return { q: '', cat: '', sort: '', page: 1 };
}
function writeUrl(push) {
  // TODO(1): keep only non-default values; pushState when push is true, else replaceState.
}
function apiUrl({ q, cat, sort, page }) {
  // TODO(2): choose the endpoint and add limit, skip, select (FIELDS), q, sortBy and order.
  return `${API}/products?limit=${PAGE}&select=${FIELDS}`;
}

async function load() {
  // TODO(3): abort the previous request, show 8 .skel placeholders, use the cache,
  // throw when !res.ok, ignore AbortError, and show message('⚠️', …, 'Retry', load) on errors.
  const res = await fetch(apiUrl(state));
  render(await res.json());
}

function render({ products, total }) {
  products.forEach((p) => seen.set(p.id, p));
  $('#grid').replaceChildren(...products.map(card));
  // TODO(4): empty state, "Showing 1–12 of 194" status, page info, disable Prev/Next at the ends.
  $('#status').textContent = `${total} products`;
}

function card(p) {
  const node = $('#card').content.firstElementChild.cloneNode(true);
  node.dataset.id = p.id;
  const img = $('img', node);
  img.src = p.thumbnail;
  img.alt = p.title;
  $('.off', node).textContent = `−${Math.round(p.discountPercentage)}%`;
  $('.eyebrow', node).textContent = p.brand ?? p.category.replaceAll('-', ' ');
  $('.title', node).textContent = p.title;
  $('.rating', node).textContent = `★ ${p.rating.toFixed(1)}`;
  $('.price', node).textContent = usd.format(p.price);
  $('.was', node).textContent = usd.format(p.price / (1 - p.discountPercentage / 100));
  $('.add', node).setAttribute('aria-label', `Add ${p.title} to cart`);
  return node;
}
function message(icon, text, label, action) {
  const box = el('div', 'state');
  const btn = el('button', 'primary', label);
  btn.style.width = 'auto';
  btn.addEventListener('click', action);
  box.append(el('span', '', icon), text, el('br', ''), btn);
  return box;
}

function update(patch, push = false) {
  Object.assign(state, patch);
  writeUrl(push);
  syncControls();
  load();
}
function syncControls() {
  if ($('#q').value.trim() !== state.q) $('#q').value = state.q;
  $('#sort').value = state.sort;
  document.querySelectorAll('.chip').forEach((c) => c.setAttribute('aria-pressed', c.value === state.cat));
}

// TODO(5): search input with a 300 ms debounce → update({ q, cat: '', page: 1 }),
// chips (fetch /products/categories), sort, Prev/Next and a popstate listener.

// TODO(6): openDetail(id) with showModal() and /products/{id}; addToCart(p) and saveCart()
// with localStorage; click delegation on #grid for .add and .title; the cart dialog.

syncControls();
load().catch((err) => console.error('TODO(3) will handle this properly:', err.message));
