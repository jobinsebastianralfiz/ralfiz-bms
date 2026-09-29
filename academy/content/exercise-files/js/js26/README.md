# js26 – Ralfiz lead cleaner

Partners send leads as pasted text: "name | email | phone | PIN", with messy
spacing and five phone formats. Clean, validate and summarise them with
regular expressions.

## Run

    cd javascript/js26/start
    node index.js

Node.js 22 or newer. The starter runs from the first minute; each TODO makes
more of the output correct.

## Tasks

1. TODO(1): write anchored EMAIL, MOBILE and PIN patterns.
2. TODO(2): split lines with a regex so spaces around "|" disappear.
3. TODO(3): normalise email (trim, lowercase), phone (+91 and 10 digits) and PIN.
4. TODO(4): total the paid orders in the log with matchAll and named groups.
5. TODO(5): redact phone numbers in a message, keeping the last 4 digits.
6. TODO(6): escape a search term before building a RegExp from it.
7. TODO(7): rewrite dd/mm/yyyy dates as yyyy-mm-dd with named groups.

## Acceptance criteria

- Anu and Meera are ok; Ravi is INVALID email; Sara is INVALID PIN;
  Tom is INVALID phone. "Valid leads: 2 of 5".
- Phones print as +919847012345 style, whatever the input format.
- "Paid total: ₹3,754.00" (refunded orders are ignored).
- "Redacted: Call Anu on ****2345 or Meera on ****5555 today."
- The search for "C++ (basics)" finds only "C++ (basics) batch" and does not throw.
- ISO dates: [ '2026-09-28', '2026-10-01' ].
