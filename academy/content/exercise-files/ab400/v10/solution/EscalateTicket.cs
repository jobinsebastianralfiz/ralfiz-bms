using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace ChdPlugins
{
    /// <summary>
    /// SOLUTION - lesson D.10. Main plug-in for the custom API chd_EscalateTicket
    /// (Binding type Entity on chd_ticket, Is function No).
    /// Link it through the custom API's Plugin Type column. Do not register a step.
    /// Request parameter: chd_Reason (String, required).
    /// Response property: chd_NewPriority (Integer).
    /// </summary>
    public class EscalateTicket : IPlugin
    {
        private const int PriorityHigh = 100000002; // your High choice value
        private const int StatusClosed = 100000002; // your Closed choice value
        private const int MaxReasonLength = 200;    // length of the chd_escalationreason column

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            var factory = (IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory));
            var service = factory.CreateOrganizationService(context.UserId);

            tracing.Trace("EscalateTicket called: message {0}", context.MessageName);

            // 1. Bound API: Target is a reference to the ticket row.
            var ticketRef = context.InputParameters.Contains("Target")
                ? context.InputParameters["Target"] as EntityReference
                : null;
            if (ticketRef == null || ticketRef.LogicalName != "chd_ticket")
                throw new InvalidPluginExecutionException("chd_EscalateTicket must be called on a ticket.");

            // 2. Validate the reason.
            var reason = context.InputParameters.Contains("chd_Reason")
                ? context.InputParameters["chd_Reason"] as string
                : null;
            if (string.IsNullOrWhiteSpace(reason))
                throw new InvalidPluginExecutionException("Please give a reason for escalation.");
            reason = reason.Trim();
            if (reason.Length > MaxReasonLength)
                reason = reason.Substring(0, MaxReasonLength);

            // 3. Closed tickets cannot be escalated (rule from the D.3 design spec).
            var current = service.Retrieve("chd_ticket", ticketRef.Id, new ColumnSet("chd_status"));
            if (current.GetAttributeValue<OptionSetValue>("chd_status")?.Value == StatusClosed)
                throw new InvalidPluginExecutionException("Closed tickets cannot be escalated.");

            // 4. Update the ticket as the calling user, so their security role applies.
            var update = new Entity("chd_ticket", ticketRef.Id);
            update["chd_priority"] = new OptionSetValue(PriorityHigh);
            update["chd_escalationreason"] = reason;
            service.Update(update);
            tracing.Trace("Ticket {0} escalated. Reason: {1}", ticketRef.Id, reason);

            // 5. Response property (Integer).
            context.OutputParameters["chd_NewPriority"] = PriorityHigh;
        }
    }
}