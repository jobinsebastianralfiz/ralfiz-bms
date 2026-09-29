// Interview kata pack: 8 classic challenges and a tiny test runner.
// Run: node index.js   Most tests fail at first; make them pass one by one.
// Say each step out loud as you go: clarify, examples, brute force, improve,
// code, test by hand.

// TODO(1): reverse the order of words. Ignore leading, trailing and repeated
// spaces. reverseWords('  a   b  ') returns 'b a'.
function reverseWords(s) {
  return s;
}

// TODO(2): return true if a and b use the same letters and digits the same
// number of times, ignoring case, spaces and punctuation. Aim for O(n) with a Map.
function isAnagram(a, b) {
  return false;
}

// TODO(3): return an array of n strings. For each number k from 1 to n, join
// the words of every rule [divisor, word] that divides k, or use String(k).
function fizzBuzz(n, rules = [[3, 'Fizz'], [5, 'Buzz']]) {
  return [];
}

// TODO(4): flatten nested arrays up to `depth` levels (like arr.flat(depth)),
// without calling .flat().
function flatten(arr, depth = Infinity) {
  return arr;
}

// TODO(5): deep clone primitives, arrays, plain objects and Date. Use the
// `seen` WeakMap to return the existing copy for circular references.
function deepClone(value, seen = new WeakMap()) {
  return value;
}

// TODO(6): return a function that waits until calls stop for `wait` ms, then
// calls fn once with the latest arguments and the same `this`.
function debounce(fn, wait) {
  return function (...args) {
    return fn.apply(this, args);
  };
}

// TODO(7): collect arguments until there are at least fn.length of them,
// then call fn. add3(1)(2)(3), add3(1, 2)(3) and add3(1, 2, 3) all work.
function curry(fn) {
  return (...args) => fn(...args);
}

// TODO(8): sleep(ms) resolves after ms milliseconds. retry(task, options)
// calls task(attempt); on failure it waits delay * factor ** attempt ms and
// tries again, up to `retries` extra times, then throws
// new Error(`Failed after N attempts`, { cause: lastError }).
function sleep(ms) {
  return Promise.resolve();
}

async function retry(task, { retries = 3, delay = 10, factor = 2 } = {}) {
  return task(0);
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
