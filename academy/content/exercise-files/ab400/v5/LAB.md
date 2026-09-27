# AB-400 · D.5 Client scripting in model-driven apps

## Files
- shared-data/hd/tickets.csv
- start/ticket.js
- solution/ticket.js
- test-script.md

## Steps
1. Download the files, open start/ticket.js in VS Code and follow “Prepare the data” in test-script.md (deactivate the 16 Closed tickets).
2. Fill TODO 1 to TODO 5 in ticket.js: addOnChange, setRequiredLevel, clearFormNotification, setFormNotification and Xrm.WebApi.retrieveMultipleRecords with Xrm.Navigation.openAlertDialog.
3. Check the numeric value of High in your chd_priority choice and update CHD.Ticket.HIGH if it differs.
4. In the Campus Help Desk solution add a JavaScript web resource named chd_/scripts/ticket.js and upload your ticket.js.
5. Open the Ticket main form, add the web resource under Form libraries, and register CHD.Ticket.onLoad on OnLoad with “Pass execution context as first parameter” ticked; save and publish.
6. Run tests T1 to T6 in test-script.md, using F12 > Sources to set a breakpoint in onPriorityChange.
7. In the command designer add a “Close ticket” button to the Ticket form with the Power Fx action and visibility rule in test-script.md, then run test T7.
8. If a test fails, compare your file with solution/ticket.js.

## Check your work
- [ ] Setting Priority to High on CHD-1025 shows “High priority: set a Due date.” and Due date becomes required.
- [ ] The alert on CHD-1025 reads “3 open tickets in Network.” (12 active tickets after deactivating the 16 Closed ones).
- [ ] Opening CHD-1017 shows the warning on load and the alert “3 open tickets in Hardware.”
- [ ] Setting Priority back to Medium removes the warning and makes Due date optional.
- [ ] The Close ticket button sets Status to Closed and is hidden on a closed ticket.
