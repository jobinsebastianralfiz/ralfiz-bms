# Solutions: Software design (Lesson 6.3)

**1. Answer: C, F, B, E, D, A.**
Coincidental, logical, temporal, procedural, communicational, sequential (functional would come last).

**2. Answer: D, A, E, F, B, C.**
Data, stamp, control, external, common, content. Trap: putting common (shared globals) after content; content is always the worst.

**3.** (a) Coincidental: the tasks are unrelated. (b) Sequential: output feeds input. (c) Communicational: both tasks use the same sales record. (d) Temporal: grouped by time (program end).

**4.** (a) Stamp. (b) Control. (c) Common. (d) External.

**5. Answer (1): A-III, B-I, C-II, D-IV.**

**6.** S = fan-out², D = v ÷ (fan-out + 1), C = S + D.

| Module | S | D | C |
|---|---|---|---|
| Main | 16 | 3 ÷ 5 = 0.6 | 16.6 |
| A | 4 | 6 ÷ 3 = 2 | 6 |
| B | 0 | 5 ÷ 1 = 5 | 5 |
| C | 1 | 2 ÷ 2 = 1 | 2 |

Main is the most complex (16.6), almost entirely from its fan-out of 4.

**7.** 50 × (2 × 5)² = 50 × 100 = 5,000.

**8.** Pairs = C(5, 2) = 10. Sharing pairs: (M1, M2) share x; (M3, M5) share z; (M4, M5) share w. Q = 3, P = 10 − 3 = 7. LCOM = 7 − 3 = 4.

**9.** Square → Quadrilateral → Polygon → Shape: DIT(Square) = 3. NOC(Shape) = 3 (Circle, Polygon, Line). NOC(Polygon) = 2 (Triangle, Quadrilateral).

**10. Answer (4).** A is false: logical cohesion ranks below temporal. R is a correct description of logical cohesion.

**11. Answer (3).** I is true. II is false: realisation is a dashed line with a hollow triangle pointing to the interface.

**12. Answer (1): A, B and D only.** Observer and Command are behavioural.

**13.** Incoming (afferent) flow: read timesheet → validate. Transform centre: compute gross pay → compute deductions. Outgoing (efferent) flow: format payslip → print.
First-level factoring: a Payroll main module calling three controllers: Get valid timesheet (input), Compute net pay (transform), Produce payslip (output).

**14.** (a) Place the user in control (allow easy correction and undo; do not destroy the user’s work). (b) Make the interface consistent. (c) Reduce the user’s memory load.

**15.** Size = 9 + 11 = 20. r = 11 ÷ 9 ≈ 1.22. A tree with 9 nodes has exactly 8 arcs, so this chart is not a pure tree: some modules have fan-in greater than 1.
