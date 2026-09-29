// Lab 1.3 - Receipt toolkit (starter)
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

// TODO(1): trim, split on ' ', drop empty parts, capitalise each word, join.
function formatName(raw) {
  return raw;
}

// TODO(2): 'RZ-' + first 3 letters of category in capitals + '-' +
// id padded to 4 digits with zeros. makeSku('stationery', 42) -> 'RZ-STA-0042'
function makeSku(category, id) {
  return '';
}

// TODO(3): normalize('NFD'), remove accents with
// .replace(/[\u0300-\u036f]/g, ''), lowercase, turn every run of
// characters that are not a-z or 0-9 into '-', and trim '-' from both ends.
function slugify(title) {
  return title;
}

// TODO(4): name padded to 18 (cut to 17 + '…' when longer than 18),
// qty padded to 5 on the left, amount (qty * price, 2 decimals) padded to 11.
function receiptLine(name, qty, price) {
  return name;
}

// TODO(5): return a multi-line template literal:
// RALFIZ STORE, Customer: <formatted name>, a divider made with repeat,
// one receiptLine per line, a divider, Total: <INR total>,
// Served by: <cashiers with Intl.ListFormat>
function formatReceipt(data) {
  return 'receipt goes here';
}

// TODO(6): count graphemes with Intl.Segmenter.
function countChars(text) {
  return text.length;
}

console.log('Customer:', formatName(order.customer));
console.log('SKU:', makeSku('stationery', 42));
console.log('Slug:', slugify('Café Menu: Autumn 2026!'));
console.log(formatReceipt(order));
const review = 'Great tee 👍🏽';
console.log(`${review} -> ${countChars(review)} characters (length ${review.length})`);
