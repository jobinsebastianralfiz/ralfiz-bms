# PL-300 · B.8 CALCULATE and filter context

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- measures-start.txt
- measures-solution.txt

## Steps
1. Complete the DAX console challenges above.
2. Download measures-start.txt and measures-solution.txt. Fill the TODOs in the starter before you look at the solution.
3. In Power BI Desktop, add High Tickets = CALCULATE([Total Tickets], Tickets[Priority] = "High").
4. Add All Tickets with ALL(Tickets) and Share of Total with DIVIDE, formatted as a percentage.
5. Build a matrix with Priority on rows and Total Tickets, High Tickets, All Tickets and Share of Total as values.
6. Add High Tickets Keep with KEEPFILTERS to the matrix and compare the rows.
7. On the Categories table add two calculated columns: Rows Plain = COUNTROWS(Tickets) and Rows Per Category = CALCULATE(COUNTROWS(Tickets)). Compare them in Table view.

## Check your work
- [ ] Total Tickets per row: High 15, Low 15, Medium 30. High Tickets shows 15 on every row and on the total.
- [ ] All Tickets shows 60 on every row; Share of Total is 25.0% for High and Low and 50.0% for Medium, 100% in total.
- [ ] High Tickets Keep shows 15 on the High row and blank on Low and Medium.
- [ ] Rows Plain is 60 on all four categories; Rows Per Category is Network 16, Hardware 22, Accounts 10, Software 12.
