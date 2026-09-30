# Solutions: practice set 4.6

First, the item counts for the stationery database: Pen 5, Paper 5, Ink 4, Stapler 3; {Ink, Paper} 4, {Paper, Pen} 4, {Ink, Pen} 3, {Ink, Stapler} 2, {Paper, Stapler} 2, {Pen, Stapler} 2; {Ink, Paper, Pen} 3.

**1. Answer (2).** Support{Ink, Paper} = 4/6 = 66.7%. Conf(Paper → Ink) = 4/5 = 80%, because you divide by the count of Paper. Option (1) gives Ink → Paper (4/4 = 100%). Trap: dividing by the wrong side.

**2. Answer (3).**
- L1 = {Ink}, {Paper}, {Pen}, {Stapler}: 4 itemsets, since all counts are at least 3.
- C2 has 6 pairs. L2 = {Ink, Paper} 4, {Ink, Pen} 3, {Paper, Pen} 4. Every pair with Stapler has count 2, so all of them fail.
- Joining on the prefix Ink gives C3 = {Ink, Paper, Pen}. All its 2-subsets are in L2, so it survives the prune. Its count is 3, so L3 = {Ink, Paper, Pen}.
- Total = 4 + 3 + 1 = **8**.

**3. Answer (2).** 3⁶ − 2⁷ + 1 = 729 − 128 + 1 = 602. 729 = 3⁶ has not yet removed the empty sides, and 63 = 2⁶ − 1 counts itemsets.

**4. Answer (1).** Lift = sup(Ink ∪ Paper) / (sup(Ink) × sup(Paper)) = (4/6) / ((4/6)(5/6)) = 6/5 = 1.2. A lift above 1 means positive correlation.

**5. Answer (4).** Π(Lᵢ + 1) = (3 + 1)(2 + 1)(2 + 1) = 4 × 3 × 3 = 36. 8 = 2³ ignores the hierarchies, and 12 = 3 × 2 × 2 forgets "all".

**6. Answer (1).** A-II, B-IV, C-I, D-III. Star = one fact table with flat dimensions. Snowflake = normalised dimensions. Constellation = several fact tables. A factless fact table records events such as attendance.

**7. Answer (1).** Time-variant means the warehouse keeps history, with time as part of the key. That is exactly what A describes, so R explains A.

**8. Answer (2).** Entropy(S) = H(5/8, 3/8) = 0.954. Sunny: H(1/4, 3/4) = 0.811. Cloudy: pure, so 0. Weighted entropy = 0.5 × 0.811 = 0.406. Gain = 0.954 − 0.406 = **0.549**. 0.406 is the weighted entropy, not the gain.

**9. Answer (2).**
- Iteration 1: 2 → centre 1 (distance 1 vs 10). 5 → centre 1 (4 vs 7). 6 → centre 1 (5 vs 6). 11 → centre 12. The clusters are {1, 2, 5, 6} and {11, 12}, with means 3.5 and 11.5.
- Iteration 2: 6 is 2.5 from 3.5 and 5.5 from 11.5, so nothing moves. The final centroids are **3.5 and 11.5**.

**10. Answer (3).** Precision = 45/60 = 0.75. Recall = 45/50 = 0.90. F1 = 2(0.75)(0.90)/(1.65) = 0.818. Accuracy would be 180/200 = 0.90, which is the trap in option (2).

**11. Answer (2).** Semijoin = 300 × 10 + 1,000 × 200 = 3,000 + 200,000 = 203,000 bytes. Shipping all of R = 5,000 × 200 = 1,000,000 bytes. Option (1) forgets the cost of shipping the join column.

**12. Answer (3).** R + W > N gives R > 2, so R = 3. 2PC: 4 messages per participant × 4 participants = 16.

**13. Answer (1).** Selection → Preprocessing → Transformation → Data mining → Interpretation/evaluation, which is C, E, A, D, B.

**14. Answer (2).** SQL:1999 added structured UDTs, REF types and UNDER inheritance, and SQL:2003 added MULTISET. E is nonsense.

**15. Answer (3).** Statement I is true. Statement II is false: a quadtree has four children per node (four quadrants). Eight children describe an octree, which is used for 3D space.
