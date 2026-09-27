# Release checklist - Help Desk Staff Dashboard (code app)

## 1. Publish into the right solution
- [ ] npm run build finishes without errors (creates the dist folder)
- [ ] pa solution list shows CampusHelpDesk; copy its ID (a GUID, not the name)
- [ ] pa app push --solution-id <GUID> returns an app URL
- [ ] In make.powerapps.com, Solutions > Campus Help Desk > Objects shows "Help Desk Staff Dashboard" as an app

## 2. Share
- [ ] pa app share --principal <colleague object ID> --access play  (or Share in Power Apps)
- [ ] The colleague has a Power Apps Premium licence, or the environment uses pay-as-you-go, App Pass or auto-claim
- [ ] For CI/CD: shared once with the service principal using --access edit

## 3. Content Security Policy
Default connect-src for code apps is 'none', so calls to outside sites are blocked.
- [ ] Open the app, press F12 > Console. Record each "Refused to connect ... violates the following Content Security Policy directive: connect-src" error.
- [ ] Admin center > Environments > your environment > Settings > Product > Privacy + Security > Content security policy > App tab
- [ ] Add to connect-src (use the exact hosts from your errors), for example:
      https://*.in.applicationinsights.azure.com
      https://js.monitor.azure.com
      https://directory-test.example.edu
- [ ] Save, wait a few minutes, reload the app: the CSP errors are gone
- Remember: this setting affects every code app in the environment. Add only what you need, and never add these hosts to script-src to fix a fetch.

## 4. Telemetry
- [ ] telemetry.ts is in src and initTelemetry() runs in main.tsx
- [ ] Open the app 3 times, wait 5 minutes, run query 1 in queries.txt: you see sessionLoadSummary rows
- [ ] Run query 2 and save the chart to a workbook or dashboard

## 5. Troubleshooting notes
- DevTools Network: filter apihub.net for connector calls and dynamics.com for Dataverse calls
- Power Apps Monitor shows app open success rate, sessions and time to interactive; not data request latency
- Keep secrets out of the bundle: it is served from a public endpoint
