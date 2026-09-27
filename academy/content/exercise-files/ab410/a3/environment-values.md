# Values per environment

## Environment variable
| Property | Value |
|---|---|
| Display name | Support Email |
| Schema name | chd_SupportEmail |
| Data type | Text |
| Default value | (leave empty) |

| Environment | Current value |
|---|---|
| CHD Dev | helpdesk-dev@staff.example.edu (or your own address) |
| CHD Test | helpdesk-test@staff.example.edu (or a second address you can read) |

Leave the default value empty so each environment must be given its own value
at import time (in the import wizard or in a deployment settings file).

## Connection references
| Display name | Connector | Used by |
|---|---|---|
| CHD Dataverse | Microsoft Dataverse | New ticket notification flow (trigger and actions) |
| CHD Outlook | Office 365 Outlook | New ticket notification flow (Send an email (V2)) |

## Flow change
Before: Send an email (V2) To = anu.sebastian@staff.example.edu (hard-coded)
After:  Send an email (V2) To = Support Email (environment variable from dynamic content)

## Test ticket to use after import into CHD Test
| Field | Value |
|---|---|
| Title | Deployment test: projector in Hall B |
| Description | Created in CHD Test to prove the flow uses the test Support Email value. |
| Category | Classroom AV |
| Priority | Medium |
| Campus | South |
| Student Email | hari.ali@students.example.edu |
