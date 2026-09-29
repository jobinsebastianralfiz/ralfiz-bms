// Pure core of the checkout. No console, no I/O: data in, data out.

export const GST_RATE = 0.18;
export const MAX_COUPON_DISCOUNT = 500;
export const FREE_STANDARD_FROM = 999;

export const shippingStrategies = {
  standard: ({ subtotal }) => (subtotal >= FREE_STANDARD_FROM ? 0 : 49),
  express: ({ weightKg }) => 99 + Math.ceil(weightKg) * 20,
  pickup: () => 0,
};

// Expected failures return a result object
export function parseCoupon(code) {
  if (!code) return { ok: true, value: null };
  if (code === 'FREESHIP') return { ok: true, value: { freeShipping: true } };
  const match = /^SAVE(\d{1,2})$/.exec(code);
  if (!match) return { ok: false, error: `Coupon ${code} ignored` };
  return { ok: true, value: { percent: Number(match[1]) } };
}

const activeItems = items => items.filter(item => item.qty > 0);
const sumBy = (items, fn) => items.reduce((sum, item) => sum + fn(item), 0);
const roundMoney = amount => Math.round(amount * 100) / 100;

export const lowStockItems = items => items.filter(item => item.stock < item.qty);

export function priceOrder(order, coupon) {
  const items = activeItems(order.items);
  const subtotal = sumBy(items, i => i.price * i.qty);
  const weightKg = sumBy(items, i => i.kg * i.qty);
  const discount = coupon?.percent
    ? Math.min((subtotal * coupon.percent) / 100, MAX_COUPON_DISCOUNT)
    : 0;
  const shippingCost = shippingStrategies[order.ship];
  if (!shippingCost) throw new Error(`Unknown shipping method: ${order.ship}`);
  const delivery = coupon?.freeShipping ? 0 : shippingCost({ subtotal, weightKg });
  const tax = roundMoney((subtotal - discount) * GST_RATE);
  return { subtotal, discount, delivery, tax, total: subtotal - discount + delivery + tax };
}

export function formatReceipt(order, p) {
  return [
    `Receipt for ${order.customer.name}`,
    `  Subtotal  ${p.subtotal.toFixed(2)}`,
    `  Discount  ${p.discount.toFixed(2)}`,
    `  Delivery  ${p.delivery.toFixed(2)} (${order.ship})`,
    `  GST       ${p.tax.toFixed(2)}`,
    `  Total     ${p.total.toFixed(2)}`,
  ];
}

// Observer: a tiny emitter
export function createEmitter() {
  const handlers = new Map();
  return {
    on(event, fn) {
      if (!handlers.has(event)) handlers.set(event, new Set());
      handlers.get(event).add(fn);
      return () => handlers.get(event).delete(fn);
    },
    emit(event, payload) {
      for (const fn of [...(handlers.get(event) ?? [])]) fn(payload);
    },
  };
}