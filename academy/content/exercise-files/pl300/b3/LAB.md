# PL-300 · B.3 Get and connect to data

## Files
- shared-data/pbi/tickets.csv
- shared-data/pbi/categories.csv
- parameter-queries.txt

## Steps
1. Download parameter-queries.txt and keep tickets.csv and categories.csv in one folder.
2. Open HelpDesk.pbix and choose Transform data to open Power Query Editor.
3. Choose Manage parameters, then New parameter. Name it DataFolder, type Text, and set its value to the folder that holds your CSV files, ending with a backslash.
4. Select the tickets query, open Advanced Editor, and replace the hard-coded path in File.Contents with DataFolder & "tickets.csv", as in parameter-queries.txt. Do the same for categories with "categories.csv".
5. Test the parameter: set DataFolder to a folder that does not exist and select the tickets query, read the error, then set it back to the right folder.
6. Choose Close & Apply. Then choose File, Options and settings, Data source settings. Select your folder source and look at Edit Permissions to see the credential type and privacy level.
7. In Model view, select the tickets table and open its Advanced properties. Confirm the Storage mode is Import.
8. Choose Get data, then Power BI semantic models. Note that this connects live to a published model; close the window without connecting.

## Check your work
- [ ] With the correct DataFolder, tickets still loads 60 rows and 9 columns, and categories 4 rows.
- [ ] With a wrong DataFolder, the tickets query shows a DataSource.Error saying the file or path could not be found.
- [ ] The Source step of both queries contains DataFolder & and no hard-coded folder.
- [ ] The tickets table Storage mode is Import.
