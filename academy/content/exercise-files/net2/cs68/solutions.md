# Solutions: practice set 10.4 (fuzzy sets and fuzzy logic)

**1.** Work element by element.

| | x1 | x2 | x3 | x4 |
|---|---|---|---|---|
| A ∪ B (max) | 0.5 | 0.6 | 0.9 | 1.0 |
| A ∩ B (min) | 0.1 | 0.2 | 0.7 | 0.4 |
| A′ | 0.9 | 0.4 | 0.1 | 0.6 |
| B′ | 0.5 | 0.8 | 0.3 | 0.0 |
| (A ∪ B)′ | 0.5 | 0.4 | 0.1 | 0.0 |
| A′ ∩ B′ | 0.5 | 0.4 | 0.1 | 0.0 |

(A ∪ B)′ = A′ ∩ B′, so **De Morgan’s law holds** for fuzzy sets with the standard operations. Trap: De Morgan does not fail; only excluded middle and contradiction fail.

**2.** (a) μ ≥ 0.4: **{x2, x3, x4}** (x4 has exactly 0.4, so it is in). (b) μ > 0.4: **{x2, x3}**. (c) Support (μ > 0): **{x1, x2, x3, x4}**. (d) Core (μ = 1): **empty**. (e) Height = **0.9**, so A is **subnormal**. (f) |A| = 0.1 + 0.6 + 0.9 + 0.4 = **2.0**.

**3.** At x3, a = 0.9 and b = 0.7. Product = **0.63**. Algebraic sum = 0.9 + 0.7 − 0.63 = **0.97**. At x2, bounded sum = min(1, 0.6 + 0.2) = **0.8**. At x3, bounded difference = max(0, 0.9 + 0.7 − 1) = **0.6**. Check the order at x3: 0.6 ≤ 0.63 ≤ min 0.7.

**4.** Row of R with column of S, mins then max.

- T(x1, z1) = max(min(0.8, 0.4), min(0.3, 0.6)) = max(0.4, 0.3) = 0.4
- T(x1, z2) = max(min(0.8, 0.7), min(0.3, 0.2)) = max(0.7, 0.2) = 0.7
- T(x1, z3) = max(min(0.8, 1.0), min(0.3, 0.5)) = max(0.8, 0.3) = 0.8
- T(x2, z1) = max(min(0.5, 0.4), min(0.9, 0.6)) = max(0.4, 0.6) = 0.6
- T(x2, z2) = max(min(0.5, 0.7), min(0.9, 0.2)) = max(0.5, 0.2) = 0.5
- T(x2, z3) = max(min(0.5, 1.0), min(0.9, 0.5)) = max(0.5, 0.5) = 0.5

**T = [0.4 0.7 0.8 ; 0.6 0.5 0.5]** (2 × 3, as (2 × 2) ∘ (2 × 3) must be).

**5.** Products, then max.

- (x1, z1): max(0.32, 0.18) = **0.32**; (x1, z2): max(0.56, 0.06) = **0.56**; (x1, z3): max(0.80, 0.15) = **0.8**
- (x2, z1): max(0.20, 0.54) = **0.54**; (x2, z2): max(0.35, 0.18) = **0.35**; (x2, z3): max(0.50, 0.45) = **0.5**

It differs from max–min at (x1, z1), (x1, z2), (x2, z1) and (x2, z2); it is equal at (x1, z3) and (x2, z3). Every max–product entry is ≤ the max–min entry, because ab ≤ min(a, b).

**6.** Answer **(1) A-III, B-I, C-II, D-IV**. Triangle = single linear peak; trapezoid = flat top; Gaussian = smooth bell; singleton = one point.

**7.** Answer **(1)**. Normal means height 1, so some element has μ = 1 and the core is not empty. R states exactly this reason.

**8.** Fuzzify x = 3: μLow = 0.7, μHigh = 0.3. Clip Small at 0.7 and Large at 0.3, then take the max:

| z | 0 | 2 | 4 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|
| Small clipped at 0.7 | 0.7 | 0.7 | 0.5 | 0.2 | 0 | 0 |
| Large clipped at 0.3 | 0 | 0 | 0.2 | 0.3 | 0.3 | 0.3 |
| Aggregate (max) | 0.7 | 0.7 | 0.5 | 0.3 | 0.3 | 0.3 |

Centroid = (0.7×0 + 0.7×2 + 0.5×4 + 0.3×6 + 0.3×8 + 0.3×10) / (0.7 + 0.7 + 0.5 + 0.3 + 0.3 + 0.3) = (0 + 1.4 + 2 + 1.8 + 2.4 + 3) / 2.8 = 10.6 / 2.8 = **3.7857**. The maximum 0.7 occurs at z = 0 and z = 2, so MOM = **1**. Trap: dividing 10.6 by 6 points gives a wrong 1.77.

**9.** z1 = 2×3 + 2 = 8. z2 = 3 − 2 + 10 = 11. Output = (0.6×8 + 0.2×11) / (0.6 + 0.2) = (4.8 + 2.2) / 0.8 = 7 / 0.8 = **8.75**.

**10.** (a) Triangle centroid = (1 + 3 + 8)/3 = **4**. (b) Area = 0.4×5 + 0.8×3 = 2 + 2.4 = 4.4. Moment = 0.4×(25 − 0)/2 + 0.8×(64 − 25)/2 = 5 + 15.6 = 20.6. Centroid = 20.6/4.4 = **4.6818**.

**11.** Answer **(1) A, C and D only**. A is true (min is the largest t-norm). B is false: the drastic product is the smallest. C is true. D is true: 1 − (1 − a)(1 − b) = a + b − ab. E is false: the bounded sum is a t-conorm.

**12.** max = 0.5; algebraic sum = 0.5 + 0.4 − 0.2 = 0.7; bounded sum = min(1, 0.9) = 0.9; drastic sum = 1 (neither value is 0). Increasing order: **B, D, A, C**.

**13.** Diagonal is all 1, so Q is **reflexive**. Q(a, b) = Q(b, a) and so on, so Q is **symmetric**. Q ∘ Q:

| Q ∘ Q | a | b | c |
|---|---|---|---|
| a | 1 | 0.8 | 0.5 |
| b | 0.8 | 1 | 0.5 |
| c | 0.5 | 0.5 | 1 |

(Q ∘ Q)(a, c) = max(min(1, 0.4), min(0.8, 0.5), min(0.4, 1)) = 0.5 > Q(a, c) = 0.4, so Q ∘ Q ⊄ Q and Q is **not max–min transitive**. Q is a **tolerance** relation, not an equivalence relation. Q ∘ Q is transitive, so it is the equivalence relation reached in n − 1 = 2 steps.

**14.** very = 0.8² = **0.64**; very very = 0.8⁴ = **0.4096**; somewhat = √0.8 = **0.8944**. Since 0.8 > 0.5, INT = 1 − 2(1 − 0.8)² = 1 − 0.08 = **0.92**. At 0.3 (≤ 0.5), INT = 2 × 0.3² = **0.18**. INT pushes values away from 0.5.

**15.** Mamdani: min(0.7, 0.4) = **0.4**. Larsen: 0.7 × 0.4 = **0.28**. Łukasiewicz: min(1, 1 − 0.7 + 0.4) = **0.7**. Zadeh: max(min(0.7, 0.4), 1 − 0.7) = max(0.4, 0.3) = **0.4**.
