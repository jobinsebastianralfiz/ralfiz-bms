// Lab 1.3 - Receipt toolkit (solution)
// Run: node index.js

const order = {
  customer: '  anu   KRISHNAN ',
  cashiers: ['Bala', 'Chitra'],
  lines: [
    { name: 'Notebook A5', qty: 3, price: 89 },
    { name: 'Gel pen (blue)', qty: 10, price: 15 },
    { name: 'Stainless steel bottle 1L', qty: 1, price: 649 },
    { name: 'Sticky notes', qty: 2, price: 99.5 },
  ],
};

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const andList = new Intl.ListFormat('en', { type: 'conjunction' });
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });

function formatName(raw) {
  return raw
    .trim()
    .split(' ')
    .filter((part) => part !== '')
    .map((word) => word[0].toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

function makeSku(category, id) {
  const prefix = category.slice(0, 3).toUpperCase();
  return `RZ-${prefix}-${String(id).padStart(4, '0')}`;
}

function slugify(title) {
  return title
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function receiptLine(name, qty, price) {
  const label = name.length > 18 ? name.slice(0, 17) + '…' : name;
  const amount = (qty * price).toFixed(2);
  return label.padEnd(18) + String(qty).padStart(5) + amount.padStart(11);
}

function formatReceipt(data) {
  const divider = '-'.repeat(34);
  const total = data.lines.reduce((sum, l) => sum + l.qty * l.price, 0);
  const body = data.lines
    .map((l) => receiptLine(l.name, l.qty, l.price))
    .join('\n');
  return `RALFIZ STORE
Customer: ${formatName(data.customer)}
${divider}
${body}
${divider}
Total: ${inr.format(total)}
Served by: ${andList.format(data.cashiers)}`;
}

function countChars(text) {
  return [...segmenter.segment(text)].length;
}

console.log('Customer:', formatName(order.customer));
console.log('SKU:', makeSku('stationery', 42));
console.log('Slug:', slugify('Café Menu: Autumn 2026!'));
console.log(formatReceipt(order));
const review = 'Great tee 👍🏽';
console.log(`${review} -> ${countChars(review)} characters (length ${review.length})`);
