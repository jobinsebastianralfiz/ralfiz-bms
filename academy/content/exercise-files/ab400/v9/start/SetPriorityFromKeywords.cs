using System;
using System.Linq;
using Microsoft.Xrm.Sdk;

namespace ChdPlugins
{
    /// <summary>
    /// STARTER - lesson D.9. Compiles as it is, but does nothing yet.
    /// Rule: when a ticket's title or description contains an urgent keyword,
    /// set Priority to High before the row is saved.
    /// Steps: Create of chd_ticket (PreOperation, Synchronous) and
    ///        Update of chd_ticket (PreOperation, Synchronous,
    ///        filtering attributes chd_title,chd_description, pre-image "PreImage").
    /// </summary>
    public class SetPriorityFromKeywords : IPlugin
    {
        // Check the stored value of High in your chd_priority choice column.
        private const int PriorityHigh = 100000002;
        private const string PreImageName = "PreImage";

        // Keywords are compared in lower case.
        private static readonly string[] UrgentKeywords = { "outage", "exam", "fire", "cannot log in" };

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            tracing.Trace("SetPriorityFromKeywords: {0} of {1}, depth {2}",
                context.MessageName, context.PrimaryEntityName, context.Depth);

            // TODO 1: Return if InputParameters has no "Target", or Target is not an Entity
            //         with LogicalName "chd_ticket".

            // TODO 2: Read chd_title and chd_description from Target.
            //         On Update, Target only holds changed columns, so fall back to the
            //         pre-image: context.PreEntityImages[PreImageName] (check Contains first).

            // TODO 3: Build one lower-case string from title + " " + description and check
            //         whether it contains any value in UrgentKeywords (use UrgentKeywords.Any).

            // TODO 4: If it does, set Target["chd_priority"] = new OptionSetValue(PriorityHigh)
            //         and write a trace line naming the keyword. Do NOT call service.Update:
            //         in PreOperation, changing Target changes what is saved.
        }
    }
}