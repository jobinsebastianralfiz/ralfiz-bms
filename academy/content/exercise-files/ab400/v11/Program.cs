// BulkLoad - lesson D.11: CreateMultiple vs single Create, and ExecuteTransaction.
// Setup:
//   dotnet new console -n BulkLoad
//   cd BulkLoad
//   dotnet add package Microsoft.PowerPlatform.Dataverse.Client
//   (replace Program.cs with this file and copy tickets.csv next to it)
// Connection string (application user from step 1 of the lab), for example:
//   AuthType=ClientSecret;Url=https://yourorg.crm.dynamics.com;ClientId=...;ClientSecret=...
// Put it in the environment variable DATAVERSE_CONNECTION, then: dotnet run
using System.Diagnostics;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Query;

const int RowCount = 200;
var priorities = new Dictionary<string, int> {
    ["Low"] = 100000000, ["Medium"] = 100000001, ["High"] = 100000002 };

string? conn = Environment.GetEnvironmentVariable("DATAVERSE_CONNECTION");
if (string.IsNullOrEmpty(conn)) { Console.WriteLine("Set DATAVERSE_CONNECTION first."); return; }
using var svc = new ServiceClient(conn);
if (!svc.IsReady) { Console.WriteLine("Connection failed: " + svc.LastError); return; }
Console.WriteLine("Connected to " + svc.ConnectedOrgFriendlyName);

// Read tickets.csv (28 rows) and cycle through it to build test rows.
var source = ReadCsv("tickets.csv");
Console.WriteLine("Read " + source.Count + " tickets from tickets.csv");

List<Entity> BuildRows(string prefix)
{
    var list = new List<Entity>();
    for (int i = 0; i < RowCount; i++)
    {
        var row = source[i % source.Count];
        var e = new Entity("chd_ticket");
        e["chd_title"] = prefix + " " + row["Title"];
        e["chd_description"] = row["Description"];
        e["chd_priority"] = new OptionSetValue(priorities[row["Priority"]]);
        list.Add(e);
    }
    return list;
}

// 1. CreateMultiple: one request for 200 rows.
var sw = Stopwatch.StartNew();
var bulk = (CreateMultipleResponse)svc.Execute(new CreateMultipleRequest {
    Targets = new EntityCollection(BuildRows("[Bulk]")) { EntityName = "chd_ticket" } });
sw.Stop();
Console.WriteLine("CreateMultiple: " + bulk.Ids.Length + " rows in " + sw.ElapsedMilliseconds + " ms");

// 2. The same number of single Create calls.
var singleIds = new List<Guid>();
sw.Restart();
foreach (var e in BuildRows("[Single]")) singleIds.Add(svc.Create(e));
sw.Stop();
Console.WriteLine("Single Create:  " + singleIds.Count + " rows in " + sw.ElapsedMilliseconds + " ms");

// 3. ExecuteTransaction: the second update fails, so the first must be rolled back.
Guid firstId = bulk.Ids[0];
string before = svc.Retrieve("chd_ticket", firstId, new ColumnSet("chd_title")).GetAttributeValue<string>("chd_title");
var tx = new ExecuteTransactionRequest { Requests = new OrganizationRequestCollection() };
var good = new Entity("chd_ticket", firstId); good["chd_title"] = "[Tx] this change must not stay";
var bad = new Entity("chd_ticket", Guid.NewGuid()); bad["chd_title"] = "row that does not exist";
tx.Requests.Add(new UpdateRequest { Target = good });
tx.Requests.Add(new UpdateRequest { Target = bad });
try { svc.Execute(tx); Console.WriteLine("Transaction unexpectedly succeeded."); }
catch (Exception ex) { Console.WriteLine("Transaction failed as planned: " + ex.Message); }
string after = svc.Retrieve("chd_ticket", firstId, new ColumnSet("chd_title")).GetAttributeValue<string>("chd_title");
Console.WriteLine("Title before: " + before);
Console.WriteLine("Title after:  " + after);
Console.WriteLine("First update rolled back: " + (before == after));

// 4. Clean up the test rows with ExecuteMultiple in batches of 100.
Console.Write("Delete the " + (bulk.Ids.Length + singleIds.Count) + " test rows? (y/n) ");
if (Console.ReadLine()?.Trim().ToLower() == "y")
{
    var all = bulk.Ids.Concat(singleIds).ToList();
    for (int i = 0; i < all.Count; i += 100)
    {
        var batch = new ExecuteMultipleRequest {
            Settings = new ExecuteMultipleSettings { ContinueOnError = true, ReturnResponses = false },
            Requests = new OrganizationRequestCollection() };
        foreach (var id in all.Skip(i).Take(100))
            batch.Requests.Add(new DeleteRequest { Target = new EntityReference("chd_ticket", id) });
        svc.Execute(batch);
    }
    Console.WriteLine("Deleted " + all.Count + " rows.");
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