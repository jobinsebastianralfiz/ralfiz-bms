// Lab 1.4 - GST invoice in paise (starter)
// Run: node index.js

const invoice = {
  date: '2026-01-31',
  termsDays: 30,
  discountPct: 10,
  gstRate: 18,
  lines: [
    { name: 'Chai mug', price: '199.99', qty: 3 },
    { name: 'Coaster set', price: 0.1, qty: 7 },
    { name: 'Tea caddy', price: 2897.8, qty: 1 },
  ],
};

// TODO(1): accept a number or a string, return whole paise with Math.round.
// Return NaN when the input is not a finite number.
function toPaise(rupees) {
  return 0;
}

// TODO(2): unit price in paise * qty.
function lineTotal(line) {
  return 0;
}

// TODO(3): percent of subtotal, rounded to the nearest paisa.
function discountPaise(subtotal, percent) {
  return 0;
}

// TODO(4): gst = Math.round(taxable * rate / 100);
// cgst = Math.floor(gst / 2); sgst = gst - cgst. Return { cgst, sgst, total: gst }.
function gstSplit(taxable, ratePercent) {
  return { cgst: 0, sgst: 0, total: 0 };
}

// TODO(5): create ONE Intl.NumberFormat('en-IN', currency INR) outside the
// function and use it here. Remember to divide by 100.
function formatINR(paise) {
  return String(paise);
}

// TODO(6): parse 'YYYY-MM-DD' into year, month, day numbers, use Date.UTC,
// add the days and return a 'YYYY-MM-DD' string (toISOString().slice(0, 10)).
function addDays(isoDate, days) {
  return isoDate;
}

// TODO(6): whole days between two 'YYYY-MM-DD' strings using Date.UTC.
function daysBetween(fromIso, toIso) {
  return 0;
}

console.log('toPaise checks:', toPaise('249.99'), toPaise(0.1), toPaise('abc'));

const subtotal = invoice.lines.reduce((sum, line) => sum + lineTotal(line), 0);
const discount = discountPaise(subtotal, invoice.discountPct);
const taxable = subtotal - discount;
const gst = gstSplit(taxable, invoice.gstRate);
const total = taxable + gst.total;

console.log('Subtotal     ', formatINR(subtotal));
console.log(`Discount (${invoice.discountPct}%)`, formatINR(-discount));
console.log('Taxable value', formatINR(taxable));
console.log('CGST         ', formatINR(gst.cgst));
console.log('SGST         ', formatINR(gst.sgst));
console.log('Total payable', formatINR(total));
console.log('All integers?', [subtotal, discount, taxable, gst.cgst, gst.sgst, total]
  .every(Number.isInteger));

const due = addDays(invoice.date, invoice.termsDays);
console.log('Due on', due);
console.log('Days until due', daysBetween(invoice.date, due));
