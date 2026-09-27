# AB-400 · D.3 Designing solution components

## Files
- component-design-worksheet.md
- escalate-ticket-api-spec.md

## Steps
1. Download component-design-worksheet.md and escalate-ticket-api-spec.md.
2. Open the Campus Help Desk solution, count every component by type and fill the inventory table in the worksheet.
3. Fill the design table in the worksheet for the six components: component type, reuse, security and monitoring.
4. In the solution select New > More > Other > Custom API (or open the Custom API table) and compare the form fields with the table in escalate-ticket-api-spec.md; only look, do not save.
5. Open Power Automate > Custom connectors and check whether a Campus Directory connector exists; write its authentication type (or “OAuth 2.0 with Entra ID, planned”) in row 3.
6. In the Power Platform admin center open your environment and find where Application Insights data export and monitoring are managed; note the path without changing settings.
7. Write one failure sentence per component in the worksheet, then compare the table with the model answer at the end.

## Check your work
- [ ] The design table has six complete rows, and row 1 says Custom API implemented by a plug-in.
- [ ] You located the Custom API form fields Unique name, Binding type and Is Function, and the spec’s values are Entity, chd_ticket and No.
- [ ] Row 2 names a PCF field component and row 4 an MCP server.
- [ ] Each of the six components has one failure sentence that names where you would see the failure.
