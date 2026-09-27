# Security matrix: Help Desk Student (Lesson 2.7)

## Scenario

Students can report tickets and follow their own tickets.
They must not see other students' tickets and must not delete anything.
They need to see all categories to choose one.

## Role to create

Copy the Basic User role. Name the copy: Help Desk Student.
Leave the privileges Basic User already has on other tables as they are.

## Matrix to implement

Access levels: None, User, Business Unit, Parent: Child Business Units, Organization.

| Table | Create | Read | Write | Delete | Append | Append To | Assign | Share |
|---|---|---|---|---|---|---|---|---|
| Ticket | User | User | User | None | User | None | None | None |
| Category | None | Organization | None | None | None | Organization | None | None |

Why Append and Append To?
- Append on Ticket lets a student attach a ticket to another record (set the Category lookup).
- Append To on Category lets a ticket be attached to a category.
Without both, a student could create a ticket but not choose its category.

## Compare: Help Desk Agent (optional second role)

Agents from staff.csv (for example Anu Sebastian and Rahul Varma) work tickets for every student.

| Table | Create | Read | Write | Delete | Append | Append To | Assign | Share |
|---|---|---|---|---|---|---|---|---|
| Ticket | Organization | Organization | Organization | None | Organization | Organization | Organization | None |
| Category | None | Organization | None | None | None | Organization | None | None |

## Who gets which role

| Person (staff.csv or students.csv) | Role |
|---|---|
| Any student, e.g. aisha.nair@students.example.edu | Help Desk Student |
| Help desk agents (4 people in staff.csv) | Help Desk Agent |
| Suresh Kumar, Help desk manager | Help Desk Agent plus reporting access |

## Remember

Sharing an app does not give access to its data. A student also needs this role.
