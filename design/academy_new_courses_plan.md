# Ralfiz Academy: new course plan and Claude prompts

Written 29 September 2026. Skills outlines were copied from Microsoft Learn study guides on that date.

PL-500 (Power Automate RPA Developer) and PL-600 retired on 30 June 2026 with no replacement, so they are not in this plan. Microsoft's business-apps certifications are now the AB series. The courses below fill the gaps next to what the Academy already has (PL-900, AB-410, PL-300, AB-400, Flutter, JavaScript, DOM).

---

## 1. Which courses to build, and in what order

| # | Course | Level | Lessons | Why build it | Lab needs |
|---|---|---|---|---|---|
| 1 | **AB-620** AI Agent Builder Associate (Copilot Studio) | Associate, developer | 19 | Closest to your existing Power Platform students; qualifies for AB-100 | Copilot Studio trial in a developer environment, Azure free account for Foundry parts |
| 2 | **AB-900** Microsoft 365 Copilot and Agent Administration Fundamentals | Fundamentals | 22 | Easy entry point like PL-900; big IT/admin audience | Microsoft 365 admin tenant (trial). Copilot licence optional: every lab has a no-licence path |
| 3 | **AB-730** AI Business Professional | Associate, no code | 16 | Widest audience: any student or office worker using Copilot | Microsoft 365 Copilot licence. Every lab has a no-licence path |
| 4 | **AB-100** Agentic AI Business Solutions Architect | Expert | 20 | Top of the path; needs one associate cert (AB-410, AB-620, PL-200, PL-400 and others) | Mostly design labs (documents, diagrams, decision tables) |
| 5 | AB-731 AI Transformation Leader (optional) | Associate, leaders | 13 | Corporate and management batches, not students | Design labs only |

Two learning paths come out of this:

- **Power Platform and agents:** PL-900 → AB-410 → AB-620 / AB-400 → AB-100
- **Microsoft 365 Copilot:** AB-900 → AB-730 (→ AB-731 for managers)

**Outlines are changing in October 2026.** AB-900 changes on 14 Oct, AB-100 on 14 Oct (both minor), and AB-730 on 20 Oct (major: a new agents and Copilot Cowork group). Build all three on the **new** outlines printed in section 5. AB-620's study guide gives no "as of" date and no practice assessment yet, so it is probably new or in beta. Check its page again before publishing.

---

## 2. How the content is produced

Work in a **Claude Project** (claude.ai → Projects), one project per course. Do the steps in order, and review each one before the next.

| Step | Prompt | Output | Size |
|---|---|---|---|
| 0 | Paste **Prompt A** into the project's instructions, and the course brief from section 5 as a project file | – | – |
| 1 | **Prompt B**: course blueprint | Module and lesson plan, lab plan, coverage matrix (markdown) | one reply |
| 2 | **Prompt C**: one module's lessons | `<course>-<module>.json` with full lessons | one module per chat turn (2–4 lessons) |
| 3 | **Prompt D**: exercise files | the lab files for one module | one module per turn |
| 4 | **Prompt E**: question bank | `questionBank` JSON, 60 questions | one reply |
| 5 | **Prompt F**: review | list of fixes, then corrected JSON | per module |
| 6 | Give the files to Claude Code in this repo | Claude Code assembles `academy/content/<id>.json`, adds the exercise files, runs `import_labs` and the tests | – |

**Why module by module:** a full lesson is about 1,000 words of HTML plus quiz and lab. Asking for a whole course in one reply makes it shallow. Two to four lessons per reply keeps the depth of the existing courses.

**Fact rule (the most important one):** every product fact must come from Microsoft Learn. Turn on web search in the project, and let the model mark anything it cannot confirm with `[VERIFY: …]`. Before import, you (or the review step) resolve every `[VERIFY]`. Never publish a UI click-path or a licence rule that was guessed.

---

## 3. The content format (what the importer accepts)

Claude Code builds the final file, but the model must produce these shapes exactly.

### Course (track)
```json
{
 "id": "ab620", "code": "AB-620", "name": "AI Agent Builder",
 "level": "Associate", "status": "Live", "outline": "31 Jul 2026", "order": "After AB-410",
 "blurb": "One or two sentences for the course card.",
 "facts": [["700", "score out of 1000 to pass"], ["3", "skill areas on the exam"], ["40–45%", "of the exam is integration"], ["Yearly", "free online renewal"]],
 "tool": "your developer environment",
 "guide": "https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-620",
 "note": "Based on Microsoft's AB-620 study guide. …",
 "data": ["hd/tickets.csv", "hd/categories.csv"],
 "domains": [ … ],
 "questionBank": [ … ]
}
```

### Module (domain)
```json
{"id": "g1", "name": "Plan and configure agent solutions", "weight": "30–35%", "blurb": "One sentence.", "lessons": [ … ]}
```
The first module is always `{"id": "g0", "name": "Start here", "weight": "Orientation", …}`.

### Lesson
```json
{
 "id": "g4", "num": "G.4", "title": "Agent flows: build, inputs and outputs", "minutes": 55,
 "summaryHtml": "<p>…</p><ul><li>…</li></ul>",
 "contentHtml": "<h3>In plain words</h3>…",
 "terms": [{"term": "Agent flow", "definition": "…"}],
 "examTip": "One or two sentences.",
 "widget": null, "sorter": null,
 "lab": {
  "files": ["ab620/g4/flow-spec.md", "hd/tickets.csv"],
  "steps": ["…", "…"],
  "check": ["…", "…"]
 },
 "quiz": [{"question": "…", "options": ["…", "…", "…", "…"], "answer": 1, "explanation": "…"}]
}
```

### Question bank item
```json
{"question": "…", "options": ["…","…","…","…"], "answer": 0, "explanation": "…", "lesson": "g4"}
```

### Exercise files
Each file has an id `<courseid>/<lessonid>/<filename>` (for example `ab620/g4/flow-spec.md`), text content, and a one-line description. The shared Campus Help Desk data (`hd/tickets.csv`, `hd/categories.csv`, `hd/students.csv`, `hd/staff.csv`, `hd/feedback.csv`) already exists and can be listed in `lab.files` without being recreated.

