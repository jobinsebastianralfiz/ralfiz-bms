// Custom code for the Campus Directory API custom connector (lesson D.16).
// Paste this into the connector's Code page, turn code on, and apply it to the
// GetStaff and SearchStaff operations. The class must be named Script and inherit ScriptBase.
// It adds fullName = firstName + " " + lastName to every staff member the API returns.
public class Script : ScriptBase
{
    public override async Task<HttpResponseMessage> ExecuteAsync()
    {
        // Call the backend (the Azure Function) with the original request.
        HttpResponseMessage response = await this.Context.SendAsync(this.Context.Request, this.CancellationToken)
            .ConfigureAwait(false);

        // Only change successful responses of the two staff operations.
        if (!response.IsSuccessStatusCode) return response;
        if (this.Context.OperationId != "GetStaff" && this.Context.OperationId != "SearchStaff") return response;

        string content = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        JToken body = JToken.Parse(content);

        if (body is JObject single)
        {
            AddFullName(single);                       // GetStaff returns one object
        }
        else if (body is JArray list)
        {
            foreach (JObject item in list.OfType<JObject>())
                AddFullName(item);                     // SearchStaff returns an array
        }

        response.Content = CreateJsonContent(body.ToString());
        return response;
    }

    private static void AddFullName(JObject staff)
    {
        string first = (string)staff["firstName"] ?? string.Empty;
        string last = (string)staff["lastName"] ?? string.Empty;
        staff["fullName"] = (first + " " + last).Trim();
    }
}