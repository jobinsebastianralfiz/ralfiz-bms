// Lesson D.15 - TicketWebhook: an HTTP-triggered function that receives Dataverse webhook posts.
// Add this file to the NightlySlaCheck project from lesson D.12 (same packages, same host).
// Register it in the Plug-in Registration Tool: Register New Web Hook,
//   Endpoint URL  https://<your-function-app>.azurewebsites.net/api/ticket-webhook
//   Authentication WebhookKey, value = the function key (Dataverse sends it as ?code=...)
// then a step: Update of chd_ticket, filtering attribute chd_status, PostOperation, Asynchronous.
using System.Net;
using System.Text.Json;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace ChdFunctions
{
    public class TicketWebhook
    {
        private readonly ILogger<TicketWebhook> _log;

        public TicketWebhook(ILogger<TicketWebhook> log) { _log = log; }

        [Function("TicketWebhook")]
        public async Task<HttpResponseData> Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = "ticket-webhook")] HttpRequestData req)
        {
            // Dataverse adds these headers to every webhook post.
            req.Headers.TryGetValues("x-ms-dynamics-request-name", out var messageHeader);
            req.Headers.TryGetValues("x-ms-correlation-request-id", out var correlation);
            _log.LogInformation("Webhook: message {Message}, correlation {Correlation}",
                messageHeader?.FirstOrDefault() ?? "(none)", correlation?.FirstOrDefault() ?? "(none)");

            JsonDocument doc;
            try { doc = await JsonDocument.ParseAsync(req.Body); }
            catch (JsonException)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await bad.WriteStringAsync("Body is not a JSON execution context.");
                return bad;
            }

            using (doc)
            {
                // The body is the RemoteExecutionContext serialized as JSON.
                var root = doc.RootElement;
                string message = Text(root, "MessageName");
                string table = Text(root, "PrimaryEntityName");
                string id = Text(root, "PrimaryEntityId");
                _log.LogInformation("{Message} of {Table} {Id}, depth {Depth}",
                    message, table, id, root.TryGetProperty("Depth", out var d) ? d.GetInt32() : 0);

                // InputParameters is a list of { key, value }. Target.Attributes is too.
                int closed = int.Parse(Environment.GetEnvironmentVariable("StatusClosedValue") ?? "100000002");
                foreach (var p in root.GetProperty("InputParameters").EnumerateArray())
                {
                    if (Text(p, "key") != "Target") continue;
                    foreach (var a in p.GetProperty("value").GetProperty("Attributes").EnumerateArray())
                    {
                        string name = Text(a, "key");
                        JsonElement v = a.GetProperty("value");
                        // Choice values arrive as { "__type": "OptionSetValue:...", "Value": 100000002 }
                        string shown = v.ValueKind == JsonValueKind.Object && v.TryGetProperty("Value", out var inner)
                            ? inner.ToString() : v.ToString();
                        _log.LogInformation("  changed {Column} = {Value}", name, shown);

                        if (name == "chd_status" && shown == closed.ToString())
                            _log.LogInformation("Ticket {Id} was closed: send the satisfaction survey link.", id);
                    }
                }
            }

            // Answer quickly with 200. Dataverse treats non-success codes as failures and
            // retries asynchronous steps, so do slow work elsewhere (for example a queue).
            var ok = req.CreateResponse(HttpStatusCode.OK);
            await ok.WriteStringAsync("received");
            return ok;
        }

        private static string Text(JsonElement e, string name) =>
            e.TryGetProperty(name, out var v) ? v.ToString() : string.Empty;
    }
}