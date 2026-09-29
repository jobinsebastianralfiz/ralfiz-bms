// js19 · The event loop in Node.js (solution)
// Run: node index.js

// ---------- Part 1: predict the order ----------
const predicted = [
  'timer callback (task)',
  'end of callback (sync)',
  'process.nextTick',
  'promise.then',
  'queueMicrotask',
  'setImmediate',
  'setTimeout 0',
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

// Why is this order fixed? We are inside the timers phase. After the callback,
// Node drains nextTick, then promise microtasks. The loop then moves on to the
// check phase (setImmediate) before it comes back round to timers (setTimeout 0).
// At the top level of a script, the loop may start before or after the 1 ms
// timer is due, so setTimeout(0) versus setImmediate can go either way.

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

function runChunked(sliceMs = 5) {
  return new Promise((resolve) => {
    const stop = heartbeat();
    const t0 = performance.now();
    let sum = 0;
    let i = 0;
    let slices = 0;

    function next() {
      const sliceStart = performance.now();
      while (i < TOTAL && performance.now() - sliceStart < sliceMs) {
        sum += processInvoice(i++);
      }
      slices++;
      if (i < TOTAL) setImmediate(next); // yield: timers and I/O get a turn
      else resolve({ sum, ticks: stop(), ms: Math.round(performance.now() - t0), slices });
    }
    next();
  });
}

part1()
  .then((order) => {
    console.log('Actual order:', order);
    const same = order.every((label, i) => label === predicted[i]);
    console.log('Prediction correct?', same);
    const blocking = runBlocking();
    console.log(`Blocking: ${blocking.ticks} heartbeat ticks in ${blocking.ms} ms`);
    return runChunked().then((chunked) => ({ blocking, chunked }));
  })
  .then(({ blocking, chunked }) => {
    console.log(
      `Chunked:  ${chunked.ticks > 0 ? 'more than 0' : '0'} heartbeat ticks ` +
        `(${chunked.slices} slices, about ${chunked.ms} ms)`,
    );
    console.log('Same invoice sum?', blocking.sum === chunked.sum);
    console.log('The blocking run starved the heartbeat; the chunked run shared the thread.');
  });
