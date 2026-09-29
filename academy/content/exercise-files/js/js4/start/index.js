// Lesson 1.2: Shop Bill, version 2 (checkout rules)
// Orders arrive from a web form, so prices, quantities and gift wrap are STRINGS.
// deliveryFee comes from the shipping API: a number, or null when not set.
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

// TODO(1): convert form text to a number. Missing values (undefined or '')
//          and text that is not a number should count as 0.
function toNumber(text) {
  return text;
}

// TODO(2): use toNumber for both price and qty.
function lineTotal(line) {
  return line.price * line.qty;
}

function subtotalOf(order) {
  let sum = 0;
  for (const line of order.lines) {
    sum += lineTotal(line);
  }
  return sum;
}

// TODO(4): read order.coupon?.percent with optional chaining and ?? 0,
//          and return subtotal * percent / 100.
function couponDiscount(order, subtotal) {
  return 0;
}

// TODO(5): the rule is "members, or subtotals of 999 and above, ship free,
//          but never bulky items". Add parentheses so the code says that.
function isFreeShipping(order, subtotal) {
  return order.isMember || subtotal >= 999 && !order.isBulky;
}

// TODO(3): a fee of 0 is valid. Only null or undefined should become 40.
function deliveryFee(order, subtotal) {
  if (isFreeShipping(order, subtotal)) return 0;
  return order.deliveryFee || 40;
}

for (const order of orders) {
  const subtotal = subtotalOf(order);
  const discount = couponDiscount(order, subtotal);
  const fee = deliveryFee(order, subtotal);
  // TODO(1) also applies here: giftWrap is text from the form (or missing)
  const total = subtotal - discount + fee + (order.giftWrap || 0);
  // TODO(6): replace == with ===
  const who = order.isMember == true ? 'member' : 'guest';
  console.log(`${order.id} (${who}) subtotal ${subtotal}, discount ${discount}, delivery ${fee}`);
  console.log(`  Total: ${total}`);
}
