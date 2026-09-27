# AB-400 · D.13 Advanced cloud flows and Copilot Studio workflows

## Files
- start/flow-expressions.txt
- solution/flow-expressions.txt
- sample-flow-data.json

## Steps
1. Download the exercise files. Open flow-expressions.txt from the start folder and sample-flow-data.json, and write your answers to E1 to E10 before you build anything.
2. In make.powerautomate.com open Solutions > Campus Help Desk and create an automated cloud flow Escalate High Tickets with the Dataverse trigger When a row is added, modified or deleted: Added or Modified, table Tickets, Select columns chd_priority.
3. In the trigger settings add your E2 expression as a trigger condition, using the Priority and Status values stored in your environment.
4. Add a scope named Try with Get a row by ID (table Categories, row ID from the ticket’s category lookup) and a Teams post whose message uses your E6 expression. Set the Teams action’s retry policy from E10.
5. Add a scope named Catch, set Configure run after to has failed and has timed out only, and inside it add Filter array (E7), a Compose with E8, a Compose with E9 and a Terminate action with status Failed.
6. Create a child flow Calculate SLA in the solution with Manually trigger a flow (inputs Priority and Created on), Composes for E3 and E4 using those inputs, and Respond to a PowerApp or flow returning DueDate. Call it from Try with Run a child flow.
7. Change the Dataverse connection reference to a connection that uses a service principal (client ID, secret, tenant) for your application user from lesson D.11.
8. Test: set CHD-1025 to High, then change only its Title. Next, put 00000000-0000-0000-0000-000000000000 as the row ID in Get a row by ID and set CHD-1025 to High again.
9. Compare your answers with flow-expressions.txt in the solution folder, then set CHD-1025 back to Priority Medium and restore the row ID.

## Check your work
- [ ] Your answers match the solution: E1 and E2 return true, E3 returns 1, E4 returns 2026-08-29 and E7 keeps 1 item (Get_a_row_by_ID).
- [ ] Setting CHD-1025 to High starts exactly one run; changing only its Title starts none.
- [ ] With the empty row ID the run shows Failed in run history, the Catch scope ran, and the E8 Compose output ends with “Does Not Exist”.
- [ ] The Calculate SLA child run returns a due date one day after the ticket’s Created on value (High = 1 day).
