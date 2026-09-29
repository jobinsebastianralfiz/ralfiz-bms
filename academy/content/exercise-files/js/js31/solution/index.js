// Interview kata pack: 8 classic challenges and a tiny test runner.
// Run: node index.js

// 1. Reverse the order of words, ignoring extra spaces.
function reverseWords(s) {
  return s.trim().split(/\s+/).filter(Boolean).reverse().join(' ');
}

// 2. Anagram check, ignoring case, spaces and punctuation. O(n).
function isAnagram(a, b) {
  const clean = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  const x = clean(a);
  const y = clean(b);
  if (x.length !== y.length) return false;
  const counts = new Map();
  for (const ch of x) counts.set(ch, (counts.get(ch) ?? 0) + 1);
  for (const ch of y) {
    const left = counts.get(ch);
    if (!left) return false;
    counts.set(ch, left - 1);
  }
  return true;
}

// 3. FizzBuzz driven by a rules table.
function fizzBuzz(n, rules = [[3, 'Fizz'], [5, 'Buzz']]) {
  return Array.from({ length: n }, (_, i) => {
    const k = i + 1;
    const word = rules.filter(([d]) => k % d === 0).map(([, w]) => w).join('');
    return word || String(k);
  });
}

// 4. Flatten to a given depth.
function flatten(arr, depth = Infinity) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) out.push(...flatten(item, depth - 1));
    else out.push(item);
  }
  return out;
}

// 5. Deep clone with Date support and circular references.
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (value instanceof Date) return new Date(value);
  if (seen.has(value)) return seen.get(value);
  const copy = Array.isArray(value) ? [] : {};
  seen.set(value, copy);
  for (const [key, v] of Object.entries(value)) copy[key] = deepClone(v, seen);
  return copy;
}

// 6. Debounce that keeps `this` and the latest arguments.
function debounce(fn, wait) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}

// 7. Curry based on fn.length.
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return (...more) => curried.apply(this, [...args, ...more]);
  };
}

// 8. sleep and retry with exponential backoff.
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function retry(task, { retries = 3, delay = 10, factor = 2 } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      return await task(attempt);
    } catch (err) {
      if (attempt >= retries) {
        throw new Error(`Failed after ${attempt + 1} attempts`, { cause: err });
      }
      await sleep(delay * factor ** attempt);
    }
  }
}

// ---- tiny test runner ----
const results = [];
async function test(name, fn) {
  try {
    await fn();
    results.push(true);
    console.log(`  PASS  ${name}`);
  } catch (err) {
    results.push(false);
    console.log(`  FAIL  ${name}: ${err.message}`);
  }
}
function eq(actual, expected) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) throw new Error(`expected ${e}, got ${a}`);
}

async function main() {
  console.log('Strings');
  await test('reverseWords basic', () =>
    eq(reverseWords('learn JavaScript today'), 'today JavaScript learn'));
  await test('reverseWords extra spaces', () => eq(reverseWords('  a   b  '), 'b a'));
  await test('reverseWords empty', () => eq(reverseWords('   '), ''));
  await test('isAnagram true', () => eq(isAnagram('Dormitory', 'dirty room'), true));
  await test('isAnagram false', () => eq(isAnagram('aab', 'abb'), false));
  await test('fizzBuzz classic', () => eq(fizzBuzz(15).slice(-3), ['13', '14', 'FizzBuzz']));
  await test('fizzBuzz custom rules', () =>
    eq(fizzBuzz(7, [[2, 'Even'], [7, 'Lucky']]).slice(-2), ['Even', 'Lucky']));

  console.log('Arrays and objects');
  await test('flatten fully', () => eq(flatten([1, [2, [3, [4]]]]), [1, 2, 3, 4]));
  await test('flatten depth 1', () => eq(flatten([1, [2, [3]]], 1), [1, 2, [3]]));
  await test('deepClone is deep', () => {
    const src = { lines: [{ qty: 1 }] };
    const copy = deepClone(src);
    copy.lines[0].qty = 5;
    eq(src.lines[0].qty, 1);
  });
  await test('deepClone keeps Date', () =>
    eq(deepClone({ d: new Date(0) }).d instanceof Date, true));
  await test('deepClone handles cycles', () => {
    const a = { name: 'loop' };
    a.self = a;
    const b = deepClone(a);
    eq([b.self === b, b !== a], [true, true]);
  });

  console.log('Functions');
  await test('debounce runs once with the last value', async () => {
    const seen = [];
    const d = debounce((q) => seen.push(q), 30);
    d('p'); d('ph'); d('phone');
    await sleep(60);
    eq(seen, ['phone']);
  });
  await test('debounce keeps this', async () => {
    const box = { label: 'box', seen: '' };
    box.log = debounce(function () { this.seen = this.label; }, 10);
    box.log();
    await sleep(30);
    eq(box.seen, 'box');
  });
  const add3 = curry((a, b, c) => a + b + c);
  await test('curry one at a time', () => eq(add3(1)(2)(3), 6));
  await test('curry mixed groups', () =>
    eq([add3(1, 2)(3), add3(1)(2, 3), add3(1, 2, 3)], [6, 6, 6]));

  console.log('Async');
  await test('sleep waits', async () => {
    const t = Date.now();
    await sleep(40);
    eq(Date.now() - t >= 35, true);
  });
  await test('retry succeeds after failures', async () => {
    let calls = 0;
    const value = await retry(async () => {
      calls++;
      if (calls < 3) throw new Error('503');
      return 'paid';
    });
    eq([value, calls], ['paid', 3]);
  });
  await test('retry gives up with cause', async () => {
    let message = '';
    try {
      await retry(async () => { throw new Error('down'); }, { retries: 2, delay: 1 });
    } catch (err) {
      message = `${err.message} / ${err.cause?.message}`;
    }
    eq(message, 'Failed after 3 attempts / down');
  });
  await test('retry backs off exponentially', async () => {
    const t = Date.now();
    await retry(async (attempt) => { if (attempt < 2) throw new Error('x'); }, { delay: 20 });
    eq(Date.now() - t >= 55, true); // waits 20 + 40 ms
  });

  const passed = results.filter(Boolean).length;
  console.log(passed === results.length
    ? `\nAll ${passed} tests passed`
    : `\n${passed}/${results.length} tests passed`);
}

main();
