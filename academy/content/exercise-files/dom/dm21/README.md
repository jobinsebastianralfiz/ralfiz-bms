# dm21 · Project: Ralfiz Money expense tracker

Build a complete expense tracker with plain HTML, CSS and JavaScript.

## Run it
Open the `start` folder in VS Code and use the Live Server extension, or run:

    npx serve start

Then open the address it prints. The `solution` folder is the finished app.

## Your tasks (see the TODOs in start/app.js)
1. TODO(1) load() and commit(): read from localStorage with a SEED fallback; every change saves, then renders.
2. TODO(2) visible() and totals: filter by month, sort newest first, sum in paise, group by category.
3. TODO(3) renderList(): clone the #row template and fill it with textContent.
4. TODO(4) submit: FormData → entry (amount in paise via Math.round) → add or update.
5. TODO(5) one delegated listener on #list for Edit and Delete, with an Undo toast.
6. TODO(6) renderChart(): SVG donut with createElementNS and stroke-dasharray, plus the legend.
7. TODO(7) exportCsv(): csvCell() escaping, Blob, object URL, download, revoke.

## Acceptance criteria
- Adding "Team lunch", 1850, Food shows a row with ₹1,850.00 and the total grows by the same amount.
- Editing an expense changes it in place (no duplicate row); Cancel leaves edit mode.
- Deleting shows a toast with Undo; Undo restores the row.
- The month select lists only months that have data; choosing one updates totals, list and chart.
- Reloading the page keeps every change.
- Export CSV downloads a file that opens in a spreadsheet with correct columns, even for a title containing a comma or quotes.
- At 375px wide nothing overflows horizontally.

## Think about it
- Why is the amount stored in paise and the date as a string?
- Which values are never stored because render() derives them?
