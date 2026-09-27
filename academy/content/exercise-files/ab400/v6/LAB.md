# AB-400 · D.6 PCF code components

## Files
- ControlManifest.Input.xml
- start/index.ts
- solution/index.ts
- StarRating.css

## Steps
1. Complete the “Which UX extension?” sorter above.
2. Create a folder StarRating and run pac pcf init --namespace Chd --name StarRating --template field --run-npm-install.
3. Replace the generated StarRating/ControlManifest.Input.xml with the downloaded ControlManifest.Input.xml, create StarRating/css and save StarRating.css in it.
4. Replace StarRating/index.ts with start/index.ts and fill TODO 1 to TODO 5 (read parameters, add the listener, store and notify, return getOutputs, remove listeners).
5. Run npm run build, then npm start watch; in the test harness set rating and maxStars in the Inputs panel and click the stars.
6. Run pac pcf push --publisher-prefix chd to deploy the component to your dev environment.
7. Add a whole number column chd_satisfaction (minimum 1, maximum 5) to Ticket; on the main form select the column, add the Star rating component for web, save and publish.
8. For ALM, in a sibling folder run pac solution init --publisher-name CampusHelpDesk --publisher-prefix chd, then pac solution add-reference --path ../StarRating and dotnet build; compare your index.ts with solution/index.ts if anything fails.

## Check your work
- [ ] npm run build finishes with no TypeScript errors.
- [ ] In the test harness, 5 stars appear; clicking the 4th fills 4 stars and the rating output shows 4. Setting maxStars to 10 draws 10 stars.
- [ ] On ticket CHD-1001 in the staff app, clicking 3 stars and saving stores 3 in chd_satisfaction (visible in an Advanced find or view column).
- [ ] dotnet build of the solution project produces a zip in bin/Debug that contains the Chd.StarRating control.
