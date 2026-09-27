# Business problem: Campus Help Desk (Lesson 3.3)

Paste the section "Problem statement" into Plan designer. If your version lets you attach
documents, you can attach this file instead.

## Problem statement
Our college has three campuses (North, South and City) and about 3,000 students.
Students report IT problems (Wi-Fi, printing, passwords, laptops, classroom projectors)
by email, phone and walking up to the desk. Emails get lost and nobody knows which
problems are still open.

We want:
1. Students report IT problems from their phone or laptop, choosing a category and describing the problem.
2. Help desk staff see new problems, triage them by priority (Low, Medium, High) and assign them to an agent.
3. Students get an email update when their problem changes status (Open, In progress, Closed).
4. After a problem is closed, the student can rate the help from 1 to 5.
5. The help desk manager sees weekly statistics: tickets by category, by campus and average rating.

There are 6 help desk staff: 4 agents, 1 team lead and 1 manager.
Categories: Network, Hardware, Accounts, Software, Printing, Classroom AV.

## Review checklist
Tick each item after reading the generated plan.

**Roles**
- [ ] Student (reporter)
- [ ] Help desk agent (or staff)
- [ ] Help desk manager

**Requirements (user stories)**
- [ ] A story for reporting a problem
- [ ] A story for triage by priority
- [ ] A story for email status updates
- [ ] A story for weekly statistics or a report

**Data model**: compare with your tables from Lessons 2.2 and 2.5
| Plan table (write its name) | My table | Same? Notes |
|-----------------------------|----------|-------------|
| | Ticket | |
| | Category | |
| | Feedback | |

**Components**
- [ ] At least one app (canvas or model-driven)
- [ ] At least one flow (for example the status email)
- [ ] Anything else suggested (agent, report): ______

## Edit to try
Change requirement 3 to: "Students get a Teams message instead of an email when status changes."
Record which parts of the plan change: ______________________
