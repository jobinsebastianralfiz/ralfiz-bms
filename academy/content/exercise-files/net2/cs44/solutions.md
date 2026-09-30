# Solutions: Software testing (cs44)

**1.** n = 5. (a) 4n + 1 = **21**. (b) 6n + 1 = **31**. (c) 5⁵ = **3125**.

**2.** Nominal x = 30, y = 5. Tests: (10, 5), (11, 5), (49, 5), (50, 5), (30, 1), (30, 2), (30, 8), (30, 9), (30, 5): **9 tests** (4 × 2 + 1).

**3.** Weak normal = the largest class count = **4**. Strong normal = 2 × 3 × 4 = **24**.

**4.** 2⁴ = **16** rules. One rule with a single don’t-care covers 2 combinations, so merging two rules into one leaves **15** rules.

**5.** V(G) = 17 − 13 + 2 = **6**. With binary predicate nodes, V(G) = predicates + 1, so there are **5** predicate nodes.

**6.** Simple conditions: a > 0, b > 0 (the || makes two predicate nodes), c > 0 and c % 2 == 0. V(G) = 4 + 1 = **5**. Trap: counting a > 0 || b > 0 once gives 4.

**7.** V(G) = E − N + 2P = 40 − 34 + 2 × 4 = **14**.

**8.** **4** tests (n + 1): (F,F,F), which is false, plus (T,F,F), (F,T,F) and (F,F,T), each true and each differing from FFF in one condition.

**9.** Score = 54 ÷ (80 − 8) = 54 ÷ 72 = **75%**. 90% of 72 = 64.8, so at least 65 kills are needed: **11 more**.

**10.** Output: **00110**. The test x = 18 returns 0 but should return 1, because the code uses x > 18 instead of x >= 18. The fault shows up only at the minimum boundary, which is exactly why BVA tests min itself.

**11.** Estimated total = 72 × 30 ÷ 24 = 90, so **18** remain.

**12.** Driver calls the module (A-II); stub stands in for a called module (B-I); oracle judges outputs (C-III); mutant has one change (D-IV). **Option (1).**

**13.** A is true (two predicates + 1). R is false: there are 2 × 2 = 4 complete paths. **Option (3).**

**14.** Equivalence partitioning, decision tables and cause–effect graphing use only the specification. Data flow testing and loop testing need the code. **Option (1): A, B and D only.**

**15.** Unit, integration, system, acceptance: **C, B, D, A, option (1).**
