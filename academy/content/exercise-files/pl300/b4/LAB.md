# PL-300 · B.4 Profile and clean data

## Files
- shared-data/pbi/tickets.csv
- clean-steps.txt

## Steps
1. Download clean-steps.txt, but do not open it until you have built the steps yourself.
2. Open HelpDesk.pbix and choose Transform data. Select the tickets query.
3. On the View tab, turn on Column quality, Column distribution and Column profile. In the status bar, change profiling to the entire dataset.
4. Select the Campus column and look at the value distribution. Find the lower-case and extra-space variants of North, South and City, and note their TicketIDs.
5. With Campus selected, choose Transform, Format, Trim, then Format, Capitalize Each Word. Check that Campus now shows exactly three distinct values.
6. Apply the same Capitalize Each Word fix to Priority, then confirm it shows only Low, Medium and High.
7. Check that CreatedDate and ClosedDate are Date type and HoursToResolve is Decimal number. Filter ClosedDate to empty values and look at Status, then remove that filter step.
8. Rename your steps to clear names, open Advanced Editor and compare your code with clean-steps.txt, then choose Close & Apply.

## Check your work
- [ ] Before cleaning, Campus shows 6 distinct values: North 20, South 24, City 13, plus north (1005), " South " (1018) and "city " (1034). Priority shows 4 distinct values, including medium (1049).
- [ ] After cleaning, Campus has 3 distinct values: South 25, North 21, City 14.
- [ ] After cleaning, Priority has 3 distinct values: Medium 30, Low 15, High 15.
- [ ] ClosedDate and HoursToResolve each have 14 empty values (23%), and all 14 tickets are Open (10) or In progress (4); no Closed ticket is missing a ClosedDate.
- [ ] The table still has 60 rows after all steps.
