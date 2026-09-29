// index.js: the entry module
// Run: node index.js          or: node index.js --save
import Cart, { formatINR, GST_RATE } from './cart.js';

const cart = new Cart()
  .add('Cotton Kurta', 1299, 2)
  .add('Steel Bottle', 499)
  .add('Laptop Sleeve', 899);

console.log(cart.lines().join('\n'));
console.log(`GST ${GST_RATE * 100}%: ${formatINR(cart.gst)}`);
console.log(`Loaded as an ES module: ${import.meta.url.split('/').at(-1)}`);

if (process.argv.includes('--save')) {
  // Only load the file-system module when we actually need it
  const { writeFile } = await import('node:fs/promises');
  const out = new URL('./invoice.txt', import.meta.url);
  await writeFile(out, cart.lines().join('\n') + '\n');
  console.log(`Saved ${out.pathname.split('/').at(-1)}`);
}
