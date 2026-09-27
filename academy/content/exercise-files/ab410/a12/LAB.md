# AB-410 · A.12 Canvas apps: errors, testing, flows and agents

## Files
- start/errors-and-flows.txt
- solution/errors-and-flows.txt
- test-plan.md

## Steps
1. Download the exercise files. In the Ticket table, set the Title column to Business required and save.
2. Open the student app. Using errors-and-flows.txt from the start folder, wrap btnSubmit in IfError, add btnQuickSave and lblErrors, and write App.OnError.
3. Run manual tests M1 to M4 from test-plan.md.
4. Open Monitor from Advanced tools and run MO1 to MO3 from test-plan.md.
5. Open Test Studio, create the suite Submit ticket with the two test cases from the solution file, and play the suite.
6. Create the cloud flow EscalateTicket in the solution as described in errors-and-flows.txt from the solution folder, add it to the app, and wire btnEscalate on scrDetail.
7. Run test M5, then do the clean-up steps at the end of test-plan.md.
8. If agent builder is available in your region, generate an agent draft from the student app and compare its suggested actions with Help Desk Assistant.

## Check your work
- [ ] Submitting with a blank Title shows a red banner starting “Could not save:” and you stay on scrNew.
- [ ] In Monitor, Quick save with a blank Title adds a Trace row starting “Error:”, and Submit with a blank Title adds none.
- [ ] Both Test Studio cases, Valid ticket saves and Blank title is rejected, show Passed.
- [ ] Escalating CHD-1025 shows the banner “Escalated CHD-1025” and its Priority changes to High.
