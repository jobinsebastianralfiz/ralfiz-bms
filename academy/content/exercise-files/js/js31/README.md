# js31 Lab: interview kata pack

Eight classic interview challenges with a tiny test runner:
reverse words, anagram check, FizzBuzz variants, flatten, deep clone,
debounce, curry, and sleep with retry.

## How to run
```bash
cd start
node index.js
```
Node.js 22 or newer. No packages needed.

## How to practise
For each TODO, before you type any code, say out loud (or write as a comment):
1. what the input and output are, and one edge case;
2. the brute-force idea and its time complexity;
3. the better idea and its time complexity.

Then implement it, run `node index.js`, and watch its tests turn from FAIL to PASS.

## Acceptance criteria
- `node index.js` ends with `All 20 tests passed`.
- No function uses `structuredClone`, `.flat()` or a library to do the work.
- `debounce` keeps `this` (the "debounce keeps this" test passes).
- `retry` throws `Failed after N attempts` with the last error as `cause`.
- Bonus: solve all eight again from a blank file in under 60 minutes.
