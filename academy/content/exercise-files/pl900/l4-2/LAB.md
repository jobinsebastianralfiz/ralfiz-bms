# PL-900 · 4.2 Common automation scenarios

## Files
- form-and-flows-spec.md
- test-responses.csv

## Steps
1. Download the exercise files and read form-and-flows-spec.md.
2. In Microsoft Forms, create the form Report an IT problem with the 3 questions in the spec.
3. In the Ticket table, open the Priority column and note the number for Low, Medium and High.
4. Build Flow A (CHD - Form to ticket): Forms trigger, Get response details, Dataverse Add a new row with the Priority expression, then the Teams message or email.
5. Build Flow B (CHD - High priority approval): Dataverse trigger, Condition on Priority, Start and wait for an approval, then Update a row based on the outcome.
6. Submit the form 5 times using the rows of test-responses.csv, in order.
7. Answer the 2 approval requests in Teams, Outlook or the Approvals app: approve the first (projector) and reject the second (account locked).

## Check your work
- [ ] The Ticket table has 5 new rows, one for each row of test-responses.csv, with the right priorities (2 High, 2 Medium, 1 Low).
- [ ] Flow A has 5 succeeded runs and you received 5 Teams messages or emails.
- [ ] Flow B has 5 runs, and only 2 of them sent an approval.
- [ ] Projector in room 204 shows no signal now has Status In progress, and Account locked before online exam has Status Closed.
