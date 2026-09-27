# Publishing and refresh checklist: Help Desk Analytics

## Before you publish
- [ ] Add this measure on Tickets so the dashboard can alert on it:
      Open Tickets = CALCULATE ( COUNTROWS ( Tickets ), Tickets[Status] = "Open" )
- [ ] Put [Open Tickets] in a card on the Overview page.
- [ ] Save HelpDesk.pbix.

## Workspace
| Setting | Value |
|---|---|
| Workspace name | Help Desk Analytics |
| Report | HelpDesk |
| Semantic model | HelpDesk (same name as the file) |
| Dashboard | Help Desk Overview |
| App | Help Desk (audience: campus leads) |

## Dashboard
- [ ] Pin the Ticket Count card, the Open Tickets card and the Campus (or category) chart.
- [ ] Alerts work only on card, KPI and gauge tiles. Set an alert on the Open Tickets tile: "Above" a threshold you choose, checked at most once a day.
- [ ] Choose a threshold above today's value so the alert does not fire straight away; write both numbers down.

## Refresh plan
| Question | Answer for this project |
|---|---|
| Storage mode | Import |
| Source | CSV files in a folder on your own PC |
| Gateway needed for scheduled refresh? | Yes. The service cannot reach a file on your PC without an on-premises data gateway (personal or standard mode) |
| Alternative without a gateway | Store the CSV files in OneDrive or SharePoint and connect to them there |
| Planned schedule | Daily at 07:00, before the morning meeting |
| Failure notice | Send refresh failure notifications to the semantic model owner |

## Distribute
- [ ] Subscription on the Overview page, emailed to you.
- [ ] App with the report and dashboard, one audience. After a change: republish from Desktop, then Update app.
- [ ] Endorsement: Promoted (Certified needs an admin to allow you).

## Sign-off
| Check | Done by | Date |
|---|---|---|
| Numbers in the service match Desktop |  |  |
| Alert saved |  |  |
| App opened by a test user |  |  |