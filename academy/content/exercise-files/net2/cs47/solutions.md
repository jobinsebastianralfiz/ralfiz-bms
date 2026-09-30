# Solutions cs47

1. Pass 1: 7 33 19 2 25 41. Pass 2: 7 19 2 25 33 41. Pass 3: 7 2 19 25 33 41. Pass 4: 2 7 19 25 33 41. Pass 5: no swap, stop.
   **5 passes, 10 swaps** (the array has 10 inversions); 15 comparisons.

2. Pass 1: 7 41 33 19 2 25. Pass 2: 7 33 41 19 2 25. Pass 3: **7 19 33 41 2 25**. Pass 4: 2 7 19 33 41 25. Pass 5: 2 7 19 25 33 41.
   Comparisons: 1 + 2 + 3 + 4 + 3 = **13** (10 shifts).

3. Pass 1: swap 2 and 41 → 2 7 33 19 41 25. Pass 2: 7 is already in place → **2 7 33 19 41 25**. Pass 3: swap 19 and 33 → 2 7 19 33 41 25. Pass 4: swap 25 and 33 → 2 7 19 25 41 33. Pass 5: swap 33 and 41.
   **4 swaps.**

4. Pivot 30. Keys ≤ 30 in order of discovery: 12, 7, 21. After the scan: 12 7 21 36 44 58 63 30 (i = 2); the pivot swaps with a[3] = 36.
   Result **12 7 21 30 44 58 63 36**; the pivot is at index **3**.

5. Runs of 2: 12 36 | 7 58 | 21 44 | 30 63 (4 comparisons). Runs of 4: 7 12 36 58 | 21 30 44 63 (3 + 3 = 6 comparisons). Final: 7 12 21 30 36 44 58 63 (7 comparisons).
   Total **17** comparisons.

6. Units: **580 71 42 263 305 17 8 919**. Tens: **305 8 17 919 42 263 71 580**. Hundreds: **8 17 42 71 263 305 580 919**.

7. Counts (0..5): **2 0 2 3 0 1**. Cumulative: **2 2 4 7 7 8**. Output: **0 0 2 2 3 3 3 5**.

8. (a) mid 5 (37) → right; mid 8 (60) → found. Compared with **37 and 60**.
   (b) Draw the decision tree for indices 0–9 with mid = ⌊(lo + hi)/2⌋: 1 key at depth 1 (index 4), 2 at depth 2 (indices 1, 7), 4 at depth 3 (0, 2, 5, 8) and 3 at depth 4 (3, 6, 9). Total 1 + 4 + 12 + 12 = 29 comparisons, average **2.9**.

9. 43→3, 36→6, 92→2, 87→7, 11→1, 4→4. 71 (home 1) probes 1, 2, 3, 4, 5 → slot 5 (**5 probes**). 13 (home 3) probes 3–8 → slot 8 (**6 probes**). 14 (home 4) probes 4–9 → slot 9 (**6 probes**).
   Table: **– 11 92 43 4 71 36 87 13 14** (slot 0 empty).

10. First six keys as before. 71: 1, 2, 5 → slot 5 (3 probes). 13: 3, 4, 7, 12 mod 10 = 2, 19 mod 10 = 9 → slot 9 (5 probes). 14: 4, 5, 8 → slot 8 (3 probes).
    Table: **– 11 92 43 4 71 36 87 14 13**.

11. 20→7. 46: home 7, step 3 → 10. 33: home 7, step 2 → 9. 59: home 7, step 4 → 11. 72: home 7, step 5 → 12. 11: home 11, step 3 → 14 mod 13 = 1. 85: home 7, step 6 → 13 mod 13 = 0. 24: home 11, step 4 → 15 mod 13 = 2.
    Table (slots 0–12): **85 11 24 – – – – 20 – 33 46 59 72**.

12. (a) ½(1 + 1/0.01) = **50.5**. (b) ½(1 + 10) = **5.5**. (c) 1/0.1 = **10**. (d) (1/0.9)·ln 10 ≈ **2.56**.

13. A: ⌊log₂ 1000⌋ + 1 = 10 (III). B: ⌈log₂ 120⌉ = 7 (I). C: Θ(n²) (II). D: ⌈3·10/2⌉ − 2 = 13 (IV). Answer **(1)**.

14. Both true, and R explains A: every partition peels off only the pivot, so the costs are (n − 1) + (n − 2) + … + 1 = n(n − 1)/2. Answer: **Both (A) and (R) are true and (R) is the correct explanation of (A)**.

15. The merge takes 3, 5, 8, 9, 10, 12, 20 using 7 comparisons, then copies 25 and 30 without comparing. out = 3 5 8 9 10 12 20 25 30. Output: **7 10 25** (verified with gcc). Merging 4 + 5 keys needs at most 8 comparisons; here it needed 7 because x ran out first.
