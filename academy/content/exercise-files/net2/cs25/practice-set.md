# Practice set 4.2: Relational model, algebra and calculus

Time: 24 minutes. No notes. Relational algebra uses set semantics (no duplicate tuples).

Problems 1–5 use these relations:

    SP(Sno, Pno)            P(Pno, Color)
    s1  p1                  p1  red
    s1  p2                  p2  blue
    s1  p3                  p3  red
    s2  p1
    s2  p2
    s3  p2
    s4  p2
    s4  p3

**1.** Find SP ÷ π Pno (σ Color='red' (P)).
(1) {s1}  (2) {s1, s2, s4}  (3) {s1, s4}  (4) {s2, s4}

**2.** How many tuples are in SP ⋈ P?
(1) 3  (2) 8  (3) 24  (4) 11

**3.** Find π Sno (SP) − π Sno (σ Color='red' (SP ⋈ P)).
(1) {s2}  (2) {s3}  (3) {s3, s4}  (4) { }

**4.** How many tuples are in π Pno (SP)?
(1) 8  (2) 4  (3) 3  (4) 2

**5.** Find SP ÷ π Pno (P).
(1) { }  (2) {s1}  (3) {s1, s4}  (4) {s1, s2}

**6.** R(A, B, C, D, E, F) has exactly two candidate keys, A and BC. How many superkeys does R have?
(1) 40  (2) 48  (3) 32  (4) 56

**7.** R(A, B, C, D) has exactly three candidate keys: AB, BC and CD. How many superkeys does R have?
(1) 12  (2) 7  (3) 8  (4) 10

**8.** R and S are union compatible, |R| = 8 and |S| = 5. What are the minimum and maximum numbers of tuples in R − S?
(1) 0 and 8  (2) 3 and 8  (3) 3 and 5  (4) 0 and 3

**9.** Match List I with List II.

| List I (Algebra) | List II (SQL) |
|---|---|
| A. σ | I. FROM R CROSS JOIN S |
| B. π | II. AS (alias) |
| C. × | III. WHERE |
| D. ρ | IV. SELECT DISTINCT |

(1) A-III, B-IV, C-I, D-II  (2) A-IV, B-III, C-I, D-II  (3) A-III, B-IV, C-II, D-I  (4) A-III, B-I, C-IV, D-II

**10.** Assertion (A): Division can be written using only π, × and −.
Reason (R): R ÷ S = π X (R) − π X ((π X (R) × S) − R).
(1) Both true, R explains A  (2) Both true, R does not explain A  (3) A true, R false  (4) A false, R true

**11.** Statement I: Deleting a tuple from a referencing relation can violate referential integrity.
Statement II: Inserting a tuple can violate entity integrity.
(1) Both true  (2) Both false  (3) I true, II false  (4) I false, II true

**12.** Which are true?
A. R ⟕ S has at least |R| tuples.  B. R ⋉ S has the attributes of R only.  C. R ⋈ S is commutative up to column order.  D. R ÷ S has degree deg R + deg S.
(1) A, B and C only  (2) A and B only  (3) B, C and D only  (4) A, C and D only

**13.** R(A, B, C, D) ÷ S(C, D): what is the degree of the result, and what is the maximum number of tuples if |R| = 20 and |S| = 6?
(1) 2 and 3  (2) 2 and 4  (3) 4 and 3  (4) 2 and 14

**14.** What is the maximum number of candidate keys of a relation with 4 attributes?
(1) 4  (2) 6  (3) 15  (4) 16

**15.** CHAIN(Id, Next) has Next as a foreign key referencing Id, ON DELETE CASCADE. The tuples are (1, NULL), (2, 1), (3, 2), (4, 3), (5, 1), (6, 5), (7, 2). Deleting the tuple with Id = 2 leaves how many tuples?
(1) 2  (2) 3  (3) 4  (4) 5
