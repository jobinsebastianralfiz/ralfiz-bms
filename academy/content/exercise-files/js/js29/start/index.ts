// Ralfiz Store: order module, loosely typed. Make it strict and safe.
// Build: npx -p typescript tsc -p .   Run: node dist/index.js

// TODO(1): create type Category = 'books' | 'electronics' | 'stationery'
// and use it for Product.category instead of string.
type OrderStatus = 'pending' | 'paid' | 'shipped' | 'cancelled';

interface Product {
  id: number;
  title: string;
  price: number; // rupees
  category: string;
  stock: number;
  discountPercentage?: number;
}

interface CartLine {
  product: Product;
  qty: number;
}

// TODO(2): turn Payment into a discriminated union:
//   { kind: 'upi'; vpa: string }
//   { kind: 'card'; last4: string; network: 'visa' | 'rupay' | 'mastercard' }
//   { kind: 'cod' }
type Payment = { kind: string; [key: string]: unknown };

interface Order {
  id: string;
  lines: CartLine[];
  payment: Payment;
  status: OrderStatus;
}

const catalogue: readonly Product[] = [
  { id: 1, title: 'Ralfiz Notebook A5', price: 120, category: 'stationery', stock: 40 },
  { id: 2, title: 'Gel Pen (pack of 5)', price: 90, category: 'stationery', stock: 3 },
  { id: 3, title: 'JavaScript: Zero to Job-Ready', price: 499, category: 'books',
    stock: 12, discountPercentage: 10 },
  { id: 4, title: 'USB-C Charger 30W', price: 1299, category: 'electronics',
    stock: 8, discountPercentage: 15 },
];

const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

function lineTotal(line: CartLine): number {
  const { price, discountPercentage = 0 } = line.product;
  return Math.round(price * (1 - discountPercentage / 100)) * line.qty;
}

function orderTotal(order: Order): number {
  return order.lines.reduce((sum, line) => sum + lineTotal(line), 0);
}

// TODO(2 continued): switch on payment.kind. upi costs 0, card 1.8% of the
// amount (rounded), cod a flat 40.
// TODO(3): add assertNever(x: never): never and call it in the default branch.
function paymentFee(payment: Payment, amount: number): number {
  return 0;
}

function describePayment(payment: Payment): string {
  return String(payment.kind);
}

// TODO(4): make this generic: groupBy<T, K extends string>(items: readonly T[],
// keyOf: (item: T) => K): Partial<Record<K, T[]>>. Remove every any.
function groupBy(items: any[], keyOf: (item: any) => string): any {
  const groups: any = {};
  for (const item of items) {
    (groups[keyOf(item)] ??= []).push(item);
  }
  return groups;
}

// TODO(5): add type Result<T> = { ok: true; value: T } | { ok: false; error: string }
// and return it instead of throwing. Update the loop in main to check result.ok.
function addToCart(lines: CartLine[], productId: number, qty: number): CartLine[] {
  const product = catalogue.find((p) => p.id === productId);
  if (!product) throw new Error(`No product with id ${productId}`);
  if (qty > product.stock) throw new Error(`Only ${product.stock} of "${product.title}" left`);
  return [...lines, { product, qty }];
}

// TODO(6): write isProduct(x: unknown): x is Product. Check id, title, price,
// stock and category, and allow discountPercentage to be missing.
function isProduct(x: unknown): boolean {
  return false;
}

// ---- main ----
let lines: CartLine[] = [];
const requests: Array<[id: number, qty: number]> = [[3, 1], [4, 1], [1, 2], [2, 5], [99, 1]];
for (const [id, qty] of requests) {
  try {
    lines = addToCart(lines, id, qty);
  } catch (err) {
    console.log('Skipped:', err instanceof Error ? err.message : err);
  }
}

const order: Order = {
  id: 'RZ-1042',
  lines,
  payment: { kind: 'card', last4: '4242', network: 'rupay' },
  status: 'pending',
};

console.log(`\nOrder ${order.id} (${order.status})`);
for (const line of order.lines) {
  const amount = inr.format(lineTotal(line)).padStart(9);
  console.log(`  ${line.qty} x ${line.product.title.padEnd(32)} ${amount}`);
}
const subtotal = orderTotal(order);
const fee = paymentFee(order.payment, subtotal);
console.log(
  `  Subtotal ${inr.format(subtotal)} | ${describePayment(order.payment)} ` +
    `fee ${inr.format(fee)} | Total ${inr.format(subtotal + fee)}`,
);

const byCategory = groupBy(order.lines, (line) => line.product.category);
console.log('  Groups:', Object.keys(byCategory).join(', '));

const payload: unknown = JSON.parse(
  '[{"id":5,"title":"Desk Lamp","price":899,"category":"electronics","stock":6},' +
    '{"id":"6","title":"Broken row","price":10,"category":"books","stock":1}]',
);
const incoming = Array.isArray(payload) ? payload : [];
const valid = incoming.filter(isProduct);
console.log(`\nAPI payload: ${valid.length} valid of ${incoming.length}`);
