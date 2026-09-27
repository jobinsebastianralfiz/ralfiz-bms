# Security matrix: Help Desk Analytics

Implement this matrix, then test every row with View as (Desktop) or Test as role (service).

## Workspace roles
| Person | Email | Workspace role | Why |
|---|---|---|---|
| You (report author) | your sign-in | Admin | Owns the workspace |
| Divya Nair | divya.nair@staff.example.edu | Contributor | Builds pages; RLS does not apply to her in the workspace |
| Suresh Kumar | suresh.kumar@staff.example.edu | none, uses the app | Reads the app |
| Anu, Rahul, Meera, Joseph | see staff.csv | none, use the app | Read only |

Remember: RLS restricts only people with read access (Viewers, app users, people you share with). Admins, Members and Contributors see all rows.

## Row-level security
| Person | RLS role | Filter | What they should see |
|---|---|---|---|
| North campus viewer | North | Tickets[Campus] = "North" | Only North tickets |
| Anu Sebastian | Own Tickets | Staff[Email] = USERPRINCIPALNAME() | Only tickets assigned to Anu |
| Joseph Mathew | Own Tickets | same | Only tickets assigned to Joseph |
| Divya Nair | Campus Lead | StaffCampus lookup | All City tickets |
| Suresh Kumar | Campus Lead | StaffCampus lookup | All tickets (three campuses) |

Write the ticket count you see for each row in the Result column of your own copy, then compare with the Check your work list.

## Item-level access
- Semantic model: give Divya **Build** permission so she can make her own reports on it.
- Report: share with a colleague without Reshare.

## Labels
- Apply the sensitivity label "General" or "Confidential" (names depend on your tenant) because the report shows staff names.
- Exported Excel files keep the label when Microsoft Purview labels are enabled.