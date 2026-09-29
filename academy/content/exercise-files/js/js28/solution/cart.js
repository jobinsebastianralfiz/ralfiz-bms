// Ralfiz Store cart module (solution). No DOM, no network: easy to test.

export const GST_RATE = 0.18;

export class CartError extends Error {
  constructor(message, options) {
    super(message, options);
    this.name = 'CartError';
  }
}

const round2 = n => Math.round(n * 100) / 100;

export function createCart({ now = () => new Date() } = {}) {
  const lines = new Map();
  let coupon = null;

  function add(product, qty = 1) {
    if (!Number.isInteger(qty) || qty <= 0) {
      throw new CartError(`Invalid quantity: ${qty}`);
    }
    if (!(product?.price >= 0)) throw new CartError('Product needs a price');
    const newQty = (lines.get(product.sku)?.qty ?? 0) + qty;   // fixed: add up
    if (newQty > product.stock) {
      throw new CartError(`Only ${product.stock} ${product.title} in stock`);
    }
    lines.set(product.sku, { ...product, qty: newQty });
  }

  function remove(sku) {
    lines.delete(sku);
  }

  function items() {
    return [...lines.values()].map(l => ({
      sku: l.sku, title: l.title, qty: l.qty, lineTotal: round2(l.price * l.qty),
    }));
  }

  function applyCoupon(next) {
    if (next.expires && now() > next.expires) {
      throw new CartError(`Coupon ${next.code} has expired`);
    }
    coupon = next;
  }

  function totals() {
    const subtotal = round2([...lines.values()].reduce((s, l) => s + l.price * l.qty, 0));
    const discount = coupon
      ? round2(Math.min((subtotal * coupon.percent) / 100, coupon.max ?? Infinity))
      : 0;
    const tax = round2((subtotal - discount) * GST_RATE);
    return { subtotal, discount, tax, total: round2(subtotal - discount + tax) };
  }

  async function checkout(payments) {
    if (lines.size === 0) throw new CartError('Cart is empty');
    const { total } = totals();
    try {
      const receipt = await payments.charge(total, 'INR');
      lines.clear();
      coupon = null;
      return { id: receipt.id, total };
    } catch (err) {
      throw new CartError('Payment failed', { cause: err });
    }
  }

  return {
    add, remove, items, applyCoupon, totals, checkout,
    get count() {
      return [...lines.values()].reduce((n, l) => n + l.qty, 0);
    },
  };
}

export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}