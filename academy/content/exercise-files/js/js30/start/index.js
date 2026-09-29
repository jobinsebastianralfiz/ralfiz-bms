// Ralfiz Store: nightly order report. It is correct but slow. Make it fast.
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

// TODO(3): memoize a one-argument pure function with a Map cache.
// TODO(5): keep at most `max` entries: on a hit, move the key to the end;
// when the cache is too big, delete cache.keys().next().value (the oldest).
// Also add memo.size = () => cache.size so the check below works.
function memoize(fn, { max = 100 } = {}) {
  const memo = (arg) => fn(arg);
  memo.size = () => 0;
  return memo;
}

function reportFast({ customers, vip, orders }) {
  // TODO(1): build a Map from customer id to customer ONCE, before the loop.
  // TODO(2): build a Set from the vip array ONCE, before the loop.
  // TODO(3): const rate = memoize(gstRate, { max: 16 }) and use rate(...)
  const byCity = {};
  let vipRevenue = 0;
  for (const o of orders) {
    const c = customers.find((x) => x.id === o.customerId);
    const gross = o.amount * (1 + gstRate(o.category));
    byCity[c.city] = (byCity[c.city] ?? 0) + gross;
    if (vip.includes(c.id)) vipRevenue += gross;
  }
  return summarise(byCity, vipRevenue);
}

// TODO(4): measure fn with performance.now(), print the label and the time,
// and return { result, ms } with the real duration.
function time(label, fn) {
  const result = fn();
  console.log(`${label.padEnd(12)}  (not measured yet)`);
  return { result, ms: 1 };
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

const square = memoize((n) => n * n, { max: 50 });
for (let i = 0; i < 10000; i++) square(i % 500);
console.log(`\nLRU cache size after 10,000 calls with 500 keys: ${square.size()}`);

// TODO(6): implement debounce (run once calls stop for `wait` ms) and
// throttle (run at most once per `interval` ms, with a trailing call).
// Keep `this` and the latest arguments. These stubs call fn every time.
function debounce(fn, wait) {
  return function (...args) {
    fn.apply(this, args);
  };
}

function throttle(fn, interval) {
  return function (...args) {
    fn.apply(this, args);
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
