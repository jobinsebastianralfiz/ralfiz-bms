// cart.js: money helpers (named exports) and the Cart class (default export)
export const GST_RATE = 0.18;

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

export function formatINR(amount) {
  return inr.format(amount);
}

export default class Cart {
  items = [];

  add(name, price, qty = 1) {
    this.items.push({ name, price, qty });
    return this;
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
