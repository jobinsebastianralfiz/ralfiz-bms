// js19 · The event loop in Node.js
// Run: node index.js

// ---------- Part 1: predict the order ----------
// TODO(1): before running, write the order you expect (7 labels)
const predicted = [
  // 'timer callback (task)', ...
];

function part1() {
  return new Promise((resolve) => {
    const order = [];
    setTimeout(() => {
      order.push('timer callback (task)');
      setTimeout(() => {
        order.push('setTimeout 0');
        resolve(order);
      }, 0);
      setImmediate(() => order.push('setImmediate'));
      Promise.resolve().then(() => order.push('promise.then'));
      queueMicrotask(() => order.push('queueMicrotask'));
      process.nextTick(() => order.push('process.nextTick'));
      order.push('end of callback (sync)');
    }, 0);
  });
}

// TODO(2): explain in a comment why this order is fixed inside a timer callback,
// but setTimeout(0) versus setImmediate at the top level of a script is not.

// ---------- Part 2: blocking versus chunked ----------
const TOTAL = 400_000;

function processInvoice(i) {
  let total = 0;
  for (let k = 0; k < 60; k++) total += ((i * 31 + k) % 997) * 1.18;
  return Math.round(total);
}

function heartbeat() {
  let ticks = 0;
  const id = setInterval(() => ticks++, 10);
  return () => {
    clearInterval(id);
    return ticks;
  };
}

function runBlocking() {
  const stop = heartbeat();
  const t0 = performance.now();
  let sum = 0;
  for (let i = 0; i < TOTAL; i++) sum += processInvoice(i);
  return { sum, ticks: stop(), ms: Math.round(performance.now() - t0) };
}

// TODO(3): runChunked() returns a Promise of { sum, ticks, ms }.
// Work for about 5 ms, then yield with setImmediate(next), until all TOTAL invoices are done.
function runChunked() {
  return Promise.resolve({ sum: 0, ticks: 0, ms: 0 });
}

part1()
  .then((order) => {
    console.log('Actual order:   ', order);
    console.log('Your prediction:', predicted);
    const blocking = runBlocking();
    console.log('Blocking:', blocking);
    return runChunked();
  })
  .then((chunked) => {
    // TODO(4): print the chunked result and compare the sums
    console.log('Chunked (TODO):', chunked);
  });
