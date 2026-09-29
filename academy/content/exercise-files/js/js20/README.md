# js20 · From callbacks to promises

The Ralfiz Store "legacy API" at the top of index.js uses error-first callbacks.
Wrap it in promises and rebuild the store's data loading with chains and combinators.
(Do not use async/await yet: that is the next lesson.)

## Run

    cd javascript/js20/start
    node index.js

Node.js 22 or newer. No dependencies.

## What to build
1. promisify(fn) and promise versions of getUser, getOrders, getStock, getReviews, slowReport
2. userSummary(id): one flat chain returning { name, orders, total }, with one catch
3. loadDashboard(): user summary + two stock levels in parallel with Promise.all
4. loadWithReviews(): Promise.allSettled so the failing reviews service does not break the page
5. withTimeout(promise, ms) built with Promise.race
6. An approval created with Promise.withResolvers and resolved later

## Acceptance criteria
- Summary for 7 prints { name: 'Anu', orders: 3, total: 5349 }
- Summary for 99 prints { name: 'unknown', orders: 0, total: 0 } (the catch recovered)
- The dashboard prints stock for SKU-1 (12) and SKU-2 (0) and finishes in about the time
  of the slowest call, not the sum
- allSettled prints fulfilled, rejected (Reviews service is down)
- withTimeout prints Timed out after 200 ms
- The approval prints Approved by Meera
