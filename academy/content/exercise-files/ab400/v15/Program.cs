// SisSync - lesson D.15: inbound sync with an alternate key + UpsertRequest,
// and outbound "what changed?" with change tracking (RetrieveEntityChanges).
// Setup:
//   dotnet new console -n SisSync
//   cd SisSync
//   dotnet add package Microsoft.PowerPlatform.Dataverse.Client
//   (replace Program.cs with this file and copy sis-tickets.csv next to it)
// Needs: text column chd_externalref with an ACTIVE alternate key, and Track changes on Ticket.
// Set DATAVERSE_CONNECTION, for example:
//   AuthType=OAuth;Url=https://yourorg.crm.dynamics.com;RedirectUri=http://localhost;AppId=51f81489-12ee-4a9e-aaae-a2591f45987d;LoginPrompt=Auto
// Run:  dotnet run            (upsert every row of sis-tickets.csv)
//       dotnet run -- changes (list tickets changed since the last "changes" run)
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Query;

const string TokenFile = "datatoken.txt";
var priorities = new Dictionary<string, int> {
    ["Low"] = 100000000, ["Medium"] = 100000001, ["High"] = 100000002 };

string? conn = Environment.GetEnvironmentVariable("DATAVERSE_CONNECTION");
if (string.IsNullOrEmpty(conn)) { Console.WriteLine("Set DATAVERSE_CONNECTION first."); return; }
using var svc = new ServiceClient(conn);
if (!svc.IsReady) { Console.WriteLine("Connection failed: " + svc.LastError); return; }

if (args.Length > 0 && args[0] == "changes") { ShowChanges(); return; }

// ---- Inbound: upsert by alternate key, no GUIDs needed ----
int created = 0, updated = 0;
foreach (var row in ReadCsv("sis-tickets.csv"))
{
    // Entity(logicalName, keyName, keyValue) addresses the row by its alternate key.
    var t = new Entity("chd_ticket", "chd_externalref", row["External Ref"]);
    t["chd_title"] = row["Title"];
    t["chd_description"] = row["Description"];
    t["chd_priority"] = new OptionSetValue(priorities[row["Priority"]]);

    var r = (UpsertResponse)svc.Execute(new UpsertRequest { Target = t });
    if (r.RecordCreated) created++; else updated++;
    Console.WriteLine(row["External Ref"] + "  " + (r.RecordCreated ? "Created" : "Updated") + "  " + r.Target.Id);
}
Console.WriteLine("Done: " + created + " created, " + updated + " updated.");

// ---- Outbound: change tracking with a saved data token ----
void ShowChanges()
{
    string? token = File.Exists(TokenFile) ? File.ReadAllText(TokenFile).Trim() : null;
    Console.WriteLine(token == null ? "First run: every ticket counts as new." : "Changes since token " + token);
    var req = new RetrieveEntityChangesRequest
    {
        EntityName = "chd_ticket",
        Columns = new ColumnSet("chd_title", "chd_externalref"),
        PageInfo = new PagingInfo { Count = 500, PageNumber = 1, ReturnTotalRecordCount = false },
        DataVersion = token
    };
    int changed = 0, removed = 0;
    while (true)
    {
        var resp = (RetrieveEntityChangesResponse)svc.Execute(req);
        foreach (var c in resp.EntityChanges.Changes)
        {
            if (c.Type == ChangeType.NewOrUpdated)
            {
                var e = ((NewOrUpdatedItem)c).NewOrUpdatedEntity;
                changed++;
                Console.WriteLine("  changed: " + e.GetAttributeValue<string>("chd_title"));
            }
            else
            {
                removed++;
                Console.WriteLine("  deleted: " + ((RemovedOrDeletedItem)c).RemovedItem.Id);
            }
        }
        if (!resp.EntityChanges.MoreRecords)
        {
            File.WriteAllText(TokenFile, resp.EntityChanges.DataToken); // save for next time
            break;
        }
        req.PageInfo.PageNumber++;
        req.PageInfo.PagingCookie = resp.EntityChanges.PagingCookie;
    }
    Console.WriteLine(changed + " new or updated, " + removed + " deleted. Token saved to " + TokenFile);
}

// Minimal CSV reader that understands quoted fields with commas.
static List<Dictionary<string, string>> ReadCsv(string path)
{
    var lines = File.ReadAllLines(path).Where(l => l.Length > 0).ToList();
    var header = SplitLine(lines[0]);
    return lines.Skip(1).Select(l => {
        var cells = SplitLine(l);
        var d = new Dictionary<string, string>();
        for (int i = 0; i < header.Count; i++) d[header[i]] = i < cells.Count ? cells[i] : "";
        return d;
    }).ToList();
}

static List<string> SplitLine(string line)
{
    var result = new List<string>(); var cell = new System.Text.StringBuilder(); bool quoted = false;
    for (int i = 0; i < line.Length; i++)
    {
        char c = line[i];
        if (c == '"' && quoted && i + 1 < line.Length && line[i + 1] == '"') { cell.Append('"'); i++; }
        else if (c == '"') quoted = !quoted;
        else if (c == ',' && !quoted) { result.Add(cell.ToString()); cell.Clear(); }
        else cell.Append(c);
    }
    result.Add(cell.ToString());
    return result;
}