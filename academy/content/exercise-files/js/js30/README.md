# js30 Lab: speed up the nightly order report

The Ralfiz Store report sums revenue by city and VIP revenue for 30,000
orders and 3,000 customers. It is correct, but slow. Make it fast without
changing its output, and make sure the cache you add cannot leak memory.

## How to run
```bash
cd start
node index.js
```
Node.js 22 or newer. No packages needed.

## Tasks
1. TODO(1): index customers in a `Map` by id, once, before the loop.
2. TODO(2): turn the `vip` array into a `Set` and use `has`.
3. TODO(3): write `memoize(fn)` with a `Map` cache and use it for `gstRate`.
4. TODO(4): measure both reports with `performance.now()`.
5. TODO(5): limit the memo cache to `max` entries with least-recently-used eviction.
6. TODO(6): implement `debounce` and `throttle` and check the simulated burst.

## Acceptance criteria
- The output prints `Same result: true`.
- The fast report is at least 10x faster than the slow one (timings vary by machine).
- `LRU cache size after 10,000 calls with 500 keys: 50`.
- `Debounced calls: 1 -> [ 'phone charger' ]`.
- Throttled calls are about 4 to 6 for 20 events over 400 ms, not 20.
