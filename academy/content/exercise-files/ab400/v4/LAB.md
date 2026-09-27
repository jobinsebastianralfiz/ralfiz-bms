# AB-400 · D.4 ALM and CI/CD for developers

## Files
- azure-pipelines.yml
- export-solution.yml
- deploymentSettings.test.json

## Steps
1. Download azure-pipelines.yml, export-solution.yml and deploymentSettings.test.json into your Git repository folder.
2. In the Campus Help Desk solution add environment variable chd_DirectoryApiUrl (Data type Text) with default value https://directory.example.edu/api.
3. Select the Ticket table in the solution, open Show dependencies and note what depends on it and what it depends on.
4. Run pac solution export --name CampusHelpDesk --path ./out/chd.zip, then pac solution unpack --zipfile ./out/chd.zip --folder ./src/CampusHelpDesk.
5. Run pac solution create-settings --solution-zip ./out/chd.zip --settings-file ./deploymentSettings.json and compare it with deploymentSettings.test.json; copy the Test value into a new deploymentSettings.test.json at the repository root.
6. In a test environment with a managed version installed, open a table form, choose See solution layers and identify the active layer.
7. Open Pipelines in the solution (or the pipelines app your admin set up) and add a Test stage as a target.
8. Create service connections chd-dev-connection and chd-test-connection with a service principal and run azure-pipelines.yml in Azure DevOps; or add PP_APP_ID, PP_CLIENT_SECRET, PP_TENANT_ID secrets and DEV_URL, TEST_URL variables and run export-solution.yml from .github/workflows in GitHub.

## Check your work
- [ ] src/CampusHelpDesk contains Other/Solution.xml and an environmentvariabledefinitions/chd_DirectoryApiUrl folder.
- [ ] Your generated deploymentSettings.json lists SchemaName chd_DirectoryApiUrl in EnvironmentVariables with an empty Value.
- [ ] The pipeline run shows the export, unpack, checker, pack and import steps succeeding, and the Test environment has CampusHelpDesk as a managed solution.
- [ ] In Test, the environment variable chd_DirectoryApiUrl has current value https://directory-test.example.edu/api.
