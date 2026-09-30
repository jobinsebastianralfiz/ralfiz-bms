# Solutions: File systems and I/O practice set

Sorted queue: 40 95 130 180 [250] 275 310 420 490.

**1.** FCFS: 60 + 215 + 325 + 240 + 140 + 235 + 215 + 360 = **1790**.
SSTF: 250 → 275 (25) → 310 (35) → 420 (110) → 490 (70) → 180 (310) → 130 (50) → 95 (35) → 40 (55) = **690**.

**2.** SCAN (down): 250 → 0 = 250, then 0 → 490 = 490. Total **740**.
LOOK (down): 250 → 40 = 210, then 40 → 490 = 450. Total **660**.

**3.** C-SCAN (down): 250 → 0 = 250, jump 0 → 499 = 499, then 499 → 275 = 224. With the jump **973**; without it **474**.

**4.** C-LOOK (down): 250 → 40 = 210, jump 40 → 490 = 450, then 490 → 275 = 215. With the jump **875**; without it **425**.

**5.** k = 1024 / 4 = 256. Blocks = 10 + 256 + 65,536 + 16,777,216 = 16,843,018. Size = **16,843,018 KB** (about 16 GB).

**6.** Block = ⌊300,000 / 1024⌋ = 292. Direct: 0–9. Single: 10–265. Double: 266–65,801. Block 292 is in the double indirect range: **3 disk reads** (double indirect block, single indirect block, data).

**7.** 2^3 × 2^12 × 2^9 × 2^9 = 2^33 bytes = **8 GB**. Sectors = 2^33 / 2^9 = 2^24, so **24 bits**.

**8.** Rotation = 60,000 / 15,000 = 4 ms, latency = 2 ms. Transfer = 4,096 / 100,000,000 s = 0.041 ms. Total ≈ 3.5 + 2 + 0.041 = **5.54 ms**.

**9.** Blocks = 2^41 / 2^13 = 2^28. Bitmap = 2^28 bits = 2^25 bytes = **32 MB**.

**10.** RAID 0: **15 TB**. RAID 1+0 with four disks: **6 TB**. RAID 5: (5 − 1) × 3 = **12 TB**. RAID 6: (5 − 2) × 3 = **9 TB**.

**11.** Contiguous–external fragmentation, linked–FAT, indexed–index block, bitmap–free space. **Option (1).**

**12.** Both are true, and the SJF-like greedy choice is exactly why it can starve. **Option (1).**

**13.** Statement I is true (two parity blocks plus at least two data blocks per stripe). Statement II is false: mirroring halves usable capacity. **Option (3).**

**14.** A true, B false (FCFS serves in order), C true, D true, E false (it stores a path name). **Option (1): A, C and D only.**

**15.** Four zero words = 32 blocks. In the fifth word the first 1 is at offset 2. First free block = **34**.
