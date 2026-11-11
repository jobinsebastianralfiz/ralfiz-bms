# Intern XP wallet: plan

Drafted 10 Nov 2026. Steps 1-4 built 11 Nov 2026 (app `wallet`); step 5 (Flutter) not started. Open questions decided for now: XP never expires, employees get a wallet only if "Give employees a wallet" is on in XP Settings, no leaderboard.

## What it is

Every intern gets a wallet. When they finish real work and it's approved, XP goes into the wallet. Ralfiz later pays the XP out as money: on that month's payslip, or as a separate payment. One fixed rate turns XP into rupees.

Decisions already made:
- **Direction:** Ralfiz pays the intern. XP doesn't reduce the internship fee.
- **Rate:** **2 XP = ₹1** (1 XP = 50 paise), set in Settings. Each payout keeps the rate it was paid at, so changing the rate never changes past payouts.
- **Awarding:** finishing work creates **pending** XP. It reaches the wallet only after Admin/HR approves it. The approver can change the amount or reject it.

## How XP moves

```
work finished ──► Pending XP ──(Admin/HR approves, can edit)──► Wallet balance ──(cash out)──► Paid
                       └──(rejected, with reason)                     └── manual + / − adjustments
```

The wallet is a **ledger**. Every change is a row, and the balance is the sum of the rows. Rows are never edited or deleted; a mistake is fixed with a correcting row. That way every rupee has a reason, a date and the name of whoever did it.

## Where XP comes from

All amounts are defaults that Admin can change in Settings. Each one is a suggestion; the approver can change it.

| Source (already in the BMS) | When pending XP is created | Default XP |
|---|---|---|
| **Work assignment** (`WorkAssignment`) | Status becomes Completed | By priority: Low 50 (₹25) · Medium 100 (₹50) · High 200 (₹100) · Urgent 300 (₹150). A new optional **XP** field on the assignment overrides this. |
| **UAT plan** (`UATPlan`) | The tester has marked every test in their sections of the plan | **A fixed XP set on the plan, like a paid task** (new field **XP reward per tester**, e.g. 600 XP = ₹300). Each tester gets the full amount once their part is done. Bugs found, passes or fails don't change it. |
| **Assessment** (`InternAssessment`) | It is graded | Score % × 1, e.g. 85% = 85 XP (₹42.50) |
| **CRM lead** | A lead the intern added becomes a client | 500 (₹250) |
| **Manual award** | Admin/HR adds it with a reason | Any amount; this is how bonuses and penalties are given |

Not counted: attendance, daily updates and Academy lessons. Those are routine, and paying for them would make the wallet about showing up rather than real work. Any of them can be added later as another row in this table.

If one task is assigned to several interns, each gets their own pending XP. The approver can split it, e.g. 60 / 40.

## Screens

**Intern (staff portal)**
- A **Wallet card on the home page** shows the balance in XP and its rupee value, pending XP, and "Paid so far".
- **`/staff/wallet/`** shows the balance, a monthly earned chart, and the ledger (date, what for, +XP / −XP, status: Pending / Approved / Rejected / Paid). Each row links to its work assignment, UAT plan or assessment. Rejected rows show the reason.
- The intern gets a notification when XP is approved, rejected or paid out, through the existing `Notification` model and push.
- Interns can only look. They can't redeem or edit anything.

**Admin / HR (BMS)**
- **HR → XP approvals:** a queue of pending XP with the intern, the source and a link to the work. Actions: **Approve**, **Approve with a different amount** (reason required), **Reject** (reason required), and approve several at once.
- **HR → Wallets:** one row per intern with balance, pending XP, paid this month and total paid. Open an intern to see their ledger, **add or remove XP** (reason required) or **Cash out**.
- **Cash out:** pick the XP amount (default: everything). The rupee value is shown at the current rate. Then choose one of:
  1. **Add to payslip**: adds it to that month's `Payroll.bonus`, marked "XP payout", and the payslip shows it as its own line.
  2. **Pay separately**: record the method (UPI / bank / cash), a reference and the date. This works for interns who have no stipend payroll.

  Either way the XP leaves the wallet as a "Paid" row. If the payslip or payment is undone, a correcting row puts the XP back.
- **Settings → XP:** the rupee rate (2 XP = ₹1 to start), default XP per source, and a monthly cap per intern (optional, off by default).
- **Work assignment form:** a new optional **XP** field, so a big task can be worth more than its priority default.
- **UAT plan (BMS → UAT → Plan details):** a new **XP reward per tester** field, also settable when loading a plan (`load_uat_plan --xp 600`). The intern's UAT card shows it: "Reward: 600 XP · ₹300". If a tester is late or careless, the approver can lower the amount when approving.

## Data (new app `wallet`)

- **`XPEntry`**: one row in the ledger, never edited after approval.
  - employee
  - xp (+ or −)
  - kind: earned / adjustment / payout / reversal
  - status: pending / approved / rejected
  - source: a generic link to the work assignment, UAT result, assessment, lead, etc., with a unique constraint so the same work can't pay twice
  - suggested_xp
  - note, decided_by, decided_at
  - rate_paise (frozen on payout rows; 50 paise per XP to start)
  - payout (link)
  - created_at
- **`XPPayout`**: one cash-out.
  - employee, xp, rate, amount ₹
  - method: payslip / UPI / bank / cash
  - payroll (link, when on a payslip)
  - reference, paid_on, created_by
- **`XPSettings`**: one row with the rate, defaults and cap.
- Balance = sum of approved entries. Pending = sum of pending entries. Neither is stored, so they can't get out of step.

**Hooks:** a signal or service call when a work assignment becomes Completed, a tester finishes all their tests in a UAT plan, or an assessment is graded. The unique source constraint means re-saving or re-completing the same work never creates a second pending row.

**Payroll:** `Payroll.calculate()` already adds `bonus`. The XP payout adds a separate field, `xp_payout`, so that HR editing the normal bonus never wipes the XP amount, and so the payslip can show the two lines separately. Regenerating a draft payroll keeps the XP payout attached.

## Rules and safety

- Work marked Completed by the intern only makes **pending** XP. Nothing reaches the wallet without approval.
- If completed work is reopened or cancelled after approval, a reversal row is added, and the approver sees it.
- You can't cash out more than the balance, and an intern's balance never goes below 0.
- Interns who leave (resignation approved) keep their balance until it is paid out or written off with a reason. Their HR page shows "XP not paid".
- Only Admin/HR can approve, adjust or cash out. Each action is logged with who did it and when.
- The rupee rate is shown everywhere next to the XP, so an intern always knows what it's worth.

## Build order

1. **Ledger and wallet pages:** models, settings, manual award, the intern wallet page and home card, and the HR wallets list. Usable on day one with manual awards.
2. **Approvals and automatic pending XP:** the approval queue, plus hooks for work assignments and UAT plans.
3. **Cash out:** to the payslip (with its own payslip line) or as a separate payment, plus reversals.
4. **More sources:** assessments and CRM leads; the monthly cap; notifications and push.
5. **Mobile app** (Flutter, later): the same wallet screen through the API.

Each step ships with tests. The main cases: the same work can't pay twice, balance equals the sum of the ledger, a payout freezes its rate, and a reopened task reverses its XP.

## Open questions

1. Should XP **expire** if it isn't paid out (e.g. after 6 months), or stay forever?
2. Should **employees** have wallets as well, or only interns? The design works for both; only the menu visibility changes.
3. Should interns see a **leaderboard** (top earners this month)? Off by default, since it can push people to chase points.
