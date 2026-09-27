# AB-400 developer toolkit checklist (Campus Help Desk)

Work through the list in order. Tick each box when the command gives the expected result.
Run verify-toolkit.js at the end: it repeats the key checks for you.

## 1. Editors and runtimes
- [ ] VS Code installed (any recent version)
- [ ] Power Platform Tools extension installed from the Extensions view (publisher: Microsoft)
- [ ] .NET SDK 8 or later: dotnet --version prints 8.x or higher
- [ ] Node.js LTS (20 or 22): node --version prints v20.x or v22.x
- [ ] npm works: npm --version prints a version number
- [ ] Git installed: git --version

## 2. Power Platform CLI (pac)
- [ ] pac on your path: running pac prints the "Microsoft PowerPlatform CLI" banner and a command list
- [ ] Alternative install if pac is missing: dotnet tool install --global Microsoft.PowerApps.CLI.Tool
- [ ] Update when asked: dotnet tool update --global Microsoft.PowerApps.CLI.Tool (or update the VS Code extension)

## 3. Connect to your developer environment
| Command | What you should see |
|---|---|
| pac auth create --environment https://yourdevenv.crm.dynamics.com | A browser sign-in, then "Authentication profile created" |
| pac auth list | One profile with an asterisk (*) marking it active |
| pac org who | Your environment URL and your user name / ID |
| pac solution list | A row with unique name CampusHelpDesk |

Tip: keep one profile per environment (dev and test). Switch with pac auth select --index N.
Always run pac org who before an import so you never deploy to the wrong place.

## 4. Plug-in Registration Tool (Windows only)
- [ ] pac tool prt downloads and opens the Plug-in Registration Tool
- [ ] Create new connection > Office 365 > sign in > choose your dev environment
- [ ] The Registered Plugins & Custom Workflow Activities list opens (it may show only Microsoft assemblies)
- On macOS or Linux: note that you need a Windows machine or VM for this step.

## 5. Prove you can move a solution
- [ ] mkdir out
- [ ] pac solution export --name CampusHelpDesk --path ./out/CampusHelpDesk.zip
- [ ] The file out/CampusHelpDesk.zip exists and is larger than 0 bytes

## 6. Run the verify script
- [ ] node verify-toolkit.js
- [ ] The last line reads: RESULT: 6 of 6 checks passed

## Troubleshooting
| Symptom | Fix |
|---|---|
| pac: command not found | Restart VS Code after installing the extension, or install the .NET tool and open a new terminal |
| Solution CampusHelpDesk not in pac solution list | You are on the wrong profile: pac auth list, then pac auth select |
| Export fails with 401/403 | Your user needs System Customizer or System Administrator in the dev environment |
| pac tool prt fails on macOS | Expected: the tool is Windows only |
