// Lesson D.12 - NightlySlaCheck: a Timer-triggered Azure Function (isolated worker).
// Every night at 02:00 UTC it finds tickets that are not Closed and are past their
// Due date, and raises their Priority to High with UpdateMultiple.
// Authentication: DefaultAzureCredential. In Azure this is the Function App's managed
// identity (added as an application user); on your PC it is your Azure CLI / VS Code sign-in.
using Azure.Core;
using Azure.Identity;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Query;

// ---- Host startup (isolated worker) ----
var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        services.AddApplicationInsightsTelemetryWorkerService();
        services.ConfigureFunctionsApplicationInsights();
    })
    .Build();
host.Run();

namespace ChdFunctions
{
    public class NightlySlaCheck
    {
        private const int BatchSize = 100;
        private readonly ILogger<NightlySlaCheck> _log;

        public NightlySlaCheck(ILogger<NightlySlaCheck> log) { _log = log; }

        [Function("NightlySlaCheck")]
        public async Task Run([TimerTrigger("0 0 2 * * *")] TimerInfo timer)
        {
            string url = Setting("DataverseUrl").TrimEnd('/');
            int high = int.Parse(Setting("PriorityHighValue", "100000002"));
            int closed = int.Parse(Setting("StatusClosedValue", "100000002"));
            bool dryRun = bool.Parse(Setting("DryRun", "false"));

            var credential = new DefaultAzureCredential();
            using var svc = new ServiceClient(new Uri(url), async _ =>
                (await credential.GetTokenAsync(
                    new TokenRequestContext(new[] { url + "/.default" }))).Token);
            if (!svc.IsReady) throw new InvalidOperationException("Dataverse connection failed: " + svc.LastError);

            // Open or In progress tickets whose Due date is before today (UTC).
            var query = new QueryExpression("chd_ticket")
            {
                ColumnSet = new ColumnSet("chd_title", "chd_priority", "chd_duedate"),
                PageInfo = new PagingInfo { Count = 5000, PageNumber = 1 }
            };
            query.Criteria.AddCondition("chd_duedate", ConditionOperator.LessThan, DateTime.UtcNow.Date);
            query.Criteria.AddCondition("chd_status", ConditionOperator.NotEqual, closed);

            var overdue = new List<Entity>();
            while (true)
            {
                EntityCollection page = await svc.RetrieveMultipleAsync(query);
                overdue.AddRange(page.Entities);
                if (!page.MoreRecords) break;
                query.PageInfo.PageNumber++;
                query.PageInfo.PagingCookie = page.PagingCookie;
            }

            // Only tickets that are not already High need an update.
            var updates = overdue
                .Where(t => t.GetAttributeValue<OptionSetValue>("chd_priority")?.Value != high)
                .Select(t =>
                {
                    var u = new Entity("chd_ticket", t.Id);
                    u["chd_priority"] = new OptionSetValue(high);
                    u["chd_escalationreason"] = "Overdue: raised by the nightly SLA check";
                    return u;
                })
                .ToList();

            _log.LogInformation("Found {Overdue} overdue tickets, {ToEscalate} need escalation.",
                overdue.Count, updates.Count);
            foreach (var t in overdue)
                _log.LogInformation("Overdue: {Title} (due {Due:yyyy-MM-dd})",
                    t.GetAttributeValue<string>("chd_title"), t.GetAttributeValue<DateTime>("chd_duedate"));

            if (dryRun)
            {
                _log.LogWarning("DryRun is true: no rows were updated.");
                return;
            }

            // UpdateMultiple in batches: one request per 100 rows.
            for (int i = 0; i < updates.Count; i += BatchSize)
            {
                var batch = updates.Skip(i).Take(BatchSize).ToList();
                await svc.ExecuteAsync(new UpdateMultipleRequest
                {
                    Targets = new EntityCollection(batch) { EntityName = "chd_ticket" }
                });
                _log.LogInformation("Updated {Count} tickets.", batch.Count);
            }

            if (timer.ScheduleStatus is not null)
                _log.LogInformation("Next run: {Next}", timer.ScheduleStatus.Next);
        }

        private static string Setting(string name, string? fallback = null) =>
            Environment.GetEnvironmentVariable(name) ?? fallback
            ?? throw new InvalidOperationException("Missing app setting " + name);
    }
}