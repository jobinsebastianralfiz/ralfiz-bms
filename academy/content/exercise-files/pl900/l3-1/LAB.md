# PL-900 · 3.1 Canvas apps

## Files
- shared-data/hd/tickets.csv
- shared-data/hd/categories.csv
- canvas-formulas.txt
- app-test-script.md

## Steps
1. Download the exercise files for this lab. If your Ticket table does not hold the 28 rows from tickets.csv yet, import categories.csv into Category and then tickets.csv into Ticket (open the table and choose Import > Import data from Excel or CSV, mapping Category to the lookup).
2. In Power Apps, create a canvas app from data: choose Dataverse and the Ticket table. Power Apps builds a browse, detail and edit screen.
3. Play the app and follow rows 1, 7, 8 and 9 of app-test-script.md: check the count, add the test ticket, edit it and delete it.
4. Insert a Text input above the gallery, rename it txtSearch, and paste formula 1 from canvas-formulas.txt into the gallery’s Items property.
5. Replace Items with formula 2 so the newest tickets come first. Optionally add the ddStatus dropdown and formula 3.
6. Play the app and run steps 2 to 6 of app-test-script.md.
7. Run App checker > Accessibility, then paste formula 5 into txtSearch’s AccessibleLabel and HintText and run the checker again.
8. Save and publish the app, install the Power Apps mobile app, sign in and open the app on your phone.

## Check your work
- [ ] With the search box empty the gallery shows 28 tickets.
- [ ] Typing Print shows 2 tickets and typing Pr shows 3 (the extra one is Projector not working in Hall B).
- [ ] Adding the test ticket shows 29 rows; after deleting it the gallery is back to 28.
- [ ] Choosing Open in ddStatus (optional part) shows 6 tickets, CHD-1023 to CHD-1028.
- [ ] App checker no longer lists a missing accessible label for txtSearch.
