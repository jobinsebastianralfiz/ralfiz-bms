# AB-400 · D.12 Azure Functions for Power Platform

## Files
- NightlySlaCheck.csproj
- NightlySlaCheck.cs
- host.json
- local.settings.sample.json

## Steps
1. Download the exercise files into a folder named NightlySlaCheck and open it in VS Code with the Azure Functions extension installed.
2. Copy local.settings.sample.json to local.settings.json and set DataverseUrl to your environment URL. Keep DryRun set to true.
3. Start Azurite (the local storage emulator), sign in with az login using your developer account, and start the project with F5 or func start.
4. Run the timer function now instead of waiting for 02:00 UTC: send POST http://localhost:7071/admin/functions/NightlySlaCheck with Content-Type application/json and the body {}, then read the log.
5. Create a Function App (.NET 8, isolated worker) in Azure, deploy the project and add the app settings DataverseUrl, PriorityHighValue, StatusClosedValue and DryRun (true).
6. Turn on the system-assigned managed identity. Copy its application (client) ID from Microsoft Entra ID > Enterprise applications and add an application user for it in the Power Platform admin center with a role that can read and update chd_ticket.
7. Run the function from the portal (Test/Run) and check the traces in Application Insights. Keep DryRun true so the shared ticket data stays as in tickets.csv; set it to false only in an environment you can reset.

## Check your work
- [ ] The project builds, and the local run logs “Found 12 overdue tickets, 11 need escalation.” (with the 28 rows of tickets.csv, run after 3 September 2026).
- [ ] The log lists 12 “Overdue:” lines and ends with “DryRun is true: no rows were updated.”; no ticket Priority changes.
- [ ] Before the application user exists, the Azure run fails with “Dataverse connection failed”; after you add it, the same run logs “Found 12 overdue tickets”.
- [ ] Application Insights shows the “Found 12 overdue tickets, 11 need escalation.” trace for the portal run.