### HTML rules (the sanitizer removes anything else)
- Allowed tags: `h3 p ul ol li strong em code pre table thead tbody tr th td div br kbd`.
- Only these classes: `<pre class="code">`, `<div class="example">`, `<div class="callout">`, `<div class="callout warn">`.
- No links, images, inline styles, `h1`, `h2`, `h4`, scripts or iframes.

### House numbers (match the existing courses)
- `contentHtml`: 950–1,200 words.
- `quiz`: exactly 4 questions, 4 options, `answer` is 0–3.
- `lab.steps`: 7–9 steps. `lab.check`: 3–5 checks.
- `terms`: 4–6.
- `minutes`: 40–60.
- Lesson ids use one letter per course and are numbered through the whole course: `g1…g19` with `num` "G.1…G.19". Letters used so far: A (AB-410), B (PL-300), D (AB-400). New: **G** AB-620, **M** AB-900, **W** AB-730, **X** AB-100, **T** AB-731.

---

## 4. The prompts

Copy each prompt as it is. Replace the `{{…}}` parts.

### Prompt A: project instructions (paste once per course project)

```text
You are the lead author of Ralfiz Academy, an online academy in Kerala, India, that prepares
college students and early-career professionals for Microsoft certification exams. You are
writing the course {{COURSE CODE}} {{COURSE NAME}}. The course brief (exam outline, audience,
modules, lab scenario) is in the project file "course-brief.md". Treat the brief's skills
outline as the contract: every bullet in it must be taught somewhere, and nothing outside the
exam's scope should be taught as if it were examined.

AUDIENCE
- Indian college students and early-career makers. English is their second language.
- Many have never used an enterprise Microsoft tenant. Explain every term the first time.
- They learn best from one concrete running scenario, analogies from daily life, and doing.

ACCURACY (non-negotiable)
- Every product fact, limit, licence rule, role name, admin centre path and UI label must match
  current Microsoft Learn documentation. Use web search on learn.microsoft.com to confirm.
- If you cannot confirm something, keep the sentence but mark it [VERIFY: what to check].
  Never invent a click-path, a setting name, a price, a number or a limit.
- Say "at the time of writing (September 2026)" when you describe something that changes often,
  such as licensing or preview features. Mark preview features as "(preview)".
- Name products exactly as Microsoft does now (for example "Microsoft Foundry", "Microsoft
  Entra ID", "Microsoft Purview", "Copilot Studio").

WRITING STYLE
- Short sentences. Plain words. Active voice. Second person ("you").
- No marketing language ("powerful", "seamless", "revolutionary"). No emoji.
- Use numbers only when Microsoft documents them.
- The running scenario is Campus Help Desk (CHD) at Ralfiz Campus: students raise IT tickets,
  six help desk staff handle them. Reuse it in every lesson's Example section and lab.

LESSON STRUCTURE (contentHtml), always these h3 sections in this order:
1. <h3>In plain words</h3> - what it is, with one everyday analogy (2-3 paragraphs).
2. <h3>Why it matters</h3> - the real problem it solves, and why the exam cares.
3. <h3>How it works</h3> - the core, in depth. Use <p><strong>1. Name.</strong> …</p> numbered
   sub-points, a comparison <table> wherever the exam asks you to choose between options, and
   <pre class="code"> for any code, Power Fx, JSON, PowerShell or KQL (only real, valid syntax).
4. <h3>Example: Campus Help Desk</h3> - the concept applied step by step to CHD.
5. <h3>Common mistakes</h3> - 4-6 bullets, each "mistake, then why it is wrong".
6. <h3>How the exam asks about it</h3> - the question patterns, the distractors, and the rule
   that picks the right answer.
Use <div class="callout"> for a key rule and <div class="callout warn"> for a trap.

HTML: only h3 p ul ol li strong em code pre table thead tbody tr th td div br kbd. Only the
classes code, example, callout, callout warn. No links, images, styles, h1, h2, h4.

QUIZ QUESTIONS (lesson quiz and question bank)
- Scenario-based, like the real exam: a short CHD situation, then "What should you do?" or
  "Which should you use?".
- Exactly 4 options of similar length. One correct. Distractors are real products or settings
  that are wrong for a specific, teachable reason.
- No "all of the above", "none of the above", or trick wording.
- The explanation says why the answer is right AND why the tempting distractor is wrong.
- Spread the correct answer across positions 0-3.

LABS
- A lab is 7-9 concrete steps a student can follow alone in 40-60 minutes, ending in something
  visible they can check, plus 3-5 "check" lines that describe the result they should see.
- Every lab must work with free or trial access. If a step needs a paid licence (for example a
  Microsoft 365 Copilot licence), give a "No licence?" alternative step that practises the same
  decision with the provided files (a decision table, a policy design, a prompt review).
- Exercise files are small text files: .md briefs and templates, .csv data, .json, .yaml,
  .txt, .ps1. Reference them by id "{{courseid}}/<lessonid>/<file>".

OUTPUT FORMAT
- When asked for JSON, output only valid JSON (UTF-8, double quotes, no comments, no trailing
  commas), in one ```json block, in the exact shapes given in the request.
```

### Prompt B: course blueprint (first message in the project)

```text
Using course-brief.md, plan the full course before writing any lesson.

Give me, in markdown:
1. A module and lesson table: module id, module name (the exam's functional group), weight,
   then each lesson with id, num, title (at most 60 characters), minutes, and the exact
   skills-outline bullets it covers. Start with module "{{letter}}0 Start here" (1-2 lessons:
   what the exam tests and how to set up the lab environment). Keep the lesson count within
   the brief's target, and give more lessons to the higher-weight groups.
2. A coverage matrix: every bullet of the skills outline, verbatim, and the lesson that teaches
   it. No bullet may be missing.
3. The lab plan: for each lesson, the lab's goal, the exercise files it needs (ids and one-line
   descriptions), what the student ends up with, and whether it needs a paid licence (and the
   no-licence alternative).
