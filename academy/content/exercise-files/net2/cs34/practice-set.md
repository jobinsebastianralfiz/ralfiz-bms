# Practice set: Deadlocks (UGC NET Paper 2, Unit 5)

Time: 22 minutes for all 15 problems. No calculator needed. Write the Need matrix before any Banker's step.

## Data for problems 1–3
Types A, B, C, D. Available = (1, 0, 1, 1).

| Process | Allocation | Max |
|---|---|---|
| P0 | 1 0 2 1 | 3 2 2 2 |
| P1 | 0 1 1 0 | 1 2 2 1 |
| P2 | 2 1 0 1 | 3 1 1 2 |
| P3 | 0 0 1 1 | 2 1 3 1 |
| P4 | 1 1 0 0 | 2 2 1 1 |

**1.** Find the Need matrix and the total number of instances of each type. Is the state safe? If so, give a safe sequence.

**2.** P2 requests (1, 0, 0, 0). Can it be granted immediately? Show the working.

**3.** Starting again from the original state, P4 requests (1, 0, 0, 0). Can it be granted? And what happens if P1 requests (0, 1, 0, 0)?

**4.** Deadlock detection. Types A, B, C. Available = (0, 0, 0).

| Process | Allocation | Request |
|---|---|---|
| P0 | 1 0 0 | 0 1 0 |
| P1 | 0 1 0 | 1 0 0 |
| P2 | 0 0 1 | 0 0 0 |
| P3 | 0 1 1 | 0 0 2 |
| P4 | 0 0 1 | 1 0 0 |

Which processes are deadlocked? What changes if P3's request is (0, 0, 1) instead?

**5.** Four processes need at most 2, 3, 4 and 5 instances of one resource type. What is the minimum number of instances that guarantees no deadlock? What is the largest number of instances with which a deadlock is still possible?

**6.** A system has 20 identical resources and each process needs at most 5. What is the largest number of processes that is guaranteed deadlock-free?

**7.** Four processes share 15 identical resources, each with the same maximum demand k. What is the largest k that is guaranteed deadlock-free?

**8.** A system has 12 printers. P0 holds 5 (max 9), P1 holds 2 (max 4), P2 holds 3 (max 7). Is the state safe? If P2 asks for 1 more printer, should it be granted?

**9.** Match List I with List II.

| List I (Condition) | List II (Prevention) |
|---|---|
| A. Mutual exclusion | I. Release all held resources when a request fails |
| B. Hold and wait | II. Spooling |
| C. No preemption | III. Lock ordering |
| D. Circular wait | IV. Request everything before starting |

(1) A-II, B-IV, C-I, D-III (2) A-II, B-I, C-IV, D-III (3) A-III, B-IV, C-I, D-II (4) A-IV, B-II, C-I, D-III

**10.** Assertion (A): An unsafe state may never lead to a deadlock. Reason (R): Processes may release resources before asking for their full declared maximum.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**11.** Statement I: The detection algorithm marks a process that holds no resources as finished at the start. Statement II: The wait-for graph method works for resource types with several instances.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**12.** Which are true? A. Deadlock avoidance needs advance information about maximum claims. B. A cycle in a RAG with multiple instances always means deadlock. C. Safety checking costs O(m·n²). D. Livelocked processes are blocked. E. Circular wait implies hold and wait.
(1) A, C and E only (2) A and C only (3) A, B and C only (4) A, C, D and E only

**13.** Arrange the safety algorithm steps: A. Work = Work + Allocation_i, Finish[i] = true. B. Initialise Work = Available and Finish[i] = false. C. If all Finish[i] are true, the state is safe. D. Find i with Finish[i] = false and Need_i ≤ Work; if none, go to C.
(1) B, D, A, C (2) B, A, D, C (3) D, B, A, C (4) B, D, C, A

**14.** Single-instance resources R1–R4. Edges: R1 → P1, P1 → R2, R2 → P2, P2 → R3, R3 → P3, P3 → R4, R4 → P4. Is there a deadlock? What if the edge P4 → R2 is added?

**15.** For the data of problems 1–3, which is a safe sequence? (1) P1, P2, P0, P3, P4 (2) P2, P0, P1, P3, P4 (3) P2, P1, P3, P0, P4 (4) P0, P2, P1, P3, P4
