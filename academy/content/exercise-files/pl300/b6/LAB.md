# PL-300 · B.6 Star schema and relationships

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- date-table.txt

## Steps
1. Complete the star schema builder challenges above.
2. Download date-table.txt.
3. In Power BI Desktop, open Model view. Check that Categories to Tickets on CategoryID is one-to-many with single cross-filter direction.
4. On the Modeling tab choose New table and paste the Date table DAX from date-table.txt.
5. Select the Date table and use Mark as date table, choosing the Date column.
6. Drag Date[Date] onto Tickets[CreatedDate] (active). Then drag Date[Date] onto Tickets[ClosedDate]; this one is created inactive and shows as a dashed line.
7. Select Date[Month] and set Sort by column to MonthNo. Hide Tickets[CategoryID] and MonthNo from report view.
8. Build a table visual with Categories[Team] and Date[Month] and a count of TicketID to confirm filters flow correctly.

## Check your work
- [ ] The Date table has 365 rows (1 January to 31 December 2026).
- [ ] Model view shows three relationships into Tickets: Categories (solid), Date on CreatedDate (solid) and Date on ClosedDate (dashed).
- [ ] In the table visual, Infrastructure has 6, 3, 8, 5, 7 and 9 tickets for Jan to Jun (38 in all), Identity 10 and Applications 12; the total is 60.
- [ ] Months appear Jan, Feb, Mar… rather than alphabetical order (Apr, Feb, Jan…).
