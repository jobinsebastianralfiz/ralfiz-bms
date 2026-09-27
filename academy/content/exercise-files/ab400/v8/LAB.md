# AB-400 · D.8 Deploy and manage code apps

## Files
- telemetry.ts
- publish-code-app.yml
- queries.txt
- release-checklist.md

## Steps
1. Download the files and open release-checklist.md; work through it in order while you do these steps.
2. In the chd-staff-dashboard folder run npm run build, then pa solution list and copy the CampusHelpDesk solution ID.
3. Run pa app push --solution-id SOLUTION-ID, open the returned URL and confirm the app appears in the Campus Help Desk solution.
4. Share the app with a colleague: pa app share --principal THEIR-OBJECT-ID --access play (or Share in Power Apps).
5. Create an Application Insights resource in Azure, run npm install @microsoft/applicationinsights-web, save telemetry.ts in src, add your environment ID and connection string, and call initTelemetry() in src/main.tsx.
6. Build and push again, open the app, press F12 and note every connect-src CSP error in the Console.
7. In the admin center open Privacy + Security > Content security policy > App tab, add those hosts to connect-src, save, wait a few minutes and reload.
8. In Application Insights > Logs run the three queries in queries.txt; optionally add publish-code-app.yml to .github/workflows for service principal publishing.

## Check your work
- [ ] pa app push returns an app URL and the app is listed under Campus Help Desk > Objects.
- [ ] Before the CSP change, the Console shows connect-src violations for the Application Insights host; after it, the errors are gone.
- [ ] Query 1 in queries.txt returns sessionLoadSummary rows after you open the app a few times.
- [ ] Query 2 draws a time chart with a p75_tti_ms value for today.
