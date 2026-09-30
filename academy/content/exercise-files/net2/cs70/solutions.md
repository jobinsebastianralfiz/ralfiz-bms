# Solutions 10.6: Artificial neural networks and machine learning basics

Every number below was recomputed by the verification script (numpy for the forward and backward passes, exact perceptron and Hebb traces, the Hopfield matrix and energies, the SOM distances, Q-learning and k-means).

**1.** net = 0.5 × 1 − 0.4 × 0 + 0.2 × 1 − 0.1 = **0.6**, so y = 1 and t − y = −1. w ← w + 0.1 × (−1) × (1, 0, 1) = **(0.4, −0.4, 0.1)**; b ← −0.1 − 0.1 = **−0.2**. The middle weight does not change because x2 = 0.

**2.**

| End of epoch | w1, w2, b | Errors in the epoch |
|---|---|---|
| 1 | −1, −1, 0 | 2 |
| 2 | −2, −1, 1 | 3 |
| 3 | −2, −1, 2 | 3 |
| 4 | −2, −2, 2 | 2 |
| 5 | −2, −1, 3 | 1 |
| 6 | −2, −1, 3 | 0 |

Training stops in **epoch 6** with **w1 = −2, w2 = −1, b = 3**. Check: net = −2x1 − x2 + 3 is 3, 2, 1 and 0 for the four inputs, and only the last is not > 0, so the output is 1, 1, 1, 0 = NAND. The trap is the strict “net > 0”: at net = 0 the output is 0.

**3.** Answer (1). The boundary 3x1 + 2x2 − 6 = 0 meets x2 = 0 at x1 = 6/3 = 2 and x1 = 0 at x2 = 6/2 = 3, so Statement I is true. Statement II is true: only XOR and XNOR are not linearly separable, so 14 of 16 are.

**4.** net = 0.6 − 0.4 − 0.1 + 0.1 = **0.2**.
- (a) Step: **1**.
- (b) σ(0.2) = **0.5498**.
- (c) tanh(0.2) = **0.1974**.
- (d) ReLU: **0.2**.

**5.** It fires when 2x1 + x2 + x3 ≥ 3, which happens for **(1,0,1), (1,1,0) and (1,1,1)** and never when x1 = 0 (the most it can reach then is 2). The function is **x1 ∧ (x2 ∨ x3)**.

**6.**
- Forward: net(h1) = 0.4 − 0.3 = 0.1, h1 = σ(0.1) = **0.5250**. net(h2) = 0.1 + 0.2 = 0.3, h2 = σ(0.3) = **0.5744**. net(o) = 0.6 × 0.5250 − 0.5 × 0.5744 + 0.1 = 0.1278, o = **0.5319**. E = ½(0 − 0.5319)² = **0.1415**.
- Output delta: δo = (0 − 0.5319) × 0.5319 × 0.4681 = **−0.1324**.
- Hidden deltas (old output weights): δh1 = 0.5250 × 0.4750 × 0.6 × (−0.1324) = **−0.0198**; δh2 = 0.5744 × 0.4256 × (−0.5) × (−0.1324) = **0.0162**.
- Output layer: w(h1→o) = 0.6 − 0.1324 × 0.5250 = **0.5305**; w(h2→o) = −0.5 − 0.1324 × 0.5744 = **−0.5761**; b(o) = 0.1 − 0.1324 = **−0.0324**.
- Hidden layer: x1 = 0, so the weights from x1 stay at 0.2 and −0.3. w(x2→h1) = 0.4 − 0.0198 = **0.3802**; w(x2→h2) = 0.1 + 0.0162 = **0.1162**; b(h1) = **−0.3198**; b(h2) = **0.2162**.

The target is 0 and the output 0.53 is too high, so the weight from the positive-weighted h1 falls and the negative weight from h2 becomes more negative.

**7.**
- δ1 = (1 − 0.8) × 0.8 × 0.2 = **0.032**; δ2 = (0 − 0.4) × 0.4 × 0.6 = **−0.096**.
- δh1 = 0.5 × 0.5 × (0.3 × 0.032 + (−0.2) × (−0.096)) = 0.25 × 0.0288 = **0.0072**.
- δh2 = 0.9 × 0.1 × (0.6 × 0.032 + 0.4 × (−0.096)) = 0.09 × (−0.0192) = **−0.001728**.

