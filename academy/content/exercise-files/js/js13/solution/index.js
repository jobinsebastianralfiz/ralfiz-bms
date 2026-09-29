// Lab 3.2 - Invoice Builder (solution)
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

const snapshot = JSON.stringify(orders);

const TAX = Object.freeze({ rate: 0.18 });

const priceOf = Object.fromEntries(catalogue.map((p) => [p.sku, p.price]));

function buildInvoice({ id, customer, lines = [] }) {
  const items = lines.map(({ sku, qty = 1 }) => ({
    sku,
    qty,
    amount: priceOf[sku] * qty,
  }));
  const subtotal = items.reduce((sum, i) => sum + i.amount, 0);
  return {
    id,
    billTo: customer?.name ?? 'Walk-in customer',
    city: customer?.address?.city ?? '-',
    items,
    subtotal,
    tax: Math.round(subtotal * TAX.rate),
    total: Math.round(subtotal * (1 + TAX.rate)),
  };
}

function applyDiscount(invoice, percent) {
  const copy = structuredClone(invoice);
  const factor = 1 - percent / 100;
  for (const item of copy.items) item.amount = Math.round(item.amount * factor);
  copy.subtotal = copy.items.reduce((sum, i) => sum + i.amount, 0);
  copy.tax = Math.round(copy.subtotal * TAX.rate);
  copy.total = copy.subtotal + copy.tax;
  return copy;
}

const invoices = orders.map(buildInvoice);

for (const inv of invoices) {
  const { id, billTo, city, items, subtotal, tax, total } = inv;
  const summary = {
    'Bill to': billTo,
    City: city,
    Lines: items.length,
    Subtotal: subtotal,
    Tax: tax,
    Total: total,
  };
  console.log(`\n${id}`);
  for (const [label, value] of Object.entries(summary)) {
    console.log(`  ${label}: ${value}`);
  }
}

const discounted = applyDiscount(invoices[0], 10);
console.log('\nDiscounted total:', discounted.total, '| original:', invoices[0].total);

TAX.rate = 0; // ignored: TAX is frozen
console.log('Tax rate still', TAX.rate);
console.log('Original orders unchanged:', JSON.stringify(orders) === snapshot);
