// Lab 1.4 - GST invoice in paise (solution)
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

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const DAY_MS = 24 * 60 * 60 * 1000;

function toPaise(rupees) {
  const value = typeof rupees === 'string' ? Number(rupees.trim()) : rupees;
  if (typeof value !== 'number' || !Number.isFinite(value)) return NaN;
  return Math.round(value * 100);
}

function lineTotal(line) {
  return toPaise(line.price) * line.qty;
}

function discountPaise(subtotal, percent) {
  return Math.round(subtotal * percent / 100);
}

function gstSplit(taxable, ratePercent) {
  const gst = Math.round(taxable * ratePercent / 100);
  const cgst = Math.floor(gst / 2);
  return { cgst, sgst: gst - cgst, total: gst };
}

function formatINR(paise) {
  return inr.format(paise / 100);
}

function toUtc(isoDate) {
  const [year, month, day] = isoDate.split('-').map(Number);
  return Date.UTC(year, month - 1, day);   // months are 0-based
}

function addDays(isoDate, days) {
  const time = toUtc(isoDate) + days * DAY_MS;
  return new Date(time).toISOString().slice(0, 10);
}

function daysBetween(fromIso, toIso) {
  return Math.round((toUtc(toIso) - toUtc(fromIso)) / DAY_MS);
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
