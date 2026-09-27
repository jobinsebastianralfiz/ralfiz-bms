# Data policy spec: Help Desk DLP (Lesson 2.8)

## Policy settings

| Setting | Value |
|---|---|
| Name | Help Desk DLP |
| Scope | Add multiple environments: only your developer environment |

## Connector groups

| Connector | Group |
|---|---|
| Microsoft Dataverse | Business |
| Office 365 Outlook | Business |
| A social media connector (for example Facebook) | Blocked |
| Everything else | Leave in its default group (usually Non-business) |

Some Microsoft connectors cannot be blocked. If the Block action is greyed out, pick a different social connector.

Policies can take a few minutes to apply. Wait before testing.

## Tests

| # | Build this in Power Automate | Expected result |
|---|---|---|
| 1 | Instant flow (Manually trigger a flow) + an action from the blocked connector | The flow cannot be saved or turned on; the message says a data policy blocks the connector |
| 2 | Instant flow + Dataverse "List rows" (Business) + an RSS action (Non-business) | Blocked: Business and Non-business connectors cannot be used in the same flow |
| 3 | Instant flow + Dataverse "List rows" + Office 365 Outlook "Send an email (V2)" | Saves and runs: both connectors are Business |

Write down the exact error text from test 1: ______________________________

Delete the test flows afterwards.

## Accessibility checklist (use after Lesson 3.1)

Open your canvas app in Power Apps Studio and run App checker > Accessibility.

- [ ] Every input and button has an AccessibleLabel
- [ ] Text has enough colour contrast with its background
- [ ] Tab order moves top to bottom, left to right
- [ ] Images have a description, or are marked as decorative
- [ ] Number of accessibility issues before: ____ after: ____
