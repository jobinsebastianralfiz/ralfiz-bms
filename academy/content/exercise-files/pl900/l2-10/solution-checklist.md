# Solution checklist: Campus Help Desk (Lesson 2.10)

## Publisher

| Setting | Value |
|---|---|
| Display name | Campus Help Desk |
| Name | CampusHelpDesk |
| Prefix | chd |

The prefix is added to the schema name of every NEW component you create inside the solution.

## Solution

| Setting | Value |
|---|---|
| Display name | Campus Help Desk |
| Name | CampusHelpDesk |
| Publisher | Campus Help Desk (chd) |
| Version | 1.0.0.0 |

## Components to add

| Component | How |
|---|---|
| Ticket table | Add existing > Table (include all components, or at least its columns, forms and views) |
| Category table | Add existing > Table |
| HelpDeskEmail | New > More > Environment variable |

## Environment variable

| Setting | Value |
|---|---|
| Display name | HelpDeskEmail |
| Schema name | chd_HelpDeskEmail |
| Data type | Text |
| Default value | your work or school email |

## Export and import

- [ ] Select Publish all customizations before exporting
- [ ] Run the solution checker if offered, and read any warnings
- [ ] Export as Managed; note the version number
- [ ] Downloaded file name: ______________________ (it ends in _managed.zip)
- [ ] Switch to Help Desk Test and import the zip from Solutions > Import solution
- [ ] If asked for the HelpDeskEmail value, enter the test mailbox address

## After import, compare

| Question | Dev environment | Help Desk Test |
|---|---|---|
| Solution type (Managed or Unmanaged) | | |
| Ticket table exists? | | |
| Number of Ticket rows | | |
| HelpDeskEmail value | | |

Solutions move the design (tables, forms, views, variables), not the data rows.

## Optional: pipelines

In the admin center, look for Deployment pipelines. Write the three things an admin must set up:

1.
2.
3.
