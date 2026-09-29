// Ralfiz Store order report: legacy version. Run: node index.js
// It works, but it uses old patterns and has two quiet bugs.

var orders = [
  { id: 'ORD-1001', customer: 'anu', city: 'Kochi', status: 'paid',
    placedAt: new Date('2026-09-01T09:30:00Z'),
    items: [{ sku: 'PEN', price: 20, qty: 5 }, { sku: 'BAG', price: 1250, qty: 1 }],
    coupon: { code: 'WELCOME', percent: 10 } },
  { id: 'ORD-1002', customer: 'ravi', city: 'Chennai', status: 'paid',
    placedAt: new Date('2026-09-03T12:00:00Z'),
    items: [{ sku: 'NOTE', price: 60, qty: 4 }], coupon: null },
  { id: 'ORD-1003', customer: 'sara', city: 'Kochi', status: 'cancelled',
    placedAt: new Date('2026-09-04T15:45:00Z'),
    items: [{ sku: 'BAG', price: 1250, qty: 2 }] },
  { id: 'ORD-1004', customer: 'anu', city: 'Pune', status: 'paid',
    placedAt: new Date('2026-09-10T08:15:00Z'),
    items: [{ sku: 'LAMP', price: 2499, qty: 1 }, { sku: 'PEN', price: 20, qty: 2 }],
    coupon: { code: 'FESTIVE', percent: 0 } },
  { id: 'ORD-1005', customer: 'tom', city: 'Chennai', status: 'paid',
    placedAt: new Date('2026-09-12T18:20:00Z'),
    items: [{ sku: 'BAG', price: 1250, qty: 1 }, { sku: 'PEN', price: 20, qty: 1 }],
    coupon: { code: 'VIP' } },
  { id: 'ORD-1006', customer: 'ravi', city: 'Kochi', status: 'paid',
    placedAt: new Date('2026-09-15T11:05:00Z'),
    items: [{ sku: 'PEN', price: 20, qty: 10 }, { sku: 'NOTE', price: 60, qty: 2 }] },
];

var DEFAULT_PERCENT = 5;
var inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

function subtotal(order) {
  return order.items.reduce(function (sum, i) { return sum + i.price * i.qty; }, 0);
}

// TODO(1): percent 0 must mean 0%. Only a coupon WITHOUT percent gets the default.
function couponPercent(order) {
  return (order.coupon && order.coupon.percent) || (order.coupon ? DEFAULT_PERCENT : 0);
}

function orderTotal(order) {
  return subtotal(order) * (1 - couponPercent(order) / 100);
}

var paid = orders.filter(function (o) { return o.status === 'paid'; });
var revenue = paid.reduce(function (sum, o) { return sum + orderTotal(o); }, 0);
console.log('Ralfiz Store: order report');
console.log('Orders: ' + orders.length + ' (paid ' + paid.length + ')');
console.log('Revenue: ' + inr.format(revenue));

// TODO(2): use structuredClone so the snapshot keeps real Date objects.
var snapshot = JSON.parse(JSON.stringify(orders));
console.log('Snapshot keeps dates: ' + (snapshot[0].placedAt instanceof Date));

// TODO(3): use toSorted so the original orders array is not reordered.
var top3 = paid.sort(function (a, b) { return orderTotal(b) - orderTotal(a); }).slice(0, 3);
console.log('Top 3: ' + top3.map(function (o) { return o.id; }).join(', '));
console.log('First order in the list: ' + paid[0].id);

// TODO(4): replace this reduce with Object.groupBy.
var byCity = paid.reduce(function (acc, o) {
  if (!acc[o.city]) acc[o.city] = [];
  acc[o.city].push(o);
  return acc;
}, {});
console.log('By city:');
Object.keys(byCity).sort().forEach(function (city) {
  var total = byCity[city].reduce(function (s, o) { return s + orderTotal(o); }, 0);
  console.log('  ' + city.padEnd(10) + byCity[city].length + ' orders  ' + inr.format(total));
});

// TODO(5): build two Sets and use intersection.
function buyersOf(sku) {
  var names = [];
  paid.forEach(function (o) {
    var has = o.items.some(function (i) { return i.sku === sku; });
    if (has && names.indexOf(o.customer) === -1) names.push(o.customer);
  });
  return names;
}
var pens = buyersOf('PEN');
var bags = buyersOf('BAG');
var both = pens.filter(function (n) { return bags.indexOf(n) !== -1; });
console.log('Bought PEN and BAG: ' + both.join(', '));

// TODO(6): return a promise with Promise.withResolvers and use top-level await.
function loadUsdRate(callback) {
  setTimeout(function () { callback(null, 0.012); }, 100);
}
loadUsdRate(function (err, rate) {
  if (err) return console.log('No rate');
  console.log('Revenue in USD: $' + (revenue * rate).toFixed(2));

  // TODO(7): use iterator helpers: orders.values().filter(...).take(2).toArray()
  var big = [];
  for (var i = 0; i < orders.length && big.length < 2; i++) {
    if (orderTotal(orders[i]) > 1000) big.push(orders[i].id);
  }
  console.log('First two orders over ₹1,000: ' + big.join(', '));
});