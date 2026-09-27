# PL-900 · 4.4 Build flows with AI

## Files
- copilot-prompts.md
- expected-results.md

## Steps
1. Download the exercise files and open copilot-prompts.md.
2. On the Power Automate home page, paste Prompt 1 and review Copilot’s proposed trigger and actions against the table in the file.
3. Confirm or create the Dataverse and Office 365 Outlook connections, then create the flow.
4. Open List rows and check the Filter rows value. Fix the column name or Open value if Copilot guessed wrong.
5. Test the flow manually and compare the rows returned with expected-results.md.
6. In the designer’s Copilot pane, paste Prompt 2, check the new filter, and test again.
7. Add the ticket Exam hall projector dead (High, Open) and test once more. If any run fails, use Prompt 3.

## Check your work
- [ ] The trigger is a Recurrence set to every 1 day at 17:00.
- [ ] Before Prompt 2, List rows returns 6 rows from tickets.csv (CHD-1023 to CHD-1028), plus any Open tickets you added earlier.
- [ ] After Prompt 2, none of the 28 tickets.csv rows is returned, because none of its 4 High tickets is Open; only Open High tickets you added in earlier labs appear.
- [ ] After adding Exam hall projector dead, the test returns one more row than before and the email lists that title.
