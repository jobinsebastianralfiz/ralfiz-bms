// Ralfiz Store: a typed order module.
// Build: npx -p typescript tsc -p .   Run: node dist/index.js

type Category = 'books' | 'electronics' | 'stationery';
type OrderStatus = 'pending' | 'paid' | 'shipped' | 'cancelled';

interface Product {
  id: number;
  title: string;
  price: number; // rupees
  category: Category;
  stock: number;
  discountPercentage?: number;
}

interface CartLine {
  product: Product;
  qty: number;
}

type Payment =
  | { kind: 'upi'; vpa: string }
  | { kind: 'card'; last4: string; network: 'visa' | 'rupay' | 'mastercard' }
  | { kind: 'cod' };

interface Order {
  id: string;
  lines: CartLine[];
  payment: Payment;
  status: OrderStatus;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

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

function assertNever(x: never): never {
  throw new Error('Unhandled case: ' + JSON.stringify(x));
}

function paymentFee(payment: Payment, amount: number): number {
  switch (payment.kind) {
    case 'upi':
      return 0;
    case 'card':
      return Math.round(amount * 0.018);
    case 'cod':
      return 40;
    default:
      return assertNever(payment);
  }
}

function describePayment(payment: Payment): string {
  switch (payment.kind) {
    case 'upi':
      return `UPI (${payment.vpa})`;
    case 'card':
      return `${payment.network.toUpperCase()} card ending ${payment.last4}`;
    case 'cod':
      return 'Cash on delivery';
    default:
      return assertNever(payment);
  }
}

function groupBy<T, K extends string>(
  items: readonly T[],
  keyOf: (item: T) => K,
): Partial<Record<K, T[]>> {
  const groups: Partial<Record<K, T[]>> = {};
  for (const item of items) {
    (groups[keyOf(item)] ??= []).push(item);
  }
  return groups;
}

function addToCart(lines: CartLine[], productId: number, qty: number): Result<CartLine[]> {
  const product = catalogue.find((p) => p.id === productId);
  if (!product) return { ok: false, error: `No product with id ${productId}` };
  if (qty > product.stock) {
    return { ok: false, error: `Only ${product.stock} of "${product.title}" left` };
  }
  return { ok: true, value: [...lines, { product, qty }] };
}

const CATEGORIES: readonly Category[] = ['books', 'electronics', 'stationery'];

function isProduct(x: unknown): x is Product {
  if (typeof x !== 'object' || x === null) return false;
  const p = x as Record<string, unknown>;
  return (
    typeof p.id === 'number' &&
    typeof p.title === 'string' &&
    typeof p.price === 'number' &&
    typeof p.stock === 'number' &&
    CATEGORIES.includes(p.category as Category) &&
    (p.discountPercentage === undefined || typeof p.discountPercentage === 'number')
  );
}

// ---- main ----
let lines: CartLine[] = [];
const requests: Array<[id: number, qty: number]> = [[3, 1], [4, 1], [1, 2], [2, 5], [99, 1]];
for (const [id, qty] of requests) {
  const result = addToCart(lines, id, qty);
  if (result.ok) lines = result.value;
  else console.log('Skipped:', result.error);
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
for (const [category, group] of Object.entries(byCategory)) {
  console.log(`  ${category}: ${group?.length ?? 0} line(s)`);
}

const payload: unknown = JSON.parse(
  '[{"id":5,"title":"Desk Lamp","price":899,"category":"electronics","stock":6},' +
    '{"id":"6","title":"Broken row","price":10,"category":"books","stock":1}]',
);
const incoming = Array.isArray(payload) ? payload : [];
const valid = incoming.filter(isProduct);
const titles = valid.map((p) => p.title).join(', ');
console.log(`\nAPI payload: ${valid.length} valid of ${incoming.length}: ${titles}`);
