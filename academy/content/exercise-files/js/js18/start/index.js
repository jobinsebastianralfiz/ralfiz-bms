// js18 · Order importer
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

// TODO(1): class AppError extends Error
//   constructor(message, options) { super(message, options); this.name = new.target.name; }

// TODO(2): class ValidationError extends AppError (store this.field)
//          class ImportError extends AppError

function parseBatch(text) {
  // TODO(3): wrap JSON.parse in try/catch.
  //   On a SyntaxError: throw new ImportError('Batch is not valid JSON', { cause: err })
  //   Anything else: rethrow it.
  return JSON.parse(text);
}

function validateOrder(order) {
  // TODO(4): throw a ValidationError(field, message) when:
  //   - id is missing
  //   - email does not match /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  //   - qty is not an integer from 1 to 99
  //   - price is not a positive number
  return order;
}

function importOrders(text) {
  // TODO(5): parse, then validate each order in its own try/catch.
  //   Push valid orders to accepted and { id, field, message } to rejected.
  //   Rethrow errors that are not ValidationErrors.
  //   Use finally to print 'Import finished' even when parsing throws.
  const orders = parseBatch(text);
  return { accepted: orders, rejected: [] };
}

// TODO(6): print a report for goodBatch (counts + console.table of rejected),
//   then import brokenBatch inside try/catch and print the cause chain.
const result = importOrders(goodBatch);
console.log(`Accepted: ${result.accepted.length} | Rejected: ${result.rejected.length}`);
console.log('Nothing is validated yet: work through the TODOs.');
