using System;
using System.Linq;
using Microsoft.Xrm.Sdk;

namespace ChdPlugins
{
    /// <summary>
    /// SOLUTION - lesson D.9.
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

            // 1. Only work on a chd_ticket Target entity.
            if (!context.InputParameters.Contains("Target")) return;
            var target = context.InputParameters["Target"] as Entity;
            if (target == null || target.LogicalName != "chd_ticket") return;

            // Last-resort loop guard. This step changes Target and never calls Update,
            // so it should always run at depth 1 when a user saves a ticket.
            if (context.Depth > 2)
            {
                tracing.Trace("Depth {0} is too deep, skipping.", context.Depth);
                return;
            }

            // 2. Target holds only changed columns on Update: fall back to the pre-image.
            Entity pre = context.PreEntityImages.Contains(PreImageName)
                ? context.PreEntityImages[PreImageName]
                : null;

            string title = ReadText(target, pre, "chd_title");
            string description = ReadText(target, pre, "chd_description");

            // 3. Look for an urgent keyword.
            string text = (title + " " + description).ToLowerInvariant();
            string match = UrgentKeywords.FirstOrDefault(k => text.Contains(k));
            if (match == null)
            {
                tracing.Trace("No urgent keyword found. Priority unchanged.");
                return;
            }

            // 4. Change the value that will be saved. No service.Update call is needed.
            target["chd_priority"] = new OptionSetValue(PriorityHigh);
            tracing.Trace("Keyword '{0}' found. Priority set to High ({1}).", match, PriorityHigh);
        }

        private static string ReadText(Entity target, Entity pre, string column)
        {
            // A column the user cleared is in Target with a null value: respect that.
            if (target.Contains(column)) return target.GetAttributeValue<string>(column) ?? string.Empty;
            if (pre != null && pre.Contains(column)) return pre.GetAttributeValue<string>(column) ?? string.Empty;
            return string.Empty;
        }
    }
}