4. The course card: blurb (at most 200 characters), four facts, and the note.
5. A list of every fact you still need to verify, with the Microsoft Learn page to check.

Do not write lessons yet.
```

### Prompt C: write one module's lessons (repeat per module)

```text
Write module {{module id}} "{{module name}}": lessons {{list the lesson ids from the blueprint}}.

For each lesson produce one lesson object in the exact shape below, following the project
instructions (section order, HTML rules, accuracy, quiz and lab rules):

{"id","num","title","minutes","summaryHtml","contentHtml","terms","examTip","widget":null,
 "sorter":null,"lab":{"files","steps","check"},"quiz"}

- summaryHtml: 2 short paragraphs or a paragraph and a 3-4 item list. It is what the student
  sees first, so it must say what they will be able to do after the lesson.
- contentHtml: 950-1,200 words. Go deep in "How it works": show the real settings, the order
  things happen in, the options and when to pick each (use a comparison table).
- terms: 4-6 exam words with one-sentence definitions.
- examTip: the single most useful rule for exam questions on this topic.
- lab: exactly as planned in the blueprint. Steps are imperative sentences with the exact UI
  names (verified). Checks describe the visible result.
- quiz: exactly 4 scenario questions.

Return one ```json block containing {"id": "{{module id}}", "name": "…", "weight": "…",
"blurb": "…", "lessons": [ … ]}. After the JSON, list any [VERIFY] items you left in the text.
```

### Prompt D: exercise files (repeat per module)

```text
Write every exercise file listed in the labs of module {{module id}}.

Return one ```json block: an array of {"id": "{{courseid}}/<lessonid>/<file>", "description":
"one line", "text": "the full file content"}.

- Briefs (.md): a realistic Campus Help Desk request, with numbered requirements R1, R2, … that
  the lab steps refer to.
- Templates (.md): tables with empty cells for the student to fill, and one worked row.
- Data (.csv/.json): 10-60 rows of consistent, realistic CHD data (Indian names, campuses
  Kochi, Kozhikode and Thrissur, ticket ids CHD-xxxx). Keep ids consistent with the shared hd/
  files.
- Scripts (.ps1, .kql, .yaml, .json definitions): valid syntax only, with comments explaining
  each block. Mark any cmdlet or schema you could not verify with # VERIFY.
- Include a solution file where the lab has a single correct answer (for example
  decision-table-solution.md).
```

### Prompt E: question bank (once, after all modules)

```text
Write the course question bank: 60 exam-style questions spread across the modules in
proportion to the exam weights in course-brief.md. They must be NEW questions, not copies of
the lesson quizzes.

- Each: {"question","options","answer","explanation","lesson"} where lesson is the id of the
  lesson that teaches it.
- Mix: 60% scenario ("You need to…, what should you do?"), 25% "which tool/setting/role",
  15% "put in order" written as 4 options of different orders.
- Correct answers spread evenly across positions 0-3.
- Make 10 of them hard: two plausible answers where only a detail in the scenario decides.

Return one ```json block with the array only.
```

### Prompt F: review (per module, in a NEW chat so it reviews with fresh eyes)

```text
You are a Microsoft certification subject-matter expert reviewing a lesson module for
{{COURSE CODE}} before publication. The skills outline is in course-brief.md. The module JSON is
attached.

Check and report, lesson by lesson:
1. Accuracy: every fact, UI name, role, licence rule and limit against current Microsoft Learn
   (search it). Quote the wrong sentence and give the correction with the source page.
2. Coverage: which outline bullets this module should cover are thin or missing.
3. Exam fit: quiz answers that are wrong or arguable, distractors that are accidentally correct,
   answer positions that are not spread.
4. Labs: steps a beginner cannot follow alone, steps that need a licence without a no-licence
   path, checks that do not match the steps.
5. Format: HTML outside the allowed tags, word count outside 950-1,200, missing sections,
   quiz or term counts wrong, any [VERIFY] left.

Then return the corrected module as one ```json block in the same shape.
```

### Prompt G (later): video scripts

After a course is imported, Claude Code writes its lesson video scripts with the existing pipeline in `ralfiz-academy-video` (see its `SCRIPTS.md`). No prompt is needed here.

---

## 5. Course briefs (save each as "course-brief.md" in its project)

### 5.1 AB-620: AI Agent Builder Associate

```text
COURSE: AB-620 - AI Agent Builder (Microsoft Certified: AI Agent Builder Associate)
Exam title on the study guide: "Designing and Building Integrated AI Solutions in Copilot Studio"
Course id: ab620   Lesson letter: G   Target: 19 lessons in 4 modules (g0 + 3)
Level: Associate (developer).   Order: After AB-410.   Pass mark: 700.   Exam length: 120 min.
Study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-620
Status note: the study guide gives no "skills measured as of" date and no practice assessment
yet (checked 29 Sep 2026). Check the page again before publishing.

AUDIENCE (Microsoft): a professional developer or advanced builder who builds, extends and
integrates custom agents for enterprise solutions. Familiar with Power Fx, Dataverse, Power
Platform environments, Microsoft 365 Copilot, Microsoft Foundry and adaptive cards.
Intermediate generative AI: models, orchestration, RAG, MCP, A2A. Prompt engineering, REST
APIs and integration patterns. Already configures agents with knowledge, instructions, tools
and topics in Copilot Studio.
RALFIZ STUDENTS: have done PL-900 and usually AB-410. Lesson G.1 must recap Copilot Studio
basics (agent, instructions, knowledge, topics, tools) in one lesson.

LAB SCENARIO: the Campus Help Desk agent. Across the course students build "CHD Assistant" in
Copilot Studio: it answers IT questions from knowledge, creates and looks up tickets in the
CHD Dataverse tables through agent flows and connectors, calls a REST API, uses an MCP tool,
hands off to a Foundry agent, is tested with a test set and moved through a pipeline.
LAB ACCESS: Copilot Studio trial in a Power Platform developer environment; Azure free account
for Foundry, AI Search and Application Insights labs (mark the few steps that may cost money).

