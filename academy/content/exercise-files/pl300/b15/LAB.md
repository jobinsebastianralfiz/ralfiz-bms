# PL-300 · B.15 Security and governance

## Files
- shared-data/pbi/tickets.csv
- staff.csv
- staff-campus.csv
- rls-roles.txt
- security-matrix.md

## Steps
1. Download staff.csv, staff-campus.csv, rls-roles.txt and security-matrix.md, and read the security matrix.
2. In Power BI Desktop, open Modeling and choose Manage roles. Create roles North, South and City, each filtering Tickets[Campus] with the filters in rls-roles.txt. Save.
3. Choose View as, tick the North role and check that every visual shows only North tickets. Then stop viewing.
4. Get data from staff.csv and name the table Staff. In Model view relate Staff[AssignedTo] 1 → * Tickets[AssignedTo] with single direction.
5. Create a role named Own Tickets with the filter [Email] = USERPRINCIPALNAME() on Staff. Use View as with Other user set to anu.sebastian@staff.example.edu plus the Own Tickets role, and check the visuals.
6. Get data from staff-campus.csv and name it StaffCampus. Delete any relationship Desktop creates for it, then create the Campus Lead role on Tickets from rls-roles.txt. Test it as divya.nair@staff.example.edu and as suresh.kumar@staff.example.edu.
7. Publish to your workspace. In the service, open the semantic model’s Security page and add yourself (or a group) as a member of the North role. Use Test as role.
8. Open Manage access on the workspace and review the four roles against security-matrix.md. Then share the report with a colleague and look at the permission options.
9. Apply a sensitivity label to the report in Desktop or the service, if labels are available in your tenant.

## Check your work
- [ ] View as North shows 21 tickets; South shows 25 and City 14. If North shows 20, the Campus cleaning from B.4 is missing.
- [ ] Own Tickets as anu.sebastian@staff.example.edu shows 13 tickets (8 Closed, 4 Open, 1 In progress); as joseph.mathew@staff.example.edu it shows 17.
- [ ] Campus Lead as divya.nair@staff.example.edu shows 14 tickets (City only); as suresh.kumar@staff.example.edu it shows all 60.
- [ ] Test as role North in the service shows the same 21 tickets as in Desktop.
