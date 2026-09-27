# Performance issue: "The Help Desk report is slow"

## The complaint
> "The Overview page takes about eight seconds to load every time I change the Campus slicer. The file is also 40 MB and refresh takes ages." (Suresh Kumar, help desk manager)

The production model holds three years of tickets from all campuses. Your 60-row copy is fast, but it has the same design, so you can find and fix the same problems.

## What the previous developer built
| # | Item | Detail |
|---|---|---|
| 1 | Relationship | Categories to Tickets with cross-filter direction set to **Both** |
| 2 | Auto date/time | Left **on**, so every date column gets a hidden date table, even though a Date table exists |
| 3 | Measure | Unresolved High Slow = COUNTROWS(FILTER(Tickets, ...)) iterates the whole Tickets table |
| 4 | Granularity | One row per ticket, but most pages only show counts per day and category |
| 5 | Columns | Production also loads Description (long free text) and a CreatedDateTime to the second; no visual uses them |
| 6 | Page | 14 visuals on the Overview page, including three cards that show the same number |

## Your tasks
1. Measure first: record the page with Performance Analyzer and write down the slowest visual and its three times (DAX query, Visual display, Other).
2. Test the queries in DAX query view using dax-queries.txt. Prove the slow and fast measures return the same numbers before you swap them.
3. Try a lower-granularity copy of Tickets (Group By CreatedDate and CategoryID) and note how many rows it has compared with Tickets.
4. Fix items 1 and 2 in your own file. Items 5 and 6 exist only in production: write one sentence for each saying what you would do.
5. Measure again and compare.

## Record your results
| Measurement | Before | After |
|---|---|---|
| Slowest visual |  |  |
| DAX query (ms) |  |  |
| Visual display (ms) |  |  |
| Other (ms) |  |  |
| Tickets rows / grouped rows |  |  |

## Hints
- Hiding a column does not remove it from memory. Only removing it in Power Query does.
- High-cardinality columns (many distinct values) compress badly. A date-time to the second has almost one value per row; a date has one per day.
- "Other" time is often waiting for other visuals. Fewer visuals per page lowers it.
- On 60 rows the times are tiny and change from run to run. Look at which visual is slowest and at the DAX query share, not the exact milliseconds.