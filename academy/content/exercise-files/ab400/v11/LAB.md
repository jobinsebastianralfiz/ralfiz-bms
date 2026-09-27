# AB-400 · D.11 Platform APIs and the SDKs

## Files
- shared-data/hd/tickets.csv
- webapi-requests.md
- Program.cs
- create_ticket.py

## Steps
1. In the Azure portal register an app in Microsoft Entra ID and create a client secret. In the Power Platform admin center add it as an application user in your developer environment with a security role that can create, read, update and delete chd_ticket.
2. Download the exercise files. Send requests 1 to 6 from webapi-requests.md with Postman or the VS Code REST Client and compare each answer with its Expected line.
3. Send request 7 first with If-Match: W/"1" and then with the real @odata.etag of the row, and change the title back.
4. Run dotnet new console -n BulkLoad, then in the new folder run dotnet add package Microsoft.PowerPlatform.Dataverse.Client. Replace Program.cs with the downloaded Program.cs and copy tickets.csv next to it.
5. Set the environment variable DATAVERSE_CONNECTION to AuthType=ClientSecret;Url=https://yourorg.crm.dynamics.com;ClientId=...;ClientSecret=... for your app, then run dotnet run.
6. Write down the CreateMultiple and single Create times and the transaction lines, then answer y to delete the 400 test rows.
7. Run pip install PowerPlatform-Dataverse-Client azure-identity, set DATAVERSE_URL to your environment URL and run python create_ticket.py. Sign in when the browser opens and answer y to delete the ticket at the end.

## Check your work
- [ ] Request 3 returns @odata.count 4 (CHD-1002, CHD-1009, CHD-1014, CHD-1017), request 5 returns 12 and request 6 returns Low 10, Medium 14 and High 4.
- [ ] Request 7 with If-Match: W/"1" returns 412 Precondition Failed; with the real etag it returns 204 No Content.
- [ ] BulkLoad prints “Read 28 tickets from tickets.csv”, then “CreateMultiple: 200 rows” and “Single Create:  200 rows”, and the CreateMultiple time is normally much lower.
- [ ] BulkLoad prints “First update rolled back: True”.
- [ ] create_ticket.py prints “Created ticket”, reads back “Projector broken in room 204” and reports “High priority tickets: 4”.
