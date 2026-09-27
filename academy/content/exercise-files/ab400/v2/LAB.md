# AB-400 · D.2 Technical architecture decisions

## Files
- shared-data/hd/tickets.csv
- shared-data/hd/categories.csv
- help-desk-requirements.md
- architecture-decision-brief.md
- solution/architecture-decisions.md

## Steps
1. Complete the “Where should this logic live?” sorter above.
2. Download the files and read help-desk-requirements.md: it lists the eight requirements R1 to R8 and the constraints.
3. Open architecture-decision-brief.md and fill section 1 with a component, where and when it runs, and why, for each of R1 to R8.
4. In your dev environment open the Ticket table’s Business rules and decide which requirements a business rule alone can meet; write them in section 2.
5. Open the Power Platform admin center, open your developer environment, and record in section 4 whether it is a managed environment and which data policies apply.
6. In the Help Desk Staff app, open ticket CHD-1025 and share it with a colleague; record in section 4 how row sharing differs from a security role.
7. Draw the three-layer diagram in section 5 and place every component from section 1 on it.
8. Compare your brief with architecture-decisions.md and note any row where you chose differently and why.

## Check your work
- [ ] Your section 1 matches the model answers for at least 7 of the 8 requirements.
- [ ] Component totals: Business rule 1, Client script 1, Synchronous plug-in 1, Asynchronous plug-in or Azure Function 2 (R4, R7), Cloud flow 2 (R5, R8), Copilot Studio agent 1.
- [ ] Section 2 lists only R1 as met by a business rule alone.
- [ ] Section 4 records a Yes/No for managed environment and at least one data policy (or “none”).
