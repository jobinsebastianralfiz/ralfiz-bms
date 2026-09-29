// Ralfiz Store invoice (legacy CommonJS: everything in one file)
// Run: node index.js          or: node index.js --save
'use strict';
const { writeFile } = require('node:fs/promises'); // TODO(5): load only when --save

// ---- money helpers ----
// TODO(1): move GST_RATE and formatINR into cart.js as NAMED exports
const GST_RATE = 0.18;
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
function formatINR(amount) {
  return inr.format(amount);
}

// ---- Cart ----
// TODO(2): move the Cart class into cart.js as the DEFAULT export
class Cart {
  constructor() {
    this.items = [];
  }
  add(name, price, qty = 1) {
    this.items.push({ name, price, qty });
    return this; // allows chaining
  }
  get subtotal() {
    return this.items.reduce((sum, it) => sum + it.price * it.qty, 0);
  }
  get gst() {
    return Math.round(this.subtotal * GST_RATE * 100) / 100;
  }
  get total() {
    return this.subtotal + this.gst;
  }
  lines() {
    const rows = this.items.map(
      (it) => `${it.name.padEnd(16)} x${it.qty}  ${formatINR(it.price * it.qty).padStart(10)}`,
    );
    return [...rows, `${'Total'.padEnd(20)}  ${formatINR(this.total).padStart(10)}`];
  }
}

// ---- main ----
// TODO(3): in index.js, import Cart and the helpers from './cart.js'
// TODO(4): add a package.json with "type": "module" next to index.js
// TODO(6): replace main() and .catch() with top-level await
async function main() {
  const cart = new Cart()
    .add('Cotton Kurta', 1299, 2)
    .add('Steel Bottle', 499)
    .add('Laptop Sleeve', 899);

  console.log(cart.lines().join('\n'));
  console.log(`GST ${GST_RATE * 100}%: ${formatINR(cart.gst)}`);

  if (process.argv.includes('--save')) {
    // TODO(7): build the path with new URL('./invoice.txt', import.meta.url)
    await writeFile(__dirname + '/invoice.txt', cart.lines().join('\n'));
    console.log('Saved invoice.txt');
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});

module.exports = { Cart, formatINR }; // TODO(8): delete: cart.js exports now
