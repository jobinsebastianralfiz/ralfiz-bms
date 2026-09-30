# Solutions: practice set 8.3

TM move counts and PCP solutions were checked by simulation and breadth-first search (netv/cs55.py). Closure facts were checked against a closure table that passes the De Morgan and difference cross-checks.

**1. Answer (2) 10, 10000.** 4 moves right to the blank, 1 move left, 4 carries (1 → 0), and then the blank beyond the left end becomes 1: 4 + 1 + 4 + 1 = 10. 15 + 1 = 16 = 10000 in binary.

**2. Answer (3) 25.** The machine makes 2n² + 2n + 1 moves, which is 18 + 6 + 1 = 25 for n = 3 (the simulation agrees). The work is quadratic because each round trip crosses the whole block of marked symbols.

**3. 8 moves, 11111.** 3 moves over 111, 1 move to change the 0 to 1, 2 moves over 11, 1 move on the blank to step back, and 1 move to erase. The result is 3 + 2 = 5.

**4. Shortest solution: 1, 1, 2, 3.** Top: aa · aa · a · aba = aaaaaaba. Bottom: aaa · aaa · b · a = aaaaaaba. They are equal. Pair 2 cannot start (a against b). Breadth-first search over all index sequences shows that no solution of length 3 or less exists.

**5.** In both pairs the top is longer than the bottom (2 > 1 and 3 > 2). Any sequence of k pairs gives a top string at least k symbols longer than the bottom string, so the two can never be equal. There is no solution.

**6. Answer (1) A-IV, B-III, C-II, D-I.**

**7. Answer (1).** "0110 ∈ L(M)" depends only on L(M). It holds for Σ* and fails for ∅, so it is non-trivial, and Rice makes it undecidable. It is RE but not recursive. R is the reason.

**8. Answer (1) A, C and D only.** A: scan the transition table. C: CSL membership (LBA configurations are bounded). D: bounded simulation. B: a property of L(M), so Rice applies. E: undecidable for CFGs (reduction from PCP).

**9.** (a) RE but not recursive: simulate M on ⟨M⟩. It is the complement of L_d, and is undecidable by diagonalisation. (b) Not RE (and not co-RE either). Finiteness is not a finitely witnessed property. (c) Recursive: minimise the DFA or check reachability of a non-final state. (d) RE but not recursive: dovetail over the inputs. Rice-style undecidability applies.

**10. P ≤m Q.** A decider for Q, composed with the reduction, would decide P, which is a contradiction. Showing Q ≤m P only proves that Q is no harder than P. It says nothing about Q being undecidable.

**11. Answer (3).** Intersection: run both recognisers, and accept if both accept. Difference L₁ − L₂ = L₁ ∩ L̄₂ fails: with L₁ = Σ* it would give complement closure, which RE lacks.

**12. Answer (3) 640.** 4 × 5 × 2⁵ = 4 × 5 × 32 = 640.

**13. Answer (1) D, B, E, A, C.** Regular ⊂ CFL ⊂ CSL ⊂ Recursive ⊂ RE.

**14. Answer (3).** I: the single-tape simulation squares the running time: (n²)² = n⁴. II: false. The power is the same, and only the speed differs.

**15. Answer (2).** This is the counting argument: countably many TMs cannot cover uncountably many languages. Options (3) and (4) name specific undecidable problems, but those problems are RE, so they do not explain why non-RE languages exist.
