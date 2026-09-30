# Solutions: 7.7 Complexity theory

**1. (2)** X ≤p SAT means X is no harder than SAT. Since SAT ∈ NP and NP is closed under ≤p, X ∈ NP. Hardness would need SAT ≤p X.

**2. (2)** Maximum independent set = n − minimum vertex cover = 15 − 9 = 6.

**3. (1)** Euler circuit is in P (connected and all degrees even). Subset sum is NP-complete. Halting is NP-hard but undecidable, so not in NP. TAUTOLOGY is co-NP-complete.

**4.** k − 2 = 7 clauses and k − 3 = 6 new variables: (l₁∨l₂∨y₁)(¬y₁∨l₃∨y₂)…(¬y₆∨l₈∨l₉).

**5. (1)** Every NP problem L satisfies L ≤p 3-SAT ≤p Q, and Q ∈ P, so L ∈ P. That gives NP ⊆ P and P = NP. The NP-completeness of 3-SAT (R) is exactly what makes this work.

**6. (3)** NP-complete = NP ∩ NP-hard, so I is true. ILP is NP-hard (0/1 ILP feasibility is NP-complete). Linear programming over the reals is in P; the trap is to confuse the two. II is false.

**7. (1)** 3-colourability, independent set and set cover are NP-complete. Bipartiteness (2-colourability) and shortest path are in P.

**8.** Vertices 2n + 3m = 10 + 21 = 31. Edges n + 6m = 5 + 42 = 47. k = n + 2m = 5 + 14 = 19.

**9.** (n − 1)!/2 = 9!/2 = 362880/2 = 181,440.

**10. (1)** Membership (B), choose a known NPC problem (D), build f (C), prove correctness (A). Options 3 and 4 build f before choosing the source problem, and option 2 proves correctness before f exists.

**11.** (a) gives 4 clauses (2 new variables). (a ∨ b) gives 2 clauses (1 new variable). The 4-literal clause gives k − 2 = 2 clauses (1 new variable). Total 4 + 2 + 2 = **8 clauses**, with 4 new variables.

**12.** (a) A preorder walk shortcuts a full walk of cost 2 × MST, and by the triangle inequality shortcuts never add cost. So the tour costs ≤ 2 × 40 = 80. (b) Deleting one edge of an optimal tour leaves a spanning tree, so OPT ≥ MST = 40.

**13.** The optimum is 1 ({c}). The algorithm takes one edge c–i and adds c and i, which covers every edge, so it outputs 2. The ratio is 2/1 = 2.

**14. (4)** 0/1 knapsack has a pseudo-polynomial O(nW) DP, so it is only weakly NP-complete (I false). Bin packing remains NP-complete even with numbers written in unary (it contains 3-partition), so it is strongly NP-complete (II true).

**15. (2)** If an NP-complete X ∈ co-NP, then every L ∈ NP reduces to X, so L ∈ co-NP and NP ⊆ co-NP. By symmetry co-NP ⊆ NP, so NP = co-NP. It does not settle P versus NP.
