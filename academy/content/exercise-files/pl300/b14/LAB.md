# PL-300 · B.14 Workspaces, sharing and refresh

## Files
- shared-data/pbi/tickets.csv
- publishing-checklist.md

## Steps
1. Download publishing-checklist.md. In Power BI Desktop add the Open Tickets measure from it, put it in a card on Overview, and save.
2. In app.powerbi.com, create a workspace named Help Desk Analytics. A free trial may be offered if your licence cannot use shared workspaces.
3. In Power BI Desktop, choose Publish and select the Help Desk Analytics workspace. Open the report in the service when it finishes.
4. Pin the Ticket Count card, the Open Tickets card and the Campus chart to a new dashboard named Help Desk Overview. On the Open Tickets tile, set a data alert above a threshold higher than today’s value.
5. Open the semantic model settings. Look at Data source credentials, Gateway connection and Scheduled refresh, and fill in the Refresh plan table in the checklist.
6. On the report, create a subscription that emails you a snapshot of the Overview page.
7. In the workspace, create an app. Include the report and dashboard, add an audience, and publish it. Change the report in Desktop, republish, then choose Update app and see the change appear.
8. Open the semantic model settings and set Endorsement to Promoted.

## Check your work
- [ ] The workspace lists a report and a semantic model, both named HelpDesk, plus the Help Desk Overview dashboard.
- [ ] The dashboard tiles show Ticket Count 60 and Open Tickets 10.
- [ ] The semantic model settings say scheduled refresh needs a gateway for the local CSV files, so the scheduled refresh cannot be turned on until a gateway (or a OneDrive/SharePoint source) is set up.
- [ ] The app shows the report and dashboard, and after Update app it shows your change.
