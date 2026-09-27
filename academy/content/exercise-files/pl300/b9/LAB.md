# PL-300 · B.9 Time intelligence and advanced calculations

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- date-table.txt
- measures-start.txt
- measures-solution.txt

## Steps
1. Download measures-start.txt and measures-solution.txt. If you have no Date table yet, create it from date-table.txt (B.6) with Modeling > New table.
2. Select the Date table, choose Mark as date table and pick the Date column. Set Month to sort by MonthNo.
3. In Model view, relate Date[Date] to Tickets[CreatedDate] (active) and to Tickets[ClosedDate] (inactive, dashed line).
4. Complete the starter file and create the measures: Ticket Count, Tickets YTD with TOTALYTD, Tickets prev month with DATEADD, and Tickets closed with USERELATIONSHIP.
5. Build a matrix with Date[Month] on rows and Ticket Count, Tickets YTD, Tickets prev month and Tickets closed as values.
6. Add the Median hours measure with MEDIAN(Tickets[HoursToResolve]) and put it in a card.
7. Choose New quick measure > Running total on Ticket Count by Date[Date] (or Month), add it to the matrix and read the DAX it generated.
8. Select the matrix, choose New calculation (visual calculation) and add RUNNINGSUM([Ticket Count]). Compare it with the quick measure.

## Check your work
- [ ] Ticket Count is 10 for every month Jan to Jun; Tickets YTD reads 10, 20, 30, 40, 50, 60, and stays at 60 for Jul to Dec.
- [ ] Tickets prev month is blank for Jan, 10 for Feb to Jun, and 10 for Jul (June’s count).
- [ ] Tickets closed by month is Jan 9, Feb 8, Mar 9, Apr 9, May 5, Jun 6, total 46: it differs from Ticket Count because 14 tickets are not closed.
- [ ] The Median hours card shows 14.15.
- [ ] The running total and RUNNINGSUM both reach 60 at June.
