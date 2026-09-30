# Practice set 10.2: Knowledge representation and reasoning

15 exam-level problems. Pace: about 90 seconds per problem, and up to 3 minutes for problems 4, 8 and 12. Work in fractions wherever probabilities appear.

Conventions: u, v, w, x, y and z are variables; a, b and names such as Anita are constants. In forward chaining, each cycle fires the lowest-numbered applicable rule that has not fired yet.

---

**1.** Find the MGU of each pair, or say why none exists.

- (a) Q(x, g(y), y) and Q(f(z), g(f(a)), z)
- (b) R(x, f(a)) and R(g(y), f(y))
- (c) P(x, f(x)) and P(y, y)
- (d) T(f(x), y, x) and T(z, g(z), a)

**2.** Convert each formula to CNF and count its clauses.

- (a) ¬(P ∨ (Q ∧ ¬R))
- (b) P → (Q ∧ R)
- (c) (P ∧ Q) ∨ (R ∧ S)
- (d) P ↔ (Q ∨ R)

**3.** Skolemise ∀x [∃y Owns(x, y) → ∃z Insures(x, z)].

(1) ¬Owns(x, y) ∨ Insures(x, F(x)) (2) ¬Owns(x, C) ∨ Insures(x, F(x)) (3) ¬Owns(x, G(x)) ∨ Insures(x, F(x)) (4) ¬Owns(x, y) ∨ Insures(x, C)

**4.** The facts: every programmer who knows C knows pointers; everyone who knows pointers can debug; Anita is a programmer who knows C. Write the clauses and prove Debug(Anita) by resolution refutation. How many resolution steps do you need?

**5.** The rules are R1: P ∧ Q → S; R2: S → T; R3: P → Q; R4: T ∧ Q → U; R5: R → V. The facts are P and R. Run forward chaining until U is derived. Give the firing order and say which rule never fires.

(1) R1, R3, R2, R4; R5 never fires (2) R3, R1, R2, R4; R5 never fires (3) R3, R1, R2, R5, R4 (4) R3, R5, R1, R2, R4

**6.** For the same rule base, run backward chaining from the goal U. List the subgoals in the order they are raised (depth first, premises left to right).

**7.** Machines A, B and C produce 50%, 30% and 20% of a factory’s output. Their defect rates are 2%, 3% and 5%. A randomly chosen item is defective. What is the probability that it came from machine C?

(1) 1/5 (2) 10/29 (3) 1/20 (4) 9/29

**8.** Use the network from the lesson: M → F, M → T and (F, T) → L, with P(M) = 1/5, P(F | M) = 1/2, P(F | ¬M) = 1/20, P(T | M) = 3/5, P(T | ¬M) = 1/5, P(L | F, T) = 9/10, P(L | F, ¬T) = 7/10, P(L | ¬F, T) = 1/2 and P(L | ¬F, ¬T) = 1/10. Compute (a) P(L | ¬M), (b) P(T | L) and (c) P(F | T).

**9.** A Boolean Bayesian network has 6 nodes. X1 and X2 are roots; X3 has parents X1 and X2; X4 has parent X3; X5 has parents X3 and X4; X6 has parents X2, X4 and X5. How many CPT entries (independent numbers) does it need? How many would the full joint need?

(1) 19 and 63 (2) 20 and 64 (3) 20 and 63 (4) 18 and 63

**10.** Which of the following statements are correct?

- A. In A → B → C, observing B makes A and C independent.
- B. In A ← B → C, A and C are dependent when B is not observed.
- C. In A → B ← C, observing B makes A and C independent.
- D. In A → B ← C with B → D, observing D can make A and C dependent.
- E. Every node is independent of its non-descendants given its parents.

(1) A, B and C only (2) A, B, D and E only (3) A, D and E only (4) B, C, D and E only

**11.** Rule R1 (CF 0.8): IF a AND b THEN h, with CF(a) = 0.9 and CF(b) = 0.7. Rule R2 (CF 0.6): IF c OR d THEN h, with CF(c) = 0.5 and CF(d) = 0.3. What is the final CF of h?

**12.** Let Θ = {A, B, C}. Evidence 1 gives m₁({A, B}) = 0.8 and m₁(Θ) = 0.2. Evidence 2 gives m₂({B, C}) = 0.6, m₂({A}) = 0.3 and m₂(Θ) = 0.1. Combine them, then give Bel and Pl for {B} and for {A}.

**13.** Match List I with List II.

| List I (Frame feature) | List II (Meaning) |
|---|---|
| A. Default value | I. A procedure run when a value is stored in the slot |
| B. If-needed demon | II. A value assumed unless something more specific overrides it |
| C. If-added demon | III. A constraint on the kind of filler allowed |
| D. Type facet | IV. A procedure run to compute a value when none is stored |

(1) A-II, B-I, C-IV, D-III (2) A-III, B-IV, C-I, D-II (3) A-II, B-IV, C-III, D-I (4) A-II, B-IV, C-I, D-III

**14.** Assertion (A): In a semantic network, the fact “Tweety is a penguin” with the default “birds fly” can lead to a conclusion that must later be withdrawn. Reason (R): Default inheritance in semantic networks is non-monotonic.

(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**15.** Four hypotheses receive two pieces of evidence each (MYCIN combination):

- H1: 0.9 and −0.6
- H2: 0.5 and 0.4
- H3: −0.4 and −0.5
- H4: 0.3 and 0.6

Arrange them by final CF, lowest first.

(1) H3, H2, H1, H4 (2) H3, H4, H2, H1 (3) H3, H2, H4, H1 (4) H2, H3, H4, H1
