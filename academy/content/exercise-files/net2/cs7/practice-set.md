# Practice set 1.7: Boolean algebra

Time yourself: problems 1–8 in 12 minutes, problems 9–15 in 12 minutes. Every question has four options; choose one. Draw every K-map in Gray order (00, 01, 11, 10).

**1.** The minimal SOP of F(A, B, C, D) = Σm(0, 1, 3, 7, 8, 9, 11, 15) is:
(1) CD + B′C′  (2) CD + B′D + B′C′  (3) B′D + C′D′  (4) CD + A′B′C′

**2.** The minimal SOP of F(A, B, C, D) = Σm(1, 3, 4, 5, 9, 11, 12, 13) is:
(1) C′D + BC′  (2) B′D + BC′  (3) B′D + C′D + BC′  (4) B′D + BD′

**3.** For F(A, B, C, D) = Σm(1, 3, 7, 11, 15) + d(0, 2, 5), the minimal POS is:
(1) D(A + C)  (2) (A′ + D)(C + D)(B′ + D)  (3) D(A′ + C)  (4) C(A′ + D)

**4.** The minimal SOP of F(A, B, C, D) = Σm(0, 4, 5, 7, 8, 9, 13, 15) is:
(1) BD + C′D′ + AC′D  (2) BD + A′C′D′ + AB′C′  (3) BD + B′C′D′ + A′BC′ + AC′D  (4) BD + A′C′ + AB′C′

**5.** F(A, B, C) = AB + A′C′. Its canonical forms are:
(1) Σm(0, 2, 6, 7) and ΠM(1, 3, 4, 5)  (2) Σm(0, 1, 6, 7) and ΠM(2, 3, 4, 5)  (3) Σm(0, 2, 6, 7) and ΠM(0, 2, 6, 7)  (4) Σm(1, 3, 4, 5) and ΠM(0, 2, 6, 7)

**6.** For F = (A + B′)(C + D), the dual and the complement are respectively:
(1) AB′ + CD and A′B + C′D′  (2) A′B + C′D′ and AB′ + CD  (3) AB′ + CD and (A′ + B)(C′ + D′)  (4) A + B′C + D and A′B + C′D′

**7.** The number of self-dual Boolean functions of 4 variables is:
(1) 16  (2) 128  (3) 256  (4) 65536

**8.** The number of Boolean functions of 3 variables with F(0, 0, 0) = 0 and F(1, 1, 1) = 1 is:
(1) 32  (2) 64  (3) 128  (4) 256

**9.** Assertion (A): {⊕, ∧} is not functionally complete.
Reason (R): Both ⊕ and ∧ output 0 when all their inputs are 0.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**10.** Match List I with List II.

| List I (identity) | List II (name) |
|---|---|
| A. x + x′y = x + y | I. Involution |
| B. (x′)′ = x | II. Consensus |
| C. (x + y)(x′ + z)(y + z) = (x + y)(x′ + z) | III. Redundant literal (absorption variant) |
| D. (xy)′ = x′ + y′ | IV. De Morgan |

(1) A-III, B-I, C-II, D-IV  (2) A-II, B-I, C-III, D-IV  (3) A-III, B-IV, C-II, D-I  (4) A-I, B-III, C-II, D-IV

**11.** Which of the following sets are functionally complete?
A. {NAND}  B. {∧, ⊕}  C. {→, ¬}  D. {↔, ¬}  E. {∨, ¬}
(1) A, C and E only  (2) A, B, C and E only  (3) A and E only  (4) A, C, D and E only

**12.** The minimal SOP of F(A, B, C, D, E) = Σm(0, 2, 5, 7, 8, 10, 13, 15, 16, 18, 21, 23, 24, 26, 29, 31) is:
(1) B′E′ + BE  (2) C′E′ + CE  (3) A′C′E′ + CE  (4) C ⊕ E

**13.** Arrange in the correct order the steps of simplifying with a K-map:
A. Pick all essential prime implicants
B. Draw the map with Gray-code labels and plot the 1s and don’t-cares
C. Cover the remaining 1s with the fewest, largest prime implicants
D. Identify all prime implicants (largest possible groups)
(1) B, D, A, C  (2) B, A, D, C  (3) D, B, A, C  (4) B, D, C, A

**14.** Statement I: x + yz = (x + y)(x + z) holds in every Boolean algebra.
Statement II: x(y + z) = xy + z holds in every Boolean algebra.
(1) Both true  (2) Both false  (3) Statement I true, Statement II false  (4) Statement I false, Statement II true

**15.** For F(A, B, C) = Σm(0, 1, 2, 5, 6, 7), the numbers of prime implicants, essential prime implicants and distinct minimal SOPs are:
(1) 6, 0, 2  (2) 6, 2, 1  (3) 3, 3, 1  (4) 6, 0, 1
