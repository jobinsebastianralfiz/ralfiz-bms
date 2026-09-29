// Lab 3.3 - Order Report (starter)
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

// TODO(1): group orders by category with Object.groupBy,
// sum each group, sort high to low and print "Category: total"
console.log('Revenue by category');

// TODO(2): build a Map customer -> total spend and print the top 3
const spend = new Map();
console.log('Top customers');

// TODO(3): one Set of customer names per month
const aug = new Set();
const sep = new Set();

// TODO(4): repeat, new and lost customers with intersection/difference
const repeat = new Set();
const fresh = new Set();
const lost = new Set();
console.log('Repeat:', [...repeat], 'New:', [...fresh], 'Lost:', [...lost]);

const report = { generatedAt: new Date(), spend, repeat, fresh, lost };

// TODO(5): stringify with a replacer (Map -> object, Set -> sorted array)
const json = JSON.stringify(report);
console.log(json);

// TODO(6): parse with a reviver that turns generatedAt back into a Date
const restored = JSON.parse(json);
console.log('generatedAt is a Date:', restored.generatedAt instanceof Date);
