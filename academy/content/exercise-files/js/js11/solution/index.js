// js11 lab: Tip and Bill Splitter utilities. Run with: node index.js
// All money is in integer paise (₹1 = 100 paise).

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const money = (paise) => inr.format(paise / 100);
const toPaise = (rupees) => Math.round(rupees * 100);

const pipe = (...fns) => (x) => fns.reduce((value, fn) => fn(value), x);

const addPercent = (pct) => (paise) => Math.round(paise * (1 + pct / 100));
const discountFlat = (paiseOff) => (paise) => Math.max(paise - paiseOff, 0);
const roundUpTo = (stepPaise) => (paise) => Math.ceil(paise / stepPaise) * stepPaise;

// Whole-paise shares; the leftover paise go to the first people.
const splitEvenly = (people) => (total) => {
  const base = Math.floor(total / people);
  const leftover = total - base * people;
  return Array.from({ length: people }, (_, i) => base + (i < leftover ? 1 : 0));
};

function makeBillCalculator({ tipPercent = 10, servicePercent = 0,
  discountRupees = 0, roundToRupees = 0 } = {}) {
  const steps = [
    discountFlat(toPaise(discountRupees)),
    addPercent(servicePercent),
    addPercent(tipPercent),
  ];
  if (roundToRupees > 0) steps.push(roundUpTo(toPaise(roundToRupees)));
  return pipe(...steps);
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

// Nothing above changed the order: every helper returned new values.
console.log('Order unchanged:', JSON.stringify(order) === JSON.stringify(snapshot));