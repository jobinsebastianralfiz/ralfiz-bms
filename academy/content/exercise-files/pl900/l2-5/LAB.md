# PL-900 · 2.5 Build tables with AI

## Files
- shared-data/hd/feedback.csv
- feedback-table-brief.md

## Steps
1. Download feedback.csv and feedback-table-brief.md.
2. In Tables, start creating a table with Copilot and paste the prompt from the brief.
3. Ask Copilot: "Add a column for the date of the feedback."
4. Compare each column with the Target design in the brief. Make Rating a Whole number and make sure Ticket is a lookup to Ticket.
5. Save the table as Ticket Feedback and add the two rows listed in the brief, choosing each ticket by its title.
6. Create a second table from feedback.csv by uploading the file, and name it Feedback Import.
7. Compare the two tables: note which one has a real lookup to Ticket.

## Check your work
- [ ] Ticket Feedback has 5 columns you care about: a primary name, Rating (Whole number), Comments, Feedback date and a Ticket lookup.
- [ ] Ticket Feedback has 2 rows, linked to CHD-1001 (rating 5) and CHD-1002 (rating 2).
- [ ] Feedback Import has 12 rows; sorting by Rating descending shows five 5s at the top and five 2s at the bottom.
- [ ] In Feedback Import, Ticket Number is a plain text column, not a lookup.
