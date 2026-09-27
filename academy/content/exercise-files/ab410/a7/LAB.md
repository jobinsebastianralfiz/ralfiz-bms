# AB-410 · A.7 Dataverse security in practice

## Files
- security-matrix.md
- access-test-script.md
- shared-data/hd/staff.csv

## Steps
1. Download the exercise files and open security-matrix.md.
2. In the admin center, find where an Entra security group is assigned to CHD Dev. Do not assign one in a shared tenant.
3. Create the business units North Campus and City Campus under the root unit.
4. Copy Basic User to Help Desk Agent and set the privileges in the Help Desk Agent table of security-matrix.md. Create Help Desk Manager the same way.
5. Move your test user to North Campus, create the owner team IT Support North there, give it Help Desk Agent, add the test user, and assign CHD-1019, CHD-1021, CHD-1024 and CHD-1027 to the team.
6. Add Internal notes to Ticket with column security on, create the profile Help Desk Leads (Read, Update), add yourself, and type the note from the matrix on CHD-1019.
7. Share CHD-1023 with a City Campus user with Read access only.
8. Assign the Help Desk Agent role to the Help Desk Staff app, then run every test in access-test-script.md and fill in the Pass column.

## Check your work
- [ ] As the test user, Active Tickets shows exactly 4 rows: CHD-1019, CHD-1021, CHD-1024 and CHD-1027.
- [ ] As the test user, CHD-1023 cannot be found, and the Category lookup lists all 6 categories.
- [ ] As the test user, Internal notes on CHD-1019 is locked and empty, while you see the note text.
- [ ] The City Campus user opens CHD-1023 but cannot edit it.
