# Lesson 1.1 lab: Shop Bill, version 1

## Task
Build the first version of the Ralfiz Store console bill using only
variables, primitive types and arithmetic. Later lessons extend it.

## How to run
```bash
cd javascript/js3/start
node index.js
```
Solve the TODOs in order and run the file after each one. Use `const`
everywhere unless a value is reassigned.

## Acceptance criteria
- The bill prints Subtotal: 580, Member discount: 58, Taxable: 522,
  GST (18%): 93.96 and Total: 615.96.
- Setting `isMember` to `false` gives Member discount: 0 and Total: 684.40.
- The typeof report prints string, boolean, object, bigint and symbol.
- The items line prints 4 items, including Sticky notes.
- There is no `let` or `var` in your finished file.

## Think about it
- Why is `typeof couponCode` `'object'` when couponCode is null?
- Why can you push to `items` even though it is a const?
