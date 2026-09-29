# Lab 3.3 - Order Report

Build the month-end report for the Ralfiz Store with Map, Set,
Object.groupBy and JSON.

## Run it

    cd javascript/js14/start
    node index.js

Node.js 22 or newer (Object.groupBy and the Set methods are built in).

## Tasks (TODO markers in start/index.js)

1. TODO(1): revenue per category with Object.groupBy, sorted high to low.
2. TODO(2): spend per customer in a Map; print the top 3 customers.
3. TODO(3): a Set of customers for August and one for September.
4. TODO(4): repeat customers (bought in both months), new customers
   (September only) and lost customers (August only), using Set methods.
5. TODO(5): export the report with JSON.stringify and a replacer that turns
   Maps into objects and Sets into sorted arrays.
6. TODO(6): parse it back with a reviver that turns generatedAt into a Date.

## Acceptance criteria

- The first category line is Bags: 4495.
- The top customer is John with 3297.
- Repeat customers: Anu, Faris, John.
- New in September: Meera, Zara. Lost after August: Kiran.
- The last line prints generatedAt is a Date: true.

## Think about it

- Why can the Map not go straight into JSON.stringify?
- How would you write the repeat-customer check without Set methods?
