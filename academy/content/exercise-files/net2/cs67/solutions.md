# Solutions 10.3: Planning, NLP and multi-agent systems

Every state, plan length, parse count, probability, weight and game-theory result below was recomputed by the verification script (a STRIPS simulator with breadth-first plan search, a CYK parse counter, exact fractions for the n-gram model, numpy for cosine similarity and a Levenshtein table).

**1.**

| After | State |
|---|---|
| Unstack(A,B) | On(B,C), OnTable(C), Holding(A), Clear(B) |
| Putdown(A) | On(B,C), OnTable(C), Clear(B), OnTable(A), Clear(A), HandEmpty |
| Unstack(B,C) | OnTable(C), OnTable(A), Clear(A), Holding(B), Clear(C) |
| Stack(B,A) | OnTable(C), OnTable(A), Clear(C), On(B,A), Clear(B), HandEmpty |

Final state: **On(B,A), OnTable(A), OnTable(C), Clear(B), Clear(C), HandEmpty** (6 atoms). Check each precondition before you apply the action: Unstack(B,C) is legal only because Putdown(A) restored HandEmpty and Unstack(A,B) had made B clear.

**2.** Stack(B,C) adds On(B,C), Clear(B), HandEmpty and deletes Holding(B), Clear(C). It adds a goal atom and deletes none, so it is relevant. Regression: (g − ADD) ∪ PRE = ({On(B,C), Clear(A)} − ADD) ∪ {Holding(B), Clear(C)} = **{Clear(A), Holding(B), Clear(C)}**. Unstack(B,C) is **not relevant**: it adds no goal atom, and it even deletes On(B,C).

**3.** Answer (3), **6 actions**: Unstack(A,B), Putdown(A), Unstack(B,C), Stack(B,A), Pickup(C), Stack(C,B). Every block has to move and each move costs two actions (pick up, put down or stack), so 3 moves × 2 = 6 is also a lower bound. Breadth-first search over the 18 ground actions confirms that no shorter plan exists.

**4.**
- (a) Choose the 3 positions for the first chain out of 6: C(6, 3) = **20**.
- (b) 6!/(2! × 2! × 2!) = 720/8 = **90**.

The trap is 3! × 3! = 36 or 6! = 720: the order inside each chain is fixed, so only the interleaving counts.

**5.** Answer (1). Ordering the threat before the producer is demotion, a legitimate fix (A is true). R gives the reason it works: a threat only matters if it can fall inside the protected interval, and C ≺ A rules that out. (Promotion, B ≺ C, works for the same reason.)

**6.** Answer (1), **A-IV, B-I, C-II, D-III**. Inconsistent effects: one action negates the other’s effect. Interference: one deletes the other’s precondition. Competing needs: preconditions mutex one level down. Inconsistent support is the literal mutex. Option (2) swaps the first two; option (3) swaps the last two.

**7.**
- (a) Morphological, syntactic, semantic, discourse, pragmatic: **C, B, E, A, D**.
- (b) (i) **syntactic (structural)**: the chicken is either the eater or the thing eaten, two different structures for the same words. (ii) **lexical**: bank has two senses. (iii) **semantic (quantifier scope)**: one film for everyone, or possibly different films. (iv) **anaphoric**: “she” may be Meena or Priya.

**8.**
- (a) The sentence has 7 words, so the table has 7 × 8/2 = **28** cells.
- (b) Cell (saw … hill) holds **VP**, with **2** derivations: VP → V NP with NP = “the man on the hill”, and VP → VP PP with VP = “saw the man” and PP = “on the hill”.
- (c) S → NP VP with NP = I, so S has **2** parse trees: the PP attaches either to the VP (I was on the hill) or to the NP (the man was on the hill).

**9.** Counts: c(<s>) = 4, c(agents) = 3, c(plan) = 3, c(robots) = 1, c(share) = 1, c(tasks) = 2, c(routes) = 2.
- (a) P(agents plan routes) = 3/4 × 2/3 × 2/3 × 2/2 = **1/3**. P(robots share tasks) = 1/4 × 0/1 × … = **0**, because “robots share” was never seen. This is why smoothing is needed.
- (b) Add-one, V = 7: P(agents | <s>) = 4/11, P(plan | agents) = 3/10, P(routes | plan) = 3/10, P(</s> | routes) = 3/9. Product = **3/275**. For the second sentence: 2/11 × 1/8 × 2/8 × 3/9 = **1/528**. Smoothing takes probability from seen bigrams and gives it to unseen ones, so the first sentence’s probability also falls.

**10.** N = 4. df: text 2, agents 2, and every other term 1. So idf(text) = idf(agents) = log₁₀ 2 ≈ 0.301, and every other idf is log₁₀ 4 ≈ 0.602.
- (a) D2: agents 1 × 0.301 = 0.301, plan 2 × 0.602 = **1.204**, tasks 0.602. D4: text 2 × 0.301 = **0.602**, retrieval 0.602, ranks 0.602.
- (b) q = (plan 0.602, text 0.301), |q| ≈ 0.6731.

| Doc | q·d | length of d | cosine |
|---|---|---|---|
| D2 | 1.204 × 0.602 ≈ 0.7250 | 1.3795 | **0.7807** |
| D4 | 0.301 × 0.602 ≈ 0.1812 | 1.0428 | **0.2582** |
| D1 | 0.301 × 0.301 ≈ 0.0906 | 0.9031 | **0.1491** |
| D3 | 0 | – | **0** |

Ranking: **D2, D4, D1, D3**.

**11.** At rank 5 the list has 3 relevant documents (R N R R N): P@5 = **3/5**, R@5 = **3/5**. At rank 8 it has 4: P@8 = 4/8 = **1/2**, R@8 = **4/5**. F₁@8 = 2 × (1/2)(4/5)/(1/2 + 4/5) = **8/13** ≈ 0.615. Going deeper in the list raised recall and lowered precision, the usual trade-off.

**12.**
- (a) **1**: substitute the fifth letter, n → t (plan-n-ing → plan-t-ing).
- (b) **2**: insert r after the a (a-r-gents), then delete the final s (argent).

**13.**
- (a) Up is dominant for the row player (2 > 1 and 4 > 3). Given Up, the column player prefers Left (3 > 1). So the unique Nash equilibrium is **(Up, Left) = (2, 3)**. It is **not Pareto optimal**: (Down, Right) = (3, 4) is better for both. This game has the same structure as the prisoner’s dilemma.
- (b) The bidder of 60 wins in both. First-price: pays **60**. Vickrey: pays the second-highest bid, **52**.

**14.**
- (a) Plurality: A has 6 first places, so **A** wins. Borda: A = 6 × 3 = 18; B = 6 × 2 + 5 × 3 + 4 × 2 = 35; C = 6 × 1 + 5 × 2 + 4 × 3 = 28; D = 5 × 1 + 4 × 1 = 9. **B** wins. Condorcet: B beats A 9–6, B beats C 11–4 and B beats D 15–0, so **B** is the Condorcet winner. A, the plurality winner, loses every pairwise contest.
- (b) A’s risk = (10 − 7)/10 = 3/10. B’s risk = (8 − 5)/8 = 3/8. A’s risk is smaller, so **A concedes**.

**15.** Answer (1), **A, D and E only**. B reverses the roles: the manager announces, the contractors bid. C is false: in the prisoner’s dilemma (and in problem 13(a)) the Nash equilibrium is Pareto dominated.
