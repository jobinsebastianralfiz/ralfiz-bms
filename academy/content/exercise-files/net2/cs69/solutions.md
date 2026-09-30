# Solutions: practice set 10.5 (genetic algorithms)

**1.** Decode the strings, square, and divide.

| String | x | f = x² | p = f/Σf | Expected count f/f̄ |
|---|---|---|---|---|
| 01011 | 11 | 121 | 0.0971 | 0.3884 |
| 10100 | 20 | 400 | 0.3210 | 1.2841 |
| 00111 | 7 | 49 | 0.0393 | 0.1573 |
| 11010 | 26 | 676 | 0.5425 | 2.1701 |

Σf = 1246 and f̄ = 311.5. Check: the probabilities add to 1 and the expected counts add to 4.

**2.** Σf = 100, so the probabilities are 0.08, 0.22, 0.14, 0.36, 0.20 and the cumulative values are 0.08, 0.30, 0.44, 0.80, 1.00.

| r | 0.07 | 0.31 | 0.44 | 0.93 | 0.66 |
|---|---|---|---|---|---|
| Selected | 1 | 3 | 4 | 5 | 4 |

Trap: r = 0.44 equals the cumulative value of individual 3. Under the stated rule (strictly greater), it selects individual **4**.

**3.** Pointers 0.05, 0.25, 0.45, 0.65, 0.85 select **1, 2, 4, 4, 5**. Individual 4 (expected count 1.8) gets two copies; individual 3 (expected 0.7) gets none.

**4.** P1 = 110010|1101, P2 = 001101|0110. Children: **1100100110** and **0011011101**.

**5.** P1 = 11|00101|101, P2 = 00|11010|110. Swap the middles: **1111010101** and **0000101110**.

**6.** Mask 1 0 1 0 0 1 1 0 0 1. Child 1 takes P1 where the mask is 1 and P2 where it is 0: **1001001111**. Child 2 takes the opposite: **0110110100**. Check: at each position the two children hold the two parent bits.

**7.** Fixed positions are 1, 4, 5 and 7. (a) o(H) = **4**. (b) δ(H) = 7 − 1 = **6**. (c) 2^(8 − 4) = **16** strings. (d) 1 − 0.8 × 6/7 = **0.3143**. (e) 0.995⁴ = **0.9801** (the approximation 1 − 4 × 0.005 = 0.98).

**8.** m(H, t + 1) ≥ 20 × (15/10) × [1 − 0.9 × 2/9 − 2 × 0.01] = 30 × [1 − 0.2 − 0.02] = 30 × 0.78 = **23.4**. The schema is expected to grow because it is short, low-order and above average.

**9.** (a) d = 128 + 64 + 8 = 200. x = 2 + 3 × 200/255 = **4.3529**. Trap: dividing by 256 gives 4.3438. (b) Values needed = 5 × 100 + 1 = 501. 2⁸ = 256 is too few and 2⁹ = 512 is enough, so **9 bits**.

**10.** Binary 0110 → Gray: 0, 0⊕1 = 1, 1⊕1 = 0, 1⊕0 = 1, giving **0101**. Gray 1011 → binary: 1, 1⊕0 = 1, 1⊕1 = 0, 0⊕1 = 1, giving **1101**.

**11.** Answer **(1) A-III, B-IV, C-II, D-I**. Selection exploits fitness; crossover recombines; mutation brings diversity; elitism preserves the best.

**12.** Answer **(1)**. Selection only makes copies, so the set of distinct strings can only shrink. R is exactly the reason for A.

**13.** (a) The best wins if it is drawn at least once: 1 − (19/20)³ = 1 − 0.857375 = **0.1426** (0.142625). (b) The worst wins only if all three draws pick it: (1/20)³ = **0.000125**.

**14.** The segment is positions 3 to 5 of P1: 6 8 1.

(a) OX: read P2 from position 6, wrapping: 6 7 8 1 2 3 4 5. Remove 6, 8, 1 to get 7 2 3 4 5. Fill positions 6, 7, 8, 1, 2: child = **4 5 6 8 1 7 2 3**.

(b) PMX: the mapping is 6↔3, 8↔4, 1↔5. Copy P2 outside the segment: position 1 gets 1, which clashes and maps to 5; position 2 gets 2; position 6 gets 6, which clashes and maps to 3; position 7 gets 7; position 8 gets 8, which clashes and maps to 4. Child = **5 2 6 8 1 3 7 4**.

**15.** Answer **(1) B, C and D only**. B is the theorem’s message. The mutation loss o·pm grows with the order (C), and the crossover loss pc·δ/(L − 1) grows with the defining length (D). A is false: it is a lower bound for one generation, not a convergence proof. E is false: the theorem ignores schemata gained through crossover, which is why it is an inequality.
