// Ralfiz Store order report: modern version (Node 22+). Run: node index.js

const orders = [
  { id: 'ORD-1001', customer: 'anu', city: 'Kochi', status: 'paid',
    placedAt: new Date('2026-09-01T09:30:00Z'),
    items: [{ sku: 'PEN', price: 20, qty: 5 }, { sku: 'BAG', price: 1_250, qty: 1 }],
    coupon: { code: 'WELCOME', percent: 10 } },
  { id: 'ORD-1002', customer: 'ravi', city: 'Chennai', status: 'paid',
    placedAt: new Date('2026-09-03T12:00:00Z'),
    items: [{ sku: 'NOTE', price: 60, qty: 4 }], coupon: null },
  { id: 'ORD-1003', customer: 'sara', city: 'Kochi', status: 'cancelled',
    placedAt: new Date('2026-09-04T15:45:00Z'),
    items: [{ sku: 'BAG', price: 1_250, qty: 2 }] },
  { id: 'ORD-1004', customer: 'anu', city: 'Pune', status: 'paid',
    placedAt: new Date('2026-09-10T08:15:00Z'),
    items: [{ sku: 'LAMP', price: 2_499, qty: 1 }, { sku: 'PEN', price: 20, qty: 2 }],
    coupon: { code: 'FESTIVE', percent: 0 } },
  { id: 'ORD-1005', customer: 'tom', city: 'Chennai', status: 'paid',
    placedAt: new Date('2026-09-12T18:20:00Z'),
    items: [{ sku: 'BAG', price: 1_250, qty: 1 }, { sku: 'PEN', price: 20, qty: 1 }],
    coupon: { code: 'VIP' } },
  { id: 'ORD-1006', customer: 'ravi', city: 'Kochi', status: 'paid',
    placedAt: new Date('2026-09-15T11:05:00Z'),
    items: [{ sku: 'PEN', price: 20, qty: 10 }, { sku: 'NOTE', price: 60, qty: 2 }] },
];

const DEFAULT_PERCENT = 5;
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

const subtotal = order => order.items.reduce((sum, i) => sum + i.price * i.qty, 0);

// (1) No coupon: 0%. Coupon without percent: default. percent: 0 stays 0.
const couponPercent = order =>
  order.coupon ? (order.coupon.percent ?? DEFAULT_PERCENT) : 0;

const orderTotal = order => subtotal(order) * (1 - couponPercent(order) / 100);

const paid = orders.filter(o => o.status === 'paid');
const revenue = paid.reduce((sum, o) => sum + orderTotal(o), 0);
console.log('Ralfiz Store: order report');
console.log(`Orders: ${orders.length} (paid ${paid.length})`);
console.log(`Revenue: ${inr.format(revenue)}`);

// (2) A real deep copy: Date objects survive
const snapshot = structuredClone(orders);
console.log(`Snapshot keeps dates: ${snapshot[0].placedAt instanceof Date}`);

// (3) A sorted copy; paid keeps its order
const top3 = paid.toSorted((a, b) => orderTotal(b) - orderTotal(a)).slice(0, 3);
console.log(`Top 3: ${top3.map(o => o.id).join(', ')}`);
console.log(`First order in the list: ${paid[0].id}`);

// (4) Grouping in one line (null-prototype object)
const byCity = Object.groupBy(paid, o => o.city);
console.log('By city:');
for (const city of Object.keys(byCity).toSorted()) {
  const list = byCity[city];
  const total = list.reduce((s, o) => s + orderTotal(o), 0);
  console.log(`  ${city.padEnd(10)}${list.length} orders  ${inr.format(total)}`);
}

// (5) Set methods (ES2025)
const buyersOf = sku =>
  new Set(paid.filter(o => o.items.some(i => i.sku === sku)).map(o => o.customer));
const both = buyersOf('PEN').intersection(buyersOf('BAG'));
console.log(`Bought PEN and BAG: ${[...both].join(', ')}`);

// (6) Promise.withResolvers + top-level await
function loadUsdRate() {
  const { promise, resolve } = Promise.withResolvers();
  setTimeout(() => resolve(0.012), 100);
  return promise;
}
const rate = await loadUsdRate();
console.log(`Revenue in USD: $${(revenue * rate).toFixed(2)}`);

// (7) Iterator helpers are lazy: they stop after two matches
const big = orders.values()
  .filter(o => orderTotal(o) > 1_000)
  .map(o => o.id)
  .take(2)
  .toArray();
console.log(`First two orders over ₹1,000: ${big.join(', ')}`);