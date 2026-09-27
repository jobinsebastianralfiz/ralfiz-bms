# PL-300 · B.13 Find patterns and trends

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- measures.txt
- analysis-worksheet.md

## Steps
1. Download measures.txt and analysis-worksheet.md. Create Total Hours and Average Hours (and Ticket Count if missing) from measures.txt.
2. On a new page, add a column chart of [Ticket Count] by Campus. Right-click the tallest column and choose Analyze, then Explain the increase or a similar option if shown.
3. In the Data pane, right-click HoursToResolve and choose New group. Create bins of size 4. Build a column chart of Ticket Count by the new bin column.
4. Add a line chart with Date[Month] on the X-axis and [Ticket Count] on the Y-axis. In the Analytics pane, add an Average line and a Forecast if the option is available for your axis.
5. Add a Key influencers visual. Put Priority in Analyze and Campus, Categories[Name] and AssignedTo in Explain by. Choose High as the value to explain and read the result.
6. Add a Decomposition tree with [Total Hours] in Analyze and Campus, Name and AssignedTo in Explain by. Expand the tree and use the high-value AI split once.
7. Build a scatter chart of AssignedTo (Values), [Ticket Count] (X) and [Average Hours] (Y). Try the automatic clusters option from the visual’s More options menu if it appears.
8. Fill in every answer in analysis-worksheet.md, including the one-sentence finding.

## Check your work
- [ ] The Campus column chart reads South 25, North 21, City 14.
- [ ] In the bins chart the tallest bin is 12 (12 to under 16 hours) with 11 tickets, then 8 with 10; 14 tickets fall in (Blank) because they are not closed.
- [ ] The Average line on the monthly chart sits at 10, and every month equals it.
- [ ] The Decomposition tree starts at 795.8 Total Hours and splits North 331.9, South 323.7, City 140.2; under South, Joseph has the most hours (148.6).
- [ ] The scatter chart has four points: Rahul 18 tickets / 16.13 hours, Joseph 17 / 19.28, Anu 13 / 15.90, Meera 12 / 16.65.
