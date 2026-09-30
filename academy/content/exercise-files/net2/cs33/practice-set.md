# Practice set: CPU scheduling (Paper 2, Unit 5.3)

Conventions (unless a problem says otherwise): times in ms; ties go to the earlier arrival, then the lower process number; preemption only when the newcomer is strictly better; in RR a process arriving at the instant a quantum expires is queued before the pre-empted process; a smaller priority number is higher priority; context-switch time is 0.

Use this table for problems 1–5:

| Process | Arrival | Burst | Priority |
|---|---|---|---|
| P1 | 0 | 7 | 2 |
| P2 | 2 | 4 | 1 |
| P3 | 3 | 2 | 4 |
| P4 | 5 | 5 | 3 |
| P5 | 6 | 3 | 1 |

1. Under FCFS, find the average waiting time.
2. Under non-preemptive SJF, find the average turnaround time.
3. Under SRTF, find the average waiting time and the number of context switches between different processes.
4. Under preemptive priority, find the completion time of P1.
5. Under round robin with q = 3, find the average turnaround time and the completion time of P4.

6. Five jobs all arrive at time 0 with bursts 9, 4, 1, 7, 3. Find the average waiting time under SJF and under FCFS (in the order given).

7. HRRN is used for: P1 (0, 4), P2 (1, 5), P3 (3, 2), P4 (5, 6), P5 (6, 3) as (arrival, burst). Give the dispatch order and the average waiting time.

8. The exponential average uses α = 0.25 and τ₀ = 16. The actual bursts are 12, 8, 20. Find τ₁, τ₂, τ₃.

9. Eight CPU-bound processes run under RR with q = 25 ms and context switch s = 5 ms. (a) Find the useful CPU fraction. (b) Ignoring switch time, find the longest gap between two consecutive quanta of one process.

10. Match List I with List II.

| List I | List II |
|---|---|
| A. SRTF | I. Never pre-empts; uses (W + S)/S |
| B. HRRN | II. Degenerates to FCFS for a huge quantum |
| C. Round robin | III. Pre-empts when a strictly shorter job arrives |
| D. Multilevel queue | IV. Processes permanently bound to one queue |

Options: (1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-I, C-IV, D-II (4) A-III, B-II, C-I, D-IV

11. Assertion (A): SRTF can starve a long job. Reason (R): A stream of short jobs can keep pre-empting or bypassing the long job. Choose from the four standard A–R options.

12. Statement I: For non-preemptive algorithms, response time equals waiting time. Statement II: In RR, response time is always equal to waiting time. Choose from the four standard statement options.

13. A multilevel feedback queue has Q0 (RR, q = 4), Q1 (RR, q = 8) and Q2 (FCFS). A process with burst 25 arrives into an otherwise empty system. How much of its burst runs in each queue?

14. LRTF with ties going to the lower process number (even against the running process): P1 (0, 3), P2 (0, 5), P3 (0, 7). Find the completion time of each process and the average turnaround time.

15. Each process waits for I/O 60% of the time. What is the smallest number of processes in memory that gives a CPU utilisation of at least 90%?
