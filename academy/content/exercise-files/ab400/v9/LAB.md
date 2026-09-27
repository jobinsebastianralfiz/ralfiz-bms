# AB-400 · D.9 Dataverse plug-ins

## Files
- start/ChdPlugins.csproj
- start/SetPriorityFromKeywords.cs
- solution/SetPriorityFromKeywords.cs
- test-cases.md

## Steps
1. Complete the sorter above.
2. Download the exercise files. In an empty folder named ChdPlugins run pac plugin init; it creates ChdPlugins.csproj, a ChdPlugins.snk key and sample classes.
3. Replace the generated ChdPlugins.csproj with the downloaded ChdPlugins.csproj, delete the generated sample plug-in class (Plugin1.cs) and add SetPriorityFromKeywords.cs from the start folder.
4. Open test-cases.md, check the Priority choice values in your Ticket table, then fill TODO 1 to 4 in SetPriorityFromKeywords.cs and run dotnet build -c Release (compare with the solution file if you get stuck).
5. Run pac tool prt, connect to your developer environment and register bin/Release/net462/ChdPlugins.dll as a new assembly.
6. Register the two steps exactly as in the Step registrations table of test-cases.md: Create (PreOperation, Synchronous) and Update with filtering attributes chd_title and chd_description plus a pre-image named PreImage.
7. Turn the plug-in trace log setting to All, run test cases T1 to T6 from test-cases.md in the Help Desk Staff app, and read the newest trace rows with GET /api/data/v9.2/plugintracelogs?$select=typename,messageblock&$orderby=createdon desc&$top=5.
8. Add the assembly and both steps to the Campus Help Desk solution, then do the Clean up section of test-cases.md.

## Check your work
- [ ] dotnet build -c Release ends with 0 errors and creates bin/Release/net462/ChdPlugins.dll.
- [ ] T1 “Wi-Fi outage in library” and T3 “Cannot Log In to the LMS” are saved with Priority High; T2 “Printer out of toner in lab 3” keeps Priority Low.
- [ ] T5 (only the Title of CHD-1017 changes) sets Priority back to High, because “exam” is read from the pre-image description.
- [ ] T4 and T6 add no new trace row, because Priority and Status are not filtering attributes.
- [ ] The trace row for T1 has typename ChdPlugins.SetPriorityFromKeywords and its messageblock contains “Keyword 'outage' found”.
