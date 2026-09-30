# Solutions 10.1: AI approaches and search

Every order, cost and count below was recomputed by the verification script (graph search implementations with the stated conventions, a minimax and alpha–beta evaluator, and brute-force counting).

True costs to G, used for the admissibility check: S 7, A 5, B 6, C 3, D 2, E 1, G 0.

**1.** The queue grows as S | A, B | C, E (from A; B is already queued) | D (from B) | G (from C). The expansion order is **S, A, B, C, E, D, G**. The path is S–A–C–G, with cost 3 + 2 + 6 = **11**. BFS minimises edges, not cost.

**2.** Answer (3). S → A (A’s neighbours in order: B, C, E) → B (its unvisited neighbour is D) → D (D’s neighbours in order: C, G) → C → G. The order is **S, A, B, D, C, G**, and the path S–A–B–D–C–G costs 3 + 1 + 5 + 1 + 6 = **16**.

**3.**

| Step | Expand (g) | Frontier after the step |
|---|---|---|
| 1 | S (0) | B 1, A 3 |
| 2 | B (1) | A 2 (improved), D 6 |
| 3 | A (2) | C 4, D 6, E 8 |
| 4 | C (4) | D 5 (improved), E 8, G 10 |
| 5 | D (5) | G 7 (improved), E 8 |
| 6 | G (7) | goal |

The path is S–B–A–C–D–G with cost **7**. The goal was first generated with cost 10 at step 4. Stopping there would be wrong.

**4.** (a) h ≤ h* for every node, so h is **admissible**. Checking all ten edges in both directions shows no violation of h(n) ≤ c + h(n′), so h is also **consistent**.

(b) The trace:

| Step | Expand (f) | Frontier after the step (f) |
|---|---|---|
| 1 | S (5) | B 1+5 = 6, A 3+4 = 7 |
| 2 | B (6) | A 2+4 = 6, D 6+2 = 8 |
| 3 | A (6) | C 4+3 = 7, D 8, E 8+1 = 9 |
| 4 | C (7) | D 5+2 = 7, E 9, G 10 |
| 5 | D (7) | G 7, E 9 |
| 6 | G (7) | goal |

A* expands **6 nodes** (S, B, A, C, D, G) and returns cost 7. The f values along the path are 5, 6, 6, 7, 7, 7, which never decrease.

**5.** From S, A (h 4) beats B (h 5). From A, E (h 1) beats C (h 3). From E, the search reaches G. The path S–A–E–G costs 3 + 6 + 1 = **10**, which is **3 more** than the optimum of 7.

**6.** Answer (3). The iterations are:
- limit 0: S (1 visit);
- limit 1: S, A, B (3);
- limit 2: S, A, B, C, E, B, A, D (8);
- limit 3: S, A, B, D, C, D, G (7), and the goal is found.

The goal is found at **limit 3**, after 1 + 3 + 8 + 7 = **19** visits. The path is S–A–C–G, the shallowest one.

**7.**
1. The first MIN node needs all its leaves: min(8, 3, 5) = 3, so α = 3.
2. The second MIN node sees 2 ≤ 3, so 9 and 4 are pruned.
3. The third MIN node sees 6, 7 and 1. It needs all three, because 1 is the first leaf ≤ 3, and it is also the last. Its value is 1.
4. The fourth MIN node sees 4, 8 and 6, none ≤ 3, so its value is 4.

The root is max(3, 2, 1, 4) = **4**, and **2 leaves** are pruned. Notice that the best child came last, which is the worst place for pruning at the root.

**8.** The MAX nodes are 6, 8, 7, 5, 9 and 6. The MIN nodes are min(6, 8) = 6, min(7, 5) = 5 and min(9, 6) = 6. The root is **6**.

Alpha–beta prunes **0 leaves**. Trace it: MIN 1 sets β = 6 after its first MAX child; in the second MAX child (2, 8) the leaf that reaches β is 8, but it is already the last leaf. Then α = 6. MIN 2 evaluates (7, 3) = 7 and (1, 5) = 5, and it drops to α or below only after its last child. MIN 3 evaluates (9, 2) = 9 and (6, 3) = 6 in full, for the same reason. Every value that would trigger a cut-off arrives at the last position, so nothing is skipped. With the worst ordering, alpha–beta examines every leaf, exactly like minimax. Good ordering (best moves first) is what makes pruning pay.

**9.** Answer (4). Poker hides the opponents’ cards (partially observable). Each image is classified independently (episodic). A crossword does not change while you think and has one solver (static and single-agent). Driving involves continuous speeds, positions and steering angles (continuous).

**10.** Answer (1). Each restart is an independent random trial with some fixed chance p > 0 of starting in the global optimum’s basin. The chance that all k restarts fail is (1 − p)^k, which tends to 0. That independence comes from R, so R explains A.

**11.** Answer (2). A, B, D and E are standard facts. C is false: forward checking looks only at arcs from the newly assigned variable to its neighbours. It misses conflicts between two unassigned variables, which arc consistency catches.

**12.** (a) W, X and Y form a triangle, so there are 3! = 6 ways to colour them. Z is adjacent to X and Y, so it must take W’s colour. V is adjacent to Z (W’s colour) and Y, so it must take X’s colour. The total is **6** (brute force confirms).

(b) After W = red and X = green, Y (adjacent to both) has only {blue} left, and Z (adjacent to X) has {red, blue}. MRV picks **Y**, the variable with 1 remaining value.

**13.** BFS: 1 + 5 + 25 + 125 = **156**. IDS: 4·1 + 3·5 + 2·25 + 1·125 = 4 + 15 + 50 + 125 = **194**. The overhead is 38/156 ≈ **24%**.

**14.** At T = 10: e^(−5/10) = e^(−0.5) ≈ **0.607**. At T = 1: e^(−5) ≈ **0.0067**. At a low temperature, bad moves are almost never taken.

**15.** Answer (2). The worst-case memory is:
- depth-limited search: bl = 30;
- IDS: bd = 50;
- DFS: bm = 80;
- BFS: b^d = 100,000.

So the order is D, C, B, A.
