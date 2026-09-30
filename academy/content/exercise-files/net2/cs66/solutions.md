# Solutions 10.2: Knowledge representation and reasoning

Every MGU, CNF, probability and combination below was recomputed by the verification script (a Robinson unifier with the occurs check, sympy CNF conversion, exact enumeration over the Bayesian network, and exact fractions for CF and Dempster–Shafer).

**1.**
- (a) x/f(z), then g(y) against g(f(a)) gives y/f(a), then y (now f(a)) against z gives z/f(a). Applied throughout, the MGU is **{x/f(f(a)), y/f(a), z/f(a)}**.
- (b) x/g(y), then f(a) against f(y) gives y/a. The MGU is **{x/g(a), y/a}**.
- (c) x/y, then f(x) = f(y) against y. The **occurs check fails**, so there is no unifier.
- (d) z/f(x), then y against g(z) gives y/g(f(x)), then x/a. The MGU is **{x/a, y/g(f(a)), z/f(a)}**.

**2.**
- (a) De Morgan gives ¬P ∧ ¬(Q ∧ ¬R) = ¬P ∧ (¬Q ∨ R). That is **2 clauses**.
- (b) ¬P ∨ (Q ∧ R) = (¬P ∨ Q) ∧ (¬P ∨ R). That is **2 clauses**.
- (c) Distributing gives (P ∨ R) ∧ (P ∨ S) ∧ (Q ∨ R) ∧ (Q ∨ S). That is **4 clauses**. Distribution can multiply the number of clauses.
- (d) (¬P ∨ Q ∨ R) ∧ (P ∨ ¬Q) ∧ (P ∨ ¬R). That is **3 clauses**.

**3.** Answer (1). First eliminate →: ∀x [¬∃y Owns(x, y) ∨ ∃z Insures(x, z)]. Then move ¬ inwards: ∀x [∀y ¬Owns(x, y) ∨ ∃z Insures(x, z)]. The ∃y has become ∀y, so it needs no Skolem term. ∃z lies in the scope of ∀x only, so z becomes F(x): **¬Owns(x, y) ∨ Insures(x, F(x))**. The trap is Skolemising y, which is really universal because it sits inside the negated antecedent.

**4.** The clauses are:
1. ¬Programmer(x) ∨ ¬KnowsC(x) ∨ KnowsPointers(x)
2. ¬KnowsPointers(y) ∨ Debug(y)
3. Programmer(Anita)
4. KnowsC(Anita)
5. ¬Debug(Anita) (the negated goal)

The proof: 5 + 2 with {y/Anita} gives ¬KnowsPointers(Anita). With 1 and {x/Anita}, this gives ¬Programmer(Anita) ∨ ¬KnowsC(Anita). With 3, it gives ¬KnowsC(Anita). With 4, it gives □. That is **4 resolution steps**.

**5.** Answer (2).
- Cycle 1: R3 (P) and R5 (R) match. R1 does not match yet, because Q is unknown. R3 fires, giving Q.
- Cycle 2: R1 (P, Q) and R5 match. R1 fires, giving S.
- Cycle 3: R2 and R5 match. R2 fires, giving T.
- Cycle 4: R4 (T, Q) and R5 match. R4 fires, giving U.

The system stops with U, and **R5 never fires**. Option (1) fires R1 before Q exists.

**6.** U is concluded by R4, so the subgoals are T, then Q. T comes from R2, with subgoal S. S comes from R1, with subgoals P (a fact) and Q. Q comes from R3, with subgoal P (a fact). Back in R4, Q is already proved. The subgoals in order are **T, S, P, Q, P**. R4’s second premise, Q, is then already established. Backward chaining never looks at R5, because V is irrelevant to U.

**7.** Answer (2). P(defective) = 0.5 × 0.02 + 0.3 × 0.03 + 0.2 × 0.05 = 0.010 + 0.009 + 0.010 = 0.029. So P(C | defective) = 0.010/0.029 = **10/29** ≈ 0.345. The trap 1/5 is the prior. 9/29 is machine B’s posterior.

**8.**
- (a) Given ¬M, P(F) = 1/20 and P(T) = 1/5. So P(L | ¬M) = (1/20)(1/5)(9/10) + (1/20)(4/5)(7/10) + (19/20)(1/5)(1/2) + (19/20)(4/5)(1/10) = **26/125** = 0.208.
- (b) By enumeration, P(T, L) = 209/1250 and P(L) = 353/1250. So P(T | L) = **209/353** ≈ 0.592. The prior P(T) is 7/25 = 0.28, so observing L raises it.
- (c) P(F, T) = 1/5 × 1/2 × 3/5 + 4/5 × 1/20 × 1/5 = 3/50 + 1/125 = 17/250. With P(T) = 7/25, P(F | T) = **17/70** ≈ 0.243, above the prior P(F) = 7/50 = 0.14. F and T are dependent through their common cause M.

**9.** Answer (3). The node counts are:
- X1: 1
- X2: 1
- X3: 4
- X4: 2
- X5: 4
- X6: 2³ = 8

That totals **20**. The full joint needs 2⁶ − 1 = **63**.

**10.** Answer (2). A is true (a chain is blocked by its middle node). B is true (a common cause links A and C while it is hidden). C is false: observing a collider makes its parents dependent. D is true (observing a descendant of the collider also opens it). E is the local Markov property, so it is true.

**11.**
- R1: 0.8 × min(0.9, 0.7) = 0.8 × 0.7 = 0.56.
- R2: 0.6 × max(0.5, 0.3) = 0.6 × 0.5 = 0.30.
- Combined: 0.56 + 0.30 × (1 − 0.56) = 0.56 + 0.132 = **0.692**.

**12.** Every intersection is non-empty, so K = 0. The products are:

| m₁ \ m₂ | {B, C} 0.6 | {A} 0.3 | Θ 0.1 |
|---|---|---|---|
| {A, B} 0.8 | {B} 0.48 | {A} 0.24 | {A, B} 0.08 |
| Θ 0.2 | {B, C} 0.12 | {A} 0.06 | Θ 0.02 |

Combined: m({B}) = 0.48, m({A}) = 0.30, m({A, B}) = 0.08, m({B, C}) = 0.12, m(Θ) = 0.02.
- Bel({B}) = **0.48**. Pl({B}) = 0.48 + 0.08 + 0.12 + 0.02 = **0.70**.
- Bel({A}) = **0.30**. Pl({A}) = 0.30 + 0.08 + 0.02 = **0.40**.

**13.** Answer (4). A default is an overridable assumed value. If-needed runs on read, when the slot is empty. If-added runs on write. A type facet restricts the filler.

**14.** Answer (1). Tweety inherits “can fly” from bird until the more specific penguin node overrides it. The conclusion is withdrawn when more knowledge arrives, which is exactly the non-monotonicity that R states. R explains A.

**15.** Answer (3).
- H1: (0.9 − 0.6)/(1 − 0.6) = 0.75.
- H2: 0.5 + 0.4 × 0.5 = 0.70.
- H3: −0.4 − 0.5 × 0.6 = −0.70.
- H4: 0.3 + 0.6 × 0.7 = 0.72.

Lowest first, the order is **H3 (−0.70), H2 (0.70), H4 (0.72), H1 (0.75)**.
