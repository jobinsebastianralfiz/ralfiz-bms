# Lab 1.3 - Receipt toolkit

Build small, pure string helpers for the Ralfiz Store till and use them to
print a neat plain-text receipt.

## Run it

    cd javascript/js5/start
    node index.js

The starter runs straight away but prints placeholder values. Work through
the TODO markers in order. The finished version is in ../solution.

## Tasks

1. TODO(1) formatName: '  anu   KRISHNAN ' -> 'Anu Krishnan'
2. TODO(2) makeSku: makeSku('stationery', 42) -> 'RZ-STA-0042'
3. TODO(3) slugify: 'Café Menu: Autumn 2026!' -> 'cafe-menu-autumn-2026'
4. TODO(4) receiptLine: one 34-character line; names longer than 18
   characters are cut to 17 characters plus '…'
5. TODO(5) formatReceipt: a multi-line template literal with the customer,
   every line, an INR total (Intl.NumberFormat) and the cashiers joined with
   Intl.ListFormat
6. TODO(6) countChars: count graphemes with Intl.Segmenter

## Acceptance criteria

- node index.js prints Customer: Anu Krishnan and SKU: RZ-STA-0042
- The slug line prints cafe-menu-autumn-2026
- Every item line in the receipt is exactly 34 characters wide and the long
  name ends with …
- The total line prints Total: ₹1,265.00 and the cashier line prints
  Served by: Bala and Chitra
- The last line prints Great tee 👍🏽 -> 11 characters (length 14)
- No function changes its input; each returns a new string
