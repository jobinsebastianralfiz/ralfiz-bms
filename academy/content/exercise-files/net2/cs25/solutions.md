# Solutions: Practice set 4.2

**1. Answer: (1) {s1}.** Red parts = {p1, p3}. s1 has p1 and p3. s2 lacks p3, s3 has neither, and s4 lacks p1. Trap: (3) counts suppliers with at least one red part and ignores s2.

**2. Answer: (2) 8.** Every SP tuple’s Pno exists in P exactly once (Pno is P’s key), so the join keeps all 8 SP tuples.

**3. Answer: (2) {s3}.** Suppliers of some red part: s1 (p1, p3), s2 (p1), s4 (p3). All suppliers: {s1, s2, s3, s4}. Difference: {s3}.

**4. Answer: (3) 3.** {p1, p2, p3}: duplicates are removed.

**5. Answer: (2) {s1}.** Only s1 supplies all three parts.

**6. Answer: (1) 40.** Supersets of A: 2⁵ = 32. Supersets of BC: 2⁴ = 16. Supersets of ABC: 2³ = 8. Total 32 + 16 − 8 = 40.

**7. Answer: (3) 8.** |AB| = |BC| = |CD| = 2² = 4 each, for a sum of 12. Pairwise overlaps: AB∪BC = ABC gives 2, AB∪CD = ABCD gives 1, BC∪CD = BCD gives 2, for a sum of 5. The triple overlap ABCD gives 1. So 12 − 5 + 1 = 8. Check by listing: AB, BC, CD, ABC, ABD, ACD, BCD, ABCD.

**8. Answer: (2) 3 and 8.** At most all 5 S tuples are also in R, so at least 8 − 5 = 3 remain. If they share nothing, all 8 remain.

**9. Answer: (1) A-III, B-IV, C-I, D-II.**

**10. Answer: (1).** Both are true, and the identity in R shows how.

**11. Answer: (4).** Removing a referencing tuple cannot leave a dangling reference, so I is false. An insert with a NULL primary key breaks entity integrity, so II is true.

**12. Answer: (1) A, B and C only.** D is false: the degree of R ÷ S is deg R − deg S.

**13. Answer: (1) 2 and 3.** The degree is 4 − 2 = 2. At most ⌊20/6⌋ = 3.

**14. Answer: (2) 6.** C(4, 2) = 6: AB, AC, AD, BC, BD, CD.

**15. Answer: (2) 3.** Deleting 2 cascades to 3 and 7 (Next = 2), then to 4 (Next = 3). Removed: 2, 3, 4, 7. Remaining: 1, 5, 6, which is 3 tuples.
