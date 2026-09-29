// Lesson 1.2: Shop Bill, version 2 (solution)
// Run with: node index.js

const orders = [
  { id: 'R-1001', isMember: false, isBulky: false, deliveryFee: null, giftWrap: '30',
    lines: [{ name: 'Notebook', price: '120', qty: '3' }, { name: 'Gel pen', price: '25', qty: '4' }] },
  { id: 'R-1002', isMember: true, isBulky: false, deliveryFee: null,
    coupon: { code: 'WELCOME10', percent: 10 },
    lines: [{ name: 'Desk lamp', price: '899', qty: '1' }] },
  { id: 'R-1003', isMember: false, isBulky: true, deliveryFee: 0,
    coupon: { code: 'CHAIR10', percent: 10 },
    lines: [{ name: 'Office chair', price: '1180', qty: '1' }] },
  { id: 'R-1004', isMember: false, isBulky: false, deliveryFee: null,
    lines: [{ name: 'Stapler', price: '150', qty: '2' }, { name: 'Staples box', price: '40', qty: '' }] },
  { id: 'R-1005', isMember: true, isBulky: true, deliveryFee: null,
    lines: [{ name: 'Bookshelf', price: '2400', qty: '1' }] },
];

// Convert at the edge: text from the form becomes a real number once.
function toNumber(text) {
  const n = Number(text ?? 0); // Number('') is 0, Number(undefined) is NaN
  return Number.isNaN(n) ? 0 : n;
}

function lineTotal(line) {
  return toNumber(line.price) * toNumber(line.qty);
}

function subtotalOf(order) {
  let sum = 0;
  for (const line of order.lines) {
    sum += lineTotal(line);
  }
  return sum;
}

function couponDiscount(order, subtotal) {
  const percent = order.coupon?.percent ?? 0; // no coupon: 0, no crash
  return (subtotal * percent) / 100;
}

function isFreeShipping(order, subtotal) {
  return (order.isMember || subtotal >= 999) && !order.isBulky;
}

function deliveryFee(order, subtotal) {
  if (isFreeShipping(order, subtotal)) return 0;
  return order.deliveryFee ?? 40; // keeps a real 0, defaults null/undefined
}

for (const order of orders) {
  const subtotal = subtotalOf(order);
  const discount = couponDiscount(order, subtotal);
  const fee = deliveryFee(order, subtotal);
  const total = subtotal - discount + fee + toNumber(order.giftWrap);
  const who = order.isMember === true ? 'member' : 'guest';
  console.log(`${order.id} (${who}) subtotal ${subtotal}, discount ${discount}, delivery ${fee}`);
  console.log(`  Total: ${total.toFixed(2)}`);
}
