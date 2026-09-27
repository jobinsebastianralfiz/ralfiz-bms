# PL-300 · B.2 Power BI and the Power Platform

## Files
- shared-data/pbi/tickets.csv
- integration-scenario.md

## Steps
1. Download integration-scenario.md and read the escalation rule and the table of which product does what.
2. In Power BI Desktop choose Get data and search for Dataverse. Read the connector description; if you still have your PL-900 developer environment, sign in and look at its tables, including Ticket.
3. Open HelpDesk.pbix and add a page named Escalations. Add a table visual with TicketID, Priority, Status, Campus and AssignedTo, set TicketID to Don’t summarize, then add page filters Priority is High and Status is not Closed.
4. On the Visualizations pane, find the Power Apps visual and the Power Automate visual icons (add them from Get more visuals if they are missing).
5. Add the Power Automate visual to the Escalations page and drag TicketID into its data field. Read the steps it shows for creating a flow; build the optional flow from the scenario if you have a Power Automate licence.
6. In make.powerautomate.com, open a new instant cloud flow and search the Power BI connector. Note the action that refreshes a semantic model (still called dataset in some places) and the trigger for data-driven alerts.
7. In make.powerapps.com, open a canvas app in edit mode, choose Insert and search for Power BI tile. Note that it shows a tile from a dashboard in the service.
8. In Microsoft Teams, open a channel, choose Add a tab and search Power BI. Note that a published report can be added as a tab.

## Check your work
- [ ] The Escalations table shows exactly 3 tickets: 1012 (In progress, Rahul), 1047 (Open, Rahul) and 1054 (In progress, Anu).
- [ ] All three escalations are on the South campus.
- [ ] The Power BI connector in Power Automate lists the action Refresh a dataset and the trigger When a data driven alert is triggered.
- [ ] The Power Automate visual shows TicketID in its data well and offers to create a new flow.
