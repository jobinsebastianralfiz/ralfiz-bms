# Solutions: practice set 1.8 (Optimization)

**1. Answer (3) 10.5.**
The corners are (0, 0), (3, 0), (2, 2), (1.5, 2.5) and (0, 3). The point (2, 2) comes from 2x + y = 6 and x + y = 4. The point (1.5, 2.5) comes from x + y = 4 and x + 3y = 9.
Z = 0, 6, 10, 10.5, 9, so the maximum is 10.5 at (1.5, 2.5).
Option (4), 12, comes from the point (0, 4), which violates x + 3y ≤ 9.

**2. Answer (2) Z = 12 at (6, 0).**
The corners of the (unbounded) region are (0, 8), (2, 4) and (6, 0), with Z = 24, 16 and 12. The minimum is 12.
The region is unbounded, but Z = 2x + 3y has a finite minimum, so option (4) is wrong.

**3. Answer (1) 20 and 23.**
Iteration 1: x1 enters (−5). The ratios are 8/2 = 4 and 7/1 = 7, so s1 leaves. Now x1 = 4 and Z = 20.
Iteration 2: x2 enters (−3/2). The ratios are 4 ÷ (1/2) = 8 and 3 ÷ (3/2) = 2, so s2 leaves.
The optimum is x1 = 3, x2 = 2, Z = 15 + 8 = 23. The shadow prices are 2 and 1.

**4. Answer (1).**
For a minimisation with ≥ constraints, the dual is a maximisation with ≤ constraints. The right-hand sides (8, 9) become the objective, and the columns of A become the rows.
The primal corners are (0, 9), (2, 3) and (8, 0), with Z = 45, 21 and 24, so the minimum is 21.
The dual optimum is (12/5, 1/5), with W = 96/5 + 9/5 = 21.

**5. Answer (2) 870.**
The NWCR allocations are S1D1 = 35, S1D2 = 25, S1D3 = 10, S2D3 = 15, S2D4 = 5 and S3D4 = 20.
Cost = 210 + 275 + 40 + 90 + 15 + 240 = 870.

**6. Answer (1) 585.**
The allocations in order of cost are:
1. S2D1 = 20 (cost 2; S2 is exhausted)
2. S1D3 = 25 (cost 4)
3. S3D2 = 20 (cost 5; S3 is exhausted)
4. S1D1 = 15 (cost 6)
5. S1D4 = 25 (cost 8)
6. S1D2 = 5 (cost 11)

Cost = 40 + 100 + 100 + 90 + 200 + 55 = 585.

**7. Answer (3) 565.**
Step 1: the penalties are rows 2, 1, 4 and columns 4, 1, 2, 5. The largest is 5 (D4: 8 − 3), so allocate S2D4 = 20. S2 is now exhausted.
Step 2: the penalties are rows S1 = 2 and S3 = 4, and columns D1 = 5, D2 = 6, D3 = 5, D4 = 4. The largest is 6 (D2), so allocate S3D2 = 20. S3 is now exhausted.
Only S1 remains: S1D1 = 35, S1D2 = 5, S1D3 = 25, S1D4 = 5.
Cost = 60 + 100 + 210 + 55 + 100 + 40 = 565.

**8. Answer (2) 555.**
Run MODI on the VAM solution, with u1 = 0:
- v1 = 6, v2 = 11, v3 = 4, v4 = 8, u2 = −5, u3 = −6.
- The empty cells give d(S2D1) = 1, d(S2D2) = 4 − (−5 + 11) = −2, d(S2D3) = 7, d(S3D1) = 11, d(S3D3) = 11 and d(S3D4) = 10.

Enter S2D2 on the loop S2D2 (+), S2D4 (−), S1D4 (+), S1D2 (−). θ = min(20, 5) = 5, so the cost falls by 2 × 5 = 10, to 555.
A new MODI test gives all d > 0, so 555 is the unique optimum.

**9. Answer (3) 23.**
After row and column reduction, the zeros can be covered by 3 lines: row W2 and columns J1 and J4.
The smallest uncovered entry is 1. Adjusting by it creates a zero at W4J3.
The assignment is W3→J4 (5), W1→J1 (5), W4→J3 (9) and W2→J2 (4), for a total of 23. This is confirmed over all 24 permutations.

**10. Answer (1) 23.**
Add a dummy worker W4 with zero costs, so the matrix is 4 × 4. The optimum is W1→J3 (8), W2→J2 (7), W3→J4 (8), and the dummy takes J1 (job J1 is not done).
Total = 23. This is confirmed over all 24 choices.

**11. Answer (3) (3, 3), Z = 27.**
Option (1), (3, 4), violates 5x + y ≤ 18, because 19 > 18.
Among the feasible integer points, (3, 3) gives 15 + 12 = 27. Branch and bound, and full enumeration, confirm it is the best. The points (2, 4) and (1, 5) give 26 and 25.

**12. Answer (1) A-II, B-IV, C-I, D-III.**

**13. Answer (2).**
The dual values are (5/3, 2/3), both positive, so (A) is true. (R) is a true statement of complementary slackness.
But (R) speaks about constraints with positive slack. Here both constraints are tight, and tightness alone does not force a positive dual value. So (R) is not the explanation of (A).

**14. Answer (1) B and C only.**
- A ≥ constraint (B) needs an artificial variable.
- An = constraint (C) needs an artificial variable.
- E must first be multiplied by −1 to make the right-hand side non-negative. That gives −x + y ≤ 3, which needs only a slack. So E needs no artificial variable. Option (2) falls into the trap of reading the ≥ sign without first fixing the sign of the right-hand side.
- A and D are ≤ constraints with non-negative right-hand sides, so they need only slacks.

**15. Answer (1) B, D, A, C.**
1. Start from an IBFS with m + n − 1 cells (B).
2. Solve for the u and v values (D).
3. Evaluate the empty cells (A).
4. If some d_ij < 0, move θ around the loop (C), and repeat from D.
