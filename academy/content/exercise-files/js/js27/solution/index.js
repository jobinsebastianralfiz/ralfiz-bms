// Imperative shell: input, output and side effects live here. Run: node index.js
import {
  parseCoupon, priceOrder, formatReceipt, lowStockItems, createEmitter,
} from './checkout.js';

const events = createEmitter();
const eventLog = [];

// Subscribers: each one has a single job
events.on('stock:low', item => {
  console.log(`WARNING: low stock for ${item.name}`);
  eventLog.push(`stock:low ${item.sku}`);
});
events.on('coupon:rejected', message => console.log(message));
events.on('order:placed', ({ order }) => console.log(`Email sent to ${order.customer.email}`));
events.on('order:placed', ({ pricing }) =>
  eventLog.push(`order:placed ${pricing.total.toFixed(2)}`));

function checkout(order) {
  lowStockItems(order.items).forEach(item => events.emit('stock:low', item));
  const coupon = parseCoupon(order.coupon);
  if (!coupon.ok) events.emit('coupon:rejected', coupon.error);
  const pricing = priceOrder(order, coupon.ok ? coupon.value : null);
  formatReceipt(order, pricing).forEach(line => console.log(line));
  events.emit('order:placed', { order, pricing });
  return pricing.total;
}

checkout({
  customer: { name: 'Anu', email: 'anu@ralfiz.dev' },
  items: [
    { sku: 'PEN', name: 'Gel pen set', price: 180, kg: 0.2, qty: 2, stock: 40 },
    { sku: 'BAG', name: 'Laptop bag', price: 1250, kg: 0.9, qty: 1, stock: 1 },
    { sku: 'LAMP', name: 'Desk lamp', price: 2499, kg: 1.3, qty: 1, stock: 0 },
  ],
  coupon: 'SAVE10',
  ship: 'express',
});

checkout({
  customer: { name: 'Ravi', email: 'ravi@ralfiz.dev' },
  items: [{ sku: 'NOTE', name: 'Notebook', price: 60, kg: 0.3, qty: 4, stock: 100 }],
  coupon: 'FREESHIP',
  ship: 'standard',
});

console.log(`Events: ${eventLog.join(', ')}`);