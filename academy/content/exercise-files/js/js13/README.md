# Lab 3.2 - Invoice Builder

Turn messy shop orders into clean invoices using modern object techniques,
without mutating the original data.

## Run it

    cd javascript/js13/start
    node index.js

Node.js 22 or newer. No packages needed.

## Tasks (TODO markers in start/index.js)

1. TODO(1): freeze the TAX config so it cannot be changed.
2. TODO(2): build priceOf, an object that maps sku to price, with Object.fromEntries.
3. TODO(3): in buildInvoice, destructure the order with a default of [] for lines,
   and each line with a default qty of 1.
4. TODO(4): read the customer name and city with ?. and ??
   (fallbacks: 'Walk-in customer' and '-').
5. TODO(5): write applyDiscount(invoice, percent) that returns a NEW invoice
   (use structuredClone) with every item amount and the totals reduced.
6. TODO(6): print a summary object per invoice with Object.entries, and prove
   the original orders array is unchanged.

## Acceptance criteria

- INV-1 prints Total: 1126 (subtotal 954 + tax 172).
- INV-2 (no customer address) prints City: - and does not crash.
- INV-3 (no customer at all) prints Bill to: Walk-in customer.
- After applyDiscount(..., 10) the discounted INV-1 total is 1014,
  and the original invoice still shows 1126.
- The last line prints Original orders unchanged: true.

## Think about it

- Why is { ...invoice } not enough inside applyDiscount?
- What would happen if an order line had qty: null? How would you fix it?
