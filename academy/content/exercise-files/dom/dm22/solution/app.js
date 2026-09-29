// Ralfiz Store · solution. Flow: control → update(patch) → URL → load() → render().
const API = 'https://dummyjson.com';
const PAGE = 12;
const FIELDS = 'title,price,rating,thumbnail,category,discountPercentage,stock,brand';
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, className, text = '') => Object.assign(document.createElement(tag), { className, textContent: text });
const state = readUrl();
const cache = new Map();
const seen = new Map();
let cart = JSON.parse(localStorage.getItem('ralfiz-cart') ?? '{}');
let controller;
let current;
function readUrl() {
  const p = new URLSearchParams(location.search);
  return { q: p.get('q') ?? '', cat: p.get('cat') ?? '', sort: p.get('sort') ?? '',
    page: Math.max(1, Number(p.get('page')) || 1) };
}
function writeUrl(push) {
  const p = new URLSearchParams(Object.entries(state).filter(([k, v]) => v && !(k === 'page' && v === 1)));
  history[push ? 'pushState' : 'replaceState'](null, '', p.size ? `?${p}` : location.pathname);
}
function apiUrl({ q, cat, sort, page }) {
  const p = new URLSearchParams({ limit: PAGE, skip: (page - 1) * PAGE, select: FIELDS });
  if (q) p.set('q', q);
  if (sort) { const [by, order] = sort.split('-'); p.set('sortBy', by); p.set('order', order); }
  const path = q ? 'products/search' : cat ? `products/category/${encodeURIComponent(cat)}` : 'products';
  return `${API}/${path}?${p}`;
}
async function load() {
  controller?.abort();
  controller = new AbortController();
  const url = apiUrl(state);
  $('#status').textContent = 'Loading products…';
  $('#grid').setAttribute('aria-busy', 'true');
  $('#grid').replaceChildren(...Array.from({ length: 8 }, () => el('div', 'skel')));
  try {
    let data = cache.get(url);
    if (!data) {
      const res = await fetch(url, { signal: controller.signal });
      if (!res.ok) throw new Error(`The server answered ${res.status}`);
      data = await res.json();
      cache.set(url, data);
    }
    render(data);
  } catch (err) {
    if (err.name === 'AbortError') return;
    $('#status').textContent = 'Could not load products';
    $('#grid').replaceChildren(message('⚠️', `${err.message}. Check your connection.`, 'Retry', load));
  } finally {
    $('#grid').setAttribute('aria-busy', 'false');
  }
}

