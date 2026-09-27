// src/OpenTickets.tsx - STARTER
// After "pa app add data-source --connector dataverse --table chd_ticket", open src/generated/services
// and check the generated service name. The lesson calls it TicketService; the CLI names it after the
// table's entity set, for example Chd_ticketsService. Fix the import if yours differs.
import { useEffect, useState } from "react";
// TODO 1: import the generated Dataverse service for chd_ticket
// TODO 5: import Office365UsersService from "./generated/services/Office365UsersService"

type TicketRow = {
  chd_ticketid?: string;
  chd_title?: string;
  chd_priority?: number;
  chd_duedate?: string;
};

// Check the High value in your chd_priority choice (same value as in ticket.js).
const HIGH = 100000002;

export default function OpenTickets() {
  const [tickets, setTickets] = useState<TicketRow[]>([]);
  const [userName, setUserName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        // TODO 2: call the service's getAll with
        //   select:  chd_title, chd_priority, chd_duedate
        //   filter:  statecode eq 0   (active tickets only)
        //   orderBy: chd_duedate asc
        //   top:     50
        // TODO 3: store result.data (or an empty array) with setTickets
        // TODO 6: call Office365UsersService.MyProfile_V2 and store data.displayName with setUserName
      } catch (e) {
        setError(String(e));
      }
    };
    void load();
  }, []);

  if (error) {
    return <p role="alert">Could not load tickets: {error}</p>;
  }

  return (
    <section>
      <h1>Open tickets</h1>
      <p>{userName ? "Signed in as " + userName : "Loading user..."}</p>
      <p>{tickets.length + " open tickets"}</p>
      <ul>
        {/* TODO 4: render one <li> per ticket: title, due date (first 10 characters), and a "High" badge */}
      </ul>
    </section>
  );
}
