// Ralfiz Store: nightly order report, before and after optimisation.
// Run: node index.js

const CITIES = ['Kochi', 'Kozhikode', 'Thrissur', 'Malappuram', 'Dubai', 'Toronto'];
const CATEGORIES = ['books', 'electronics', 'stationery', 'grocery'];

function makeData(customerCount = 3000, orderCount = 30000) {
  const customers = Array.from({ length: customerCount }, (_, i) => ({
    id: `C${i + 1}`,
    name: `Customer ${i + 1}`,
    city: CITIES[i % CITIES.length],
  }));
  const vip = customers.filter((_, i) => i % 10 === 0).map((c) => c.id);
  const orders = Array.from({ length: orderCount }, (_, i) => ({
    id: i + 1,
    customerId: `C${((i * 7) % customerCount) + 1}`,
    category: CATEGORIES[i % CATEGORIES.length],
    amount: 100 + ((i * 37) % 900),
  }));
  return { customers, vip, orders };
}

// Pretend this reads a rules table and is expensive.
function gstRate(category) {
  let spin = 0;
  for (let i = 0; i < 2000; i++) spin += i % 7;
  const rates = { books: 0, electronics: 0.18, stationery: 0.12, grocery: 0.05 };
  return rates[category] + spin * 0; // spin only burns time
}

function summarise(byCity, vipRevenue) {
  const rounded = Object.fromEntries(
    Object.entries(byCity).map(([city, v]) => [city, Math.round(v)]),
  );
  return { byCity: rounded, vipRevenue: Math.round(vipRevenue) };
}

function reportSlow({ customers, vip, orders }) {
  const byCity = {};
  let vipRevenue = 0;
  for (const o of orders) {
    const c = customers.find((x) => x.id === o.customerId); // O(n) per order
    const gross = o.amount * (1 + gstRate(o.category));   // recomputed every time
    byCity[c.city] = (byCity[c.city] ?? 0) + gross;
    if (vip.includes(c.id)) vipRevenue += gross;          // O(m) per order
  }
  return summarise(byCity, vipRevenue);
}

// Memoize a one-argument pure function, keeping at most `max` entries (LRU).
function memoize(fn, { max = 100 } = {}) {
  const cache = new Map();
  const memo = (arg) => {
    if (cache.has(arg)) {
      const value = cache.get(arg);
      cache.delete(arg);
      cache.set(arg, value); // most recently used goes to the end
      return value;
    }
    const value = fn(arg);
    cache.set(arg, value);
    if (cache.size > max) cache.delete(cache.keys().next().value);
    return value;
  };
  memo.size = () => cache.size;
  return memo;
}

function reportFast({ customers, vip, orders }) {
  const byId = new Map(customers.map((c) => [c.id, c]));
  const vipSet = new Set(vip);
  const rate = memoize(gstRate, { max: 16 });
  const byCity = {};
  let vipRevenue = 0;
  for (const o of orders) {
    const c = byId.get(o.customerId);
    const gross = o.amount * (1 + rate(o.category));
    byCity[c.city] = (byCity[c.city] ?? 0) + gross;
    if (vipSet.has(c.id)) vipRevenue += gross;
  }
  return summarise(byCity, vipRevenue);
}

function time(label, fn) {
  const start = performance.now();
  const result = fn();
  const ms = performance.now() - start;
  console.log(`${label.padEnd(12)} ${ms.toFixed(1).padStart(8)} ms`);
  return { result, ms };
}

const data = makeData();
console.log(`Orders: ${data.orders.length}, customers: ${data.customers.length}\n`);
const slow = time('Slow report', () => reportSlow(data));
const fast = time('Fast report', () => reportFast(data));
const same = JSON.stringify(slow.result) === JSON.stringify(fast.result);
console.log(`\nSame result: ${same}`);
console.log(`Speed-up: ${Math.round(slow.ms / Math.max(fast.ms, 0.1))}x`);
console.log('Revenue by city:', fast.result.byCity);
console.log('VIP revenue:', fast.result.vipRevenue.toLocaleString('en-IN'));

// The cache stays bounded however many different keys arrive.
const square = memoize((n) => n * n, { max: 50 });
for (let i = 0; i < 10000; i++) square(i % 500);
console.log(`\nLRU cache size after 10,000 calls with 500 keys: ${square.size()}`);

// Debounce and throttle, tested with a simulated burst of keystrokes.
function debounce(fn, wait) {
  let timer;
  const debounced = function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
  debounced.cancel = () => clearTimeout(timer);
  return debounced;
}

function throttle(fn, interval) {
  let last = -Infinity;
  let timer = null;
  let pending;
  return function (...args) {
    const now = performance.now();
    if (now - last >= interval) {
      clearTimeout(timer); // a late trailing call is now redundant
      timer = null;
      last = now;
      fn.apply(this, args);
    } else {
      pending = args;
      timer ??= setTimeout(() => {
        last = performance.now();
        timer = null;
        fn.apply(this, pending);
      }, interval - (now - last));
    }
  };
}

const calls = { debounced: [], throttled: [] };
const onSearch = debounce((q) => calls.debounced.push(q), 100);
const onScroll = throttle((y) => calls.throttled.push(y), 100);
let n = 0;
const burst = setInterval(() => {
  n++;
  onSearch('phone charger'.slice(0, Math.min(n, 13)));
  onScroll(n * 40);
  if (n === 20) clearInterval(burst); // 20 events, 20 ms apart
}, 20);

setTimeout(() => {
  console.log(`\nRaw events: ${n}`);
  console.log(`Debounced calls: ${calls.debounced.length} ->`, calls.debounced.slice(-3));
  console.log(`Throttled calls: ${calls.throttled.length} (about one per 100 ms)`);
}, 700);
