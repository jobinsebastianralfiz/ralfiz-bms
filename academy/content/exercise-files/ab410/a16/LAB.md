# AB-410 · A.16 AI models in apps and flows

## Files
- shared-data/hd/feedback.csv
- sentiment-test-sheet.md
- ai-model-formulas.txt

## Steps
1. Download the exercise files. In AI hub > AI models, open Sentiment analysis and test comment 1 and comment 2 from sentiment-test-sheet.md.
2. In the Campus Help Desk solution, add a Feedback text column and a Feedback sentiment text column to Ticket if you do not have them.
3. Create the automated flow on Tickets (Modified, Select columns set to the Feedback column) and add Analyze positive or negative sentiment with Language en.
4. Add the Condition and both Update a row branches using ai-model-formulas.txt.
5. Paste each of the 8 comments from sentiment-test-sheet.md into the Feedback column of the named ticket and fill in the probability table.
6. Answer the three questions in sentiment-test-sheet.md.
7. In the student app, add Key phrase extraction from Add data > AI models, then set up btnPhrases and galPhrases from ai-model-formulas.txt and run the canvas app check.

## Check your work
- [ ] Comment 2 (“Took too long, I missed my class.”) sets Feedback sentiment to Negative and sends the team-lead email.
- [ ] Comments 1, 3, 5 and 7 (ratings 4 and 5) never take the negative branch.
- [ ] Changing only the Title of CHD-1001 starts no run.
- [ ] Typing in txtDescription does not call the model; phrases appear only after you select btnPhrases.
