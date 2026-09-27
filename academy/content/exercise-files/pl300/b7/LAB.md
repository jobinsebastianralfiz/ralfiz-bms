# PL-300 · B.7 DAX fundamentals

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- measures-start.txt
- measures-solution.txt

## Steps
1. Complete the DAX console challenges above.
2. Download measures-start.txt and measures-solution.txt. Work from the starter and open the solution only to check.
3. In Power BI Desktop, select the Tickets table and choose New measure: Total Tickets = COUNTROWS(Tickets).
4. Complete and add Avg Hours and Closed Tickets from the starter file.
5. Add Close Rate with DIVIDE and format it as a percentage with 1 decimal place.
6. Add the calculated column Team = RELATED(Categories[Team]) to Tickets with New column.
7. Build a matrix with Campus on rows and all four measures as values.
8. Add a Priority slicer, select High, and watch the measures change while the Team column stays the same per row in Table view.

## Check your work
- [ ] Matrix totals with no slicer: Total Tickets 60, Closed Tickets 46, Close Rate 76.7%, Avg Hours 17.30.
- [ ] Rows: City 14 tickets (78.6%, 12.75 hours), North 21 (85.7%, 18.44 hours), South 25 (68.0%, 19.04 hours).
- [ ] With Priority = High: Total Tickets 15, Closed Tickets 12, Close Rate 80.0%, Avg Hours 11.04; South shows 8 tickets and 62.5%.
- [ ] Every ticket with CategoryID 1 or 2 shows Team = Infrastructure, 3 shows Identity and 4 shows Applications.
