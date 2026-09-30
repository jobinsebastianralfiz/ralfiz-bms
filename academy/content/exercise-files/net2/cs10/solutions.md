# Solutions: practice set 2.2

**1. Answer (1) 9C.D.** 156 = 10011100 = 9C. 0.8125 × 16 = 13.0 → D. So 9C.D. Option (4) is the octal form 234.64.

**2. Answer (2) 5.** 1·b² + 3b + 2 = 42 → b² + 3b − 40 = 0 → (b + 8)(b − 5) = 0 → b = 5. The digit 3 is valid in base 5. Check: 25 + 15 + 2 = 42.

**3. Answer (3) −3253.** No end carry, so the result is negative and its magnitude is the 10’s complement of 6747: 10000 − 6747 = 3253. Answer −3253.

**4. Answer (2) 10100001, V = 1.** 110 + 51 = 161 > 127. Binary sum 01101110 + 00110011 = 10100001 (reads −95). Carry into the sign bit = 1, carry out = 0; they differ, so V = 1.

**5. Answer (2) −120.0.** C2F00000 = 1100 0010 1111 0000 …. Sign 1. Exponent 10000101 = 133, so e = 6. Fraction 1110000…, significand 1.875. −1.875 × 64 = −120.0.

**6. Answer (1) 42AA4000.** 85.125 = 1010101.001₂ = 1.010101001 × 2^6. Sign 0; exponent 6 + 127 = 133 = 10000101; fraction 010101001 then zeros. Bits 0 10000101 01010100100000000000000 = 0100 0010 1010 1010 0100 0… = 42AA4000.

**7. Answer (2) 2^−127.** 00400000 = 0 00000000 10000000000000000000000. Exponent field 0 with non-zero fraction: denormal, value 0.1₂ × 2^−126 = 2^−1 × 2^−126 = 2^−127. Option (1) forgets that a denormal has no hidden 1.

**8. Answer (1) 1010101.** Data d3 = 1, d5 = 1, d6 = 0, d7 = 1.
- p1 (1, 3, 5, 7): d3 ⊕ d5 ⊕ d7 = 1 ⊕ 1 ⊕ 1 = 1
- p2 (2, 3, 6, 7): d3 ⊕ d6 ⊕ d7 = 1 ⊕ 0 ⊕ 1 = 0
- p4 (4, 5, 6, 7): d5 ⊕ d6 ⊕ d7 = 1 ⊕ 0 ⊕ 1 = 0

Code word p1 p2 d3 p4 d5 d6 d7 = 1 0 1 0 1 0 1.

**9. Answer (2) 6 and 38.** r = 5: 32 ≥ 38 fails. r = 6: 64 ≥ 39 holds. Code word = 32 + 6 = 38 bits.

**10. Answer (1) A-III, B-IV, C-I, D-II.** +5 = 0101. Sign-magnitude: 1101. 1’s complement: 1010. 2’s complement: 1011. Excess-8: −5 + 8 = 3 = 0011.

**11. Answer (1).** Both true, and (R) explains (A). Example: 1011 (−8 + 3 = −5) becomes 11011: −16 + 8 + 3 = −5. The new sign bit has weight −16 and the old sign position now has weight +8; together −16 + 8 = −8, the old sign weight. Each extra copy repeats this cancellation.

**12. Answer (1).** ASCII defines 128 characters (0–127) in 7 bits; EBCDIC is IBM’s 8-bit code. Both true.

**13. Answer (1) A, B and E only.** 8421, 2421 and 5211 assign a fixed weight to each bit position. Excess-3 is BCD + 3 (non-weighted) and Gray code is non-weighted.

**14. Answer (1) C, A, D, B.**
- A: 1011.01₂ = 11 + 0.25 = 11.25
- B: 13.3₈ = 8 + 3 + 3/8 = 11.375
- C: B.2₁₆ = 11 + 2/16 = 11.125
- D: 11.3

Increasing: C (11.125) < A (11.25) < D (11.3) < B (11.375).

**15. Answer (2) Units digit; 1000 0101.** Units: 1001 + 0110 = 1111 (15 > 9), add 0110 → 1 0101: digit 5, carry 1. Tens: 0011 + 0100 + 1 = 1000 (8), valid, no correction. Result 1000 0101 = 85.
