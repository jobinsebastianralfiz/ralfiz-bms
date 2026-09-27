# AB-410 · A.3 Solutions and ALM strategy

## Files
- environment-values.md
- deploy-settings.json
- pac-commands.txt

## Steps
1. Download the exercise files and open environment-values.md.
2. In the Campus Help Desk solution in CHD Dev, create the environment variable Support Email (schema chd_SupportEmail, Text) with the CHD Dev current value from environment-values.md.
3. Open the new-ticket notification flow and replace the hard-coded To address in Send an email (V2) with Support Email from dynamic content. Save.
4. Open Connection references in the solution and check that the flow uses one for Microsoft Dataverse and one for Office 365 Outlook, as listed in environment-values.md.
5. Run Solution checker on the solution and read any warnings.
6. Export the solution as managed and import it into CHD Test. When prompted, enter helpdesk-test@staff.example.edu (or your second address) and pick a connection for each reference.
7. In CHD Test, create the test ticket from environment-values.md and check which mailbox receives the email.
8. Open the Ticket table in CHD Test, select a column and open Solution layers.
9. Optional: run the commands in pac-commands.txt, then compare the generated deploy-settings.json with the sample file.

## Check your work
- [ ] In CHD Dev the flow’s To field shows the Support Email variable, not a typed address.
- [ ] In CHD Test, Support Email shows the test value, and the email for "Deployment test: projector in Hall B" arrives at that address, not the Dev one.
- [ ] The solution contains exactly 2 connection references: Dataverse and Office 365 Outlook.
- [ ] Solution layers in CHD Test shows a managed layer from Campus Help Desk.
- [ ] If you used pac, the generated settings file has one EnvironmentVariables entry (chd_SupportEmail) and two ConnectionReferences entries.
