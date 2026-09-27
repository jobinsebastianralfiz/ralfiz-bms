# AB-400 · D.1 The developer toolkit

## Files
- setup-checklist.md
- verify-toolkit.js

## Steps
1. Download setup-checklist.md and verify-toolkit.js into a new folder, for example chd-dev, and open that folder in VS Code.
2. Install the Power Platform Tools extension, the .NET SDK (8 or later) and Node.js LTS, ticking each item in section 1 of setup-checklist.md; confirm with dotnet --version and node --version.
3. In a new VS Code terminal run pac; if it is not found, run dotnet tool install --global Microsoft.PowerApps.CLI.Tool and open a new terminal.
4. Run pac auth create --environment https://yourdevenv.crm.dynamics.com (your own URL) and sign in with your developer account.
5. Run pac auth list, pac org who and pac solution list, and compare each output with the table in section 3 of the checklist.
6. On Windows, run pac tool prt, create a new connection to your developer environment and confirm the list of registered assemblies opens.
7. Run mkdir out, then pac solution export --name CampusHelpDesk --path ./out/CampusHelpDesk.zip.
8. Run node verify-toolkit.js in the same folder and fix any FAIL line using the troubleshooting table in setup-checklist.md.

## Check your work
- [ ] dotnet --version prints 8.x or higher and node --version prints v20 or higher.
- [ ] pac auth list shows exactly one profile marked with an asterisk, and pac org who shows your developer environment URL.
- [ ] pac solution list includes a row with unique name CampusHelpDesk.
- [ ] out/CampusHelpDesk.zip exists and is larger than 0 bytes.
- [ ] node verify-toolkit.js ends with “RESULT: 6 of 6 checks passed”.
