# Practice set 10.4: Fuzzy sets and fuzzy logic

15 exam-level problems. Work without notes. Use the standard operations (max, min, 1 − μ) unless a problem says otherwise. Give answers to 4 decimal places where they are not exact.

Use these sets for problems 1 to 3. On X = {x1, x2, x3, x4}:

- A = 0.1/x1 + 0.6/x2 + 0.9/x3 + 0.4/x4
- B = 0.5/x1 + 0.2/x2 + 0.7/x3 + 1.0/x4

**1.** Find A ∪ B, A ∩ B, A′ and (A ∪ B)′. Then find A′ ∩ B′ and state which law your two last answers confirm.

**2.** For A, find: (a) the α-cut at 0.4, (b) the strong α-cut at 0.4, (c) the support, (d) the core, (e) the height, and say whether A is normal, (f) the cardinality |A|.

**3.** At x3, find the algebraic product and the algebraic sum of A and B. At x2, find the bounded sum. At x3, find the bounded difference max(0, a + b − 1).

**4.** R is a relation on X × Y and S on Y × Z:

| R | y1 | y2 |
|---|---|---|
| x1 | 0.8 | 0.3 |
| x2 | 0.5 | 0.9 |

| S | z1 | z2 | z3 |
|---|---|---|---|
| y1 | 0.4 | 0.7 | 1.0 |
| y2 | 0.6 | 0.2 | 0.5 |

Find T = R ∘ S by max–min composition.

**5.** For the same R and S, find R ∘ S by max–product composition, and name every entry where it differs from problem 4.

**6.** Match List I with List II.

| List I (membership function) | List II (key property) |
|---|---|
| A. Triangular | I. Flat top where μ = 1 over an interval |
| B. Trapezoidal | II. Smooth bell, e^(−(x − c)²/(2σ²)) |
| C. Gaussian | III. Rises linearly to a single peak, then falls linearly |
| D. Singleton | IV. μ = 1 at one point only, 0 elsewhere |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-I, C-IV, D-II  (4) A-III, B-II, C-I, D-IV

**7.** Assertion (A): The core of a normal fuzzy set is never empty.
Reason (R): A normal fuzzy set has height 1, so at least one element has membership 1.

(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**8.** A Mamdani controller has input x in [0, 10] with Low: μ(x) = (10 − x)/10 and High: μ(x) = x/10. The output universe is {0, 2, 4, 6, 8, 10} with

| z | 0 | 2 | 4 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|
| Small | 1.0 | 0.8 | 0.5 | 0.2 | 0 | 0 |
| Large | 0 | 0 | 0.2 | 0.5 | 0.8 | 1.0 |

Rules: IF x is Low THEN z is Small; IF x is High THEN z is Large. For x = 3, use min clipping and max aggregation. Find the aggregated set, its centroid and its mean of maxima.

**9.** A first-order Sugeno system has two rules. Rule 1 fires with strength 0.6 and gives z1 = 2x + y. Rule 2 fires with strength 0.2 and gives z2 = x − y + 10. Find the output for x = 3, y = 2.

**10.** (a) Find the centroid of the triangle trimf(z; 1, 3, 8). (b) An aggregated output has μ(z) = 0.4 on [0, 5] and μ(z) = 0.8 on (5, 8]. Find its centroid.

**11.** Which of the following statements are correct?

- A. Every t-norm T satisfies T(a, b) ≤ min(a, b).
- B. The drastic product is the largest t-norm.
- C. max(a, b) is the smallest t-conorm.
- D. The algebraic sum a + b − ab is the De Morgan dual of the algebraic product under the standard complement.
- E. The bounded sum is a t-norm.

(1) A, C and D only  (2) A, B and C only  (3) C, D and E only  (4) A and D only

**12.** For a = 0.5 and b = 0.4, arrange these t-conorm values in increasing order: A. bounded sum, B. max, C. drastic sum, D. algebraic sum.

**13.** On {a, b, c}, the relation Q has rows a: (1, 0.8, 0.4), b: (0.8, 1, 0.5), c: (0.4, 0.5, 1). Is Q reflexive? Symmetric? Max–min transitive? Compute Q ∘ Q and classify Q as a tolerance or an equivalence relation.

**14.** For μA(x) = 0.8, find the membership in: very A, very very A, somewhat A, and the contrast intensification INT(A). Also find INT at μ = 0.3.

**15.** For μA(x) = 0.7 and μB(y) = 0.4, find the value of the implication R(x, y) under: Mamdani min, Larsen product, Łukasiewicz min(1, 1 − a + b) and Zadeh max(min(a, b), 1 − a).
