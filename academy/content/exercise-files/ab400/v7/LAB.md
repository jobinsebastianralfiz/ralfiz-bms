# AB-400 · D.7 Build Power Apps code apps

## Files
- package.json
- start/OpenTickets.tsx
- solution/OpenTickets.tsx

## Steps
1. Turn on Power Apps code apps in your developer environment’s Features settings in the Power Platform admin center.
2. Run npx degit github:microsoft/PowerAppsCodeApps/templates/vite chd-staff-dashboard, cd into it, and compare its package.json with the downloaded package.json (keep the template’s versions).
3. Run npm install --global @microsoft/power-apps-cli, npm install --global @microsoft/power-apps and npm install.
4. Run pa app init --display-name "Help Desk Staff Dashboard" --environment-id YOUR-ENVIRONMENT-ID and sign in when asked.
5. Run pa app add data-source --connector dataverse --table chd_ticket and open src/generated/services to find the generated service name.
6. Copy start/OpenTickets.tsx into src, fix the service import, and fill TODO 1 to TODO 4 with getAll (select, filter statecode eq 0, orderBy chd_duedate asc, top 50) and the list.
7. Run pa connection create --connector shared_office365users, then pa app add data-source --connector shared_office365users --connection-id CONNECTION-ID, and fill TODO 5 and 6 with MyProfile_V2.
8. Render OpenTickets from src/App.tsx, run pa app run and open the Local Play URL in the browser profile you use for Power Platform; compare with solution/OpenTickets.tsx if needed.

## Check your work
- [ ] src/generated/models and src/generated/services contain files for chd_ticket and Office 365 Users.
- [ ] With the 16 Closed tickets deactivated (as in lesson v5), the page shows “12 open tickets”.
- [ ] The first row is “Laptop will not charge - due 2026-08-20” with a High badge, and it is the only High row.
- [ ] The page shows “Signed in as” followed by your display name.
