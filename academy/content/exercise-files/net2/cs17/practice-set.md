# Practice set: Multiprocessors (cs17)

Time: 24 minutes.

**1. Match List I with List II**

| List I | List II |
|---|---|
| A. Time-shared bus | I. n × m crosspoints |
| B. Crossbar | II. One transfer at a time |
| C. Omega network | III. Nodes linked when addresses differ in one bit |
| D. Hypercube | IV. log2 N stages of 2 × 2 switches |

(1) A-II, B-I, C-IV, D-III (2) A-I, B-II, C-IV, D-III (3) A-II, B-IV, C-I, D-III (4) A-II, B-I, C-III, D-IV

**2.** A program is 80% parallelisable. Find the speedup on 8 processors and the upper limit.

**3.** A program is 90% parallelisable. What is the smallest number of processors for a speedup of at least 6?

**4.** On 32 processors, the serial part takes 5% of the parallel run. Find the scaled (Gustafson) speedup.

**5.** How many 2 × 2 switches and stages does a 32 × 32 omega network need? How many crosspoints would a 32 × 32 crossbar need?

**6.** For a 5-cube, give the number of links and the diameter. How many hops separate 10110 and 01100?

**7.** A full-map directory keeps one presence bit per processor and 2 state bits for each 32-byte block. With 64 processors, what is the overhead?

**8.** A bus provides 2400 MB/s and each processor needs 300 MB/s after its cache. How many processors saturate it?

**9.** A speedup of 5 is measured on 10 processors. Compute the Karp–Flatt serial fraction.

**10.** Three processors use MESI; the block starts Invalid everywhere. Operations: P1 reads, P1 writes, P0 reads, P2 reads, P2 writes. Give the states (P0, P1, P2) after each operation.

**11. Assertion–Reason.**
A: A directory protocol does not need a broadcast bus.
R: The directory records which caches hold each block, so messages go only to those caches.

**12. Two statements.**
Statement I: In MESI, a write to a line in the Exclusive state causes a bus invalidation.
Statement II: A crossbar allows simultaneous access to different memory modules.

**13. Order.** Arrange the use of a test-and-set lock:
A. Enter the critical section
B. Execute test-and-set on the lock
C. If the old value was 1, repeat B
D. Clear the lock to 0

**14. Which are correct?**
A. Master–slave systems run the OS on one processor.
B. NUMA gives equal access time to all memory.
C. Write-update protocols send new data to other caches.
D. A rotating daisy chain is a dynamic arbitration scheme.

**15.** 70% of a program is parallelised over 7 processors; the rest stays serial. Find the speedup.
