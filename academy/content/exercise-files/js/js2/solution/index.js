// Lesson 0.2: solution. Run with: npm start  (or node index.js)

const orders = [
  { id: 'R-1001', item: 'Notebook', price: 120, qty: 3 },
  { id: 'R-1002', item: 'Gel pen', price: 25, qty: 4 },
];

const taxRate = 0.18;

function printEnvironment() {
  console.log('Node.js:', process.version);
  console.log('Platform:', process.platform);
  console.log('Folder:', process.cwd());
}

function formatOrder(order) {
  const total = order.price * order.qty;
  const withGst = total * (1 + taxRate);
  return `${order.id}: ${order.qty} x ${order.item} = ${total} (incl. GST ${withGst.toFixed(2)})`;
}

printEnvironment();
console.log(formatOrder(orders[0]));
console.log(formatOrder(orders[1]));
