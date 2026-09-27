# PL-900 · 5.4 Tools: agent flows, connectors and MCP

## Files
- create-ticket-tool.md

## Steps
1. Download create-ticket-tool.md.
2. In your agent, open Tools > Add a tool > New tool > Agent flow, and name the flow Create ticket.
3. Add the Title and Priority text inputs to the trigger, with the input descriptions from the file.
4. Add Dataverse Add a new row to Ticket using the Priority expression, then Respond to the agent with the TicketId output. Save and publish the flow.
5. Back in the agent, add the flow as a tool and set its description to the text in the file.
6. Note the Ticket row count, then run the 3 tests in the test pane.
7. Open Add a tool again and browse the Model Context Protocol options to see which servers are available.

## Check your work
- [ ] Test 1 calls Create ticket with Priority High and the agent replies with a ticket ID.
- [ ] Test 2 makes the agent ask how urgent the problem is before calling the tool.
- [ ] Test 3 is answered from it-faq.md and the tool is not called.
- [ ] The Ticket table has exactly 2 more rows than before the tests, and the laptop row has Priority High and Status Open.
