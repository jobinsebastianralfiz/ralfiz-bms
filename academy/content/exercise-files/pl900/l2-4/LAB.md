# PL-900 · 2.4 Business logic and Power Fx

## Files
- business-rule-spec.md
- summary-formula.txt

## Steps
1. Complete the Power Fx challenges in the console above.
2. Download business-rule-spec.md and summary-formula.txt.
3. On the Ticket table, create the business rule "High priority needs description" exactly as in the Rule design table, including the Else action. Save and Activate it.
4. Run test cases 1 to 5 from business-rule-spec.md on the main form, and discard your test changes.
5. Add a formula column named Summary and paste the first formula from summary-formula.txt. Ask Copilot in the formula bar if you get stuck.
6. Save the column and open Edit data to read Summary for CHD-1001.
7. Optional: add the Short label variation and compare its value with the expected one.

## Check your work
- [ ] Opening CHD-1017 (High) shows Description as required; switching it to Low removes the marker.
- [ ] Saving a High ticket with an empty Description is blocked.
- [ ] Clearing Description on CHD-1001 (Medium) shows no required marker.
- [ ] Summary for CHD-1001 reads "Printer out of toner in library - The black and white printer on the ground floor of the library prints faded pages. It probably needs toner."
- [ ] The rule shows as Activated in the table’s Business rules list.
