# Solutions 1.1: Mathematical logic

**1. Answer: (3)**
(¬q ∧ (p → q)) → ¬p is modus tollens. To falsify it we need ¬p false (p = T) and ¬q ∧ (p → q) true, so q = F and p → q true; but p = T, q = F makes p → q false. No falsifying row exists. (1) is the inverse fallacy (false at p = F, q = T); (2) is false at p = F, q = F, r = T; (4) is false at p = F, q = T.

**2. Answer: (3)**
(p → q) → r is false when p → q is true and r is false. p → q is true in 3 of the 4 (p, q) rows, and r = F is one choice, so 3 × 1 = 3 false rows.

**3. Answer: (2)**
p ↔ q is true at 00 (row 0) and 11 (row 3): Σm(0, 3). Σm(1, 2) is p ⊕ q.

**4. Answer: (1)**
(p ∧ q) ∨ r is false when r = F and p ∧ q = F: rows 000 (0), 010 (2), 100 (4). So ΠM(0, 2, 4) = (p ∨ q ∨ r) ∧ (p ∨ ¬q ∨ r) ∧ (¬p ∨ q ∨ r). Option (2) lists the true rows.

**5. Answer: (1)**
Absorption is p ∨ (p ∧ q) ≡ p (III); De Morgan is I; exportation is II; distribution of ∨ over ∧ is IV: A-III, B-I, C-II, D-IV.

**6. Answer: (1)**
Any formula using only ∧ and ∨ outputs T when every input is T (induction on the formula). ¬p outputs F at p = T, so it cannot be built, and the set is incomplete. R is exactly the reason.

**7. Answer: (4)**
Statement I fails: in domain {1, 2} with P true only at 1 and Q true only at 2, the right side is true and the left side is false. Only the one-way implication ∃x (P ∧ Q) ⇒ ∃x P ∧ ∃x Q holds. Statement II is the genuine distribution of ∀ over ∧.

**8. Answer: (3)**
¬r and ¬r → ¬q give ¬q (modus ponens). ¬q and p → q give ¬p (modus tollens). Brute force confirms that the only row satisfying all premises is p = q = r = F, where ¬p holds and p, q, r are all false.

**9. Answer: (2)**
Original: ∀x (S(x) → ∃y (P(y) ∧ Solved(x, y))). Negate: ∃x (S(x) ∧ ¬∃y (P(y) ∧ Solved(x, y))) = ∃x (S(x) ∧ ∀y (P(y) → ¬Solved(x, y))): some student solved no problem. (1) says no student solved any problem, which is stronger. (4) says some student left some problem unsolved, which is weaker.

**10. Answer: (1)**
¬(p ↔ q) is true exactly when p and q differ. A, B, C and E all have that truth table. D, ¬p ↔ ¬q, is equivalent to p ↔ q itself.

**11. Answer: (2)**
(i) needs a y in {1, …, 6} divisible by 1 to 6, a multiple of 60: false. (ii) fails for y = 1, which has no other divisor: false. (iii) x = 1 divides every y: true. (iv) fails for x = 4 (8 is outside the domain), and also for 5 and 6: false. One statement is true.

**12. Answer: (2)**
The 8 rows pair up into 4 complementary pairs (a row and its bitwise complement). Self-duality fixes the value on the second row of each pair once the first is chosen, so there are 2⁴ = 16 self-dual functions. In general there are 2^(2^(n−1)).

**13. Answer: (1)**
¬ binds tightest, then ∧, then ∨, then →, then ↔: C, B, E, D, A.

**14. Answer: (3)**
Resolving p ∨ q with ¬p ∨ r gives q ∨ r; resolving that with ¬q ∨ r gives r. Adding ¬r then yields the empty clause. Brute force: the original set is satisfiable, and with ¬r it has no model. Adding ¬p or ¬q leaves models (for example p = F, q = T, r = T).

**15. Answer: (3)**
“At least one” (P(x)) and “at most one” (every y with P(y) equals x). (2) is also true when nothing has P (if the domain is non-empty); (4) says “at most one”; (1) says “at least one”.
