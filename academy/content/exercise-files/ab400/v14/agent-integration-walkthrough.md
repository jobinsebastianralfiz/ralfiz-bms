# Agent integration walkthrough (lesson D.14)

Several features here are in **preview** and change often. Each part lists only what
Microsoft documents; where a screen may look different, the step says what to look for.
Check the linked Microsoft Learn pages before you rely on a detail.

## Part A. Turn on the Dataverse MCP server (admin)
1. Go to https://admin.powerplatform.microsoft.com and choose **Manage > Environments**.
2. Select your developer environment, then **Settings > Product > Features**.
3. Find **Dataverse Model Context Protocol** and turn on
   **Allow MCP clients to interact with Dataverse MCP server**.
4. Only the Microsoft Copilot Studio client is allowed by default. To allow another client,
   open **Advanced Settings** from the environment settings, open the client record
   (for example *Microsoft GitHub Copilot*), set **Is Enabled** to **Yes** and choose
   **Save & Close**.

Facts to remember
- The endpoint is your environment URL plus /api/mcp, for example
  https://yourorg.crm.dynamics.com/api/mcp. Find the URL in make.powerapps.com under
  Settings (gear) > Session details > Instance url.
- The allow list applies to the /api/mcp entry point.
- Turning the setting off stops every tool and agent that uses the server.

## Part B. Use the server from VS Code with GitHub Copilot
1. In VS Code open the Command Palette (Ctrl+Shift+P) and run **MCP: Add Server**.
2. Choose **HTTP or Server Sent Events** and paste your /api/mcp URL.
3. Accept or type a server name, then choose **Global** or **Workspace**.
4. Open Copilot Chat (Ctrl+Alt+I) and select **Agent** mode.
5. Ask: "List the Ticket rows whose status is Open, with title and priority."
6. Before you approve each tool call, read which tool Copilot wants to run and with which
   input. Write the tool names down; do not hard-code them in your own code, because
   Microsoft notes that tool names can change.

## Part C. A code-first agent in Microsoft Foundry
1. In the Foundry portal create (or open) a project and create a prompt agent named
   **Ticket Analyst**. Paste the instructions from ticket-analyst-instructions.md.
2. Add an MCP tool. The settings you need are the ones named in the lesson:
   server_label (dataverse), server_url (your /api/mcp URL), require_approval,
   allowed_tools and a project connection that holds the authentication.
3. Set require_approval to **always** and limit allowed_tools to the read tools you noted
   in Part B (for example search_data and read_query), so the agent can never create,
   update or delete tickets during testing.
4. Run the test questions from ticket-analyst-instructions.md. With approval set to
   always, each tool call waits for you to approve it.

The same settings in the Python SDK (from the lesson):

    tool = MCPTool(
        server_label="dataverse",
        server_url="https://yourorg.crm.dynamics.com/api/mcp",
        require_approval="always",
        allowed_tools=["search_data", "read_query"],
        project_connection_id=DATAVERSE_CONNECTION)

## Part D. Connect agents in Copilot Studio
1. Open **Help Desk Assistant** in Copilot Studio and go to the **Agents** page.
2. Choose **Add an agent** and look at the options: other Copilot Studio agents,
   agents over the Agent2Agent (A2A) protocol, and Microsoft Foundry agents (preview).
3. For a Foundry agent you pick a connection to the Foundry project and give a name, a
   description and the agent ID. Read the prerequisites on that screen first: the Foundry
   agent must expose what Copilot Studio needs.
4. Write the description with care. Generative orchestration reads it to decide when to
   route to that agent. Use the description in ticket-analyst-instructions.md.

## Part E. Talk to a Copilot Studio agent from your own code
The Copilot Studio client library is part of the Microsoft 365 Agents SDK (.NET,
JavaScript and Python).
1. Publish Help Desk Assistant with Microsoft authentication (or manual authentication).
   The client library does not work with "No authentication".
2. Collect the connection details your app needs (environment ID and the agent's schema
   name, or the connection details shown for the agent).
3. Register an app in Microsoft Entra ID with the delegated Power Platform API permission
   **CopilotStudio.Copilots.Invoke**.
4. Clone the Microsoft Agents repository on GitHub (github.com/microsoft/Agents), open the
   Copilot Studio client sample for your language and follow its README. In .NET the
   CopilotClient class starts a conversation (StartConversationAsync) and sends questions
   (AskQuestionAsync).

## Security rules for every part
- MCP does not copy data into the agent. Tools run at request time and Dataverse security
  still applies to the identity that calls them.
- Limit tools with allowed_tools and require approval for anything that writes or deletes.
- Work IQ tools run on behalf of the signed-in user; app-only access is not supported.