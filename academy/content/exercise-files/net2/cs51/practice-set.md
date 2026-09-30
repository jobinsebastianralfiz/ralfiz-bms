# Practice set: 7.7 Complexity theory

Time: 24 minutes for all 15 (about 90 seconds each). No notes.

**1.** A problem X is shown to satisfy X ≤p SAT. What does this prove?
(1) X is NP-hard (2) X ∈ NP (3) X is NP-complete (4) X ∈ P

**2.** Graph G has 15 vertices and a minimum vertex cover of size 9. What is the size of its maximum independent set?
(1) 9 (2) 6 (3) 7 (4) 15

**3.** Match List I with List II.

| List I (Problem) | List II (Status) |
|---|---|
| A. Euler circuit | I. NP-complete |
| B. Subset sum | II. In P |
| C. Halting problem | III. NP-hard, not in NP |
| D. TAUTOLOGY | IV. co-NP-complete |

(1) A-II, B-I, C-III, D-IV (2) A-I, B-II, C-III, D-IV (3) A-II, B-I, C-IV, D-III (4) A-II, B-III, C-I, D-IV

**4.** In converting a CNF formula to 3-CNF by the standard method, a clause with 9 literals becomes how many clauses, using how many new variables?

**5.** Assertion (A): If 3-SAT ≤p Q and Q ∈ P, then P = NP.
Reason (R): 3-SAT is NP-complete.
Choose: (1) both true, R explains A (2) both true, R does not explain A (3) A true, R false (4) A false, R true

**6.** Statement I: Every NP-complete problem is NP-hard.
Statement II: Integer linear programming is in P.
(1) both true (2) both false (3) I true, II false (4) I false, II true

**7.** Which of the following are NP-complete? A. 3-colourability B. Bipartiteness C. Independent set D. Set cover (decision) E. Shortest path (decision)
(1) A, C and D only (2) A, B and C only (3) C, D and E only (4) A, C, D and E only

**8.** A 3-CNF formula has n = 5 variables and m = 7 clauses. For the variable-edge/clause-triangle reduction to VERTEX COVER, give the number of vertices, the number of edges and k.

**9.** How many distinct tours does brute force examine for a symmetric TSP with 10 cities?

**10.** Arrange in the order used to show NP-completeness: A. prove the reduction preserves yes and no answers; B. show the problem is in NP; C. build a polynomial-time transformation; D. pick a known NP-complete problem.
(1) B, D, C, A (2) D, A, C, B (3) B, C, D, A (4) C, D, A, B

**11.** For the formula (a) ∧ (a ∨ b) ∧ (a ∨ ¬b ∨ c ∨ d), how many clauses does the standard 3-CNF conversion produce?

**12.** Metric TSP: an MST of the instance weighs 40. Give (a) the upper bound guaranteed on the MST-preorder tour cost, (b) the lower bound on the optimal tour cost.

**13.** Graph G is a star with centre c and leaves 1 to 6. Give the minimum vertex cover size, the output size of APPROX-VERTEX-COVER, and the ratio.

**14.** Statement I: 0/1 knapsack is strongly NP-complete. Statement II: Bin packing (decision) is strongly NP-complete.
(1) both true (2) both false (3) I true, II false (4) I false, II true

**15.** Which conclusion follows if some NP-complete problem is proved to be in co-NP?
(1) P = NP (2) NP = co-NP (3) P = co-NP (4) PSPACE = NP
