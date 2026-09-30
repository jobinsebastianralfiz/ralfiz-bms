# Solutions: OS case studies and distributed systems (Lesson 5.8)

All clock values were computed by a Python simulation (netv/cs38.py), and the C program was run with gcc.

**1.**
- P1: p1 = 1, p2 = 2 (m1 carries 2), p3 = 3.
- P2: q1 = 1, q2 = 2, q3 = 3 (m2 carries 3).
- P3: r1 = max(0, 2) + 1 = 3, r2 = 4 (m3 carries 4), r3 = 5.
- P1: p4 = max(3, 3) + 1 = 4.
- P2: q4 = max(3, 4) + 1 = 5.

**2.**
- p4: P1 is at (3,0,0) after p3; m2 carries q3 = (0,3,0). Max = (3,3,0), then +1 in P1’s entry gives (4,3,0).
- q4: P2 is at (0,3,0); m3 carries r2 = (2,0,2). Max = (2,3,2), then +1 gives (2,4,2).
- r3: r1 = (2,0,1), r2 = (2,0,2), so r3 = (2,0,3).

**3.** Vectors: p3 = (3,0,0), q3 = (0,3,0), p2 = (2,0,0), q4 = (2,4,2), r3 = (2,0,3), p1 = (1,0,0), q1 = (0,1,0).
(a) p3 and q3: incomparable, so concurrent.
(b) p2 and q4: (2,0,0) ≤ (2,4,2), so p2 → q4 (through m1 and m3). Not concurrent.
(c) r3 and q4: (2,0,3) vs (2,4,2): r3 has the larger P3 entry, q4 the larger P2 entry, so concurrent (m3 was sent at r2, before r3).
(d) p1 and q1: concurrent.
Answer: (a), (c) and (d).

**4. Answer (1): both true.**
Statement I is the Lamport clock condition. Statement II is the vector clock property (vector clocks capture causality exactly). The false statement to watch for is the converse of I.

**5. Answer (1): A-IV, B-I, C-II, D-III.**

**6.** θ = ((260 − 200) + (263 − 225)) ÷ 2 = (60 + 38) ÷ 2 = 49 ms (server ahead).
δ = (225 − 200) − (263 − 260) = 25 − 3 = 22 ms.

**7.** RTT = 160 − 100 = 60 ms. One-way estimate = (60 − 20) ÷ 2 = 20 ms. New time = 08:30:12.000 + 0.020 = 08:30:12.020.

**8.** Offsets from the master: 0, +25, −10, +5 minutes. Average = 20 ÷ 4 = +5 minutes, so the target is 3:05.
Adjustments: master +5, slave 3:25 → −20, slave 2:50 → +15, slave 3:05 → 0.

**9.** Interval = δ ÷ (2ρ) = 0.01 ÷ (4 × 10⁻⁶) = 2500 s (about 41.7 minutes).

**10.**
(a) To every higher ID: 4, 5, 6 and 7.
(b) 4, 5 and 6 answer OK and hold their own elections; 6 gets no answer from 7, so 6 becomes coordinator and announces it.
(c) If 6 is also down, 5 is the highest live ID and wins.

**11. Output: xxx (3 characters).**
The parent gets non-zero from the first fork and does not fork again. The child gets 0 and forks once more, creating a grandchild. Parent, child and grandchild each print one x.

**12. Answer: B, D, C, A** (Core OS, Core Services, Media, Cocoa Touch).

**13. Answer (2): A, B, C and E only.**
D is false: a hard link shares the target’s inode; a symbolic link is a separate file (with its own inode) that stores a path.

**14.**
(a) R + W > N gives R > 4, so R = 5. W = 5 > 4.5 also holds.
(b) No. R + W = 10 > 9 is fine, but W = 4 is not greater than N/2 = 4.5, so two writes could succeed on disjoint sets of servers and conflict.

**15. Answer (1).** Both true: 2(N − 1) is less than 3(N − 1), and the saving is exactly the release round, which Ricart–Agrawala replaces with deferred replies. R explains A.
