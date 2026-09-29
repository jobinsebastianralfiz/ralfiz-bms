# js18 · Order importer (errors and debugging)

Ralfiz Store receives batches of orders as JSON text. Build an importer that
never crashes on bad data, never hides real bugs, and reports every problem clearly.

## Run

    cd javascript/js18/start
    node index.js

Node.js 22 or newer. No dependencies.

## What to build
1. AppError extends Error (sets name from new.target, passes { cause } to super)
2. ValidationError (with a field) and ImportError
3. parseBatch(text): invalid JSON becomes an ImportError whose cause is the SyntaxError
4. validateOrder(order): id required; email must look like an email;
   qty an integer from 1 to 99; price a positive number
5. importOrders(text): collect all rejected orders, and always print "Import finished" (finally)
6. A report with console.table and a printed cause chain

## Acceptance criteria
- The good batch prints Accepted: 2 | Rejected: 4 and a table of the rejected orders
  with the field that failed, then Revenue from accepted orders: 1296.50
- The broken batch prints ImportError: Batch is not valid JSON, caused by a SyntaxError line
- "Import finished" is printed for both batches, even the broken one
- An unexpected error (not a ValidationError) is rethrown, not swallowed

## Debugging exercise
Run node --inspect-brk index.js, open chrome://inspect in Chrome, click "inspect",
set a conditional breakpoint in validateOrder with order.id === 'A-105', and step through it.
