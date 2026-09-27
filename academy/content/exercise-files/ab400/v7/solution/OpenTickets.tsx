// src/OpenTickets.tsx - SOLUTION
// Service names come from src/generated/services; check yours and adjust the imports.
import { useEffect, useState } from "react";
import { Chd_ticketsService } from "./generated/services/Chd_ticketsService";
import { Office365UsersService } from "./generated/services/Office365UsersService";

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
        const result = await Chd_ticketsService.getAll({
          select: ["chd_title", "chd_priority", "chd_duedate"],
          filter: "statecode eq 0",
          orderBy: ["chd_duedate asc"],
          top: 50
        });
        setTickets((result.data ?? []) as TicketRow[]);

        const profile = await Office365UsersService.MyProfile_V2("displayName,userPrincipalName");
        setUserName(profile.data?.displayName ?? "");
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
        {tickets.map((t) => (
          <li key={t.chd_ticketid}>
            <strong>{t.chd_title}</strong>
            {" - due " + (t.chd_duedate ? t.chd_duedate.substring(0, 10) : "not set")}
            {t.chd_priority === HIGH ? <span className="badge-high"> High</span> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
