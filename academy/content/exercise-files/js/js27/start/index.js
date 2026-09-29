// checkout.js: written in a hurry before the festive sale. It works.
// Run: node index.js   Save this output first; your refactor must print the same.

// TODO(1): rename short variables (d, t, w, s, fs, disc, tot) to clear names
// and replace magic numbers (0.18, 999, 49, 99, 20, 500) with named constants.

var log = [];

function go(d) {
  var t = 0;
  var w = 0;
  for (var i = 0; i < d.items.length; i++) {
    var it = d.items[i];
    if (it.qty > 0) {
      t = t + it.price * it.qty;
      w = w + it.kg * it.qty;
    }
    // TODO(5): emit a 'stock:low' event instead of logging here
    if (it.stock < it.qty) {
      console.log('WARNING: low stock for ' + it.name);
      log.push('stock:low ' + it.sku);
    }
  }

  // TODO(2): extract parseCoupon(code) that returns { ok, value } or { ok, error }
  var disc = 0;
  var fs = false;
  if (d.coupon) {
    if (d.coupon.substring(0, 4) == 'SAVE') {
      var p = parseInt(d.coupon.substring(4));
      disc = t * p / 100;
      if (disc > 500) disc = 500;
    } else if (d.coupon == 'FREESHIP') {
      fs = true;
    } else {
      console.log('Coupon ' + d.coupon + ' ignored');
    }
  }

  // TODO(3): replace this if/else chain with a shipping strategy map
  var s = 0;
  if (d.ship == 'standard') {
    if (t >= 999) s = 0; else s = 49;
  } else if (d.ship == 'express') {
    s = 99 + Math.ceil(w) * 20;
  } else if (d.ship == 'pickup') {
    s = 0;
  }
  if (fs) s = 0;

  // TODO(4): move all the maths above into a pure priceOrder(order) function
  var tax = Math.round((t - disc) * 0.18 * 100) / 100;
  var tot = t - disc + s + tax;

  // TODO(6): build the receipt text in a pure formatReceipt(order, pricing)
  console.log('Receipt for ' + d.customer.name);
  console.log('  Subtotal  ' + t.toFixed(2));
  console.log('  Discount  ' + disc.toFixed(2));
  console.log('  Delivery  ' + s.toFixed(2) + ' (' + d.ship + ')');
  console.log('  GST       ' + tax.toFixed(2));
  console.log('  Total     ' + tot.toFixed(2));

  // TODO(5): emit 'order:placed' and let subscribers send email and log
  console.log('Email sent to ' + d.customer.email);
  log.push('order:placed ' + tot.toFixed(2));
  return tot;
}

go({
  customer: { name: 'Anu', email: 'anu@ralfiz.dev' },
  items: [
    { sku: 'PEN', name: 'Gel pen set', price: 180, kg: 0.2, qty: 2, stock: 40 },
    { sku: 'BAG', name: 'Laptop bag', price: 1250, kg: 0.9, qty: 1, stock: 1 },
    { sku: 'LAMP', name: 'Desk lamp', price: 2499, kg: 1.3, qty: 1, stock: 0 },
  ],
  coupon: 'SAVE10',
  ship: 'express',
});

go({
  customer: { name: 'Ravi', email: 'ravi@ralfiz.dev' },
  items: [{ sku: 'NOTE', name: 'Notebook', price: 60, kg: 0.3, qty: 4, stock: 100 }],
  coupon: 'FREESHIP',
  ship: 'standard',
});

// TODO(7): move the pure parts to checkout.js (ES module) and keep this file as
// the shell. Add package.json with "type": "module".
console.log('Events: ' + log.join(', '));