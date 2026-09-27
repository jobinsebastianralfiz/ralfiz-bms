// chd_/scripts/ticket.js - Campus Help Desk Ticket form script (STARTER)
// Register CHD.Ticket.onLoad on the form OnLoad event and tick
// "Pass execution context as first parameter".
var CHD = window.CHD || {};

CHD.Ticket = {
  // Value of "High" in your chd_priority choice. Check it in the column's choice settings.
  HIGH: 100000002,
  NOTIFICATION_ID: "chd_high",

  onLoad: function (executionContext) {
    var formContext = executionContext.getFormContext();
    // TODO 1: register CHD.Ticket.onPriorityChange on the chd_priority column
    //         with formContext.getAttribute("chd_priority").addOnChange(...)

    // Run once on load so an existing High ticket shows the warning straight away.
    CHD.Ticket.onPriorityChange(executionContext);
  },

  onPriorityChange: function (executionContext) {
    var formContext = executionContext.getFormContext();
    var priority = formContext.getAttribute("chd_priority").getValue();
    var isHigh = priority === CHD.Ticket.HIGH;

    // TODO 2: make chd_duedate "required" when isHigh, otherwise "none"
    //         (setRequiredLevel on the attribute)

    if (!isHigh) {
      // TODO 3: clear the form notification with id CHD.Ticket.NOTIFICATION_ID
      return;
    }

    // TODO 4: show a WARNING form notification "High priority: set a Due date."
    //         with id CHD.Ticket.NOTIFICATION_ID

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

    // TODO 5: call Xrm.WebApi.retrieveMultipleRecords("chd_ticket", query)
    //         then open an alert dialog with Xrm.Navigation.openAlertDialog
    //         showing result.entities.length + " open tickets in " + category[0].name + "."
    //         Handle errors by logging error.message to the console.
  }
};
