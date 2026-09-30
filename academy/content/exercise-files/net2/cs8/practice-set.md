# Practice set 1.8: Optimization

Time yourself: problems 1–8 in 14 minutes, problems 9–15 in 12 minutes. Every question has four options; choose one.

**1.** Maximise Z = 2x + 3y subject to x + y ≤ 4, 2x + y ≤ 6, x + 3y ≤ 9, x, y ≥ 0. The optimal value of Z is:
(1) 9  (2) 10  (3) 10.5  (4) 12

**2.** Minimise Z = 2x + 3y subject to x + y ≥ 6, 2x + y ≥ 8, x, y ≥ 0. The optimum is:
(1) Z = 16 at (2, 4)  (2) Z = 12 at (6, 0)  (3) Z = 24 at (0, 8)  (4) The problem is unbounded

**3.** Maximise Z = 5x1 + 4x2 subject to 2x1 + x2 ≤ 8, x1 + 2x2 ≤ 7, x ≥ 0, by simplex starting from the slack basis. The value of Z after the first iteration and the optimal Z are:
(1) 20 and 23  (2) 16 and 23  (3) 20 and 25  (4) 14 and 20

**4.** The primal is: minimise Z = 3x1 + 5x2 subject to x1 + 2x2 ≥ 8, 3x1 + x2 ≥ 9, x ≥ 0. Its dual and the common optimal value are:
(1) Maximise W = 8y1 + 9y2 subject to y1 + 3y2 ≤ 3, 2y1 + y2 ≤ 5, y ≥ 0; value 21
(2) Maximise W = 3y1 + 5y2 subject to y1 + 2y2 ≤ 8, 3y1 + y2 ≤ 9, y ≥ 0; value 21
(3) Maximise W = 8y1 + 9y2 subject to y1 + 3y2 ≤ 3, 2y1 + y2 ≤ 5, y ≥ 0; value 24
(4) Minimise W = 8y1 + 9y2 subject to y1 + 3y2 ≥ 3, 2y1 + y2 ≥ 5, y ≥ 0; value 21

Problems 5–8 use this transportation problem (rows S1–S3, columns D1–D4):

| | D1 | D2 | D3 | D4 | Supply |
|---|---|---|---|---|---|
| S1 | 6 | 11 | 4 | 8 | 70 |
| S2 | 2 | 4 | 6 | 3 | 20 |
| S3 | 11 | 5 | 9 | 12 | 20 |
| Demand | 35 | 25 | 25 | 25 | 110 |

**5.** The total cost of the North-West Corner Rule solution is:
(1) 585  (2) 870  (3) 840  (4) 565

**6.** The total cost of the Least Cost Method solution is:
(1) 585  (2) 565  (3) 555  (4) 600

**7.** The total cost of the Vogel's approximation method solution is:
(1) 555  (2) 585  (3) 565  (4) 575

**8.** The optimal total cost (after MODI) is:
(1) 545  (2) 555  (3) 560  (4) 565

**9.** Assign workers W1–W4 to jobs J1–J4 at minimum cost. Cost matrix (rows W1–W4): W1: 5 17 19 5; W2: 19 4 3 12; W3: 20 11 16 5; W4: 8 12 9 10. The minimum cost is:
(1) 21  (2) 22  (3) 23  (4) 25

**10.** Three workers must do three of four jobs (one job each; one job is left undone). Costs (rows W1–W3, columns J1–J4): W1: 10 12 8 11; W2: 9 7 13 10; W3: 12 11 9 8. The minimum total cost is:
(1) 23  (2) 24  (3) 25  (4) 26

**11.** Maximise Z = 5x + 4y subject to x + 2y ≤ 11, 5x + y ≤ 18, x, y ≥ 0 and integer. The LP relaxation optimum is (25/9, 37/9). The optimal integer solution is:
(1) (3, 4), Z = 31  (2) (2, 4), Z = 26  (3) (3, 3), Z = 27  (4) (1, 5), Z = 25

**12.** Match List I with List II.

| List I (graphical outcome) | List II (cause) |
|---|---|
| A. Infeasible | I. Objective line parallel to a binding edge |
| B. Unbounded | II. Constraints have no common point |
| C. Alternative optima | III. A constraint that does not change the feasible region |
| D. Redundant constraint | IV. Region open in the direction in which Z improves |

(1) A-II, B-IV, C-I, D-III  (2) A-IV, B-II, C-I, D-III  (3) A-II, B-IV, C-III, D-I  (4) A-II, B-I, C-IV, D-III

**13.** Assertion (A): At the optimum of the problem in Example 3 of the lesson (max 4x1 + 3x2, 2x1 + x2 ≤ 10, x1 + 2x2 ≤ 8), both dual variables are positive.
Reason (R): By complementary slackness, if a primal constraint has positive slack at the optimum, its dual variable is zero.
(1) Both true and (R) is the correct explanation of (A)
(2) Both true but (R) is NOT the correct explanation of (A)
(3) (A) true, (R) false
(4) (A) false, (R) true

**14.** Which of the following require an artificial variable when setting up the initial simplex tableau?
A. x + y ≤ 10  B. 2x + y ≥ 4  C. x + 3y = 9  D. −x + y ≤ 2  E. x − y ≥ −3 (with a negative right-hand side)
(1) B and C only  (2) B, C and E only  (3) A, B and C only  (4) B only

**15.** Arrange the steps of the MODI method in the correct order:
A. Compute d_ij = c_ij − (u_i + v_j) for every empty cell
B. Obtain an initial basic feasible solution with m + n − 1 allocations
C. Form a closed loop from the entering cell and shift θ units around it
D. Find u_i and v_j from u_i + v_j = c_ij for occupied cells, taking u_1 = 0
(1) B, D, A, C  (2) D, B, A, C  (3) B, A, D, C  (4) B, D, C, A
