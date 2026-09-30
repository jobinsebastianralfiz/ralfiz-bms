# Solutions: Deadlocks practice set

Convention: when several processes can run, we take the lowest-numbered one and restart the scan. Other valid safe sequences are also correct answers.

**1.** Need = Max − Allocation: P0 (2,2,0,1), P1 (1,1,1,1), P2 (1,0,1,1), P3 (2,1,2,0), P4 (1,1,1,1).
Total = Available + column sums of Allocation = (1,0,1,1) + (4,3,4,3) = **(5, 3, 5, 4)**.
Work = (1,0,1,1). P0 and P1 need B ≥ 1, but B = 0. P2 (1,0,1,1) fits → Work = (3,1,1,2).
P0 needs B = 2 > 1. P1 (1,1,1,1) fits → Work = (3,2,2,2). P0 (2,2,0,1) fits → Work = (4,2,4,3). P3 (2,1,2,0) fits → Work = (4,2,5,4). P4 fits → Work = (5,3,5,4) = Total.
**Safe: P2, P1, P0, P3, P4.** (This state has 10 safe sequences, and all start with P2.)

**2.** (1,0,0,0) ≤ Need P2 (1,0,1,1) ✓ and ≤ Available (1,0,1,1) ✓. Pretend: Available = (0,0,1,1), Allocation P2 = (3,1,0,1), Need P2 = (0,0,1,1).
Work = (0,0,1,1): P2 fits → (3,1,1,2); P1 → (3,2,2,2); P0 → (4,2,4,3); P3 → (4,2,5,4); P4 → (5,3,5,4). **Safe, so it is granted** (sequence P2, P1, P0, P3, P4).

**3.** P4 (1,0,0,0): ≤ Need (1,1,1,1) ✓, ≤ Available ✓. Pretend: Available = (0,0,1,1), Need P4 = (0,1,1,1). Work = (0,0,1,1): P0 needs A; P1 needs A, B; P2 needs A = 1 > 0; P3 needs A; P4 needs B. Nobody fits: **unsafe, P4 waits.**
P1 (0,1,0,0): ≤ Need ✓ but B available = 0, so **P1 waits because the resource is not available** (no safety check needed).

**4.** Work = (0,0,0). P2's request is 0 → Work = (0,0,1). P0 wants B (held by P1, P3); P1 wants A (held by P0); P3 wants 2 more C but only 1 is free; P4 wants A. No other request fits. **Deadlocked: P0, P1, P3, P4.**
With P3 requesting (0,0,1): after P2, Work = (0,0,1) → P3 finishes → (0,1,2) → P0 → (1,1,2) → P1 → (1,2,2) → P4. **No deadlock.**

**5.** Minimum = (1 + 2 + 3 + 4) + 1 = **11**. Largest number that can still deadlock = **10**.

**6.** n(5 − 1) + 1 ≤ 20 → 4n ≤ 19 → **n = 4**.

**7.** 4(k − 1) + 1 ≤ 15 → k − 1 ≤ 3.5 → **k = 4**.

**8.** Available = 12 − 10 = 2. Need: P0 4, P1 2, P2 4. P1 fits → 4 free; P0 fits → 9; P2 fits. **Safe: P1, P0, P2.**
P2 asks for 1: Available = 1, Needs P0 4, P1 2, P2 3. Nobody fits → **unsafe, deny (P2 waits).**

**9.** Spooling → mutual exclusion; all-at-once → hold and wait; release on failure → no preemption; ordering → circular wait. **Option (1).**

**10.** Both are true, and R is exactly why an unsafe state need not deadlock. **Option (1).**

**11.** Statement I is true (a process holding nothing cannot be in a deadlock). Statement II is false: the wait-for graph is for single instances. **Option (3).**

**12.** A true, B false (cycle is only necessary), C true, D false (livelocked processes keep running), E true (every process on a circular wait holds one resource and waits for another). **Option (1): A, C and E only.**

**13.** Initialise, find, update, repeat, then decide: **B, D, A, C, option (1).**

**14.** Wait-for graph: P1 → P2 → P3 → P4. No cycle, so **no deadlock**: P4 can finish, then P3, P2 and P1.
With P4 → R2 added: P4 → P2 as well, giving the cycle P2 → P3 → P4 → P2. **P2, P3 and P4 are deadlocked**, and P1 also waits for ever on R2 (the detector would report all four).

**15.** Work = (1,0,1,1). Option (1) starts with P1, which needs B: fails. Option (4) starts with P0: fails. Option (2): P2 → (3,1,1,2), then P0 needs B = 2: fails. Option (3): P2 → (3,1,1,2); P1 → (3,2,2,2); P3 (2,1,2,0) → (3,2,3,3); P0 (2,2,0,1) → (4,2,5,4); P4 → (5,3,5,4). **Option (3) is safe.**
