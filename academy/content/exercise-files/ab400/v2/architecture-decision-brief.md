# Architecture decision brief - Campus Help Desk release 2

Author: ____________   Date: ____________   Environment: ____________

## 1. Decisions
Allowed components: Business rule, Client script (JavaScript), Synchronous plug-in,
Asynchronous plug-in or Azure Function, Cloud flow, Copilot Studio agent.

| ID | Component | Runs where / when | Why this and not the next option | Deterministic? |
|---|---|---|---|---|
| R1 | | | | |
| R2 | | | | |
| R3 | | | | |
| R4 | | | | |
| R5 | | | | |
| R6 | | | | |
| R7 | | | | |
| R8 | | | | |

## 2. Out-of-the-box check
List every requirement a business rule alone can meet: ____________
List every requirement that needs code: ____________

## 3. Data decision
Campus Directory student data: standard table / virtual table / elastic table / connector?
Choice: ____________   Reason: ____________

## 4. Security findings
- Managed environment: ____
- Data policies: ____
- Row sharing test: I shared ticket CHD-____ with ____. Their access came from ____ (sharing) and not from ____ (role).

## 5. Three-layer diagram
Draw (or paste) a diagram with three layers and place every component from section 1:

    User experience :  staff model-driven app | student canvas app | agent chat
    Logic           :  ...
    Data            :  Dataverse (chd_ticket, Category) | Campus Directory API

## 6. Risks
One sentence per risk (performance, licensing, data policy, AI variability).
