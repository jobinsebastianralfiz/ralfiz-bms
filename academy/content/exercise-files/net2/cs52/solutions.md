# Solutions: 7.8 Advanced algorithms

**1.** π = 0 0 0 0 1 2 3 1. The borders of abcda, abcdab and abcdabc are a, ab and abc. At the last a, extending abc needs P[4] = d, so fall back to π[3] = 0, where P[1] = a matches, giving 1.

**2.** π = 0 1 0 1 2 2 3. After aabaa (2), the next character is a but P[3] = b. Fall back to π[2] = 1, where P[2] = a matches, giving 2. For the last b, P[3] = b matches, giving 3.

**3.** p = 26 mod 11 = 4. The window hashes of 31, 14, 41, 15, 59, 92, 26, 65, 53 are 9, 3, 8, 4, 4, 4, 4, 10, 9. Hash 4 occurs at shifts 3, 4, 5 and 6. Only shift 6 (26) is valid, so there are **3 spurious hits** (15, 59, 92).

**4.** There are n − m + 1 = 10 shifts. Every shift matches fully in 3 comparisons, so 30 comparisons and **10 matches**.

**5.** 3276 = 2·1260 + 756; 1260 = 1·756 + 504; 756 = 1·504 + 252; 504 = 2·252 + 0. The gcd is **252**, in 4 steps.

**6.** 40 = 5·7 + 5; 7 = 1·5 + 2; 5 = 2·2 + 1. Back-substituting: 1 = 5 − 2·2 = 5 − 2(7 − 5) = 3·5 − 2·7 = 3(40 − 5·7) − 2·7 = 3·40 − 17·7. So 7⁻¹ ≡ −17 ≡ **23**. Check: 7 × 23 = 161 = 4·40 + 1.

**7.** n = 221 and φ = 12 × 16 = 192. d = 5⁻¹ mod 192 = **77** (5 × 77 = 385 = 2·192 + 1). C = 2⁵ mod 221 = **32**.

**8.** By Fermat, 6¹⁰ ≡ 1 (mod 11). 73 mod 10 = 3, so 6³ = 216 = 19·11 + 7, and the answer is **7**.

**9. (1)** Automaton preprocessing O(m|Σ|), KMP π Θ(m), Rabin–Karp expected O(n + m), naive needs no preprocessing.

**10.** 31 local steps plus log₂ 32 = 5 tree steps = **36 steps**. Cost = 32 × 36 = 1152 = Θ(n), so it is cost-optimal (compared with 1023 sequential additions).

**11. (1)** Markov: P(time ≥ 2·E[T]) ≤ 1/2. Stopping there and reporting failure gives a bounded-time algorithm that errs with probability ≤ 1/2, which is exactly the conversion.

**12.** (1/2)ᵏ < 0.001 needs 2ᵏ > 1000. k = 10 gives 1/1024 ≈ 0.00098. The answer is **10 runs**.

**13.** The candidates for x ≡ 3 (mod 7) are 3, 10, 17, … and 17 is the first that is ≡ 2 (mod 5). 17 mod 4 = 1 also holds. **x = 17** (unique mod 140).

**14. (4)** Carmichael numbers such as 561 = 3·11·17 satisfy a⁵⁶⁰ ≡ 1 (mod 561) for every a coprime to 561. So the Fermat test can call a composite prime (I false), and II is true.

**15.** The first edge chosen, c–i, puts c and i in the cover, which covers every edge. The algorithm returns **2** against an optimum of **1**, a ratio of **2**, which is tight.
