# Cloud flows and desktop flows (Lesson 4.1)

## Flows to build
| # | Name | Type | Trigger | Action |
|---|------|------|---------|--------|
| 1 | CHD - New ticket log | Automated cloud flow | Dataverse: When a row is added, modified or deleted (Change type Added, Table Ticket, Scope Organization) | Compose with the Title from dynamic content |
| 2 | CHD - Say hello | Instant cloud flow | Manually trigger a flow | Send a push notification (Notifications connector) or Send an email (V2) to yourself: "Hello from Power Automate" |
| 3 | CHD - Daily 9 am check | Scheduled cloud flow | Recurrence: every 1 day at 9:00, your time zone | Compose "Daily check ran" |
| 4 | Hello Notepad | Desktop flow (Power Automate for desktop) | Run manually | Run application notepad.exe, then Send keys "Hello" |

## Test ticket for flow 1
Add this row to Ticket (Edit data in the table, or your canvas app):
- Title: Flow test - lab 4.1
- Priority: Low
- Status: Open

## Classify these scenarios
Write: Automated, Instant, Scheduled, Desktop (attended) or Desktop (unattended).

1. Every Friday at 16:00, email the manager a count of open tickets. ____
2. When a student submits the feedback form, save the rating. ____
3. An agent presses a button in Teams to send a "we are on it" message. ____
4. Copy ticket numbers into an old Windows asset system that has no API, overnight, nobody at the PC. ____
5. Same as 4, but an agent watches it run on their own PC and fixes prompts when needed. ____
6. When a new ticket row is added, post it to the help desk Teams channel. ____

---
## Answer key
1 Scheduled, 2 Automated, 3 Instant, 4 Desktop (unattended), 5 Desktop (attended), 6 Automated.
