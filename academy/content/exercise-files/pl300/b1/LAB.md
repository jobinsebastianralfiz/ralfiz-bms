# PL-300 · B.1 Power BI essentials

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- data-dictionary.md

## Steps
1. Use the dataset panel above to copy tickets.csv and categories.csv (the same two files are in this lab’s downloads), and save them in a folder such as Documents\HelpDesk.
2. Download data-dictionary.md and read what each column of tickets.csv and categories.csv means.
3. Install Power BI Desktop on Windows from the Microsoft Store or the Microsoft download page. On a Mac, use a Windows virtual machine or cloud PC.
4. Open Power BI Desktop, choose Get data, then Text/CSV, and select tickets.csv. Look at the preview and choose Load.
5. Repeat for categories.csv. In the Data pane, confirm you now have two tables: tickets and categories.
6. Switch between Report view, Table view and Model view using the icons on the left. In Model view, check whether Desktop created a relationship on CategoryID; if not, drag categories[CategoryID] onto tickets[CategoryID].
7. Drag a Card visual onto the report page and put TicketID in it, set to Count.
8. Save the file as HelpDesk.pbix. You will keep improving this file through the whole track.

## Check your work
- [ ] The card shows 60 (Count of TicketID).
- [ ] Table view shows 9 columns in tickets (TicketID to AssignedTo) and 4 rows in categories.
- [ ] Model view shows one relationship: categories[CategoryID] (1) to tickets[CategoryID] (*).
- [ ] The categories table lists three teams: Infrastructure, Identity and Applications.
