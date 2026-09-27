# AB-410 · A.2 Design solutions with AI-enabled tools

## Files
- requirements-brief.md
- decision-table-template.md
- shared-data/hd/staff.csv

## Steps
1. Download the exercise files and read requirements-brief.md from top to bottom.
2. In CHD Dev, open Plan designer and paste the Background and Roles sections of requirements-brief.md as your description.
3. Review the generated plan: roles, user stories, process map and suggested tables. Compare the tables with your Ticket and Category tables and staff.csv.
4. Go through R1 to R12 in the brief and note which ones the plan covered. Write at least three it missed at the top of decision-table-template.md.
5. Open Help Desk Staff in the app designer and review the Copilot and agent settings. Note which built-in AI features could meet R5 and R6.
6. Fill every row of decision-table-template.md with a component, a reason and any extensibility, then fill the environment-type table.
7. Compare your answers with the model answer at the bottom of the file and mark any row where your choice differs, with a reason.

## Check your work
- [ ] Your decision table has 12 rows, R1 to R12, with no empty Component cells.
- [ ] Exactly one requirement, R12 (the asset system REST API), needs extensibility: a custom connector.
- [ ] R9 (visitors without an account) maps to Power Pages and R8 (chat at any hour) to a Copilot Studio agent.
- [ ] R7 and R11 map to scheduled cloud flows, and R4 maps to an automated cloud flow triggered by email.
- [ ] Your environment table lists Developer for development, Sandbox for test and Production for live use.
