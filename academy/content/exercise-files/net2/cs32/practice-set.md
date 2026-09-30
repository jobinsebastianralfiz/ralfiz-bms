# Practice set: Processes, threads and synchronization (Paper 2, Unit 5.2)

1. How many times is "H" printed?

        int main(void) { fork(); fork(); if (fork() == 0) fork(); printf("H"); return 0; }

2. How many processes exist in total (including the original) after: fork() || fork() && fork(); ?

3. A semaphore S = 4. The operations performed are 9 P and 3 V. What is the final value? If this is the blocking implementation and no process has finished, how many processes are blocked?

4. Shared x = 3. P1: x = x - 1. P2: x = x * 3. Each statement is load–compute–store. List all possible final values of x.

5. A counting semaphore is used so that at most 4 processes can use a pool of printers. What is its initial value? Five processes request a printer and none has released one: what is the value, and how many are waiting (blocking implementation)?

6. Buffer size 8, standard producer–consumer semaphores. From an empty buffer, the producer inserts 6 items and the consumer removes 2. Give mutex, empty and full at rest.

7. Nine philosophers: what is the maximum number eating simultaneously? What is the maximum number allowed at the table under the "n − 1" deadlock-avoidance rule?

8. Precedence: S1 → S3, S2 → S3, S3 → S4, S3 → S5, S4 → S6, S5 → S6. How many semaphores (one per edge)?

9. A semaphore S = 1 guards a CS for 8 correct processes (wait; CS; signal). A ninth process runs wait(S); CS; wait(S) by mistake. Each runs once. What is the maximum number ever in the CS, and what happens to the other processes?

10. Match List I with List II.

| List I | List II |
|---|---|
| A. Peterson | I. Mutual exclusion and progress, but not bounded waiting |
| B. TestAndSet spin loop | II. All three requirements for two processes |
| C. Strict alternation | III. Mutual exclusion, but progress violated |
| D. Check-then-set flags | IV. Mutual exclusion violated |

11. Assertion (A): User-level threads can be switched without entering the kernel. Reason (R): The kernel schedules user-level threads individually on different CPUs.

12. Statement I: A named pipe can connect two unrelated processes. Statement II: An ordinary pipe is bidirectional.

13. Which are private to each thread? A. Registers B. Heap C. Stack D. Thread ID E. Open files.

14. Arrange the bounded-buffer producer's steps in order: A. signal(full) B. wait(mutex) C. add the item to the buffer D. wait(empty) E. signal(mutex).

15. Two processes each run x++ twice (load, add, store) on x = 0. List every possible final value.
