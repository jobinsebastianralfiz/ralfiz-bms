# Practice set: Memory hierarchy (cs16)

Time: 24 minutes. Addresses are byte addresses unless stated.

**1. Match List I with List II**

| List I | List II |
|---|---|
| A. Direct mapping | I. Any block in any line |
| B. Fully associative | II. Block goes to set (block mod sets), any line inside it |
| C. Set-associative | III. Block goes to line (block mod lines) |
| D. TLB | IV. Associative cache of page-table entries |

(1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-II, C-I, D-IV (4) A-III, B-I, C-IV, D-II

**2.** How many 128 × 8 chips build a 4K × 16 memory? What decoder selects the rows, and how many address lines are needed in total?

**3.** An 8-way set-associative cache of 256 KB has 64-byte blocks; addresses are 32 bits. Find the offset, set and tag bits.

**4.** The CPU checks a 2 ns cache first; on a miss it goes to 60 ns memory. The hit ratio is 0.98. Find the average access time.

**5.** L1: 1 ns, miss rate 10%. L2: 6 ns, local miss rate 30%. Memory: 90 ns. Find the AMAT.

**6.** TLB 4 ns, memory 60 ns, TLB hit ratio 95%, single-level page table. Find the effective access time.

**7.** A disk spins at 15,000 rpm. What is its average rotational latency?

**8.** Memory access is 150 ns; a page fault takes 5 ms to service. What is the largest page-fault rate that keeps the effective access time at or below 300 ns?

**9.** A fully associative cache with 3 blocks starts empty. References: 1 3 1 4 2 3 1 5 2 1. Count misses under FIFO and under LRU. What does the result show?

**10. Assertion–Reason.**
A: A set-associative cache has fewer conflict misses than a direct-mapped cache of the same size.
R: In a set-associative cache a block can be placed in any of k lines of its set.

**11. Two statements.**
Statement I: The tag directory of a write-back cache stores a dirty bit for each line.
Statement II: The simultaneous-access formula for average access time is T1 + (1 − h)T2.

**12. Order.** Arrange the handling of a page fault:
A. The OS finds a free frame (or chooses a victim)
B. The MMU finds the valid bit is 0 and traps to the OS
C. The page is read from disk into the frame
D. The page table is updated and the instruction restarts

**13. Which are correct?**
A. Low-order interleaving puts consecutive words in different modules.
B. Rotational latency is on average one full revolution.
C. A CAM compares all words in parallel.
D. An inverted page table has one entry per frame.

**14.** A 12-bit address space holds four 512 × 8 RAM chips and one 2K × 8 ROM. Write the address map and state which address bits select RAM/ROM and which RAM chip.

**15.** In an associative memory, A = 0110 1010 and K = 0000 1111. Which of these words match: 1101 1010, 0110 1011, 0000 1010, 1010 0101?
