# Lab 1.4 - GST invoice in paise

Build the maths behind a Ralfiz Billing invoice so it never loses a paisa,
and handle due dates without time zone surprises.

## Run it

    cd javascript/js6/start
    node index.js

The starter runs and prints placeholder values. Complete TODO(1) to TODO(6).
The finished version is in ../solution.

## Rules

- Convert rupees to paise once (toPaise). After that, only integers.
- Round with Math.round exactly where the task says: the discount and the GST.
- CGST and SGST are the two halves of GST and must add up exactly to it.
- Format money only for display, with one shared Intl.NumberFormat.
- Do date maths with Date.UTC so the result is the same in every time zone.

## Acceptance criteria

- toPaise('249.99') is 24999, toPaise(0.1) is 10 and toPaise('abc') is NaN
- Subtotal prints ₹3,498.47, Discount (10%) prints -₹349.85,
  Taxable value prints ₹3,148.62
- CGST prints ₹283.37, SGST prints ₹283.38 and Total payable prints ₹3,715.37
- Every paise value printed by the check line is an integer (true)
- Due on prints 2026-03-02 and Days until due prints 30