SKILLS MEASURED
Plan and configure agent solutions (30-35%)
 Plan an agent solution
  - Plan integration with enterprise systems
  - Plan identity strategy
  - Plan channels and deployment
  - Plan responsible AI strategy
  - Evaluate security and governance considerations
  - Plan reusable agent components
  - Design agents for internal or external audiences
 Create and monitor agent flows in Copilot Studio
  - Create an agent flow
  - Create a human-in-the-loop agent flow
  - Configure actions and connectors
  - Monitor agent flows
  - Add input and output parameters
  - Implement error handling in agent flows
 Configure topics
  - Add agent flows to a topic
  - Configure agent response formatting
  - Add tools to a topic
  - Configure advanced agent responses with custom prompts
  - Configure advanced agent responses with custom knowledge sources
  - Configure advanced agent responses with API and Send HTTP requests
  - Configure generative answers node
  - Configure adaptive cards
  - Manage variables
Integrate and extend agents in Copilot Studio (40-45%)
 Connect to enterprise knowledge sources
  - Connect to Copilot connectors
  - Connect to Microsoft Power Platform connectors
  - Connect to Azure AI Search
 Add tools to agents
  - Configure and monitor computer use for an agent
  - Configure MCP tools
  - Add a tool by using an existing custom connector
  - Add REST APIs to an agent
 Configure multi-agent collaboration from Copilot Studio
  - Design multi-agent solutions in Copilot Studio
  - Integrate a Foundry agent
  - Integrate an existing agent in Copilot Studio
  - Integrate a Fabric data agent
  - Create a multi-agent solution by using A2A protocol
 Integrate agents with Azure
  - Configure generative answers by using Azure AI Search with Foundry
  - Configure custom prompts to use the Foundry model catalog
  - Monitor agents by using Application Insights
Test and manage agents (20-25%)
 Evaluate agent performance
  - Create a test set
  - Choose an evaluation method
  - Review test results
 Implement application lifecycle management (ALM) for agents in Copilot Studio
  - Create a solution
  - Add existing agents to a solution
  - Create and use environment variables
  - Implement and extend Microsoft Power Platform Pipelines

SUGGESTED MODULES (the blueprint may adjust titles)
g0 Start here: G.1 What AB-620 tests, and a Copilot Studio refresher
g1 Plan and configure (30-35%): G.2 Planning an agent: systems, identity, channels ·
   G.3 Responsible AI, security, governance and reusable parts · G.4 Agent flows: build,
   inputs and outputs · G.5 Human in the loop, errors and monitoring · G.6 Topics: variables,
   formatting and adaptive cards · G.7 Generative answers, custom prompts and knowledge ·
   G.8 Calling APIs with HTTP requests
g2 Integrate and extend (40-45%): G.9 Enterprise knowledge with connectors · G.10 Azure AI
   Search and Foundry for answers · G.11 Tools from custom connectors and REST APIs ·
   G.12 MCP tools · G.13 Computer use · G.14 Designing multi-agent solutions ·
   G.15 Foundry agents, Fabric data agents and A2A · G.16 Foundry model catalog and
   Application Insights
g3 Test and manage (20-25%): G.17 Evaluating agents with test sets · G.18 Solutions and
   environment variables · G.19 Pipelines and extending them
```

### 5.2 AB-900: Microsoft 365 Copilot and Agent Administration Fundamentals

```text
COURSE: AB-900 - Microsoft 365 Copilot and Agent Administration Fundamentals
Course id: ab900   Lesson letter: M   Target: 22 lessons in 4 modules (m0 + 3)
Level: Fundamentals.   Order: Start here for Microsoft 365.   Pass mark: 700.
Study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-900
Build on the outline "as of October 14, 2026" below (the change from the previous outline is
minor, in the core security features group).

AUDIENCE (Microsoft): familiar with Microsoft 365 core services, security, identity and access,
data protection and governance, Microsoft 365 Copilot and agents, and the admin centres
(Exchange Online, SharePoint, Teams, Microsoft Entra, Microsoft Purview). Can identify core
objects (users, groups, teams, sites, libraries) and core security features (authentication
methods, conditional access, SSO).
RALFIZ STUDENTS: beginners with no admin experience. Explain every admin object from zero.

LAB SCENARIO: Ralfiz Campus has a Microsoft 365 tenant. The same Campus Help Desk staff and
students (shared hd/ files) are the users. Students act as the new IT admin: set up users and
licences, a help desk team and site, protect ticket data with labels and DLP, then roll out
Copilot and a help desk agent safely.
LAB ACCESS: a Microsoft 365 trial tenant [VERIFY which trial and developer options are
available in September 2026 and whether Copilot can be trialled]. Every step that needs a
Copilot licence or Purview premium features must have a "No licence?" path using the exercise
files (policy design tables, reading a sample report, decision tables).

SKILLS MEASURED (as of October 14, 2026)
Identify the core features and objects of Microsoft 365 services (30-35%)
 Identify the core objects of Microsoft 365 services
  - Explain how license types assigned to users and groups affect access to Microsoft 365 features
  - Explore the organization configurations by using the Microsoft 365 admin center (domain names and org settings)
  - Identify the appropriate objects to configure by using the Exchange admin center (mailboxes and distribution groups)
  - Identify the appropriate objects to configure by using the SharePoint admin center (sites, libraries, and folders)
  - Identify the appropriate roles and permissions for sites in SharePoint in Microsoft 365
  - Identify the appropriate objects to configure by using the Teams admin center (teams, channels, and policies)
 Understand the Microsoft 365 security principles
  - Explain the core Zero Trust principles
  - Understand authorization
  - Understand authentication methods
  - Understand threat protection and intelligence
  - Understand features and capabilities of Microsoft Defender XDR
 Identify the core security features of Microsoft 365 services
  - Understand features and capabilities of Microsoft Entra ID
  - Understand conditional access policies
  - Understand the purpose and benefits of SSO
  - Identify the appropriate security object to use in an organization (users and groups)
  - Identify the appropriate tools to troubleshoot common sign-in issues (MFA, conditional access, and risky sign-ins)
  - Interpret Identity Secure Score in Microsoft Entra ID
  - Use the appropriate tools to review audit logs for user and admin activity
  - Identify the role of Privileged Identity Management (PIM) in an organization
  - Understand App registrations and Enterprise applications
