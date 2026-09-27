# PL-300 · B.5 Transform and shape data

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- tickets-jul.csv
- campus-targets.json
- survey-wide.csv

## Steps
1. Download tickets-jul.csv, campus-targets.json and survey-wide.csv into the same folder as tickets.csv, then open your Help Desk file and select Transform data.
2. In the Tickets query, set data types: TicketID and CategoryID to Whole number, CreatedDate and ClosedDate to Date, HoursToResolve to Decimal number, the rest to Text. Then add a Conditional column named IsClosed that returns Yes when Status equals Closed and No otherwise.
3. Right-click Tickets and choose Reference. Rename the new query Agents, keep only AssignedTo, then Remove duplicates.
4. Choose New source, Text/CSV and load tickets-jul.csv as a query named TicketsJul. Choose Home, Append queries as new, append TicketsJul to Tickets, and rename the result TicketsAll.
5. Right-click TicketsJul and TicketsAll and clear Enable load, so your model keeps the 60 January to June tickets for later lessons. Notice the names turn italic.
6. Choose New source, JSON and select campus-targets.json. Drill into the targets list, choose To table, expand Column1 (all fields), then expand the lead and supportHours records. Rename the query CampusTargets.
7. Load survey-wide.csv as a query named Survey. Select the Month column, choose Unpivot other columns, and rename Attribute to Campus and Value to Responses.
8. Select Tickets and use Group By on Campus with a Count rows operation. Look at the result, then delete that step so Tickets keeps its detail rows.
9. Select Close & Apply and confirm Tickets, Categories, Agents, CampusTargets and Survey appear in the Data pane, and TicketsJul and TicketsAll do not.

## Check your work
- [ ] Agents has 4 rows: Anu, Rahul, Joseph and Meera.
- [ ] TicketsAll has 72 rows (60 + 12). Its IsClosed column is null for the 12 July rows, because TicketsJul has no IsClosed column.
- [ ] CampusTargets has 3 rows (North 16, South 18, City 12 target hours) and columns such as lead.name and lead.email instead of a nested Record.
- [ ] Survey changes from 6 rows by 4 columns to 18 rows by 3 columns, and Responses adds up to 304 (North 106, South 129, City 69).
- [ ] The Group By preview shows South 25, North 21 and City 14, the cleaned values from B.4.
