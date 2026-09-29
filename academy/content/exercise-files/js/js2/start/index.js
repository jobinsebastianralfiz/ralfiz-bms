// Lesson 0.2: a small program for your professional project setup
// Copy this file into your new ralfiz-setup folder, then run: node index.js

const orders = [
  { id: 'R-1001', item: 'Notebook', price: 120, qty: 3 },
  { id: 'R-1002', item: 'Gel pen', price: 25, qty: 4 },
];

// TODO(4): ESLint will report this as "assigned a value but never used".
// Use it in formatOrder to show the price including GST, or delete it.
const taxRate = 0.18;

function printEnvironment() {
  // TODO(1): print the Node.js version with process.version
  // TODO(2): print the platform (process.platform) and the current
  //          folder (process.cwd()), each on its own line
  console.log('Environment: not implemented yet');
}

function formatOrder(order) {
  // TODO(3): return a string like  R-1001: 3 x Notebook = 360
  return order.id;
}

printEnvironment();
console.log(formatOrder(orders[0]));
console.log(formatOrder(orders[1]));
