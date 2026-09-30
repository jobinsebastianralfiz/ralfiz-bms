# Solutions: Security, protection and virtual machines (Lesson 5.7)

All numerical answers were checked with a Python script (netv/cs37.py), and the C program with gcc.

**1. Answer (1): A-II, B-IV, C-I, D-III.**
Virus = needs a host (II). Worm = standalone, network spread (IV). Rootkit = hides the intruder (I). Logic bomb = trigger condition (III). Option (2) swaps virus and worm, the classic trap.

**2.**
(a) ACL of F2 is its column: <D1, {read, write}>, <D2, {read*}>.
(b) Capability list of D3 is its row: <F1, {owner, write}>, <F3, {read}>.
(c) Yes. D2 holds read* on F2. The asterisk is the copy right, so D2 can copy read (or read*, under unrestricted copy) into D3’s entry for F2.
(d) Yes. D3 is the owner of F1, and the owner may add any right to any entry in F1’s column, so D3 can add read to access(D2, F1).

**3. Answer (2): both false.**
An ACL is a column (per object), not a row. Capabilities are scattered across domains, so revoking a right everywhere is hard, not easy.

**4.** Final mode = requested & ~umask. ~077 clears every group and other bit.
(a) 0666 & ~0077 = 0600 = rw-------.
(b) 0777 & ~0077 = 0700 = rwx------.

**5.**
(a) 2755: setgid with group execute gives rwxr-sr-x.
(b) 1777: sticky with others execute gives rwxrwxrwt.
(c) 4711: 7 = rwx becomes rws (setuid with owner execute), 1 = --x, 1 = --x. Answer rws--x--x.
Trap: the special digit changes only the execute letter of one triple; it never adds a tenth character.

**6.** Alphabet = 26 + 10 = 36. Space = 36⁶ = 2,176,782,336.
Time = 2,176,782,336 ÷ (5 × 10⁶) ≈ 435.4 s, about 7.3 minutes (average about 3.6 minutes).
Strength = 6 × log₂ 36 = 6 × 5.17 ≈ 31.0 bits.

**7. Answer (3): A true, R false.**
Salting forces one table per salt value, so A is true. But the salt is stored in clear next to the hash, so a search on one user’s hash costs exactly the same as without salt. R is false.

**8.**
(a) C(40, 2) = 40 × 39 ÷ 2 = 780 keys.
(b) 40 key pairs = 80 keys.

**9.** n = 33. φ(n) = 2 × 10 = 20. d = 3⁻¹ mod 20 = 7, because 3 × 7 = 21 ≡ 1 (mod 20).
C = 4³ mod 33 = 64 mod 33 = 31. Check: 31⁷ mod 33 = 4.

**10.** Rules: no read up, no write down.
O1 (Unclassified, below): read yes, write no.
O2 (Confidential, same level): read yes, write yes.
O3 (Secret, above): read no, write (blind append) yes.

**11. Answer: D, B, E, A, C** (C1 < C2 < B1 < B3 < A1). The full order is D < C1 < C2 < B1 < B2 < B3 < A1.

**12. Answer (2): A, B, C and E only.**
D is false: hardware assistance (Intel VT-x, AMD-V) exists exactly so that unmodified guests can run. Modified guests are the paravirtualisation approach (C).

**13.** FAR = 45 ÷ 15,000 = 0.3%. FRR = 96 ÷ 4,800 = 2%.
A stricter threshold accepts fewer people: FAR goes down and FRR goes up. The equal error rate is where the two curves cross.

**14. Output: 42-ro|7|5**
The full text would be "42-root", 7 characters. buf has 6 bytes, so snprintf stores 5 characters and a null terminator: "42-ro". It returns 7, the length the full output needed, and strlen is 5. Trap: expecting n to be 5 or 6.

**15.** Total load = 20 × 6% = 120% of one server. Hosts for load = ⌈120 ÷ 70⌉ = ⌈1.71⌉ = 2. Adding one failover host gives 3 hosts in total.
