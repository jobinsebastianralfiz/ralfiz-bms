// js11 lab: Tip and Bill Splitter utilities. Run with: node index.js
// All money is in integer paise (₹1 = 100 paise).

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const money = (paise) => inr.format(paise / 100);
const toPaise = (rupees) => Math.round(rupees * 100);

// TODO(1): pipe(f, g, h)(x) should return h(g(f(x))). Hint: reduce.
const pipe = (...fns) => (x) => x;

// TODO(2): curried helpers.
// addPercent(10)(1000) -> 1100   discountFlat(300)(1000) -> 700 (never below 0)
const addPercent = (pct) => (paise) => paise;
const discountFlat = (paiseOff) => (paise) => paise;

// TODO(3): roundUpTo(1000)(127050) -> 128000
const roundUpTo = (stepPaise) => (paise) => paise;

// TODO(4): splitEvenly(3)(100) -> [ 34, 33, 33 ]. Shares must add up to total.
const splitEvenly = (people) => (total) => [total];

// TODO(5): build the pipeline: discount, then service charge, then tip,
// then (only if roundTo > 0) rounding. Return pipe(...steps).
function makeBillCalculator({ tipPercent = 10, servicePercent = 0,
  discountRupees = 0, roundToRupees = 0 } = {}) {
  return (paise) => paise;
}

// ---- Try it ----
const order = {
  table: 7,
  guests: 3,
  items: [
    { name: 'Chicken biryani', price: 280, qty: 3 },
    { name: 'Fresh lime soda', price: 60, qty: 3 },
    { name: 'Kulfi', price: 90, qty: 2 },
  ],
};
const snapshot = structuredClone(order);

const subtotal = order.items.reduce((sum, i) => sum + toPaise(i.price) * i.qty, 0);
console.log('Subtotal:', money(subtotal));

const tipTable = [0, 5, 10, 15].map((pct) => ({
  tip: pct + '%',
  total: money(addPercent(pct)(subtotal)),
}));
console.table(tipTable);

const calculate = makeBillCalculator({
  tipPercent: 10, servicePercent: 5, discountRupees: 100, roundToRupees: 10,
});
const total = calculate(subtotal);
const shares = splitEvenly(order.guests)(total);
console.log('Total to pay:', money(total));
console.log('Shares:', shares.map(money).join(', '));
console.log('Shares add up:', shares.reduce((a, b) => a + b, 0) === total);

// TODO(6): compare order with snapshot (JSON.stringify both) and log
// "Order unchanged: true".