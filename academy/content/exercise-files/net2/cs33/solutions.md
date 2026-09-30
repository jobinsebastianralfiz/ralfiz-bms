# Solutions: CPU scheduling practice set

TAT = CT − AT; WT = TAT − BT; RT = first run − AT.

**1. FCFS.** P1 0–7, P2 7–11, P3 11–13, P4 13–18, P5 18–21.
WT: P1 0, P2 5, P3 8, P4 8, P5 12 → sum 33 → **average 6.6**.

**2. SJF (non-preemptive).** P1 runs 0–7. At 7 the ready bursts are P2 4, P3 2, P4 5, P5 3, so the order is P3 7–9, P5 9–12, P2 12–16, P4 16–21.
TAT: P1 7, P2 14, P3 6, P4 16, P5 6 → sum 49 → **average 9.8**.

**3. SRTF.** Chart: P1 0–2, P2 2–3, P3 3–5, P2 5–8, P5 8–11, P1 11–16, P4 16–21.
Key decisions: at 2, P2 (4) < P1's remaining 5, so P2 pre-empts. At 3, P3 (2) < P2's remaining 3, so P3 pre-empts. At 5, P2 has 2 left, the smallest. At 6, P5 (3) is not less than P2's 2, so P2 continues. At 8 the choice is P1 5, P4 5, P5 3, so P5 runs. At 11, P1 and P4 tie at 5, and the tie goes to the earlier arrival, P1.
CT: P1 16, P2 8, P3 5, P4 21, P5 11. WT: P1 9, P2 2, P3 0, P4 11, P5 2 → sum 24 → **average 4.8**.
Context switches: P1→P2→P3→P2→P5→P1→P4 = **6**.

**4. Preemptive priority.** P1 (2) runs 0–2. P2 (1) pre-empts and runs 2–6. At 6, P2 finishes and P5 (priority 1) arrives. The ready priorities are P1 2, P3 4, P4 3 and P5 1, so P5 runs 6–9. Then P1 9–14, P4 14–19, P3 19–21.
**P1 completes at 14.**

**5. RR, q = 3.** P1 runs 0–3. P2 arrived at 2, and P3 arrives at 3, the same instant P1's quantum expires, so P3 goes before P1. Queue: P2, P3, P1. P2 3–6 (1 left); P4 (5) and P5 (6) have arrived: queue P3, P1, P4, P5, P2. P3 6–8 (done). P1 8–11 (1 left). P4 11–14 (2 left). P5 14–17 (done). P2 17–18 (done). P1 18–19 (done). P4 19–21 (done).
CT: P1 19, P2 18, P3 8, P4 21, P5 17. TAT: 19, 16, 5, 16, 11 → sum 67 → **average 13.4**. **P4 completes at 21.**

**6.** SJF order 1, 3, 4, 7, 9 → waits 0, 1, 4, 8, 15 → sum 28 → **5.6**. FCFS order 9, 4, 1, 7, 3 → waits 0, 9, 13, 14, 21 → sum 57 → **11.4**.

**7. HRRN.** P1 0–4. At 4: P2 (3 + 5)/5 = 1.6, P3 (1 + 2)/2 = 1.5, so P2 runs 4–9. At 9: P3 (6 + 2)/2 = 4, P4 (4 + 6)/6 = 1.67, P5 (3 + 3)/3 = 2, so P3 runs 9–11. At 11: P4 (6 + 6)/6 = 2, P5 (5 + 3)/3 = 2.67, so P5 runs 11–14, then P4 14–20.
Order **P1, P2, P3, P5, P4**. WT: 0, 3, 6, 9, 5 → sum 23 → **average 4.6**.

**8.** τ₁ = 0.25·12 + 0.75·16 = **15**; τ₂ = 0.25·8 + 0.75·15 = **13.25**; τ₃ = 0.25·20 + 0.75·13.25 = **14.9375**.

**9.** (a) 25/(25 + 5) = **83.33%**. (b) (n − 1)q = 7 × 25 = **175 ms**.

**10.** SRTF pre-empts on a strictly shorter job (A-III); HRRN uses the ratio and never pre-empts (B-I); RR with a huge quantum is FCFS (C-II); a multilevel queue binds processes permanently (D-IV). **Option (1).**

**11.** Both are true and R explains A. **Option 1.**

**12.** I is true (a non-preemptive process never waits after starting). II is false: in RR a process can wait again after its first slice, so WT ≥ RT. **Statement I is true but Statement II is false.**

**13.** 4 in Q0 (21 left), 8 in Q1 (13 left), **13 in Q2**. So 4 / 8 / 13.

**14.** P3 runs 0–2 (7 → 5). Now P2 and P3 tie at 5, so P2 (the lower number) runs 2–3; then P3 (5 > 4) runs 3–4. They tie again at 4, so P2 runs 4–5, then P3 5–6. Now all three are at 3, so P1 runs 6–7, and from here they rotate one unit at a time: P2 7–8, P3 8–9, P1 9–10, P2 10–11, P3 11–12, P1 12–13, P2 13–14, P3 14–15.
Completions: **P1 13, P2 14, P3 15**. Average TAT = 42/3 = **14**.

**15.** Utilisation = 1 − 0.6ⁿ ≥ 0.9 requires 0.6ⁿ ≤ 0.1. 0.6⁴ = 0.1296 and 0.6⁵ = 0.07776, so **n = 5**.
