# AB-410 · A.15 AI Hub prompts

## Files
- shared-data/hd/categories.csv
- classify-ticket-prompt.md
- expected-output.json
- classify-samples.csv

## Steps
1. Download the exercise files. In make.powerapps.com, go to AI hub > Prompts > Build your own prompt and name it Classify ticket.
2. Paste the instruction from classify-ticket-prompt.md and insert a Text input named TicketDescription where the placeholder is.
3. Enter the sample value from classify-ticket-prompt.md, select Test and read the Text response.
4. Add Dataverse knowledge: the Categories table with the Name and Description columns. Test again.
5. Apply the settings table in classify-ticket-prompt.md, switch Output to JSON, test, and compare the format with expected-output.json. Edit and Save custom if the property names differ.
6. Test each row of classify-samples.csv by pasting the Description as the sample value, and record the category and priority you get.
7. Save the prompt. In a new instant flow in the solution, add Run a prompt with Classify ticket and confirm category, priority and reason are separate dynamic content.
8. In the student app, add the prompt as data and on a button run Set(varClass, 'Classify ticket'.Predict(txtDescription.Text)); use IntelliSense on varClass to show the category in a label.

## Check your work
- [ ] The lab sample (projector in room B12) returns category Classroom AV and priority High, matching expected-output.json.
- [ ] Every category returned for the 6 rows in classify-samples.csv is one of the 6 names in categories.csv.
- [ ] At least 5 of the 6 rows in classify-samples.csv match both the expected category and the expected priority; re-read the instruction rules for any row that does not.
- [ ] Testing the same description twice with temperature 0 gives the same category and priority.
- [ ] In the flow, Run a prompt exposes category, priority and reason without a Parse JSON action.
