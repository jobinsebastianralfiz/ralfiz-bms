# Solutions: Multiprocessors (cs17)

**1. Answer (1): A-II, B-I, C-IV, D-III.** A bus serialises transfers; a crossbar has n × m crosspoints; omega has log2 N stages; a hypercube links one-bit neighbours.

**2. 3.33 and 5.** S = 1 ÷ (0.2 + 0.8/8) = 1 ÷ 0.3 = 3.33. Limit = 1 ÷ 0.2 = 5.

**3. 14.** 1 ÷ (0.1 + 0.9/n) ≥ 6 gives 0.9/n ≤ 1/6 − 0.1 = 0.0667, so n ≥ 13.5. With 13 processors S ≈ 5.91; with 14, S ≈ 6.09. Answer 14.

**4. 30.45.** S = 32 − 0.05 × 31 = 32 − 1.55 = 30.45.

**5. 80 switches, 5 stages; 1024 crosspoints.** Stages = log2 32 = 5; switches = 5 × 16 = 80; crossbar = 32 × 32 = 1024.

**6. 80 links, diameter 5, 3 hops.** Links = 5 × 2^4 = 80. Diameter = 5. 10110 XOR 01100 = 11010, three 1s.

**7. About 25.78%.** Bits per block = 64 + 2 = 66; data bits = 32 × 8 = 256; 66 ÷ 256 = 0.2578. A full-map directory becomes costly as processors grow.

**8. 8.** 2400 ÷ 300 = 8.

**9. About 0.111.** e = (1/5 − 1/10) ÷ (1 − 1/10) = 0.1 ÷ 0.9 = 0.111.

**10.** P1 reads: (I, E, I). P1 writes: (I, M, I), silently. P0 reads: P1 flushes, (S, S, I). P2 reads: (S, S, S). P2 writes: invalidates the others, (I, I, M).

**11. Both true, R explains A.** Point-to-point messages to the listed sharers replace broadcasting.

**12. Statement I false, Statement II true.** E → M is silent; that is the purpose of the Exclusive state. A crossbar allows parallel access to different modules.

**13. B, C, A, D.** Test-and-set; loop while it was already set; enter; release.

**14. A, C and D only.** B is false: NUMA means non-uniform access; UMA is uniform.

**15. 2.5.** S = 1 ÷ (0.3 + 0.7/7) = 1 ÷ 0.4 = 2.5.
