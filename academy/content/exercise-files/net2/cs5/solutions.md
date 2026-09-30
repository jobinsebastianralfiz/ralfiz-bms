# Solutions: Practice set 1.5

**1.** Generators of ℤₙ are the k coprime to n: φ(18) = 18 × (1 − ½)(1 − ⅓) = 6, namely 1, 5, 7, 11, 13, 17. Trap: 17 assumes every non-zero element generates, which is true only for prime n. **Answer: (2) 6**

**2.** o(4) = 18 / gcd(18, 4) = 18/2 = 9. Check: 9 × 4 = 36 ≡ 0 and no smaller multiple of 4 is a multiple of 18. **Answer: (3) 9**

**3.** 2, 4, 8, 16 ≡ 1 (mod 15). So o(2) = 4. It divides |U(15)| = 8 as Lagrange requires. U(15) is not cyclic: its largest element order is 4. **Answer: (1) 4**

**4.** One subgroup per divisor of 20: 1, 2, 4, 5, 10, 20, so 6 subgroups. Trap: 8 is φ(20), the number of generators. **Answer: (4) 6**

**5.** Identity: a + e + 3 = a gives e = −3. Inverse b: a + b + 3 = −3 gives b = −a − 6, so the inverse of 4 is −10. Check: 4 * (−10) = 4 − 10 + 3 = −3 = e. Trap: −4 uses the identity of ordinary addition. **Answer: (3) −10**

**6.** Index = 42/6 = 7 cosets. **Answer: (2) 7**

**7.** Disjoint cycles of lengths 3 and 5: lcm(3, 5) = 15. Trap: 8 adds the lengths. **Answer: (3) 15**

**8.** In a cyclic group of order 25, the elements of order 5 number φ(5) = 4: they are 5, 10, 15, 20. **Answer: (1) 4**

**9.** Non-zero elements: 19. Units: φ(20) = 8 (1, 3, 7, 9, 11, 13, 17, 19). Zero divisors: 19 − 8 = 11 (2, 4, 5, 6, 8, 10, 12, 14, 15, 16, 18). **Answer: (4) 11**

**10.** (ℕ, +): no identity, since 0 ∉ ℕ, so a semigroup only (III). (ℕ ∪ {0}, +): identity 0 but no negatives, so a monoid (IV). (ℤ, +): abelian group (I). (ℤ, −): closed but not associative, so only a groupoid (II). **Answer: (1) A-III, B-IV, C-I, D-II**

**11.** 3² = 9 ≡ 1, 5² = 25 ≡ 1, 7² = 49 ≡ 1 (mod 8). A cyclic group of order 4 needs an element of order 4, and there is none, so R explains A. **Answer: (1) Both (A) and (R) are true and (R) is the correct explanation of (A)**

**12.** Statement I is false: S₃ has order 6 and is not abelian. Statement II is true: 5 is prime, so the group is cyclic by Lagrange. **Answer: (4) Statement I is false but Statement II is true**

**13.** The subgroups of ℤ₁₂ are exactly ⟨d⟩ for d dividing 12: ⟨6⟩ = {0, 6}, ⟨4⟩ = {0, 4, 8}, ⟨3⟩ = {0, 3, 6, 9}, ⟨2⟩ = {0, 2, …, 10}. {0, 5} is not closed: 5 + 5 = 10 is missing. **Answer: (2) A, B, C and E only**

**14.** φ(11) = 10, φ(6) = 2, φ(15) = 8, φ(5) = 4, φ(7) = 6. Increasing: ℤ₆ (2), ℤ₅ (4), ℤ₇ (6), ℤ₁₅ (8), ℤ₁₁ (10). **Answer: (1) B, D, E, C, A**

**15.** f(x) = 3x ≡ 0 (mod 12) exactly when x ∈ {0, 4, 8}, so the kernel has 3 elements. The image is {0, 3, 6, 9} (4 elements), and 3 × 4 = 12 = |ℤ₁₂|, as the first isomorphism theorem requires. **Answer: (3) 3**