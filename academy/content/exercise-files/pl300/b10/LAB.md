# PL-300 · B.10 Optimize model performance

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- performance-scenario.md
- dax-queries.txt

## Steps
1. Download performance-scenario.md and dax-queries.txt, and read the complaint and the list of design problems.
2. Open your Help Desk report. Choose Optimize (or View) > Performance analyzer, then Start recording and Refresh visuals. Write the slowest visual and its DAX query, Visual display and Other times in the Before column.
3. Expand the slowest visual and choose Copy query. Open DAX query view, paste the query and run it. Confirm you get the same numbers as the visual.
4. Open a new query tab, paste Query 1 and Query 2 from dax-queries.txt and run each. Compare the Slow and Fast columns.
5. Run Query 3 and note which columns have the most distinct values.
6. In Power Query, right-click Tickets and choose Reference, then Group By CreatedDate and CategoryID with Count rows. Name it TicketsDaily, note its row count, and clear Enable load.
7. In Model view, check every relationship and set any Both cross-filter direction to Single. Keep Status and AssignedTo: the Close Rate measure and the matrix use them.
8. Open File > Options > Current file > Data load and turn off Auto date/time, since you now have your own Date table.
9. Record again with Performance Analyzer, fill in the After column of performance-scenario.md, and write one sentence each on items 5 and 6.

## Check your work
- [ ] Query 1 returns 4 rows: Accounts 10, Hardware 22, Network 16, Software 12.
- [ ] Query 2 returns one row, South, with Slow = 3 and Fast = 3 (North and City have no unresolved High tickets, so they are left out).
- [ ] Query 3 returns TicketID 60, CreatedDate 48, Campus 3, Priority 3.
- [ ] TicketsDaily has 54 rows instead of 60, because six day-and-category pairs have more than one ticket.
- [ ] After turning off Auto date/time, the date columns in the Data pane no longer show an expandable Date hierarchy.
