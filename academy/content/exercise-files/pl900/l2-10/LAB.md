# PL-900 · 2.10 ALM with Power Platform pipelines

## Files
- solution-checklist.md
- deployment-settings.json

## Steps
1. Download solution-checklist.md and deployment-settings.json.
2. In your first environment, create the solution Campus Help Desk with a new publisher using the prefix chd.
3. Add the existing Ticket and Category tables to the solution.
4. Add the environment variable HelpDeskEmail (Text) with your email as the default value.
5. Publish all customizations, then export the solution as Managed.
6. Switch to Help Desk Test and import the managed zip file.
7. Fill in the "After import, compare" table in the checklist.
8. Optional: read deployment-settings.json and, in the admin center, look at what setting up Deployment pipelines involves.

## Check your work
- [ ] The environment variable’s schema name is chd_HelpDeskEmail.
- [ ] The exported file name ends in _managed.zip.
- [ ] In Help Desk Test, the Campus Help Desk solution is listed as Managed; in your first environment it is Unmanaged.
- [ ] In Help Desk Test, the Ticket table exists but has 0 rows: solutions move the design, not the 28 tickets.
