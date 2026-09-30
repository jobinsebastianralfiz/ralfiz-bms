# Solutions: Memory management practice set

**1.**
| Request | First fit | Best fit | Worst fit |
|---|---|---|---|
| 210 | 300 → 90 left | 220 → 10 left | 500 → 290 left |
| 140 | 150 → 10 left | 150 → 10 left | 300 → 160 left |
| 280 | 500 → 220 left | 300 → 20 left | 290 → 10 left |
| 260 | waits (largest hole 220) | 500 → 240 left | waits (largest hole 220) |

**Only best fit places all four.**

**2.** Offset = 14 bits (16 KB = 2^14). Page bits = 36 − 14 = 22. Size = 2^22 × 4 B = 2^24 B = **16 MB**.

**3.** Entries per page = 4096 / 8 = 512 = 2^9. Page bits = 57 − 12 = 45. Levels = ⌈45 / 9⌉ = **5** (this is five-level paging on x86-64).

**4.** Page = ⌊7000 / 2048⌋ = 3, offset = 7000 − 6144 = 856. Physical = 11 × 2048 + 856 = **23384**.

**5.** (2, 280): 280 < 300, so 800 + 280 = **1080**. (1, 950): 950 ≥ 900, so **trap** (addressing error).

**6.** Hit = 165, miss = 15 + 150 + 150 = 315. EAT = 0.9 × 165 + 0.1 × 315 = 148.5 + 31.5 = **180 ns**.

**7.** Hit = 120, miss = 20 + 4 × 100 = 420. 120h + 420(1 − h) = 140 → 420 − 300h = 140 → h = 280/300 ≈ **0.933 (93.3%)**.

**8.** p = 0.0002, s = 10,000,000 ns. EAT = 0.9998 × 100 + 0.0002 × 10,000,000 = 99.98 + 2,000 = **2,099.98 ns ≈ 2.1 µs**.

**9.** FIFO **12**, LRU **12**, optimal **8**. (There are 5 distinct pages, so 5 faults is the floor for any algorithm.)

**10.** 3 frames: **9 faults**. 4 frames: **10 faults**. More frames, more faults: **Belady's anomaly**.

**11.** S = 600. 120 × 50/600 = **10**, 120 × 150/600 = **30**, 120 × 400/600 = **80**.

**12.** References 5–8 are 2 4 4 5, so WS = **{2, 4, 5}**, WSS = 3.

**13.** FIFO–anomaly, OPT–future, LRU–least recently used, clock–reference bit. **Option (1).**

**14.** Both are true, and waiting for the paging device is exactly why the CPU idles. **Option (1).**

**15.** A true, B false (segmentation causes external fragmentation), C true, D true, E false (OPT is a stack algorithm). **Option (1): A, C and D only.**
