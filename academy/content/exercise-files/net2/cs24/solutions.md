# Solutions: Practice set 4.1

**1. Answer: (2) 6.** Entities: DOCTOR, PATIENT, WARD, HOSPITAL = 4. HOSPITAL–WARD (1:N) and WARD–PATIENT (1:N) are absorbed as foreign keys (+0). TREATS (M:N) = +1 → 5. Qualification (multivalued) = +1 → 6. Age is derived, so it is not stored. Trap: option (4) counts both 1:N relationships.

**2. Answer: (2) 2.** E1(a, b, c) with c UNIQUE NOT NULL referencing E2, and E2(c, d). A merged table would need NULL in a for unpaired E2 entities.

**3. Answer: (1) 1.** Every E1 pairs with exactly one E2 and vice versa, so E(a, b, c, d) stores all of them with no NULLs.

**4. Answer: (3) 3.** ROOM’s key = (BId, RoomNo). BED’s key = ROOM’s key + BedNo = (BId, RoomNo, BedNo).

**5. Answer: (1) 18 and 18.** Each B is in at most one instance (1:N, with B on the many side) and at least one (total), so there are exactly 18. Trap: 540 = 30 × 18 applies only to M:N.

**6. Answer: (1) A-I, B-II, C-III, D-IV.** An index is an internal-schema change (physical). A new column changes the conceptual schema (logical). Inserting rows changes the instance, not any schema. Redefining one view changes only that external schema. Trap: option (2) swaps physical and logical.

**7. Answer: (1).** Both are true, and R explains A: one row of SUPPLIER cannot hold a set of (part, project) pairs.

**8. Answer: (4).** Statement I is false: a DBMS controls redundancy but does not remove it entirely (foreign keys repeat, and replication and indexes duplicate data). Statement II is true.

**9. Answer: (2) A, B, D and E only.** Query optimisation is a DBMS feature, not a file-system problem.

**10. Answer: (1) D, B, C, A, E.** Strong entities, then weak entities, then 1:1 and 1:N, then M:N, then multivalued attributes, then n-ary relationships.

**11. Answer: (2) 8D, 7 columns.** Overlapping subclasses need option 8D, a single table with one Boolean flag per subclass (8C’s single type attribute works only for disjoint subclasses). Columns: VId, Reg, Price (3 superclass attributes) + CarFlag, TruckFlag (2 flags) + Seats, Tonnage (2 local attributes) = 7. 8B is ruled out because the specialisation is partial.

**12. Answer: (2) 5.** Entities: STUDENT, COURSE, INSTRUCTOR = 3. ENROLS (M:N) = +1 → 4. MENTORS (recursive 1:N) is a self-referencing foreign key (+0). INSTRUCTOR–COURSE (1:N) = +0. Phone (multivalued) = +1 → 5.

**13. Answer: (2).** One table, with SupervisorId as a foreign key referencing EmpId in the same table.

**14. Answer: (2).** (10,60) next to SECTION means each section takes part in 10 to 60 ENROLS instances, which means 10 to 60 students. Each student takes 1 to 5 sections, so (4) is false. Since both maxima exceed 1, the ratio is M:N, not 1:N.

**15. Answer: (1) A-III, B-I, C-II, D-IV.**
