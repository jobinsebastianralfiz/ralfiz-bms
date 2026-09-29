// Lab 3.4 - Store catalogue toolkit (starter)
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

// TODO(1): make this an infinite generator (function*) yielding
// `${prefix}-${number padded to 4}`
function invoiceNumbers(prefix = 'INV', start = 1) {
  return [];
}

class Catalogue {
  #items;
  constructor(items) {
    this.#items = items;
  }
  // TODO(2): *[Symbol.iterator]() yielding only items with stock > 0
  // TODO(3): *byCategory(name) yielding in-stock items of that category
  // TODO(6): get [Symbol.toStringTag]() returning 'Catalogue'
}

// TODO(4): make this a generator that yields arrays of `size` items
function chunk(iterable, size) {
  return [];
}

const catalogue = new Catalogue(products);

console.log('Invoices:', invoiceNumbers('INV-2026', 41));
console.log('In stock:', 'TODO');
console.log('Stationery:', 'TODO');
console.log('Rows:', chunk(products, 3));

// TODO(5): Iterator.from(catalogue).filter(...).filter(...).take(3).toArray()
console.log('Best cheap picks:', 'TODO');
console.log(String(catalogue));
