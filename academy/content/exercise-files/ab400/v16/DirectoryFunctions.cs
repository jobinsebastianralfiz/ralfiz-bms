// Lesson D.16 - Campus Directory API: HTTP-triggered functions behind the custom connector.
// Add this file to the NightlySlaCheck project from lesson D.12 (same packages, same host).
// Every function uses AuthorizationLevel.Function, so callers send the function key in the
// x-functions-key header. The data is the 6 rows of staff.csv; Team is used as the department.
//   GET /api/staff?email=...              -> GetStaff
//   GET /api/departments                  -> ListDepartments
//   GET /api/staff/search?department=...  -> SearchStaff
using System.Net;
using System.Text.Json;
using System.Web;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace ChdFunctions
{
    public record StaffMember(string Email, string FirstName, string LastName,
                              string Role, string Campus, string Department);

    public record Department(string Code, string Name);

    public class DirectoryFunctions
    {
        // Same people as staff.csv (Name split into first and last name).
        private static readonly StaffMember[] Staff =
        {
            new("anu.sebastian@staff.example.edu", "Anu", "Sebastian", "Help desk agent", "North", "Infrastructure"),
            new("rahul.varma@staff.example.edu", "Rahul", "Varma", "Help desk agent", "South", "Infrastructure"),
            new("meera.iyer@staff.example.edu", "Meera", "Iyer", "Help desk agent", "City", "Identity"),
            new("joseph.mathew@staff.example.edu", "Joseph", "Mathew", "Help desk agent", "North", "Applications"),
            new("divya.nair@staff.example.edu", "Divya", "Nair", "Team lead", "City", "Infrastructure"),
            new("suresh.kumar@staff.example.edu", "Suresh", "Kumar", "Help desk manager", "City", "All"),
        };

        private readonly ILogger<DirectoryFunctions> _log;

        public DirectoryFunctions(ILogger<DirectoryFunctions> log) { _log = log; }

        [Function("GetStaff")]
        public async Task<HttpResponseData> GetStaff(
            [HttpTrigger(AuthorizationLevel.Function, "get", Route = "staff")] HttpRequestData req)
        {
            LogClient(req);
            string email = (Query(req, "email") ?? string.Empty).Trim();
            var match = Staff.FirstOrDefault(s => s.Email.Equals(email, StringComparison.OrdinalIgnoreCase));
            if (match == null)
            {
                return await Json(req, HttpStatusCode.NotFound, new { error = "No staff member with email " + email });
            }
            return await Json(req, HttpStatusCode.OK, match);
        }

        [Function("ListDepartments")]
        public async Task<HttpResponseData> ListDepartments(
            [HttpTrigger(AuthorizationLevel.Function, "get", Route = "departments")] HttpRequestData req)
        {
            LogClient(req);
            var list = Staff.Select(s => s.Department).Where(d => d != "All").Distinct()
                            .OrderBy(d => d).Select(d => new Department(d, d)).ToList();
            return await Json(req, HttpStatusCode.OK, list);
        }

        [Function("SearchStaff")]
        public async Task<HttpResponseData> SearchStaff(
            [HttpTrigger(AuthorizationLevel.Function, "get", Route = "staff/search")] HttpRequestData req)
        {
            LogClient(req);
            string department = Query(req, "department") ?? string.Empty;
            var list = Staff.Where(s => s.Department.Equals(department, StringComparison.OrdinalIgnoreCase)).ToList();
            return await Json(req, HttpStatusCode.OK, list);
        }

        // camelCase JSON: firstName, lastName ... (the names the OpenAPI definition uses).
        private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

        private static async Task<HttpResponseData> Json(HttpRequestData req, HttpStatusCode status, object body)
        {
            var res = req.CreateResponse(status);
            res.Headers.Add("Content-Type", "application/json; charset=utf-8");
            await res.WriteStringAsync(JsonSerializer.Serialize(body, JsonOptions));
            return res;
        }

        private static string? Query(HttpRequestData req, string name) =>
            HttpUtility.ParseQueryString(req.Url.Query)[name];

        // The connector policy adds x-client: campus-help-desk, so we can see who calls us.
        private void LogClient(HttpRequestData req)
        {
            string client = req.Headers.TryGetValues("x-client", out var v) ? v.First() : "(none)";
            _log.LogInformation("{Path} called by client {Client}", req.Url.AbsolutePath, client);
        }
    }
}