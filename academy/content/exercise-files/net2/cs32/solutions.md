# Solutions: Processes, threads and synchronization

**1.** fork(); fork(); gives 4 processes. Each of the 4 runs if (fork() == 0) fork();, which turns each into 3 processes (the parent, the child and the child's child). Total 4 × 3 = **12**, so H is printed 12 times.

**2.** Parse: fork() || (fork() && fork()).
- The parent gets non-zero from fork 1, so || short-circuits: 1 process.
- The child gets 0, so it evaluates fork 2 && fork 3. Its child (0) short-circuits && (1 process). The child itself (non-zero) runs fork 3, giving 2 processes. That makes 3 processes on this branch.

Total **4**.

**3.** 4 − 9 + 3 = **−2**. In the blocking implementation, **2 processes are blocked**.

**4.** Serial P1 then P2: (3 − 1) × 3 = 6. P2 then P1: 9 − 1 = 8. Lost updates: P1's store survives (2) or P2's store survives (9). The possible values are **{2, 6, 8, 9}**.

**5.** Initial value **4**. After 5 requests: 4 − 5 = **−1**, so **1 process is waiting**.

**6.** **mutex = 1, empty = 8 − 6 + 2 = 4, full = 6 − 2 = 4.**

**7.** ⌊9/2⌋ = **4** can eat. The n − 1 rule allows **8** at the table.

**8.** There are 6 edges, so **6 semaphores**.

**9.** Only **1**. The faulty process's second wait(S) blocks it while S = 0 (it never signals), and S is never raised again, so **all the other processes that have not yet entered are blocked forever**. The error causes a deadlock-like hang, not a mutual-exclusion violation.

**10.** A-II, B-I, C-III, D-IV.

**11.** A is true. R is false: the kernel does not know about user-level threads, so it cannot schedule them on different CPUs. **(A) is true but (R) is false.**

**12.** I is true. II is false: an ordinary pipe is one-way (use two pipes for two-way communication). **Statement I is true but Statement II is false.**

**13.** **A, C and D.** The heap and open files are shared.

**14.** **D, B, C, E, A.**

**15.** The possible final values are **{2, 3, 4}**. The minimum is 2: one process loads 0 and stalls, the other increments once (x = 1), the first stores 1, the other loads 1 and stalls, the first increments to 2, and the other stores 2.
