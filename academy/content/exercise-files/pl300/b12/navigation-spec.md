# Navigation and usability spec: Help Desk report

## Pages
| Page | Purpose | Visible to readers |
|---|---|---|
| Overview | Summary built in B.11 | Yes |
| Category details | Drillthrough target: every ticket of one category | Yes, reached by drillthrough |
| Hours tooltip | Report page tooltip for the bar chart | No (hide the page) |

## Drillthrough: Category details
- Drillthrough field: Categories[Name]. Keep "Keep all filters" on so the Campus slicer still applies.
- Table columns: TicketID, CreatedDate, Priority, Status, Campus, AssignedTo, HoursToResolve.
- Add a Back button at the top left (Desktop adds one automatically when you add a drillthrough field).

## Tooltip page
- Page information: Allow use as tooltip = On. Canvas settings: Type = Tooltip.
- One card: [Median hours] (from B.9). One small text box: "Median hours to resolve".
- On Overview, select the bar chart > Format > Properties > Tooltips > Type: Report page > Page: Hours tooltip.

## Interactions
- Clicking a bar on the bar chart **filters** the line chart (not highlight).
- The matrix keeps the default.

## Slicers
- Campus slicer synced across Overview and Category details (View > Sync slicers).

## Bookmarks and buttons
| Bookmark | Matrix | Other visuals |
|---|---|---|
| Summary | Hidden | Visible |
| Detail | Visible | Visible |
Two buttons, "Summary" and "Detail", with Action = Bookmark. Group them as "Nav buttons" in the Selection pane.

## Accessibility
| Visual | Alt text |
|---|---|
| Ticket count card | Total number of help desk tickets for the current filters. |
| Bar chart | Tickets by category. Hardware has the most tickets. |
| Line chart | Tickets logged per month from January to June 2026. |
| Matrix | Tickets per agent, split by status. |
Tab order: title, slicers, card, bar chart, line chart, matrix, nav buttons.

## Mobile layout
Phone view shows, top to bottom: title, Campus slicer, card, bar chart.