Understand data protection and governance tasks for Microsoft 365 and Copilot (35-40%)
 Understand Microsoft Purview
  - Understand features and capabilities of Microsoft Purview Information Protection, Microsoft Purview Data Loss Prevention (DLP), Microsoft Purview Insider Risk Management, Microsoft Purview Communication Compliance, Microsoft Purview Data Security Posture Management (DSPM) for AI, and Microsoft Purview Data Lifecycle Management
  - Identify the use cases for sensitivity labels in Microsoft Purview
  - Understand data classification in Microsoft Purview
  - Understand retention
 Understand data security implications of Copilot
  - Understand how Copilot accesses data
  - Understand how Microsoft Graph influences Copilot responses
  - Understand how Copilot uses permissions and other controls in Microsoft 365, Microsoft Purview, and Microsoft Defender to protect against risks
  - Understand responsible AI principles
 Identify data protection and governance risks for Microsoft 365 and Copilot
  - Identify compliance risks and recommendations by using Microsoft Purview Compliance Manager
  - Identify sensitive information by using Microsoft Purview Data Explorer
  - Identify risks by using Insider Risk Management
  - Identify and respond to alerts generated by Microsoft Purview DLP
  - Identify policy violations generated by Communication Compliance
  - Identify user activities reported by Microsoft Purview activity explorer
  - Discover and manage AI activity by using DSPM for AI
  - Search for files and emails by using Content search in Microsoft Purview eDiscovery
 Identify and monitor oversharing in SharePoint in Microsoft 365
  - Identify the tools to troubleshoot oversharing in an organization
  - Run a data access governance report in SharePoint
  - Understand features and capabilities of SharePoint Advanced Management, including restricted access control
Perform basic administrative tasks for Copilot and agents (25-30%)
 Understand features and capabilities of Copilot and agents
  - Compare the built-in capabilities of Copilot and agents
  - Compare Copilot monthly license model to pay-as-you-go, including SharePoint
  - Identify which Copilot features can be enabled or disabled
  - Identify use cases for Researcher
  - Identify use cases for Analyst
  - Identify use cases for custom agents
 Perform basic administrative tasks for Copilot
  - Assign Copilot licenses
  - Monitor and manage Copilot pay-as-you-go billing policies
  - Monitor Copilot usage and adoption, including Copilot Analytics and the Microsoft 365 admin center
  - Manage prompts, including saving, sharing, scheduling, and deleting
 Perform basic administrative tasks for agents
  - Identify how to configure user access to agents
  - Create an agent
  - Understand approval process for agents
  - Monitor agents, including usage, operational insights, and agent lifecycle, by working with the Microsoft 365 admin center and the Microsoft Power Platform admin center

SUGGESTED MODULES
m0 Start here: M.1 What AB-900 tests and your practice tenant · M.2 Microsoft 365 and Copilot:
   the big picture
m1 Core features and objects (30-35%): M.3 Licences for users and groups · M.4 The Microsoft
   365 admin center: domains and org settings · M.5 Exchange: mailboxes and distribution
   groups · M.6 SharePoint: sites, libraries and permissions · M.7 Teams: teams, channels and
   policies · M.8 Zero Trust, authentication and authorization · M.9 Threat protection and
   Defender XDR · M.10 Entra ID: users, groups, conditional access and SSO · M.11 Sign-in
   troubleshooting, Secure Score and audit logs · M.12 PIM, app registrations and enterprise
   apps
m2 Data protection and governance (35-40%): M.13 Microsoft Purview at a glance ·
   M.14 Sensitivity labels, classification and retention · M.15 How Copilot reaches your data ·
   M.16 Finding risk: Compliance Manager, Data Explorer, activity explorer · M.17 DLP alerts,
   insider risk and communication compliance · M.18 DSPM for AI and eDiscovery content search ·
   M.19 Oversharing in SharePoint
m3 Copilot and agents administration (25-30%): M.20 Copilot and agents: capabilities and
   licensing · M.21 Copilot admin: licences, billing, usage and prompts · M.22 Agent admin:
   access, creation, approval and monitoring
```

### 5.3 AB-730: AI Business Professional

```text
COURSE: AB-730 - AI Business Professional
Course id: ab730   Lesson letter: W   Target: 16 lessons in 5 modules (w0 + 4)
Level: Associate (no code).   Order: After AB-900 (optional).   Pass mark: 700.
Study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-730
Build on the outline "as of October 20, 2026" below. It changed a lot from the previous one:
a new group "Drive business outcomes by using agents" (prebuilt agents and Microsoft Copilot
Cowork), and "Create and manage Microsoft 365 Copilot agents" was removed. Do not teach
agent building as an exam topic.

AUDIENCE (Microsoft): uses generative AI productivity tools, including Microsoft 365 Copilot,
Copilot Cowork and prebuilt agents, and uses AI and Work IQ to improve daily work and make
decisions, without building AI apps or writing code. Knows prompt engineering, context
engineering and large language models, and Copilot notebooks and pages. Comfortable with
Outlook, Word, Teams, PowerPoint and Excel.
RALFIZ STUDENTS: final-year students and office staff. No technical background assumed.

LAB SCENARIO: the Campus Help Desk manager's week: drafting an update email, analysing ticket
data in Excel, a monthly review deck in PowerPoint, preparing and recapping a team meeting,
a shared Copilot Page for the escalation process, and delegating a multi-step task to Copilot
Cowork.
LAB ACCESS: Microsoft 365 Copilot licence. Every lab also has a "No licence?" path: the same
task with the free Copilot Chat [VERIFY what is available without a licence in Sept 2026], or
a prompt-writing and output-review exercise using provided sample outputs.

