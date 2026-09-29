// js18 · Order importer (solution)
// Run: node index.js

const goodBatch = `[
  { "id": "A-101", "email": "anu@example.com", "qty": 2, "price": 499 },
  { "id": "A-102", "email": "rahul@example", "qty": 1, "price": 1299 },
  { "id": "A-103", "email": "fathima@example.com", "qty": 0, "price": 250 },
  { "id": "A-104", "email": "joel@example.com", "qty": 3, "price": 99.5 },
  { "email": "no-id@example.com", "qty": 1, "price": 10 },
  { "id": "A-105", "email": "meera@example.com", "qty": 1, "price": -40 }
]`;
const brokenBatch = '[{ "id": "A-201", "qty": 2, }';

class AppError extends Error {
  constructor(message, options) {
    super(message, options);
    this.name = new.target.name;
  }
}

class ValidationError extends AppError {
  constructor(field, message) {
    super(message);
    this.field = field;
  }
}

class ImportError extends AppError {}

function parseBatch(text) {
  try {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) throw new ImportError('Batch must be a JSON array');
    return data;
  } catch (err) {
    if (err instanceof SyntaxError) {
      throw new ImportError('Batch is not valid JSON', { cause: err });
    }
    throw err;
  }
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateOrder(order) {
  if (!order.id) throw new ValidationError('id', 'Order id is required');
  if (!EMAIL.test(order.email ?? '')) {
    throw new ValidationError('email', `"${order.email}" is not a valid email`);
  }
  if (!Number.isInteger(order.qty) || order.qty < 1 || order.qty > 99) {
    throw new ValidationError('qty', `qty must be 1 to 99, got ${order.qty}`);
  }
  if (typeof order.price !== 'number' || !(order.price > 0)) {
    throw new ValidationError('price', `price must be positive, got ${order.price}`);
  }
  return order;
}

function importOrders(text, label) {
  const accepted = [];
  const rejected = [];
  try {
    for (const order of parseBatch(text)) {
      try {
        accepted.push(validateOrder(order));
      } catch (err) {
        if (!(err instanceof ValidationError)) throw err; // a bug: do not hide it
        rejected.push({ id: order.id ?? '(none)', field: err.field, message: err.message });
      }
    }
    return { accepted, rejected };
  } finally {
    console.log(`[${label}] Import finished`);
  }
}

function causeChain(err) {
  const lines = [];
  for (let e = err; e; e = e.cause) lines.push(`${e.name}: ${e.message}`);
  return lines.join('\n  caused by ');
}

console.log('--- Good batch ---');
const { accepted, rejected } = importOrders(goodBatch, 'good');
console.log(`Accepted: ${accepted.length} | Rejected: ${rejected.length}`);
console.table(rejected);
const revenue = accepted.reduce((sum, o) => sum + o.qty * o.price, 0);
console.log('Revenue from accepted orders:', revenue.toFixed(2));

console.log('--- Broken batch ---');
try {
  importOrders(brokenBatch, 'broken');
} catch (err) {
  if (!(err instanceof ImportError)) throw err;
  console.log(causeChain(err));
  console.log('Is the cause a SyntaxError?', err.cause instanceof SyntaxError);
}

console.log('--- An unexpected error is rethrown ---');
try {
  importOrders('[null]', 'null order');
} catch (err) {
  console.log(`Surfaced, not swallowed: ${err.name}`);
}
