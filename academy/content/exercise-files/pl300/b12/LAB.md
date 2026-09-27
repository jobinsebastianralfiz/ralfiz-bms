# PL-300 · B.12 Storytelling and usability

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- navigation-spec.md

## Steps
1. Download navigation-spec.md and keep it open while you build.
2. Create a page named Category details. Add Categories[Name] to its Drillthrough well, then add a table with the columns from the spec. Test by right-clicking a bar on Overview and choosing Drill through.
3. Create a page named Hours tooltip, turn on Allow use as tooltip in page information, set canvas size to Tooltip, and add a card with Median hours. Set it as the report page tooltip for the bar chart, then hide the page.
4. On Overview, choose Format > Edit interactions and set the line chart to Filter (not Highlight) when the bar chart is clicked.
5. Open View > Sync slicers and make the Campus slicer apply to both Overview and Category details.
6. Hide the matrix, add a bookmark named Summary, show the matrix, add a bookmark named Detail, and link two buttons to them.
7. Open the Selection pane, group the two buttons, set the tab order from the spec, and add the alt text from the spec to each chart.
8. Open View > Mobile layout and place the title, Campus slicer, card and bar chart for a phone screen.

## Check your work
- [ ] Drilling through on Hardware shows 22 tickets; on Accounts, 10.
- [ ] Hovering over the bars shows Median hours: Accounts 18.4, Network 14.1, Software 12.95, Hardware 12.5.
- [ ] With North selected on Overview, drilling through on Network shows 8 tickets, because the slicer is synced.
- [ ] Clicking the Summary button hides the matrix; Detail shows it again.