SKILLS MEASURED (as of October 20, 2026)
Understand generative AI fundamentals (25-30%)
 Understand generative AI capabilities across Microsoft 365 experiences
  - Understand how Copilot works to keep your organization's information private and secure
  - Understand how the context, like Work IQ, web data, or the app you're using, can affect Copilot responses
  - Understand when to use Microsoft 365 Copilot Chat, agents, and Microsoft Copilot Cowork
  - Understand the differences in features and capabilities across Copilot experiences and Microsoft 365 apps
 Identify responsible AI and data protection practices
  - Identify common risks, including inaccuracies, prompt injection, and over-reliance
  - Select verification steps appropriate to the task, including citation checks and human review
  - Recognize and mitigate risks to sensitive data
  - Understand how data protection restricts prompt results
Manage prompts and chats by using Microsoft 365 Copilot (20-25%)
 Create and manage prompts in Microsoft 365 Copilot
  - Understand how to create an effective prompt, including model selection
  - Select appropriate resources to reference in a prompt
  - Save a prompt
  - Schedule a prompt
  - Share a prompt
  - Refine prompts based on generated responses
  - Describe how Copilot uses memory and instructions
 Manage chats in Microsoft 365 Copilot
  - Find a previous chat
  - Delete a chat
  - Rename a chat
  - Organize and share information by using Notebooks
Manage business content and collaboration by using Microsoft 365 Copilot (20-25%)
 Draft and analyze business content by using Microsoft 365 Copilot
  - Connect to sources beyond Microsoft 365 Copilot by using connectors
  - Generate or analyze content based on specific business context, including Work IQ and connectors
  - Generate images, visuals, and charts to support business content
  - Generate or analyze content across multiple Microsoft 365 applications such as Microsoft Word, Microsoft Excel, and Microsoft PowerPoint
  - Derive insights across Work IQ
  - Interpret and validate that AI-generated content meets business goals
 Manage meetings and collaboration by using Microsoft 365 Copilot
  - Prepare for a meeting
  - Use the Facilitator agent
  - Use real-time catchup
  - Use Intelligent recap
  - Collaborate on business content by using Copilot Pages
Drive business outcomes by using agents (20-25%)
 Select and apply prebuilt Microsoft 365 Copilot agents
  - Identify scenarios where a prebuilt agent can improve a business workflow
  - Choose between using a prebuilt agent or creating a custom agent for a business task
  - Apply an agent to a business process from within various Microsoft 365 Copilot experiences
  - Filter chats by agents
 Perform business tasks by using Microsoft Copilot Cowork
  - Describe how Microsoft Copilot Cowork helps carry out multi-step business tasks
  - Understand how Cowork uses skills to complete parts of a task
  - Recognize security considerations and known limitations when using Cowork
  - Choose between prebuilt skills and custom skills
  - Delegate a piece of work to Cowork and a prebuilt skill
  - Review Cowork's plan, progress, and results
  - Manage scheduled tasks or prompts

SUGGESTED MODULES
w0 Start here: W.1 What AB-730 tests and your Copilot setup
w1 Generative AI fundamentals (25-30%): W.2 How generative AI works: models, prompts and
   context · W.3 Copilot experiences, Work IQ and privacy · W.4 Responsible AI: risks and
   verification
w2 Prompts and chats (20-25%): W.5 Writing effective prompts and choosing a model ·
   W.6 References, refinement, memory and instructions · W.7 Saving, scheduling and sharing
   prompts; chats and Notebooks
w3 Content and collaboration (20-25%): W.8 Connectors, Work IQ and business context ·
   W.9 Word, Excel and PowerPoint with Copilot · W.10 Images, charts and validating AI content ·
   W.11 Meetings: prepare, Facilitator, catch-up and recap · W.12 Copilot Pages
w4 Agents and Cowork (20-25%): W.13 Prebuilt agents: when and which · W.14 Using agents
   across Copilot experiences · W.15 Copilot Cowork: skills and delegation · W.16 Reviewing
   Cowork results and scheduled tasks
```

### 5.4 AB-100: Agentic AI Business Solutions Architect

```text
COURSE: AB-100 - Agentic AI Business Solutions Architect
(Microsoft Certified: Agentic AI Business Solutions Architect Expert)
Course id: ab100   Lesson letter: X   Target: 20 lessons in 4 modules (x0 + 3)
Level: Expert.   Order: After AB-410 or AB-620.   Pass mark: 700.
Study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-100
Prerequisite for the certification (not the exam): at least one associate certification from
Microsoft's list, which includes AB-410, AB-620, PL-200, PL-400, AI-103, MB-280, MB-230,
MB-310, MB-330, MB-500, MB-800, MB-820, AI-300, AB-210 and AB-250.
Build on the outline "as of October 14, 2026" below (minor change).

AUDIENCE (Microsoft): an accomplished solution architect who designs and delivers AI-driven
business solutions across Dynamics 365, Power Platform, Copilot Studio, Microsoft Foundry and
Foundry Models; designs agentic-first and multi-agent solutions; works with A2A and MCP;
applies the Microsoft Responsible AI Standard; secures models and data; monitors agents with
telemetry; and runs ROI analysis.
RALFIZ STUDENTS: finished AB-410 or AB-620, often working professionals. Dynamics 365 is new to
most: give a short "what this app is" box the first time each Dynamics 365 app appears.

LAB SCENARIO: an architecture engagement. Ralfiz Campus wants an agentic IT service: the CHD
agent, a triage autonomous agent, a knowledge agent in Microsoft 365 Copilot, and service
reporting. Students produce architecture artefacts: requirement analysis, agent inventory,
multi-agent diagram (described in text), build-buy-extend decision table, ROI sheet, test
strategy, ALM plan, security and responsible AI review.
LAB ACCESS: mostly design labs with templates. Optional hands-on steps in Copilot Studio and
Foundry, marked "optional, may need a trial".

