// Lab 3.2 - Invoice Builder (starter)
// Run: node index.js

const catalogue = [
  { sku: 'PEN', title: 'Gel pen', price: 20 },
  { sku: 'NB', title: 'Ralfiz Notebook', price: 149 },
  { sku: 'BAG', title: 'Laptop bag', price: 899 },
  { sku: 'BTL', title: 'Steel bottle', price: 349 },
];

const orders = [
  {
    id: 'INV-1',
    customer: { name: 'Anu', address: { city: 'Kochi' } },
    lines: [{ sku: 'PEN', qty: 3 }, { sku: 'NB' }, { sku: 'NB', qty: 5 }],
  },
  { id: 'INV-2', customer: { name: 'Faris' }, lines: [{ sku: 'BAG' }] },
  { id: 'INV-3', lines: [{ sku: 'BTL', qty: 2 }] },
];

const snapshot = JSON.stringify(orders); // used at the end to prove no mutation

// TODO(1): freeze this object
const TAX = { rate: 0.18 };

// TODO(2): build { PEN: 20, NB: 149, ... } from catalogue with Object.fromEntries
const priceOf = {};

function buildInvoice(order) {
  // TODO(3): destructure id, customer and lines (default []) from order,
  // and give each line a default qty of 1
  const items = [];
  const subtotal = items.reduce((sum, i) => sum + i.amount, 0);
  return {
    id: order.id,
    // TODO(4): use ?. and ?? for billTo and city
    billTo: 'TODO',
    city: 'TODO',
    items,
    subtotal,
    tax: Math.round(subtotal * TAX.rate),
    total: Math.round(subtotal * (1 + TAX.rate)),
  };
}

// TODO(5): return a NEW invoice with amounts and totals reduced by percent
function applyDiscount(invoice, percent) {
  return invoice;
}

const invoices = orders.map(buildInvoice);

for (const inv of invoices) {
  // TODO(6): print each field of a summary object with Object.entries
  console.log(inv.id, inv.total);
}

const discounted = applyDiscount(invoices[0], 10);
console.log('Discounted total:', discounted.total, '| original:', invoices[0].total);
console.log('Original orders unchanged:', JSON.stringify(orders) === snapshot);
