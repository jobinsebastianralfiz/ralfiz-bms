# Solutions: practice set 4.7

**1. Answer (3).** ⌈700/128⌉ = 6 blocks (5 × 128 = 640, plus a last block of 60 MB). 6 × 3 = 18 replicas. Raw space = 700 × 3 = 2,100 MB. Option (2) pads the last block to 128 MB (6 × 128 × 3 = 2,304), but HDFS does not pad.

**2. Answer (1).** Raw capacity = 12 × 16 = 192 TB. With RF 3: 192/3 = 64 TB. With RF 2: 192/2 = 96 TB.

**3. Answer (3).** Take each file separately. 100 MB needs 1 split. 260 MB needs 3 (128 + 128 + 4). 128 MB needs exactly 1. 129 MB needs 2 (128 + 1). Total = 7. Trap: adding the sizes (617 MB, ⌈617/128⌉ = 5) ignores file boundaries.

**4. Answer (1).**
- Mapper 1 emits (sun,1) (moon,1) (sun,1) (star,1): 4 pairs. After combining: (sun,2) (moon,1) (star,1), which is 3 pairs.
- Mapper 2 emits (moon,1) (moon,1) (star,1) (sun,1): 4 pairs. After combining: (moon,2) (star,1) (sun,1), which is 3 pairs.
- Total: 8 pairs emitted, 6 shuffled.
- Reducers: sun = 2 + 1 = 3, moon = 1 + 2 = 3, star = 1 + 1 = 2.

**5. Answer (1).** 11 mod 3 = 2, 7 mod 3 = 1 and 6 mod 3 = 0, so sun, moon and star go to reducers 2, 1 and 0. Each reducer writes one part file, so there are 3 output files, whatever the number of keys.

**6. Answer (1).** NameNode = metadata (III). DataNode = blocks and heartbeats (I). Secondary NameNode = checkpointing (II). NodeManager = containers (IV).

**7. Answer (3).** Input split → map → combine (on the map side) → shuffle and sort → reduce, which is E, C, B, D, A.

**8. Answer (3).** You need R + W > N = 4. (1,3) = 4, (2,2) = 4 and (3,1) = 4 all fail, because 4 is not greater than 4. Only (2,3) = 5 works.

**9. Answer (2).** Both conditions must hold (an implicit AND). Order 3 is paid with 800 and order 5 is paid with 650. Order 1 is paid but only 450, and order 2 is 1200 but pending. Count = 2.

**10. Answer (1).** Keep the paid orders: 1, 3 and 5. Group by customer: Ravi = 450 + 800 = 1,250 and Sara = 650. Sort by total descending: Ravi 1250, then Sara 650. Option (2) forgets the $match (it adds Sara’s pending 1,200).

**11. Answer (3).** Equality on an array field matches if any element equals "pen": orders 1 and 3. Order 4 has no items field and does not match. Count = 2.

**12. Answer (4).** flatMap produces 5 words: ink, pen, pen, paper, pen. count() = 5. distinct() leaves ink, pen and paper, so its count is 3. The program has two actions, so it runs two jobs.

**13. Answer (1).** R + W = 2 ≤ 3, so a read can hit a replica that has not yet received the latest write. R states exactly why.

**14. Answer (2).** D is false: Redis is a key-value store. A, B, C and E are true.

**15. Answer (3).** Statement I is true. Statement II is false: under mod placement, a key stays put only if k mod 3 = k mod 4. That happens for k mod 12 ∈ {0, 1, 2}, which is just 25% of keys, so about 75% move.
