// chd_/scripts/ticket.js - Campus Help Desk Ticket form script (SOLUTION)
// Register CHD.Ticket.onLoad on the form OnLoad event and tick
// "Pass execution context as first parameter".
var CHD = window.CHD || {};

CHD.Ticket = {
  // Value of "High" in your chd_priority choice. Check it in the column's choice settings.
  HIGH: 100000002,
  NOTIFICATION_ID: "chd_high",

  onLoad: function (executionContext) {
    var formContext = executionContext.getFormContext();
    formContext.getAttribute("chd_priority").addOnChange(CHD.Ticket.onPriorityChange);

    // Run once on load so an existing High ticket shows the warning straight away.
    CHD.Ticket.onPriorityChange(executionContext);
  },

  onPriorityChange: function (executionContext) {
    var formContext = executionContext.getFormContext();
    var priority = formContext.getAttribute("chd_priority").getValue();
    var isHigh = priority === CHD.Ticket.HIGH;

    formContext.getAttribute("chd_duedate").setRequiredLevel(isHigh ? "required" : "none");

    if (!isHigh) {
      formContext.ui.clearFormNotification(CHD.Ticket.NOTIFICATION_ID);
      return;
    }

    formContext.ui.setFormNotification("High priority: set a Due date.", "WARNING", CHD.Ticket.NOTIFICATION_ID);
    CHD.Ticket.showOpenCount(formContext);
  },

  showOpenCount: function (formContext) {
    var category = formContext.getAttribute("chd_category").getValue();
    if (!category) {
      return;
    }
    // Lookups return an array of { id, name, entityType }. Remove the braces from the id.
    var categoryId = category[0].id.replace(/[{}]/g, "");
    var query = "?$select=chd_title&$filter=_chd_category_value eq " + categoryId + " and statecode eq 0";

    Xrm.WebApi.retrieveMultipleRecords("chd_ticket", query).then(
      function (result) {
        var count = result.entities.length;
        Xrm.Navigation.openAlertDialog({
          title: "Open tickets",
          text: count + " open tickets in " + category[0].name + "."
        });
      },
      function (error) {
        console.error("CHD.Ticket.showOpenCount failed: " + error.message);
      }
    );
  }
};
