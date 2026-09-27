# AB-400 · D.16 Custom connectors

## Files
- shared-data/hd/staff.csv
- DirectoryFunctions.cs
- campus-directory-api.swagger.json
- script.cs

## Steps
1. Download the exercise files. Add DirectoryFunctions.cs to your NightlySlaCheck project from lesson D.12, run it locally and open http://localhost:7071/api/staff?email=meera.iyer@staff.example.edu.
2. Deploy the project to your Function App and copy a function key (or the default host key) from the App keys page.
3. In campus-directory-api.swagger.json replace the host value with your Function App host name, for example yourapp.azurewebsites.net.
4. In make.powerautomate.com open Solutions > Campus Help Desk and add a new custom connector named Campus Directory API by importing the OpenAPI file. On the Security page check API Key, parameter name x-functions-key, location Header, and set the label to Function key.
5. On the Definition page check GetStaff and SearchStaff and look at x-ms-summary, x-ms-visibility and x-ms-dynamic-values in the Swagger editor. Add a policy with the Set HTTP Header template: header x-client, value campus-help-desk.
6. On the Code page turn code on, paste script.cs, apply it to GetStaff and SearchStaff, and create the connector.
7. On the Test page create a connection with your function key, test GetStaff with meera.iyer@staff.example.edu, then SearchStaff with department Infrastructure.
8. In a cloud flow in the solution, look up ticket CHD-1021 and call GetStaff with its assigned staff email (anu.sebastian@staff.example.edu) to get the agent’s department.

## Check your work
- [ ] Locally, /api/staff?email=meera.iyer@staff.example.edu returns firstName Meera, lastName Iyer and department Identity, with no fullName.
- [ ] Through the connector, GetStaff returns fullName “Meera Iyer” (added by script.cs), and an unknown email returns 404.
- [ ] SearchStaff with department Infrastructure returns 3 people (Anu Sebastian, Rahul Varma, Divya Nair), and the department dropdown lists Applications, Identity and Infrastructure.
- [ ] The Function App log shows “called by client campus-help-desk”, which proves the Set HTTP Header policy runs.
- [ ] The flow returns department Infrastructure for CHD-1021.
