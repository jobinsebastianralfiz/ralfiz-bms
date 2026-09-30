# Solutions: Memory hierarchy (cs16)

**1. Answer (1): A-III, B-I, C-II, D-IV.** Direct mapping uses block mod lines; fully associative allows any line; set-associative uses block mod sets; the TLB caches translations.

**2. 64 chips, 5-to-32 decoder, 12 address lines.** Chips per row = 16 ÷ 8 = 2; rows = 4096 ÷ 128 = 32; total = 64. Each chip needs 7 address lines; 32 rows need 5 decoder inputs; 7 + 5 = 12 = log2 4096.

**3. Offset 6, set 9, tag 17.** Lines = 262,144 ÷ 64 = 4096; sets = 4096 ÷ 8 = 512 (9 bits); tag = 32 − 9 − 6 = 17.

**4. 3.2 ns.** Hierarchical: 2 + (1 − 0.98) × 60 = 2 + 1.2 = 3.2 ns.

**5. 4.3 ns.** 1 + 0.1 × (6 + 0.3 × 90) = 1 + 0.1 × 33 = 4.3 ns.

**6. 67 ns.** Hit: 4 + 60 = 64. Miss: 4 + 60 + 60 = 124. EAT = 0.95 × 64 + 0.05 × 124 = 60.8 + 6.2 = 67 ns.

**7. 2 ms.** One revolution = 60 ÷ 15,000 s = 4 ms; average latency = half = 2 ms.

**8. About 3 × 10^-5.** (1 − p) × 150 + p × 5×10^6 ≤ 300 gives p × (5×10^6 − 150) ≤ 150, so p ≤ 150 ÷ 4,999,850 ≈ 3.0 × 10^-5 (about 3 faults per 100,000 references).

**9. FIFO 6 misses, LRU 8 misses.**
FIFO: 1 M, 3 M, 1 H, 4 M {1,3,4}, 2 M evicts 1 {3,4,2}, 3 H, 1 M evicts 3 {4,2,1}, 5 M evicts 4 {2,1,5}, 2 H, 1 H. Hits 4, misses 6.
LRU: 1 M, 3 M, 1 H, 4 M, 2 M evicts 3, 3 M evicts 1, 1 M evicts 4, 5 M evicts 2, 2 M evicts 3, 1 H. Hits 2, misses 8.
LRU is better on average, but not for every string.

**10. Both true, R explains A.** Having k candidate lines means two blocks with the same set can coexist, removing conflict misses that direct mapping suffers.

**11. Statement I true, Statement II false.** T1 + (1 − h)T2 is the hierarchical (look-through) formula. Simultaneous access is hT1 + (1 − h)T2.

**12. B, A, C, D.** The trap comes first; the OS then finds a frame, reads the page, updates the table and restarts the instruction.

**13. A, C and D only.** B is false: the average latency is half a revolution.

**14.** RAM 1: 000–1FF, RAM 2: 200–3FF, RAM 3: 400–5FF, RAM 4: 600–7FF, ROM: 800–FFF. A11 = 0 selects RAM and A11 = 1 selects ROM; A10 A9 go to a 2-to-4 decoder that selects the RAM chip; A8–A0 go to every RAM chip; A10–A0 go to the ROM.

**15. Words 1 and 3.** Only the lower four bits are compared (K = 0000 1111). The argument’s lower bits are 1010. 1101 1010 and 0000 1010 end in 1010 and match; 0110 1011 ends in 1011 and 1010 0101 ends in 0101.
