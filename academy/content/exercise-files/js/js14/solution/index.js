// Lab 3.3 - Order Report (solution)
// Run: node index.js

const orders = [
  { id: 1, month: 'Aug', customer: 'Anu', category: 'Stationery', total: 954 },
  { id: 2, month: 'Aug', customer: 'Faris', category: 'Bags', total: 899 },
  { id: 3, month: 'Aug', customer: 'Kiran', category: 'Bottles', total: 698 },
  { id: 4, month: 'Aug', customer: 'John', category: 'Bags', total: 1798 },
  { id: 5, month: 'Sep', customer: 'Anu', category: 'Bottles', total: 349 },
  { id: 6, month: 'Sep', customer: 'Meera', category: 'Stationery', total: 340 },
  { id: 7, month: 'Sep', customer: 'John', category: 'Stationery', total: 1499 },
  { id: 8, month: 'Sep', customer: 'Zara', category: 'Electronics', total: 2499 },
  { id: 9, month: 'Sep', customer: 'Faris', category: 'Bags', total: 1798 },
  { id: 10, month: 'Sep', customer: 'Meera', category: 'Bottles', total: 120 },
];

const sum = (list) => list.reduce((s, o) => s + o.total, 0);

// 1. Revenue by category
const byCategory = Object.groupBy(orders, (o) => o.category);
const revenue = Object.entries(byCategory)
  .map(([category, list]) => [category, sum(list)])
  .toSorted((a, b) => b[1] - a[1]);
console.log('Revenue by category');
for (const [category, total] of revenue) console.log(`  ${category}: ${total}`);

// 2. Spend per customer
const spend = new Map();
for (const { customer, total } of orders) {
  spend.set(customer, (spend.get(customer) ?? 0) + total);
}
console.log('Top customers');
[...spend]
  .toSorted((a, b) => b[1] - a[1])
  .slice(0, 3)
  .forEach(([name, total], i) => console.log(`  ${i + 1}. ${name} ${total}`));

// 3. Unique customers per month
const byMonth = Map.groupBy(orders, (o) => o.month);
const namesIn = (month) => new Set(byMonth.get(month).map((o) => o.customer));
const aug = namesIn('Aug');
const sep = namesIn('Sep');
console.log(`Customers: Aug ${aug.size}, Sep ${sep.size}`);

// 4. Set algebra (ES2025; Node 22+)
const repeat = aug.intersection(sep);
const fresh = sep.difference(aug);
const lost = aug.difference(sep);
const sorted = (set) => [...set].sort().join(', ');
console.log('Repeat customers:', sorted(repeat));
console.log('New in September:', sorted(fresh));
console.log('Lost after August:', sorted(lost));

// 5. Export
const report = { generatedAt: new Date(), spend, repeat, fresh, lost };
const json = JSON.stringify(report, (key, value) => {
  if (value instanceof Map) return Object.fromEntries(value);
  if (value instanceof Set) return [...value].sort();
  return value;
}, 2);
console.log(json);

// 6. Import with a reviver
const restored = JSON.parse(json, (key, value) =>
  key === 'generatedAt' ? new Date(value) : value);
console.log('generatedAt is a Date:', restored.generatedAt instanceof Date);