SKILLS MEASURED (as of October 14, 2026)
Plan AI-powered business solutions (25-30%)
 Analyze requirements for AI-powered business solutions
  - Assess the use of agents in task automation, data analytics, and decision-making
  - Review data for grounding, including accuracy, relevance, timeliness, cleanliness, and availability
  - Organize business solution data to be available for other AI systems
 Design overall AI strategy for business solutions
  - Implement the AI adoption process from the Cloud Adoption Framework for Azure
  - Design the strategy for building AI and agents in business solutions
  - Design a multi-agent solution by using platforms such as Microsoft 365 Copilot, Copilot Studio, and Microsoft Foundry
  - Develop the use cases for prebuilt agents in the solution
  - Define the solution rules and constraints when building AI components with Copilot Studio, Microsoft Foundry and Microsoft Foundry Tools
  - Determine the use of generative AI and knowledge sources in agents built with Copilot Studio
  - Determine when to build custom agents or extend Microsoft 365 Copilot
  - Determine when custom AI models should be created
  - Provide guidelines for creating a prompt library
  - Develop the use cases for customized small language models for the solution
  - Provide prompt engineering guidelines and techniques for AI-powered business solutions
  - Include the elements of the Microsoft AI Center of Excellence
  - Design AI solutions that use multiple Dynamics 365 apps
 Evaluate the costs and benefits of an AI-powered business solution
  - Select ROI criteria for AI-powered business solutions, including the total cost of ownership
  - Create an ROI analysis for the proposed AI solution for a business process
  - Analyze whether to build, buy, or extend AI components for business solutions
  - Implement a model router to intelligently route requests to the most suitable model
Design AI-powered business solutions (25-30%)
 Design AI and agents for business solutions
  - Design business terms for Copilot in Dynamics 365 apps for customer experience and service
  - Design customizations of Copilot in Dynamics 365 apps for customer experience and service
  - Design connectors for Copilot in Dynamics 365 Sales
  - Design agents for integration with Dynamics 365 Contact Center channels
  - Design task agents
  - Design autonomous agents
  - Design prompt and response agents
  - Propose Microsoft Foundry Tools for a given requirement
  - Propose code-first generative pages and the use of an agent feed for apps
  - Design topics for Copilot Studio, including fallback
  - Design data processing for AI models and grounding
  - Design a business process to include AI components in a Power Apps canvas app
  - Apply the Microsoft Power Platform Well-Architected Framework to intelligent application workloads
  - Determine when to use standard natural language processing, conversational language understanding, or generative AI orchestration in Copilot Studio
  - Design agents and agent flows with Copilot Studio
  - Design prompt actions in Copilot Studio
 Design extensibility of AI solutions
  - Design AI solutions by using custom models in Microsoft Foundry
  - Design agents in Microsoft 365 Copilot
  - Design agent extensibility in Copilot Studio
  - Design agent extensibility with Model Context Protocol in Copilot Studio
  - Design agents to automate tasks in apps and websites by using Computer Use in Copilot Studio
  - Design agent behaviors in Copilot Studio, including reasoning and voice mode
  - Optimize solution design by using agents in Microsoft 365, including Teams and SharePoint
 Orchestrate configuration for prebuilt agents and apps
  - Orchestrate AI features in Dynamics 365 apps for finance and supply chain
  - Orchestrate AI features in Dynamics 365 apps for customer experience and service
  - Propose Microsoft 365 agents for business scenarios
  - Orchestrate the configuration of Microsoft 365 Copilot for Sales and Microsoft 365 Copilot for Service
  - Propose Microsoft Power Platform AI features, including AI hub
  - Design interoperability of the finance and operations agent chats to use additional knowledge sources
  - Recommend the process of adding knowledge sources to in-app help and guidance for Dynamics 365 Finance or Dynamics 365 Supply Chain Management apps
Deploy AI-powered business solutions (40-45%)
 Analyze, monitor, and tune AI-powered business solutions
  - Recommend the process and tools required for monitoring agents
  - Analyze backlog and user feedback of AI and agent usage
  - Apply AI-based tools to analyze and identify issues and perform tuning
  - Monitor agent performance and metrics
  - Interpret telemetry data for performance and model tuning
 Manage the testing of AI-powered business solutions
  - Recommend the process and metrics to test agents
  - Create validation criteria of custom AI models
  - Validate effective Copilot prompt best practices
  - Design end-to-end test scenarios of AI solutions that use multiple Dynamics 365 apps
  - Build the strategy for creating test cases by using Copilot
 Design the ALM process for AI-powered business solutions
  - Design the ALM process for data used in AI models and agents
  - Design the ALM process for Copilot Studio agents, connectors, and actions
  - Design the ALM process for Microsoft Foundry Agents Service
  - Design the ALM process for custom AI models
  - Design the ALM process for AI in Dynamics 365 apps for finance and supply chain
  - Design the ALM process for AI in Dynamics 365 apps for customer experience and service
 Design responsible AI, security, governance, risk management, and compliance
  - Design security for agents
  - Design governance for agents
  - Design model security
  - Analyze solution and AI vulnerabilities and mitigations, including prompt manipulation
  - Review solution for adherence to responsible AI principles
  - Validate data residency and movement compliance
  - Design access controls on grounding data and model tuning
  - Design audit trails for changes to models and data

SUGGESTED MODULES
x0 Start here: X.1 The AI solution architect and what AB-100 tests
x1 Plan (25-30%): X.2 Requirements: where agents fit and grounding data · X.3 AI strategy:
   Cloud Adoption Framework and the AI Center of Excellence · X.4 Choosing the platform:
   Microsoft 365 Copilot, Copilot Studio or Foundry · X.5 Custom models, small language models
   and prompt guidelines · X.6 Multi-agent and multi-Dynamics 365 solutions · X.7 ROI, TCO,
   build-buy-extend and model routing
x2 Design (25-30%): X.8 Task, autonomous and prompt-and-response agents · X.9 Copilot Studio
   design: topics, orchestration choices, flows and prompt actions · X.10 Extensibility: Microsoft
   365 agents, MCP, computer use, reasoning and voice · X.11 Foundry Tools, custom models and
   grounding pipelines · X.12 AI in apps: canvas apps, generative pages, agent feed and
   Well-Architected · X.13 Dynamics 365 customer experience and service with Copilot ·
   X.14 Dynamics 365 finance and supply chain AI, Copilot for Sales and Service, AI hub
x3 Deploy (40-45%): X.15 Monitoring, telemetry and tuning · X.16 Testing agents and custom
   models · X.17 ALM for data, Copilot Studio and Foundry · X.18 ALM for AI in Dynamics 365 ·
   X.19 Security and governance for agents and models · X.20 Responsible AI, prompt
   manipulation, residency and audit
