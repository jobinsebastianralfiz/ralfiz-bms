# Analysis worksheet: what is behind the Help Desk numbers?

Fill in the Answer column as you work through the lab. Every answer comes from a visual you build.

| # | Question | Visual or feature | Answer |
|---|---|---|---|
| 1 | Which campus logs the most tickets, and how many? | Column chart of [Ticket Count] by Campus |  |
| 2 | What does Analyze > Explain the increase (or Find where this distribution is different) suggest? | Right-click the tallest column |  |
| 3 | Which 4-hour band of HoursToResolve holds the most tickets? How many tickets have no hours yet? | Group (bins of size 4) on HoursToResolve |  |
| 4 | What is the average number of tickets per month? Is any month above it? | Line chart + Average line in the Analytics pane |  |
| 5 | Which factor most increases the chance that a ticket is High priority? | Key influencers |  |
| 6 | Which campus uses the most hours, and which agent within it? | Decomposition tree on [Total Hours] |  |
| 7 | Which agent handles the most tickets? Who has the highest average hours? | Scatter chart by AssignedTo |  |

## Notes for the analyst
- The dataset has only 60 tickets. AI visuals may say there is not enough data, or give weak results. That is normal: write down what it shows and whether you trust it.
- Forecast in the Analytics pane needs a continuous date axis. If the option is missing on a Month axis, switch the X-axis to 'Date'[Date] and set its type to Continuous.
- Groups and bins create a new column in the Data pane. You can edit them later by right-clicking the new column.
- A pattern is not a cause. Before you tell Suresh that one campus is slower, check how many tickets are behind each number.

## One-sentence finding
Write one sentence you would say to the help desk manager:

> ...