# js25 – Modernise the Ralfiz order report

The file start/index.js is a working order report written in pre-2020 style.
It also hides two bugs that modern JavaScript fixes:

- a coupon with percent: 0 is treated as missing and gets the 5% default;
- the snapshot made with JSON.parse(JSON.stringify()) turns dates into strings,
  and sorting for the top 3 reorders the paid list.

## Run

    cd javascript/js25/start
    node index.js

You need Node.js 22 or newer (Set methods and iterator helpers are ES2025).
package.json sets "type": "module", which top-level await needs.

## Tasks

Work through TODO(1) to TODO(7) in index.js. Use ??, structuredClone,
toSorted, Object.groupBy, Set.prototype.intersection, Promise.withResolvers
with top-level await, and iterator helpers. Replace var with const/let and
function expressions with arrows as you go.

## Acceptance criteria

- Revenue changes from ₹5,393.55 to ₹5,520.50 once TODO(1) is fixed (the
  FESTIVE order no longer gets 5% off).
- "Snapshot keeps dates: true".
- "First order in the list: ORD-1001" (the list is no longer reordered).
- The By city block lists Chennai, Kochi and Pune with the same counts as before.
- "Bought PEN and BAG: anu, tom".
- The USD line and "First two orders over ₹1,000: ORD-1001, ORD-1003" print
  after the report, with no callbacks left in the file.
- Compare your file with solution/index.js.
