# Lesson 1.2 lab: Shop Bill, version 2 (checkout rules)

## Task
Five orders arrive from the Ralfiz Store checkout form. The starter prints
wrong totals because of coercion bugs, a || that should be ??, a missing
coupon rule and an operator-precedence bug. Fix them TODO by TODO.

## How to run
```bash
cd javascript/js4/start
node index.js
```
Read the output before you change anything: R-1001 prints a total of 50030.
Can you explain where that number comes from?

## Acceptance criteria
- R-1001 prints Total: 530.00 (gift wrap 30 is added as a number).
- R-1002 prints discount 89.9 and Total: 809.10 (members ship free).
- R-1003 prints delivery 0 and Total: 1062.00 (a fee of 0 is kept).
- R-1004 prints subtotal 300 (an empty quantity counts as 0).
- R-1005 prints delivery 40 and Total: 2440.00 (bulky items never ship free).
- The file contains no == or !=.
