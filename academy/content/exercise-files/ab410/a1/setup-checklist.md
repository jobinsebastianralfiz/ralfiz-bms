# AB-410 setup checklist (Campus Help Desk)

Tick each line when it is done. Keep this file with your study notes.

## 1. Environments
- [ ] Power Apps Developer Plan activated with a work or school account
- [ ] Environment **CHD Dev** (type Developer, Dataverse database added)
- [ ] Environment **CHD Test** (type Developer, Dataverse database added)
- [ ] Environment URLs written down:
  - CHD Dev: https://________.crm.dynamics.com
  - CHD Test: https://________.crm.dynamics.com

## 2. Publisher and solution (in CHD Dev)
| Setting | Value |
|---|---|
| Publisher display name | Campus Help Desk |
| Publisher name | CampusHelpDesk |
| Prefix | chd |
| Choice value prefix | (generated, write it here) ______ |
| Solution display name | Campus Help Desk |
| Solution name | CampusHelpDesk |
| Version | 1.0.0.0 |
| Preferred solution | Yes |

## 3. Tables (create inside the solution if you are starting fresh)
**Category** (primary column Name)
| Column | Type |
|---|---|
| Name | Single line of text (primary) |
| Team | Single line of text |
| Description | Multiple lines of text |

**Ticket** (primary column Title)
| Column | Type | Values |
|---|---|---|
| Title | Single line of text (primary) | |
| Description | Multiple lines of text | |
| Ticket Number | Single line of text (becomes Autonumber in A.4) | CHD-1001 ... |
| Category | Lookup to Category | |
| Priority | Choice | Low, Medium, High |
| Status | Choice | Open, In progress, Closed |
| Campus | Choice | North, South, City |
| Student Email | Email | |
| Assigned To | Email | blank while Open |
| Created On (chd_createdondate) | Date only | |
| Due Date | Date only | |

Note: Dataverse already has a system column called Created On, so give your
imported date column a schema name such as chd_createdondate.

## 4. Data
- [ ] categories.csv imported first: 6 rows
- [ ] tickets.csv imported second: 28 rows (CHD-1001 to CHD-1028)

## 5. Deploy once
- [ ] Exported unmanaged: CampusHelpDesk_1_0_0_0.zip
- [ ] Exported managed: CampusHelpDesk_1_0_0_0_managed.zip
- [ ] Managed file imported into CHD Test and the model-driven app plays

## 6. AB-410 skill areas (copy the exact bullets from the study guide)
| Area | Weight | Lessons | Done |
|---|---|---|---|
| Foundation for intelligent applications | 25-30% | A.1 to A.8 | [ ] |
| Intelligent applications | 25-30% | A.9 onward | [ ] |
| Business logic and automation | 40-45% | flows, prompts, business rules, BPFs | [ ] |
