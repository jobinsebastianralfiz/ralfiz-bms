# AB-400 · D.15 Dataverse events and data synchronization

## Files
- sis-tickets.csv
- Program.cs
- TicketWebhook.cs
- sample-remote-context.json

## Steps
1. In make.powerapps.com open the Ticket table properties and turn on Track changes. Add a text column External reference (chd_externalref) and an alternate key on it, and wait until the key status is Active.
2. Download the exercise files. Run dotnet new console -n SisSync, then dotnet add package Microsoft.PowerPlatform.Dataverse.Client; replace Program.cs with the downloaded file and copy sis-tickets.csv next to it.
3. Set DATAVERSE_CONNECTION (the OAuth example is in the comments of Program.cs) and run dotnet run twice. Compare the Created and Updated lines of the two runs.
4. Run dotnet run -- changes once to save a data token, edit the Title of SIS-1041 in the app, then run dotnet run -- changes again.
5. Web API variant: send GET /api/data/v9.2/chd_tickets?$select=chd_title with the header Prefer: odata.track-changes, save the @odata.deltaLink, edit one ticket and call the delta link.
6. In the Azure portal create a Service Bus namespace and a queue chd-escalations and copy a SAS connection string with Send rights. In the Plug-in Registration Tool choose Register New Service Endpoint, paste it, keep contract Queue and choose JSON.
7. Register a step on the endpoint: Update of chd_ticket, filtering attribute chd_priority, PostOperation, Asynchronous. Change the Priority of SIS-1041, peek the message with Service Bus Explorer and compare it with sample-remote-context.json.
8. Add TicketWebhook.cs to your NightlySlaCheck project from lesson D.12, start it locally and POST sample-remote-context.json to http://localhost:7071/api/ticket-webhook with Content-Type application/json.
9. Clean up: delete the five SIS tickets (SIS-1040 to SIS-1044).

## Check your work
- [ ] First run: SIS-1040 to SIS-1044 print Created, the second SIS-1042 line prints Updated, and the summary is “Done: 5 created, 1 updated.”
- [ ] Second run prints “Done: 0 created, 6 updated.”; SIS-1042 has the title “Projector not working in room 204” and Priority High.
- [ ] After the title edit, dotnet run -- changes prints “1 new or updated, 0 deleted.”
- [ ] The Service Bus message is JSON with MessageName Update, PrimaryEntityName chd_ticket and a Target whose Attributes include chd_priority.
- [ ] The local webhook answers 200 “received” and logs “changed chd_status = 100000002” and “was closed: send the satisfaction survey link.”
