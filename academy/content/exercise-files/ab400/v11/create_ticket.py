"""Create and read Campus Help Desk tickets with the Dataverse SDK for Python (lesson D.11).

Setup:
    pip install PowerPlatform-Dataverse-Client azure-identity
    set DATAVERSE_URL=https://yourorg.crm.dynamics.com      (Windows)
    export DATAVERSE_URL=https://yourorg.crm.dynamics.com   (macOS / Linux)
Run:
    python create_ticket.py
A browser window opens so you can sign in (InteractiveBrowserCredential).
"""
import os
import sys

from azure.identity import InteractiveBrowserCredential
from PowerPlatform.Dataverse.client import DataverseClient
from PowerPlatform.Dataverse.models import col

# Choice values from the D.9 test cases. Check them in your Priority column.
PRIORITY = {"Low": 100000000, "Medium": 100000001, "High": 100000002}

NEW_TICKET = {
    "chd_title": "Projector broken in room 204",
    "chd_description": "The projector in room 204 turns on but shows a blue screen "
                       "with no input. Created from Python for lab D.11.",
    "chd_priority": PRIORITY["Medium"],
}


def main() -> int:
    url = os.environ.get("DATAVERSE_URL")
    if not url:
        print("Set the DATAVERSE_URL environment variable first.")
        return 1

    credential = InteractiveBrowserCredential()
    with DataverseClient(url, credential) as client:
        # 1. Create one ticket. create() returns the new row's ID.
        ticket_id = client.records.create("chd_ticket", NEW_TICKET)
        print("Created ticket", ticket_id)

        # 2. Read it back with only the columns we need.
        ticket = client.records.retrieve(
            "chd_ticket", ticket_id, select=["chd_title", "chd_priority"])
        print("Read back:", ticket["chd_title"], "| priority", ticket["chd_priority"])

        # 3. Query the High priority tickets (expected: 4 rows from tickets.csv).
        results = (client.query.builder("chd_ticket")
                   .select("chd_title", "chd_duedate")
                   .where(col("chd_priority") == PRIORITY["High"])
                   .order_by("chd_duedate")
                   .top(10)
                   .execute())
        rows = list(results)
        print("High priority tickets:", len(rows))
        for row in rows:
            print("  -", row["chd_title"])

        # 4. Clean up so later labs still start from the 28 tickets.
        answer = input("Delete the ticket created by this script? (y/n) ")
        if answer.strip().lower() == "y":
            client.records.delete("chd_ticket", ticket_id)
            print("Deleted", ticket_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())