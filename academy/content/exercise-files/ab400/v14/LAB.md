# AB-400 · D.14 Code-first agents with Microsoft Foundry

## Files
- shared-data/hd/tickets.csv
- agent-integration-walkthrough.md
- ticket-analyst-instructions.md

## Steps
1. Download the exercise files and read agent-integration-walkthrough.md from start to end.
2. Part A: in the Power Platform admin center check that Allow MCP clients to interact with Dataverse MCP server is on (or ask your admin), and enable the Microsoft GitHub Copilot client in Advanced Settings.
3. Part B: in VS Code run MCP: Add Server, choose HTTP, paste https://yourorg.crm.dynamics.com/api/mcp, then ask Copilot in Agent mode for the Open tickets. Write down each tool it calls.
4. Part C: in the Foundry portal create the prompt agent Ticket Analyst with the instructions from ticket-analyst-instructions.md, and add the Dataverse MCP tool with require_approval always and only read tools in allowed_tools.
5. Ask Ticket Analyst questions Q1 to Q6 from ticket-analyst-instructions.md, approve each read tool call, and record the tool and input for each answer.
6. Part D: in Copilot Studio open Help Desk Assistant > Agents > Add an agent and review the Microsoft Foundry and A2A options and their prerequisites. If your tenant allows the preview, connect Ticket Analyst with the description from the file and run the routing test.
7. Part E: clone github.com/microsoft/Agents, open the Copilot Studio client sample for your language and list the settings its README asks for.

## Check your work
- [ ] VS Code lists your Dataverse MCP server and Copilot answers with 6 Open tickets, CHD-1023 to CHD-1028.
- [ ] Ticket Analyst answers Q2 with Network (2 tickets: CHD-1025 and CHD-1028) and Q4 with 4 High priority tickets.
- [ ] Q6 changes nothing: CHD-1023 is still Open, because allowed_tools contains no write tool.
- [ ] Every tool call waited for your approval before it ran.
- [ ] Your Part E notes list the agent connection details (environment ID and schema name) and an app registration with the CopilotStudio.Copilots.Invoke permission.
