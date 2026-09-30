# Solutions: Practice set 7.5

**1. (2) 146.** Merges: 1+3 = 4, 4+4 = 8, 8+10 = 18, 12+13 = 25, 15+18 = 33, 25+33 = 58. Total bits = sum of the merge weights = 4 + 8 + 18 + 25 + 33 + 58 = 146. Code lengths: b, c, f 2; a 3; e 4; d and g 5. Check: 15·2 + 12·2 + 13·2 + 10·3 + 4·4 + 3·5 + 1·5 = 146.

**2. (4) 5.** g (1) is merged with d (3), that tree with e (4), then with a (10), then with b (15), then at the root. Five edges from the root: length 5.

**3. (3) 200.** Ratios: P 6, Q 4, R 3, S 2. Take P and Q whole (30 kg, value 140). 20 kg remain, so take 20/30 of R, worth 60. Total 200. Trap: 240 adds P, Q and R whole, which weighs 60 kg.

**4. (4) 170.** Feasible sets: Q + R = 170 (50 kg), P + R = 150 (40 kg), P + Q = 140 (30 kg), Q + S = 130 (45 kg), P + S = 110. Every triple weighs more than 50 kg (P + Q + S = 55 kg, value 190, is the trap). So the answer is Q + R = 170. Ratio-greedy would take P and Q and then nothing else fits (R and S are both too heavy), giving only 140.

**5. (2) 110.** In profit order: J1 → slot 3, J2 → slot 4, J3 (deadline 4) → slot 2, J4 (deadline 2) → slot 1. J5, J6 and J7 find no free slot at or before their deadlines. 35 + 30 + 25 + 20 = 110. Trap: 125 adds J5 as well, ignoring that only four slots exist before deadline 4.

**6. (3) 3.** O, N, E appears in both, in order: ST(O)(N)(E) and L(O)(N)G(E)ST. No common subsequence of length 4 exists.

**7. (2) 124.** p = (2, 3, 6, 4, 5). m[1,2] = 36, m[2,3] = 72, m[3,4] = 120. m[1,3] = min(0 + 72 + 2·3·4, 36 + 0 + 2·6·4) = min(96, 84) = 84. m[2,4] = min(0 + 120 + 3·6·5, 72 + 0 + 3·4·5) = min(210, 132) = 132. m[1,4] = min(0 + 132 + 2·3·5, 36 + 120 + 2·6·5, 84 + 0 + 2·4·5) = min(162, 216, 124) = 124, the order (((A1A2)A3)A4).

**8. (4) 2.** Substitute H → R (RORSE), then delete the second R (ROSE). One edit is not enough, because the lengths differ and the first letters differ as well.

**9. (1) A-II, B-IV, C-I, D-III.** Colouring is backtracking; TSP with reduced cost matrices is LC branch and bound; closest pair is divide and conquer; LCS is DP.

**10. (1).** Fixing the closest unvisited vertex for good is exactly the greedy choice, so R explains A.

**11. (4).** I is false: 0/1 knapsack has optimal substructure, but greedy fails on it. II is true.

**12. (3) 10.** The counts for n = 4, 5, 6 are 2, 10, 4.

**13. (1) A, C and D only.** Prim is greedy; merge sort is divide and conquer.

**14. (2) 1.5.** Root k2: 0.5·1 + 0.2·2 + 0.3·2 = 1.5. Root k3 (with k2 below it and k1 below k2) costs 0.3 + 1.0 + 0.6 = 1.9; root k1 costs even more. The DP minimum is 1.5.

**15. (3) B, A, D, E, C.** Build the queue, remove two, insert their sum, repeat, then read codes.

## Answer key
1-(2), 2-(4), 3-(3), 4-(4), 5-(2), 6-(3), 7-(2), 8-(4), 9-(1), 10-(1), 11-(4), 12-(3), 13-(1), 14-(2), 15-(3)
