# AB-410 · A.8 Compose model-driven apps

## Files
- app-map.md
- acceptance-tests.md

## Steps
1. Download the exercise files and open app-map.md next to the app designer.
2. Open Help Desk Staff from the Campus Help Desk solution and build the navigation in app-map.md: group Work with Tickets and Ticket Comments, group Setup with Categories.
3. Select Tickets in the Pages pane and include only the forms and the three views listed in app-map.md. Create My Open Tickets first if it is missing.
4. Create Ticket - Manager with Save as on the Ticket form, add the SLA section, and restrict it to Help Desk Manager and System Administrator. Set the forms’ order and make Ticket the fallback form.
5. Save and Publish, then Play the app and run tests 1 to 5 in acceptance-tests.md.
6. Share the app and assign the Help Desk Agent and Help Desk Manager roles to it.
7. Sign in as the test user from lesson A.7 and run tests 6 to 10 in acceptance-tests.md.

## Check your work
- [ ] The left navigation shows two groups: Work (Tickets, Ticket Comments) and Setup (Categories).
- [ ] The Tickets view selector lists exactly 3 system views, and High priority open tickets returns 1 row (CHD-1017).
- [ ] As yourself, tickets open on Ticket - Manager; as the test user they open on Ticket, and Ticket - Manager is not listed.
- [ ] As the test user, Active Tickets shows 5 rows (the 4 IT Support North tickets plus the one they created in A.7) and Categories shows 6 read-only rows.
