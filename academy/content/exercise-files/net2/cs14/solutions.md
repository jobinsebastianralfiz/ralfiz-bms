# Solutions: practice set 2.6

**1.** T = (6 + 299) × 20 = **6100 ns**. t_n = 120 ns, so the non-pipelined time is 36,000 ns and **S = 5.902**. Efficiency = 300/305 = **0.984**. Throughput = 300 / 6.1 µs = **49.18 million per second**.

**2.** Clock = 70 + 5 = **75 ns**. Non-pipelined time = 230 ns, so the limit is 230/75 = **3.067**. For 500 instructions: 500 × 230 / (503 × 75) = 115000 / 37725 = **3.048**.

**3.** 6n/(n + 5) ≥ 5 gives 6n ≥ 5n + 25, so **n = 25**.

**4.** CPI = 1 + 0.3 × 2 + 0.2 × 0.25 × 1 = **1.65**.

**5.**
(a) Without forwarding: LW1 ID 2, WB 5. LW2 ID 3, WB 6. ADD waits for WB of LW2: ID 6, WB 9. SW waits for WB of ADD: ID 9, WB 12. **12 cycles.**
(b) With forwarding: ADD needs LW2’s data after MEM (cycle 5), so ADD is in ID in cycle 5 (1 load-use stall), with WB 8. SW has ID 6 and WB 9. **9 cycles.** The ideal is 8.

**6.** Instructions 1–4 are fetched in cycles 1–4, and the branch executes in cycle 8. Instruction 5 is fetched in cycle 9, so instruction 10 is fetched in cycle 14 and finishes in cycle **18**. Check: 5 + 10 − 1 + 4 = 18.

**7.** S1 gives 3, S2 gives 4 and S3 gives 2, so forbidden = **{2, 3, 4}** and **C = 1110**.
- Latency 1 leads to 0111 OR 1110 = 1111, after which only 5 is allowed. The greedy cycle is **(1, 5)**, average 3.
- Latency 5 on its own gives an average of 5.
**MAL = 3.**

**8.** 8 + 128 − 1 = **135 cycles**.

**9.** (a) 2047 mod 4 = **module 3**, word ⌊2047/4⌋ = **511**. (b) ⌊2500/1024⌋ = **module 2**, word 2500 − 2048 = **452**.

**10.** The exponents are equal, so no alignment is needed. Subtract: 0.5130 − 0.4980 = 0.0150 × 10⁵. Normalize by shifting left one digit: **0.1500 × 10⁴** (= 1500).

**11.** **Option (1).**

**12.** Both true, and R explains A. **Option 1.**

**13.** I is false: the speedup is bounded by k. II is true: n/(k + n − 1) tends to 1. **Statement I false, Statement II true.**

**14.** **A, B, C and E.** Forwarding (D) is for data hazards.

**15.** (a) **RAW** on R1. (b) **WAR** on R2: I2 writes a register that I1 reads. (c) **WAW** on R4.
