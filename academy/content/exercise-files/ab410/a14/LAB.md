# AB-410 · A.14 Flow control, approvals and troubleshooting

## Files
- approval-test-cases.md
- try-catch-expressions.txt

## Steps
1. Download the exercise files. In the solution, create the instant flow Approve equipment ticket with the Power Apps (V2) trigger and a text input TicketId.
2. Build the outline at the top of approval-test-cases.md: Get a row by ID, a Switch with Hardware, Software and Default cases, the approval and the Condition, using the expressions in try-catch-expressions.txt.
3. Assign the approval to yourself and a second test user so you can answer it.
4. Move Get a row by ID and the Switch into a Scope named Try. Add a Scope named Catch, set its run after to has failed and has timed out on Try, and add the email and Terminate actions from try-catch-expressions.txt.
5. Copy the IDs of CHD-1026, CHD-1019, CHD-1018 and CHD-1025 from the address bar of each ticket in Help Desk Staff.
6. Run tests A1 to A6 from approval-test-cases.md, answering the approvals in Teams or Outlook.
7. For A5, open the run history and read the error and skipped actions as described in approval-test-cases.md, then do the clean-up.

## Check your work
- [ ] A1: after you approve, CHD-1026 has Status In progress and the run shows Succeeded with Catch Skipped.
- [ ] A2: after you reject, CHD-1019 has Status Closed and its description ends with “Rejected: Use a spare keyboard from lab 1”.
- [ ] A3 and A4 send no approval request; A4’s Compose output reads “Routed to general queue”.
- [ ] A5 sends you the Catch email with a working link to the run, and the run is marked Failed.
