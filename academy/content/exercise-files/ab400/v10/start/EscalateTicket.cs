using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace ChdPlugins
{
    /// <summary>
    /// STARTER - lesson D.10. Main plug-in for the custom API chd_EscalateTicket
    /// (Binding type Entity on chd_ticket, Is function No).
    /// Link it through the custom API's Plugin Type column. Do not register a step.
    /// Compiles as it is; fill in the TODOs.
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

            // TODO 1: For a bound custom API, InputParameters["Target"] is an EntityReference
            //         to the ticket. Read it into a variable named ticketRef.

            // TODO 2: Read the request parameter "chd_Reason" (a string).
            //         If it is null or white space, throw
            //         new InvalidPluginExecutionException("Please give a reason for escalation.")
            //         If it is longer than MaxReasonLength, cut it to MaxReasonLength characters.

            // TODO 3: Retrieve the ticket with new ColumnSet("chd_status"). If its chd_status
            //         OptionSetValue equals StatusClosed, throw
            //         new InvalidPluginExecutionException("Closed tickets cannot be escalated.")

            // TODO 4: Build new Entity("chd_ticket", ticketRef.Id), set chd_priority to
            //         new OptionSetValue(PriorityHigh) and chd_escalationreason to the reason,
            //         then call service.Update. (Here Update is right: the custom API's main
            //         operation is not an Update of the ticket.)

            // TODO 5: Set the response property:
            //         context.OutputParameters["chd_NewPriority"] = PriorityHigh;
        }
    }
}