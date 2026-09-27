# PL-900 · 2.7 The security model

## Files
- security-matrix.md
- shared-data/hd/staff.csv

## Steps
1. Download security-matrix.md and staff.csv.
2. In the admin center, open your environment > Settings > Users + permissions > Security roles.
3. Copy the Basic User role and name it Help Desk Student.
4. Set the Ticket privileges exactly as in the matrix: Create, Read, Write and Append at User level; no Delete.
5. Set the Category privileges: Read and Append To at Organization level. Save the role.
6. Optional: create the Help Desk Agent role from the second matrix, and use staff.csv to decide who would get it.
7. Open the Business units and Teams pages to see how users are grouped.

## Check your work
- [ ] Help Desk Student shows Delete on Ticket as None.
- [ ] Help Desk Student shows Read on Ticket at User level and Read on Category at Organization level.
- [ ] Help Desk Student has Append on Ticket and Append To on Category, so a student can set a ticket’s category.
- [ ] Your environment has one root business unit, named after the environment or organization.
- [ ] According to staff.csv, 4 of the 6 staff are help desk agents who would get the Help Desk Agent role.