**8.** w1 = Σ x1·t = −1 + 1 − 1 − 1 = **−2**; w2 = −1 − 1 + 1 − 1 = **−2**; b = −1 + 1 + 1 + 1 = **2**. The nets are −2, 2, 2 and 6, so sign(net) = −1, 1, 1, 1 = NAND.

**9.**
- Step 1: net = 0.2 − 0.1 + 0.1 = **0.2**, t − net = 0.8. w = (0.2 + 0.08, −0.1 + 0.08) = **(0.28, −0.02)**; b = **0.18**.
- Step 2: net = 0.28 + 0.02 + 0.18 = **0.48**, t − net = −1.48. Δw = 0.1 × (−1.48) × (1, −1) = (−0.148, 0.148). w = **(0.132, 0.128)**; b = 0.18 − 0.148 = **0.032**.

The delta rule keeps adjusting even when the sign is already right (step 1): it minimises squared error, not misclassifications.

**10.**
- (a) The two outer products cancel off the anti-diagonal:

        W = |  0   0   0  -2 |
            |  0   0  -2   0 |
            |  0  -2   0   0 |
            | -2   0   0   0 |

- (b) W p1 = (2, 2, −2, −2), whose signs are p1; W p2 = (2, −2, 2, −2), whose signs are p2. Both are stable.
- (c) Unit 4: net = −2 × s1 = **−2**, so s4 = −1 and the state becomes **(1, 1, −1, −1) = p1**.
- (d) E(s) = **0** before and E(p1) = **−4** after. The update lowered the energy.

Caution: the order of updates matters. If unit 1 were updated first (its net is also −2), the state would become (−1, 1, −1, 1) = −p2, the complement of a stored pattern, which is also stable. That is one of the spurious states.

**11.** Squared distances: 0.25 + 0.25 = 0.50; 0.04 + 0.04 = 0.08; 0.01 + 0.01 = **0.02**; 0.09 + 0.09 = 0.18. The winner is **unit 3**, and its neighbours are units 2 and 4.
- w2 = (0.4, 0.6) + 0.4 × (0.2, −0.2) = **(0.48, 0.52)**
- w3 = (0.7, 0.3) + 0.4 × (−0.1, 0.1) = **(0.66, 0.34)**
- w4 = (0.9, 0.1) + 0.4 × (−0.3, 0.3) = **(0.78, 0.22)**
- w1 is not a neighbour and stays at (0.1, 0.9).

**12.** Answer (2), **A-III, B-I, C-II, D-IV**. Option (1) swaps the perceptron and delta rules, the classic trap.

**13.**
- (a) First update: Q = 0 + 0.2 × (5 + 0.9 × 10 − 0) = **2.8**. Second: Q = 2.8 + 0.2 × (−1 + 9 − 2.8) = 2.8 + 0.2 × 5.2 = **3.84**.
- (b) Answer (1). The agent is never told the correct action; it only receives rewards (R), which is exactly why no labelled pairs are needed (A).

**14.**
- (a) Every point in the first group is nearer to (1,1) and every point in the second nearer to (5,6). New centroids: ((1 + 2 + 1)/3, (1 + 1 + 2)/3) = **(1.3333, 1.3333)** and ((6 + 7 + 5)/3, (5 + 6 + 6)/3) = **(6, 5.6667)**. A second iteration assigns the points the same way, so the algorithm has **converged**.
- (b) Accuracy = 80/100 = **0.8**. Precision = 45/50 = **0.9**. Recall = 45/60 = **0.75**. F1 = 2 × 0.9 × 0.75/1.65 = **0.8182**. Specificity = 35/40 = **0.875**.

**15.** Answer (2), **A, B, D and E**. C is false: Hopfield self-connections are 0. E: (784 + 1) × 128 + (128 + 1) × 10 = 100,480 + 1,290 = 101,770.
