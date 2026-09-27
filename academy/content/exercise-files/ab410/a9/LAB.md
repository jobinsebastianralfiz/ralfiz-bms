# AB-410 · A.9 Generative pages, charts and dashboards

## Files
- shared-data/hd/tickets.csv
- shared-data/hd/categories.csv
- triage-page-brief.md
- dashboard-spec.md

## Steps
1. Download the exercise files. If your Ticket and Category tables are empty, import categories.csv first and then tickets.csv (open each table and choose Import > Import data from Excel or CSV), mapping Category to the Category lookup.
2. Open the Help Desk Staff app in the app designer, select Add page > Generative page > Describe a page, add the Ticket and Category tables, and paste the description from triage-page-brief.md.
3. Preview the page, then send the three follow-up prompts from triage-page-brief.md one at a time. Run acceptance tests 1 to 6 and set CHD-1027 back to Open afterwards.
4. Open the Code tab and find the Ticket query, the Status filter and the Start work update, as listed at the end of the brief.
5. On the Ticket table, create the view Open and in progress tickets and the two charts exactly as described in dashboard-spec.md.
6. Show Chart 2 with the Active Tickets view and then with the new view, and compare the slices with the table in dashboard-spec.md.
7. Create the classic dashboard Help Desk Overview with the layout in dashboard-spec.md.
8. Add a Dashboard page for Help Desk Overview to Help Desk Staff, then Save and Publish, play the app and open both new pages.

## Check your work
- [ ] The triage board shows 6 cards: High 0, Medium 3 (CHD-1023, CHD-1025, CHD-1028) and Low 3 (CHD-1024, CHD-1026, CHD-1027).
- [ ] Filtering the board to Network leaves 2 cards, CHD-1025 and CHD-1028.
- [ ] Tickets by category and priority, shown with Active Tickets, has 6 bars: Accounts 5, Hardware 5, Network 5, Software 5, Printing 4, Classroom AV 4.
- [ ] Open tickets by status shows Closed 16, In progress 6, Open 6 with Active Tickets, and only In progress 6 and Open 6 with the Open and in progress tickets view.
- [ ] The dashboard list component shows 12 rows.
