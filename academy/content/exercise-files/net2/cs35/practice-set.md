# Practice set: Memory management and virtual memory (UGC NET Paper 2, Unit 5)

Time: 24 minutes. Write sizes as powers of two first. EAT for demand paging uses (1 − p) × ma + p × s.

**1.** Holes (in address order): 150 K, 300 K, 90 K, 500 K, 220 K. Requests: 210 K, 140 K, 280 K, 260 K. Show where each request goes under first fit, best fit and worst fit. Which strategies place all four?

**2.** A system has 36-bit virtual addresses, 16 KB pages and 4-byte PTEs. What is the size of a single-level page table?

**3.** A 57-bit virtual address, 4 KB pages and 8-byte PTEs. How many levels of paging are needed if every table fits in one page?

**4.** Page size is 2 KB and page 3 is in frame 11. Find the physical address for logical address 7000.

**5.** Segment table: segment 0 (base 2200, limit 500), segment 1 (base 5100, limit 900), segment 2 (base 800, limit 300). Translate (2, 280) and (1, 950).

**6.** TLB 15 ns, memory 150 ns, hit ratio 90%, single-level table. Find the EAT.

**7.** TLB 20 ns, memory 100 ns, three-level page table. What hit ratio gives EAT = 140 ns?

**8.** Memory access 100 ns, page-fault service 10 ms, one fault per 5,000 references. Find the EAT.

**9.** Reference string 6 1 6 2 3 1 6 4 1 2 6 3 2 1 4 with 3 empty frames. Count the faults for FIFO, LRU and optimal.

**10.** Under FIFO, run 4 3 2 1 4 2 3 1 0 4 5 3 1 0 with 3 frames and with 4 frames. What do you observe?

**11.** 120 frames are allocated proportionally to processes of 50, 150 and 400 pages. How many frames does each get?

**12.** Reference string 1 2 1 3 2 4 4 5 4 5 6 5 6 6 2 3, window Δ = 4. Give the working set just after the 8th reference.

**13.** Match List I with List II.

| List I | List II |
|---|---|
| A. FIFO | I. Needs future knowledge |
| B. Optimal | II. Belady's anomaly |
| C. LRU | III. Reference bit and circular pointer |
| D. Clock | IV. Least recently used page is the victim |

(1) A-II, B-I, C-IV, D-III (2) A-II, B-IV, C-I, D-III (3) A-I, B-II, C-IV, D-III (4) A-II, B-I, C-III, D-IV

**14.** Assertion (A): Thrashing reduces CPU utilisation. Reason (R): Processes in thrashing spend most of their time waiting for the paging device.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**15.** Which are correct? A. An inverted page table has one entry per frame. B. Segmentation causes internal fragmentation. C. A TLB miss with a two-level table costs t + 3m. D. Pure demand paging starts a process with no pages in memory. E. OPT can show Belady's anomaly.
(1) A, C and D only (2) A, B and C only (3) A, C, D and E only (4) C and D only
