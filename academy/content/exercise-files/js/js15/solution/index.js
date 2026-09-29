// Lab 3.4 - Store catalogue toolkit (solution)
// Run: node index.js

const products = [
  { title: 'Notebook', category: 'stationery', price: 149, rating: 4.6, stock: 40 },
  { title: 'Gel pen', category: 'stationery', price: 20, rating: 4.2, stock: 300 },
  { title: 'Laptop bag', category: 'bags', price: 899, rating: 4.8, stock: 12 },
  { title: 'Desk lamp', category: 'home', price: 1299, rating: 4.4, stock: 0 },
  { title: 'Steel bottle', category: 'home', price: 349, rating: 4.5, stock: 25 },
  { title: 'Sticky notes', category: 'stationery', price: 60, rating: 3.8, stock: 90 },
  { title: 'Backpack', category: 'bags', price: 1199, rating: 4.3, stock: 7 },
  { title: 'Scissors', category: 'stationery', price: 99, rating: 3.9, stock: 0 },
  { title: 'Mug', category: 'home', price: 249, rating: 3.7, stock: 60 },
  { title: 'Planner', category: 'stationery', price: 399, rating: 4.4, stock: 15 },
];

function* invoiceNumbers(prefix = 'INV', start = 1) {
  for (let n = start; ; n++) {
    yield `${prefix}-${String(n).padStart(4, '0')}`;
  }
}

class Catalogue {
  #items;
  constructor(items) {
    this.#items = items;
  }
  *[Symbol.iterator]() {
    for (const item of this.#items) {
      if (item.stock > 0) yield item;
    }
  }
  *byCategory(name) {
    for (const item of this) {
      if (item.category === name) yield item;
    }
  }
  get [Symbol.toStringTag]() {
    return 'Catalogue';
  }
}

function* chunk(iterable, size) {
  let batch = [];
  for (const item of iterable) {
    batch.push(item);
    if (batch.length === size) {
      yield batch;
      batch = [];
    }
  }
  if (batch.length) yield batch;
}

const catalogue = new Catalogue(products);
const titles = (items) => items.map((p) => p.title).join(', ');

const ids = invoiceNumbers('INV-2026', 41);
console.log('Invoices:', ids.next().value, ids.next().value, ids.next().value);

const inStock = [...catalogue];
console.log(`In stock: ${inStock.length} of ${products.length}`);
console.log('Stationery:', titles([...catalogue.byCategory('stationery')]));

console.log('Rows:');
for (const row of chunk(catalogue, 3)) {
  console.log('  ' + row.map((p) => p.title.padEnd(13)).join(''));
}

const picks = Iterator.from(catalogue)
  .filter((p) => p.price < 500)
  .filter((p) => p.rating >= 4)
  .take(3)
  .toArray();
console.log('Best cheap picks:', titles(picks));

console.log(String(catalogue));
