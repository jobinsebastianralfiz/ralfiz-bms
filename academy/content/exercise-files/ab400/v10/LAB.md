# AB-400 · D.10 Custom APIs and business events

## Files
- custom-api-spec.md
- start/EscalateTicket.cs
- solution/EscalateTicket.cs

## Steps
1. Download the exercise files and open custom-api-spec.md. Add the Escalation reason column (chd_escalationreason, text, 200 characters) to the Ticket table.
2. In the Campus Help Desk solution choose New > More > Other > Custom API and create chd_EscalateTicket with the values in section 1, then add request parameter chd_Reason and response property chd_NewPriority.
3. Copy EscalateTicket.cs from the start folder into your ChdPlugins project from lesson D.9, fill TODO 1 to 5 and build in Release mode.
4. In the Plug-in Registration Tool select the ChdPlugins assembly and choose Update. Open the chd_EscalateTicket row and set Plugin Type to ChdPlugins.EscalateTicket. Do not register a step.
5. Send requests 3.1, 3.2, 3.3 and 3.5 from custom-api-spec.md with Postman or the VS Code REST Client and compare each result with its Expected line.
6. Create the business event chd_TicketResolved from section 2 (Global, Async Only, request parameter chd_TicketId, no plug-in), plus the Help Desk events catalog, the Tickets category and a catalog assignment.
7. Build a cloud flow in the solution with the Dataverse trigger When an action is performed (catalog Help Desk events, category Tickets, action chd_TicketResolved), send request 3.4 and open the run.
8. Set CHD-1025 back to Priority Medium and clear its Escalation reason so later labs start from the data in tickets.csv.

## Check your work
- [ ] Request 3.2 returns 200 with chd_NewPriority 100000002, and CHD-1025 shows Priority High and Escalation reason “Several students in the library cannot work”.
- [ ] Request 3.3 (a reason made of spaces) returns the error “Please give a reason for escalation.” and request 3.5 on CHD-1001 returns “Closed tickets cannot be escalated.”
- [ ] The chd_EscalateTicket row shows Plugin Type ChdPlugins.EscalateTicket and the Plug-in Registration Tool lists no step for it.
- [ ] Request 3.4 returns 204 No Content and the flow shows a new successful run.
