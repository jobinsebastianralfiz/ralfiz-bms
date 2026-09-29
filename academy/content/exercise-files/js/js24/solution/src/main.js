// src/main.js: the entry module. Vite serves it in dev and bundles it for production.

// Vite replaces import.meta.env at build time. Only VITE_* variables are
// exposed, and they end up in the public bundle: never put secrets here.
// (The ?? {} keeps this file working if you open it without Vite.)
const env = import.meta.env ?? {};
const API_BASE = env.VITE_API_BASE ?? 'https://dummyjson.com';
const STORE_NAME = env.VITE_STORE_NAME ?? 'Ralfiz Store';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const $ = (selector) => document.querySelector(selector);

function productCard(product) {
  const li = document.createElement('li');
  li.className = 'card';
  const title = document.createElement('h2');
  title.textContent = product.title;
  const category = document.createElement('p');
  category.textContent = product.category;
  const price = document.createElement('div');
  price.className = 'price';
  price.textContent = money.format(product.price);
  li.append(title, category, price);
  return li;
}

async function loadProducts() {
  const url = new URL('/products', API_BASE);
  url.searchParams.set('limit', 6);
  url.searchParams.set('select', 'title,price,category');
  const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.products;
}

document.title = STORE_NAME;
$('#title').textContent = STORE_NAME;
$('#env').textContent = `mode: ${env.MODE ?? 'no build tool'} · API: ${API_BASE}`;

try {
  const products = await loadProducts();
  $('#grid').append(...products.map(productCard));
  $('#status').textContent = `${products.length} featured products`;
} catch (err) {
  $('#status').textContent = `Could not load products (${err.message}).`;
  $('#status').classList.add('error');
}
