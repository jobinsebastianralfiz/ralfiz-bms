# Solutions: practice set 1.7 (Boolean algebra)

**1. Answer (1) CD + B′C′.**
Map the 1s: 0, 1, 8, 9 form the quad B′C′ (rows 00 and 10, columns 00 and 01). 3, 7, 15, 11 form the column quad CD.
The prime implicants are CD, B′C′ and B′D (1, 3, 9, 11). CD alone covers 7 and 15, and B′C′ alone covers 0 and 8, so both are essential. Together they cover everything.
B′D is prime but redundant, so option (2) is not minimal.

**2. Answer (2) B′D + BC′.**
Quad B′D = {1, 3, 9, 11} and quad BC′ = {4, 5, 12, 13}. Both are essential and cover all eight 1s.
C′D = {1, 5, 9, 13} is also a prime implicant, but it is redundant. B′D + BD′ is wrong: BD′ contains m6, which is a 0.

**3. Answer (3) D(A′ + C).**
The 0-cells are 4, 6, 8, 9, 10, 12, 13, 14, with don't-cares 0, 2, 5. Grouping the 0s gives D′ (the octet of columns 00 and 10, using X0 and X2) and AC′ (8, 9, 12, 13). So F′ = D′ + AC′.
By De Morgan, F = D(A′ + C) = A′D + CD. Check: m1 = 0001 gives 1·1 = 1, and m9 = 1001 gives 1·0 = 0. Both are correct.
Note that the SOP has two minimal forms, CD + A′D and CD + A′B′. The POS asked for here is unique.

**4. Answer (2) BD + A′C′D′ + AB′C′.**
The prime implicants are BD, B′C′D′, A′C′D′, A′BC′, AC′D and AB′C′. Only BD is essential.
After taking BD, the uncovered 1s are 0, 4, 8, 9. The pair A′C′D′ covers 0 and 4, and the pair AB′C′ covers 8 and 9. That is 3 terms and 8 literals, and exhaustive search shows no 3-term cover with fewer literals.
Option (1) uses C′D′, which contains m12 (a 0). Option (4) uses A′C′, which contains m1 (a 0). Option (3) is correct but has 4 terms.

**5. Answer (1).**
AB gives rows 6 and 7. A′C′ gives rows 0 and 2. So F = Σm(0, 2, 6, 7), and the maxterms are the rest: ΠM(1, 3, 4, 5).

**6. Answer (1).**
Dual: swap · and +, keeping the literals: AB′ + CD.
Complement: (A + B′)′ + (C + D)′ = A′B + C′D′.
Option (3) gives the dual correctly, but its second expression (A′ + B)(C′ + D′) is the dual of the complement. It is not the complement itself.

**7. Answer (3) 256.**
The count is 2^(2^(n−1)) = 2^8 = 256. A 4-variable table has 16 rows in 8 complementary pairs, and each pair has 2 choices.

**8. Answer (2) 64.**
Two of the 8 rows are fixed, and the other 6 are free, so 2^6 = 64.

**9. Answer (1).**
(R) is true: ⊕ and ∧ are both 0-preserving, so they lie in Post's class T0. Anything built from them outputs 0 on the all-zero input, so NOT can never be produced, and (A) is true. (R) is precisely the reason.

**10. Answer (1) A-III, B-I, C-II, D-IV.**
x + x′y = x + y is the redundant-literal rule (III). (x′)′ = x is involution (I). The three-sum product is the POS form of consensus (II). (xy)′ = x′ + y′ is De Morgan (IV).

**11. Answer (1) A, C and E only.**
- {NAND} is complete.
- {→, ¬} is complete, because x′ → y = x + y.
- {∨, ¬} is complete by De Morgan.
- {∧, ⊕} is incomplete, because both operations preserve 0.
- {↔, ¬} is incomplete, because both operations are linear.

**12. Answer (2) C′E′ + CE.**
The A = 1 minterms are the A = 0 minterms plus 16, so A drops out. In the variables B, C, D, E, the corners (0, 2, 8, 10) give C′E′ and the centre (5, 7, 13, 15) gives CE.
Option (4), C ⊕ E, is the complement. Option (3) wrongly keeps A′ in the first term.

**13. Answer (1) B, D, A, C.**
Draw and plot the map, then list the prime implicants, then take the essentials, then cover the remaining 1s.

**14. Answer (3).**
Statement I is the second distributive law, which is a postulate. Statement II fails for x = 0, z = 1: the left side is 0 and the right side is 1.

**15. Answer (1) 6, 0, 2.**
The 1s form a cycle of six adjacent pairs: A′B′, B′C, AC, AB, BC′ and A′C′. Each 1 is covered by two of these pairs, so there are no essential prime implicants.
There are two alternate 3-term covers: B′C + A′C′ + AB and A′B′ + AC + BC′.
