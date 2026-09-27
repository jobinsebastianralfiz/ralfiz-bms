# Sentiment flow test sheet (A.16)

Flow: automated, Tickets, change type Modified, Select columns = your Feedback column.
Paste each comment into the Feedback column of the ticket named, save, then read the run.

feedback.csv has 12 rows but only 8 different comments (CHD-1009 to CHD-1012 repeat the
texts of CHD-1001 to CHD-1004), so test the 8 unique texts below.

| # | Ticket | Rating | Comment | Expect overall sentiment | Negative > 0.7? | Feedback sentiment column |
|---|--------|--------|---------|--------------------------|-----------------|---------------------------|
| 1 | CHD-1001 | 5 | Fixed quickly, thank you! | positive | No | positive |
| 2 | CHD-1002 | 2 | Took too long, I missed my class. | negative | Yes | Negative, and email sent |
| 3 | CHD-1003 | 5 | The agent explained everything clearly. | positive | No | positive |
| 4 | CHD-1004 | 2 | Problem came back the next day. | negative | Likely | Negative if above 0.7 |
| 5 | CHD-1005 | 5 | Great service. | positive | No | positive |
| 6 | CHD-1006 | 2 | Nobody updated me on progress. | negative | Likely | Negative if above 0.7 |
| 7 | CHD-1007 | 4 | Very helpful and polite. | positive | No | positive |
| 8 | CHD-1008 | 3 | Okay, but I had to follow up twice. | mixed or neutral | No | the overall value returned |

Model scores are probabilities, so write down the real numbers you get:

| # | Probability positive | Probability negative | Overall |
|---|----------------------|----------------------|---------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |

## Questions to answer
1. Which rows scored negative above 0.7? Compare with the 5 rows in feedback.csv that
   have Rating 2.
2. Row 8 has Rating 3. What did the model return, and would a 0.7 threshold be right
   for your team?
3. Change the Title of CHD-1001. Did a run start? (It should not: Title is not in
   Select columns.)

## Canvas app check (Key phrase extraction)
Type the CHD-1025 description into txtDescription and select the button. Phrases such
as "CampusNet Wi-Fi" or "second floor" should appear in the gallery. Typing alone must
not call the model; only the button does.
