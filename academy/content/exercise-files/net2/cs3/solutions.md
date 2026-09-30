# Solutions 1.3: Counting and recurrences

**1. Answer: (1)**
COMMITTEE: C 1, O 1, M 2, I 1, T 2, E 2; 9 letters. 9!/(2!·2!·2!) = 362880/8 = 45360.

**2. Answer: (1)**
Cases by the number of women w: w = 2: C(4, 2)·C(6, 3) = 6 × 20 = 120; w = 3: C(4, 3)·C(6, 2) = 4 × 15 = 60; w = 4: C(4, 4)·C(6, 1) = 6. Total 186. (Complement: 252 − C(6, 5) − C(4, 1)·C(6, 4) = 252 − 6 − 60 = 186.)

**3. Answer: (2)**
Give each variable 1 first; 8 is left for 4 non-negative variables: C(8 + 3, 3) = C(11, 3) = 165. 455 = C(15, 3) counts non-negative solutions.

**4. Answer: (2)**
No bounds: C(17, 2) = 136. One variable ≥ 7: total 8, C(10, 2) = 45, times 3 = 135. Two variables ≥ 7: total 1, C(3, 2) = 3, times 3 = 9. Answer 136 − 135 + 9 = 10. (Listing: (6, 6, 3), (6, 5, 4), (5, 5, 5) and their orders give 3 + 6 + 1 = 10.)

**5. Answer: (3)**
Singles 300 + 200 + 120 = 620; pairs 100 + 60 + 40 = 200; triple 20. Divisible by some: 620 − 200 + 20 = 440. None: 600 − 440 = 160 = 600 × (1/2)(2/3)(4/5).

**6. Answer: (4)**
D₇ = 7·D₆ + (−1)⁷ = 7 × 265 − 1 = 1854. 1855 uses the wrong sign.

**7. Answer: (2)**
Choose the fixed point (5 ways) and derange the other 4 (D₄ = 9): 45.

**8. Answer: (4)**
r² − 6r + 9 = (r − 3)², so aₙ = (α + βn)3ⁿ. a₀ = α = 1; a₁ = 3(1 + β) = 6 gives β = 1. aₙ = (1 + n)3ⁿ, so a₃ = 4 × 27 = 108. Direct check: a₂ = 36 − 9 = 27, a₃ = 162 − 54 = 108.

**9. Answer: (2)**
Fixed point p = 4/(1 − 3) = −2, so aₙ = 3ⁿ(1 + 2) − 2 = 3ⁿ⁺¹ − 2, and a₄ = 243 − 2 = 241. Direct: 1, 7, 25, 79, 241.

**10. Answer: (2)**
The number of BSTs on n distinct keys is Cₙ; C₆ = C(12, 6)/7 = 924/7 = 132.

**11. Answer: (3)**
Three colours are the boxes. Two of each colour (6 socks) avoid three of a kind; the 7th sock makes three. 3(3 − 1) + 1 = 7. The pile sizes do not matter, since each pile has at least 3 socks.

**12. Answer: (3)**
Round table (6 − 1)! = 120 (III); shelf 6! = 720 (IV); committee C(6, 3) = 20 (I); sweets C(6 + 2, 2) = 28 (II).

**13. Answer: (1)**
Positive solutions of x₁ + … + x₄ = 10 number C(9, 3) = 84. R gives exactly this reduction (6 left for 4 boxes, C(9, 3) = C(6 + 3, 3) = 84), so R explains A.

**14. Answer: (2)**
Write each exponent as 1 + yᵢ with yᵢ ∈ {0, 1, 2}; we need y₁ + … + y₄ = 4. Unbounded: C(7, 3) = 35; subtract the cases with some yᵢ ≥ 3: 4 × C(4, 3) = 16. Answer 35 − 16 = 19.

**15. Answer: (1)**
C₅ = 42, D₅ = 44, B₅ = 52, C(8, 3) = 56, S(6, 3) = 90. Increasing: B, A, C, E, D.