function render({ products, total }) {
  const pages = Math.max(1, Math.ceil(total / PAGE));
  const from = (state.page - 1) * PAGE + 1;
  products.forEach((p) => seen.set(p.id, p));
  $('#grid').replaceChildren(...products.map(card));
  if (!products.length) {
    $('#grid').replaceChildren(message('🔎', `No products match “${state.q}”.`, 'Clear search', () => update({ q: '', page: 1 })));
  }
  const suffix = state.q ? ` for “${state.q}”` : '';
  $('#status').textContent = total ? `Showing ${from}–${from + products.length - 1} of ${total}${suffix}` : 'No results';
  $('#pageInfo').textContent = `Page ${state.page} of ${pages}`;
  $('#prev').disabled = state.page <= 1;
  $('#next').disabled = state.page >= pages;
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
  $('.rating', node).textContent = `★ ${p.rating.toFixed(1)} · ${p.stock < 10 ? `only ${p.stock} left` : 'in stock'}`;
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

async function openDetail(id) {
  current = null;
  $('#dTitle').textContent = 'Loading…';
  ['#dMeta', '#dDesc', '#dRating', '#dStock', '#dPrice'].forEach((s) => ($(s).textContent = ''));
  $('#dImg').removeAttribute('src');
  $('#detail').showModal();
  try {
    const res = await fetch(`${API}/products/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    current = await res.json();
    Object.assign($('#dImg'), { src: current.thumbnail, alt: current.title });
    $('#dMeta').textContent = `${current.brand ?? 'Ralfiz'} · ${current.category.replaceAll('-', ' ')}`;
    $('#dTitle').textContent = current.title;
    $('#dDesc').textContent = current.description;
    $('#dRating').textContent = `★ ${current.rating.toFixed(1)}`;
    $('#dStock').textContent = current.stock;
    $('#dPrice').textContent = usd.format(current.price);
  } catch (err) {
    $('#dTitle').textContent = `Could not load this product (${err.message})`;
  }
}

function addToCart(p) {
  const line = cart[p.id] ?? { id: p.id, title: p.title, cents: Math.round(p.price * 100), qty: 0 };
  cart = { ...cart, [p.id]: { ...line, qty: line.qty + 1 } };
  saveCart();
  $('#sr').textContent = `${p.title} added to cart`;
  $('#cartBtn').classList.remove('bump');
  requestAnimationFrame(() => $('#cartBtn').classList.add('bump'));
}
function saveCart() {
  localStorage.setItem('ralfiz-cart', JSON.stringify(cart));
  const lines = Object.values(cart);
  const count = lines.reduce((n, l) => n + l.qty, 0);
  $('#cartCount').textContent = count;
  $('#cartBtn').setAttribute('aria-label', `Cart, ${count} items`);
  $('#cartTotal').textContent = usd.format(lines.reduce((n, l) => n + l.cents * l.qty, 0) / 100);
  $('#cartList').replaceChildren(...(lines.length ? lines.map((l) => {
    const li = el('li', '');
    li.dataset.id = l.id;
    const remove = el('button', '', '✕');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Remove ${l.title}`);
    li.append(el('span', '', `${l.title} × ${l.qty}`), usd.format((l.cents * l.qty) / 100), remove);
    return li;
  }) : [el('li', '', 'Your cart is empty.')]));
}

async function loadCategories() {
  try {
    const res = await fetch(`${API}/products/categories`);
    if (!res.ok) throw new Error(res.status);
    const chip = (slug, name) => Object.assign(el('button', 'chip', name), { type: 'button', value: slug });
    $('#chips').replaceChildren(chip('', 'All'), ...(await res.json()).map((c) => chip(c.slug, c.name)));
    syncControls();
  } catch {
    $('#chips').hidden = true;
  }
}

let timer;
$('#q').addEventListener('input', (ev) => {
  clearTimeout(timer);
  timer = setTimeout(() => update({ q: ev.target.value.trim(), cat: '', page: 1 }), 300);
});
$('#chips').addEventListener('click', (ev) => {
  const chip = ev.target.closest('.chip');
  if (chip) update({ cat: chip.value, q: '', page: 1 }, true);
});
$('#sort').addEventListener('change', (ev) => update({ sort: ev.target.value, page: 1 }));
$('#prev').addEventListener('click', () => update({ page: state.page - 1 }, true));
$('#next').addEventListener('click', () => update({ page: state.page + 1 }, true));
$('#grid').addEventListener('click', (ev) => {
  const id = Number(ev.target.closest('.card')?.dataset.id);
  if (ev.target.closest('.add')) addToCart(seen.get(id));
  else if (ev.target.closest('.title')) openDetail(id);
});
$('#dAdd').addEventListener('click', () => current && addToCart(current));
$('#cartBtn').addEventListener('click', () => $('#cart').showModal());
$('#cartList').addEventListener('click', (ev) => {
  const li = ev.target.closest('button') && ev.target.closest('li');
  if (!li) return;
  const { [li.dataset.id]: _removed, ...rest } = cart;
  cart = rest;
  saveCart();
});
document.querySelectorAll('dialog').forEach((d) => d.addEventListener('click', (ev) => ev.target === d && d.close()));
addEventListener('popstate', () => { Object.assign(state, readUrl()); syncControls(); load(); });

syncControls();
saveCart();
loadCategories();
load();
