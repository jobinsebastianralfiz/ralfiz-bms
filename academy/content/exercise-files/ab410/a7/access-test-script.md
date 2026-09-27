# Access test script (sign in as the test user)

Use a private browser window so you do not mix sessions.

| # | Action | Expected result | Pass? |
|---|---|---|---|
| 1 | Open Help Desk Staff | App opens (role Help Desk Agent is assigned to the app) | |
| 2 | Open the Active Tickets view | Exactly 4 rows: CHD-1019, CHD-1021, CHD-1024, CHD-1027 | |
| 3 | Search for CHD-1023 | Not found (owned in the root unit, not shared with this user) | |
| 4 | Open CHD-1019 and change Priority to High, save | Save succeeds (team-owned row counts as User access) | |
| 5 | Look at Internal notes on CHD-1019 | Field shows as locked with no value | |
| 6 | Open the Category lookup on a new ticket | All 6 categories are listed | |
| 7 | Create a new ticket | Save succeeds; owner is the test user | |
| 8 | Try to delete CHD-1021 | Delete is not offered or fails (no Delete privilege) | |

Then sign in as the City Campus user you shared CHD-1023 with:
| # | Action | Expected result | Pass? |
|---|---|---|---|
| 9 | Open CHD-1023 | Opens read-only | |
| 10 | Try to edit Title | Not allowed (Read only share) | |

If a result differs, check in this order: app role, security role privileges,
business unit of the user and of the row owner, team membership, sharing.
