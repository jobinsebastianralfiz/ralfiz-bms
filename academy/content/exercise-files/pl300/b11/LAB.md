# PL-300 · B.11 Build reports

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- report-brief.md
- helpdesk-theme.json

## Steps
1. Download report-brief.md and helpdesk-theme.json, and read the questions the page must answer.
2. Create a page named Overview. Add a card for Ticket Count, a clustered bar chart of Ticket Count by Categories[Name] sorted largest first, and a line chart by Date[Month].
3. Add slicers for Campus and Priority. In the Filters pane, add a page-level filter on Campus that excludes (Blank).
4. Add a matrix with AssignedTo on rows, Status on columns and Ticket Count as values. Apply conditional formatting: a background colour scale on the values.
5. Open View > Themes > Browse for themes and select helpdesk-theme.json. Then use Customize current theme to change one colour.
6. Set the page canvas to 16:9 and a background in the Format pane for the page, and add the title text box from the brief.
7. If your tenant has Copilot, open the Copilot pane and ask it to suggest content for a page about resolution times. Otherwise add a Narrative visual and write a short summary.

## Check your work
- [ ] The card shows 60, and still 60 after the page filter, because no Campus value is blank.
- [ ] The bar chart reads Hardware 22, Network 16, Software 12, Accounts 10; the line chart is flat at 10 per month from Jan to Jun.
- [ ] Selecting North in the Campus slicer changes the card to 21 and the Network bar to 8.
- [ ] The matrix shows Joseph with 16 Closed and 1 Open, Rahul with 12 Closed, 4 Open and 2 In progress, and Anu with 4 Open.
- [ ] The first bar series uses the theme blue #1F6FB2 after you import helpdesk-theme.json.
