# Practice set 1.1: Mathematical logic

Time yourself: problems 1–8 in 12 minutes, problems 9–15 in 12 minutes. Every question has four options; choose one.

**1.** Which of the following is a tautology?
(1) (p → q) → (¬p → ¬q)  (2) ((p → q) ∧ (q → r)) → (r → p)  (3) (¬q ∧ (p → q)) → ¬p  (4) (p ∨ q) → p

**2.** In how many rows of its truth table is (p → q) → r false?
(1) 1  (2) 2  (3) 3  (4) 5

**3.** With the order p, q (p most significant), the PDNF of p ↔ q is:
(1) Σm(1, 2)  (2) Σm(0, 3)  (3) Σm(0, 1, 3)  (4) Σm(3)

**4.** With the order p, q, r (p most significant), the PCNF of (p ∧ q) ∨ r is:
(1) ΠM(0, 2, 4)  (2) ΠM(1, 3, 5, 6, 7)  (3) ΠM(0, 1, 2)  (4) ΠM(2, 4, 6)

**5.** Match List I (law) with List II (equivalence).

| List I | List II |
|---|---|
| A. Absorption | I. ¬(p ∧ q) ≡ ¬p ∨ ¬q |
| B. De Morgan | II. (p ∧ q) → r ≡ p → (q → r) |
| C. Exportation | III. p ∨ (p ∧ q) ≡ p |
| D. Distributive | IV. p ∨ (q ∧ r) ≡ (p ∨ q) ∧ (p ∨ r) |

(1) A-III, B-I, C-II, D-IV  (2) A-III, B-II, C-I, D-IV  (3) A-IV, B-I, C-II, D-III  (4) A-I, B-III, C-II, D-IV

**6.** Assertion (A): The set {∧, ∨} is not functionally complete.
Reason (R): Every formula built only from variables with ∧ and ∨ is true when all its variables are true, so ¬p cannot be expressed.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**7.** Statement I: ∃x (P(x) ∧ Q(x)) is logically equivalent to ∃x P(x) ∧ ∃x Q(x).
Statement II: ∀x (P(x) ∧ Q(x)) is logically equivalent to ∀x P(x) ∧ ∀x Q(x).
(1) Both Statement I and Statement II are true  (2) Both Statement I and Statement II are false  (3) Statement I is true but Statement II is false  (4) Statement I is false but Statement II is true

**8.** From the premises p → q, ¬r → ¬q and ¬r, which conclusion follows validly?
(1) p  (2) q  (3) ¬p  (4) r

**9.** Let S(x): x is a student, P(y): y is a problem, Solved(x, y): x solved y. The negation of “Every student solved at least one problem” is:
(1) ∀x (S(x) → ∀y (P(y) → ¬Solved(x, y)))
(2) ∃x (S(x) ∧ ∀y (P(y) → ¬Solved(x, y)))
(3) ∃x (S(x) → ∃y (P(y) ∧ ¬Solved(x, y)))
(4) ∃x (S(x) ∧ ∃y (P(y) ∧ ¬Solved(x, y)))

**10.** Which of the following are equivalent to ¬(p ↔ q)?
A. p ⊕ q  B. p ↔ ¬q  C. (p ∨ q) ∧ ¬(p ∧ q)  D. ¬p ↔ ¬q  E. (p ∧ ¬q) ∨ (¬p ∧ q)
(1) A, B, C and E only  (2) A, C and E only  (3) A, B, C, D and E  (4) B, D and E only

**11.** Domain {1, 2, 3, 4, 5, 6}; D(x, y): x divides y. How many of these are true?
(i) ∃y∀x D(x, y)  (ii) ∀y∃x (x ≠ y ∧ D(x, y))  (iii) ∃x∀y D(x, y)  (iv) ∀x∃y (x ≠ y ∧ D(x, y))
(1) 0  (2) 1  (3) 2  (4) 3

**12.** A truth function f of three variables is self-dual if f(¬p, ¬q, ¬r) = ¬f(p, q, r) for all p, q, r. How many self-dual functions of three variables exist?
(1) 8  (2) 16  (3) 64  (4) 128

**13.** Arrange the connectives from the highest to the lowest precedence under the usual convention.
A. ↔  B. ∧  C. ¬  D. →  E. ∨
(1) C, B, E, D, A  (2) C, E, B, D, A  (3) B, C, E, D, A  (4) C, B, E, A, D

**14.** The clause set {p ∨ q, ¬p ∨ r, ¬q ∨ r} is satisfiable. Which single clause, when added, makes it unsatisfiable?
(1) ¬p  (2) ¬q  (3) ¬r  (4) p ∨ ¬r

**15.** Which formula says “exactly one x has property P”?
(1) ∃x P(x)
(2) ∃x ∀y (P(y) → y = x)
(3) ∃x (P(x) ∧ ∀y (P(y) → y = x))
(4) ∀x ∀y ((P(x) ∧ P(y)) → x = y)
