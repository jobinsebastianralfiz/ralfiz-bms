# Practice set 2.6: pipeline and vector processing

About 90 seconds per problem. Unless stated, t_n = k·t_p, and the register file is written in the first half of a cycle and read in the second half.

**1.** A 6-segment pipeline has t_p = 20 ns and processes 300 tasks. Find the total time, speedup, efficiency and throughput (million tasks per second).

**2.** Stage delays are 40, 70, 55 and 65 ns, with a 5 ns latch. Find the clock, the limiting speedup, and the speedup for 500 instructions (the non-pipelined time is the sum of the stages).

**3.** What is the minimum number of tasks for a speedup of at least 5 in a 6-segment pipeline?

**4.** 30% of instructions are branches with a 2-cycle penalty. 20% are loads, and one quarter of those cause a 1-cycle stall. Find the effective CPI.

**5.** Count the cycles for this 5-stage pipeline code (a) without forwarding and (b) with full forwarding.

    LW  R1, 0(R0)
    LW  R2, 4(R0)
    ADD R3, R1, R2
    SW  R3, 8(R0)

**6.** In a 5-stage pipeline, fetching stops when a branch is decoded and resumes after it executes (penalty k − 1). Ten instructions run, and instruction 4 is a branch that falls through. When does instruction 10 finish?

**7.** A reservation table marks S1 at cycles 0 and 3, S2 at 1 and 5, and S3 at 2 and 4. Find the forbidden latencies, the collision vector, the greedy cycle and the MAL.

**8.** An 8-stage vector pipeline processes a 128-element vector. How many cycles does it take?

**9.** (a) With 4-way low-order interleaving, where is address 2047? (b) With high-order interleaving of 4 modules × 1024 words, where is address 2500?

**10.** Trace the floating-point pipeline for 0.5130 × 10⁵ − 0.4980 × 10⁵ (four-digit mantissas).

**11.** Match List I with List II.

| List I | List II |
|---|---|
| A. SISD | I. Multiprocessor |
| B. SIMD | II. Uniprocessor |
| C. MISD | III. Array processor |
| D. MIMD | IV. No practical commercial machine |

(1) A-II, B-III, C-IV, D-I  (2) A-II, B-IV, C-III, D-I  (3) A-III, B-II, C-IV, D-I  (4) A-II, B-III, C-I, D-IV

**12.** Assertion (A): Operand forwarding removes the stall between two dependent ALU instructions. Reason (R): The ALU result is available at the end of EX and can be routed straight to the next instruction’s EX input. Choose from the four standard A–R options.

**13.** Statement I: The speedup of a pipeline can exceed the number of stages when t_n = k·t_p. Statement II: Efficiency approaches 1 as the number of tasks grows. Choose from the four standard options.

**14.** Which reduce control-hazard penalties? A. Branch prediction. B. Loop buffer. C. Delayed branch. D. Operand forwarding. E. Prefetching the branch target.

**15.** Classify each pair of instructions (I1 comes first). (a) R1 ← R2 + R3; R4 ← R1 × R5. (b) R1 ← R2 + R3; R2 ← R6 − R7. (c) R4 ← R1 × R5; R4 ← R8 + R9.
