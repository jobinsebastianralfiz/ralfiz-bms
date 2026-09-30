# Solutions: practice set 4.4 (Normalization)

**1.** (AB)⁺: start AB; AB → C gives C; C → DE gives D, E; E → F gives F. FG → A cannot fire (no G). **(AB)⁺ = ABCDEF.**
(CG)⁺: start CG; C → DE gives D, E; E → F gives F; FG → A gives A; AB → C adds nothing new because B is missing. **(CG)⁺ = ACDEFG.** Neither is a superkey: G is on no right side, so every key must contain G, and B is missing from (CG)⁺.

**2.** Answer (3). A is on no right-hand side, so it is in every key, but A⁺ = A. The chain C → D → E → F → B → (with A) C means (AB)⁺, (AC)⁺, (AD)⁺, (AE)⁺ and (AF)⁺ are all ABCDEF. Each is minimal because A⁺ = A and no single other attribute alone reaches A. Keys: AB, AC, AD, AE, AF.

**3.** Answer (2). Every key contains A plus at least one of B, C, D, E, F. A superkey is A plus any non-empty subset of the other five: 2⁵ − 1 = **31**.

**4.** Both FDs A → C and B → C are derivable from each other with A ↔ B, so exactly one of them is redundant. Minimal cover 1: {A → B, B → A, B → C}. Minimal cover 2: {A → B, B → A, A → C}. Minimal covers are not unique.

**5.** B is never on a right side. (AB)⁺ = ABCDE, (BC)⁺ = BCDEA, (BD)⁺ = BDA and then AB → CD: all. Keys: **AB, BC, BD**. Prime: A, B, C, D. D → A: D is not a superkey, A is prime, so BCNF fails but 3NF holds. BC → DE and AB → CD have key left sides. **Highest: 3NF.**

**6.** Answer (1). Only key AB (A and B are on no right side). A → DE: D, E non-prime and A is a proper subset of the key: partial dependency, so not 2NF. **1NF.**

**7.** Minimal cover: AB → C, A → D, A → E, B → F, F → G, F → H. Relations: ABC, ADE, BF, FGH. ABC contains the key AB. **4 relations**, and each is in BCNF (each has one left side, which is its key).

**8.** Tableau:

| | A | B | C | D | E |
|---|---|---|---|---|---|
| AB | a1 | a2 | b13 | b14 | b15 |
| CD | b21 | b22 | a3 | a4 | b25 |
| ACE | a1 | b32 | a3 | b34 | a5 |

A → B: rows 1 and 3 agree on A, so row 3 B = a2. C → D: rows 2 and 3 agree on C, so row 3 D = a4. Row 3 becomes a1 a2 a3 a4 a5: **lossless**.

**9.** A → B is in AB and C → D is in CD. B → E: B occurs only in AB, and inside AB the closure of B is B. E is unreachable, so **B → E is lost**. Not dependency preserving.

**10.** Keys: **A, E, BC, CD** (A⁺ = E⁺ = ABCDE, (BC)⁺ = BCD → E → A, (CD)⁺ = CDE → A → B). Every attribute is prime, so R is in **3NF**; B → D violates BCNF. Decompose on B → D: R1(B, D) and R2(A, B, C, E). In R2 the projected FDs are A → BC, E → A, BC → E (BC⁺ = ABCDE), and the keys of R2 are A, E, BC, so R2 is in BCNF. R1 is BCNF (two attributes). CD → E is lost: C and D never meet in one relation, so the decomposition is lossless but **not dependency preserving**.

**11.** Answer (1): 2NF forbids partial dependencies (II), 3NF forbids transitive dependencies of non-prime attributes (III), BCNF forbids any non-superkey determinant (IV), 4NF forbids non-trivial MVDs with a non-superkey left side (I).

**12.** Answer (1). P → Q makes P⁺ = PQ, so P is a key and the only non-trivial FD has a key on the left. R is true in general and explains A.

**13.** Answer (3). Each BCNF split on X → Y keeps X in both parts and X → XY, so it is lossless. Statement II is false: R(S, C, T) with SC → T, T → C has no dependency-preserving BCNF decomposition.

**14.** (a) Every teacher is paired with every book: 2 × 3 = **6 tuples**. (b) Course →→ Teacher and Course →→ Book (complementation of each other). The only key is all three attributes, so the MVDs have non-superkey left sides: R is in BCNF but not 4NF. (c) R1(Course, Teacher) with 2 tuples and R2(Course, Book) with 3 tuples: **5 tuples** instead of 6. The saving grows quickly: 10 teachers and 10 books need 100 tuples in R but only 20 after decomposition.

**15.** Answer (1). Supersets of AB: 2⁴ = 16. Supersets of CD: 2⁴ = 16. Supersets of ABCD: 2² = 4. Total 16 + 16 − 4 = **28**.
