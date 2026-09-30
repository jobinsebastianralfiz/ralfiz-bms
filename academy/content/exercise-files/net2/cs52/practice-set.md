# Practice set: 7.8 Advanced algorithms

Time: 24 minutes for all 15 (about 90 seconds each). No notes.

**1.** Compute the KMP prefix function of P = abcdabca.

**2.** Compute the KMP prefix function of P = aabaaab.

**3.** Rabin–Karp with d = 10 and q = 11 searches T = 3141592653 for P = 26. List the hash of P, the valid shift(s) and the number of spurious hits.

**4.** The naive matcher (left to right, stopping at the first mismatch) searches T = aaaaaaaaaaaa (12 a’s) for P = aaa. How many comparisons does it make, and how many matches does it find?

**5.** Find gcd(3276, 1260) with Euclid’s algorithm and the number of division steps.

**6.** Find 7⁻¹ mod 40.

**7.** RSA: p = 13, q = 17, e = 5. Find n, φ(n) and d, then encrypt M = 2.

**8.** Compute 6⁷³ mod 11.

**9.** Match List I with List II.

| List I | List II |
|---|---|
| A. Finite-automaton matcher preprocessing | I. Θ(m) |
| B. KMP prefix function | II. O(m·|Σ|) |
| C. Rabin–Karp expected matching time | III. O(n + m) |
| D. Naive matcher preprocessing | IV. none (0) |

(1) A-II, B-I, C-III, D-IV (2) A-I, B-II, C-III, D-IV (3) A-II, B-III, C-I, D-IV (4) A-II, B-I, C-IV, D-III

**10.** A sum of n = 1024 numbers runs on p = 32 processors: each adds 32 numbers locally, then the partial sums combine in a tree. How many parallel steps does it take, and what is the cost?

**11.** Assertion (A): A Las Vegas algorithm can be converted into a Monte Carlo algorithm.
Reason (R): Stopping a Las Vegas algorithm after twice its expected running time fails with probability at most 1/2 by Markov’s inequality.
(1) both true, R explains A (2) both true, R does not explain A (3) A true, R false (4) A false, R true

**12.** A Monte Carlo test has one-sided error at most 1/2 per run. How many independent runs push the error below 0.001?

**13.** Solve x ≡ 1 (mod 4), x ≡ 2 (mod 5), x ≡ 3 (mod 7) for the smallest non-negative x.

**14.** Statement I: The Fermat test aⁿ⁻¹ ≡ 1 (mod n) never declares a composite number prime.
Statement II: 561 is a Carmichael number.
(1) both true (2) both false (3) I true, II false (4) I false, II true

**15.** Star graph K₁,₅ (centre c, leaves 1 to 5). Give the size of the cover returned by APPROX-VERTEX-COVER, the optimum, and the ratio.