```

### 5.5 AB-731: AI Transformation Leader (optional)

```text
COURSE: AB-731 - AI Transformation Leader
Course id: ab731   Lesson letter: T   Target: 13 lessons in 4 modules (t0 + 3)
Level: Associate (business leaders, no code).   Pass mark: 700.
Study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-731
Outline as of July 22, 2026.

AUDIENCE (Microsoft): business decision-makers at all levels who guide transformation: AI
fluency, strategic vision, leading AI adoption across teams; evaluate AI opportunities,
champion responsible AI, align AI investments with business goals; experience leading adoption
or change management; familiar with Microsoft 365 services, Microsoft Foundry and general AI.
LAB SCENARIO: the Ralfiz Campus leadership team plans AI adoption for the help desk and
admissions office. Labs are strategy documents: opportunity map, model choice, cost and ROI
sheet, AI council charter, champions programme plan, licence plan.

SKILLS MEASURED (as of July 22, 2026)
Identify the business value of generative AI solutions (35-40%)
 Identify the foundational concepts of generative AI
  - Describe the differences between generative AI and other types of AI
  - Select a generative AI solution to meet a business need
  - Describe the differences between AI models, including fine-tuned and pretrained models
  - Explain the cost drivers in generative AI usage, including tokens and return-on-investment (ROI) considerations
  - Identify the challenges of using generative AI solutions, including fabrications, reliability, and bias
  - Identify when generative AI solutions can provide business value, including scalability and automation
 Identify benefits and capabilities of generative AI solutions
  - Describe the impact of prompt engineering
  - Understand techniques of prompt engineering
  - Identify business requirements for grounding solutions
  - Understand how retrieval-augmented generation (RAG) is used for AI solutions
  - Understand the impact of data on AI solutions, including data type, data quality, and representative datasets
  - Describe the importance of secure AI
  - Identify scenarios when machine learning adds value
  - Describe the lifecycle of a machine learning solution
  - Identify security considerations for AI systems, including application security, data security, and authentication requirements
Identify benefits, capabilities, and opportunities for Microsoft's AI apps and services (35-40%)
 Identify benefits and capabilities of Microsoft 365 Copilot and Microsoft Copilot
  - Map business processes and use cases to Copilot
  - Understand differences in capabilities between versions of Copilot
  - Understand capabilities of Microsoft 365 Copilot Chat web and mobile experiences
  - Understand capabilities of the Copilot experience in various Microsoft 365 apps
  - Understand capabilities of Microsoft Copilot Studio
  - Understand capabilities of Microsoft Graph
  - Identify benefits and capabilities of an integrated Microsoft AI solution, including risk mitigation and safety benefits
  - Map business processes and use cases to Microsoft's AI apps and services
  - Identify when to use Researcher or Analyst in Copilot
  - Identify when to build, buy, or extend, including the Microsoft 365 Copilot extensibility framework
 Identify benefits and capabilities of Foundry Tools
  - Map business processes and use cases to Foundry Tools
  - Identify capabilities of Foundry Tools, including Azure Vision in Foundry Tools, Azure AI Search, and Microsoft Foundry
  - Match an AI model to a business need
  - Identify the benefits of Microsoft Foundry and Foundry Tools, including scalability and security
Identify an implementation and adoption strategy for Microsoft's AI apps and services (20-25%)
 Align an AI strategy with Microsoft responsible AI policies
  - Explain the importance of responsible AI
  - Establish governance principles for AI use
  - Establish an AI council to guide strategy, oversight, and cross-functional alignment
  - Ensure that AI solutions meet responsible AI standards, including fairness, reliability, safety, privacy, security, inclusiveness, transparency, and accountability
 Plan for AI adoption across the organization
  - Establish an adoption team
  - Identify common barriers to adoption
  - Establish an AI champions program
  - Understand potential impacts to data, security, privacy, and cost
  - Understand Copilot license types, including pay-as-you go, monthly, and included with Microsoft 365 subscription
  - Understand Foundry Tools subscription models, including pay-as-you-go and commitment tiers

SUGGESTED MODULES
t0 Start here: T.1 What AB-731 tests and how leaders use it
t1 Business value of generative AI (35-40%): T.2 Generative AI versus other AI · T.3 Models,
   costs and ROI · T.4 Risks: fabrication, reliability and bias · T.5 Prompting, grounding and
   RAG · T.6 Data, machine learning and secure AI
t2 Microsoft's AI apps and services (35-40%): T.7 Copilot versions and experiences ·
   T.8 Copilot Studio, Microsoft Graph and build-buy-extend · T.9 Researcher, Analyst and use-case
   mapping · T.10 Foundry Tools and choosing a model
t3 Adoption strategy (20-25%): T.11 Responsible AI and the AI council · T.12 Adoption team,
   barriers and champions · T.13 Licensing, cost and risk planning
```

---

## 6. After a course is written

Give Claude Code in this repo the module JSON files, the question bank and the exercise files, and say "import course <id>". It will:

1. assemble `academy/content/<id>.json` and the `exercise-files/<id>/…` files, and add them to `files-index.json`;
2. run `import_labs` (it rejects bad HTML, broken quiz answers and missing files);
3. add the course to the course order, colours, icons, prerequisites (for example AB-100 after AB-410) and the catalogue text;
4. run the tests and check the lessons in a browser;
5. later, write and render the lesson videos with the existing video pipeline.

## 7. Effort estimate

| Course | Lessons | Prompt C turns | Your review time (approx.) |
|---|---|---|---|
| AB-620 | 19 | 4 | 5–6 hours |
| AB-900 | 22 | 4–5 | 6–7 hours |
| AB-730 | 16 | 5 | 4–5 hours |
| AB-100 | 20 | 4 | 6–8 hours (Dynamics 365 facts need care) |
| AB-731 | 13 | 3 | 3–4 hours |

The review time is mostly resolving `[VERIFY]` items and trying each lab once yourself in a trial tenant. That lab check is the step that keeps the courses trustworthy.
