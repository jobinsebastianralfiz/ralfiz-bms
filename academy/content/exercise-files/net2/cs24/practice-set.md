# Practice set 4.1: Database concepts, architecture and ER modelling

Time: 24 minutes (about 90 seconds per problem). No notes. Each problem has one correct option.
Convention for table counts: minimum number of tables with no NULL allowed in any primary key.

**1.** A hospital design has entity sets DOCTOR, PATIENT, WARD and HOSPITAL. HOSPITAL–WARD is 1:N, WARD–PATIENT is 1:N, DOCTOR–PATIENT (TREATS, attribute Date) is M:N, DOCTOR has a multivalued attribute Qualification and PATIENT has a derived attribute Age. What is the minimum number of tables?
(1) 5  (2) 6  (3) 7  (4) 8

**2.** E1(a, b) and E2(c, d) are linked by a 1:1 relationship. E1 participates totally and E2 partially. What is the minimum number of tables?
(1) 1  (2) 2  (3) 3  (4) 4

**3.** E1(a, b) and E2(c, d) are linked by a 1:1 relationship with total participation on both sides. What is the minimum number of tables?
(1) 1  (2) 2  (3) 3  (4) 4

**4.** BUILDING(BId) owns the weak entity set ROOM (partial key RoomNo), and ROOM owns the weak entity set BED (partial key BedNo). How many attributes make up the primary key of the BED table?
(1) 1  (2) 2  (3) 3  (4) 4

**5.** |A| = 30 and |B| = 18. Relationship R is 1:N with A on the one side and B on the many side. B participates totally. What are the minimum and maximum numbers of relationship instances?
(1) 18 and 18  (2) 0 and 18  (3) 18 and 540  (4) 30 and 540

**6.** Match List I with List II.

| List I (Change) | List II (What it needs or affects) |
|---|---|
| A. Creating a B+ tree index on Salary | I. Physical data independence |
| B. Adding a new column Email to STUDENT | II. Logical data independence |
| C. Inserting 500 new STUDENT rows | III. Only the database instance (state) changes |
| D. Redefining the view used by the accounts section | IV. Only one external schema changes |

(1) A-I, B-II, C-III, D-IV  (2) A-II, B-I, C-III, D-IV  (3) A-I, B-II, C-IV, D-III  (4) A-I, B-III, C-II, D-IV

**7.** Assertion (A): A ternary relationship always needs a separate table.
Reason (R): A single foreign key in one entity table cannot record which pair of the other two entities goes with it.
(1) Both true, R explains A  (2) Both true, R does not explain A  (3) A true, R false  (4) A false, R true

**8.** Statement I: A DBMS removes all redundancy, so no data item is ever stored twice.
Statement II: Integrity constraints in a DBMS are stored in the catalog instead of being buried in application code.
(1) Both true  (2) Both false  (3) I true, II false  (4) I false, II true

**9.** Which of the following are drawbacks of file-processing systems?
A. Data isolation  B. Atomicity problems  C. Query optimisation  D. Concurrent-access anomalies  E. Security problems
(1) A, B and D only  (2) A, B, D and E only  (3) B, C and E only  (4) A, C, D and E only

**10.** Arrange the Elmasri–Navathe mapping steps in order:
A. Multivalued attributes  B. Weak entity types  C. Binary 1:N relationships  D. Strong entity types  E. n-ary relationships
(1) D, B, C, A, E  (2) D, C, B, A, E  (3) B, D, C, A, E  (4) D, B, A, C, E

**11.** VEHICLE(VId, Reg, Price) has an overlapping, partial specialisation into CAR(Seats) and TRUCK(Tonnage). Which single-table option is correct, and how many columns does that table have?
(1) 8C, 5 columns  (2) 8D, 7 columns  (3) 8D, 5 columns  (4) 8B, 7 columns

**12.** STUDENT(RollNo) and COURSE(CId) are linked by M:N ENROLS (attribute Grade). STUDENT also has a recursive 1:N relationship MENTORS. INSTRUCTOR(IId) has a 1:N relationship to COURSE and a multivalued attribute Phone. What is the minimum number of tables?
(1) 4  (2) 5  (3) 6  (4) 7

**13.** In a recursive 1:N relationship SUPERVISES on EMPLOYEE, how many tables are required and how is it stored?
(1) 2: a separate SUPERVISES table  (2) 1: a SupervisorId foreign key in EMPLOYEE  (3) 1: SupervisorId as primary key  (4) 2: EMPLOYEE is split in two

**14.** In (min, max) notation, STUDENT (1,5) — ENROLS — (10,60) SECTION. Which statement is correct?
(1) Every student takes at least 10 sections  (2) A section has between 10 and 60 students  (3) The cardinality ratio is 1:N  (4) Students may take no sections

**15.** Match List I with List II.

| List I (Attribute) | List II (Kind) |
|---|---|
| A. Age, computed from DateOfBirth | I. Composite |
| B. Address = (Street, City, PIN) | II. Multivalued |
| C. Set of phone numbers | III. Derived |
| D. RoomNo of a ROOM owned by a BUILDING | IV. Partial key |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-II, C-I, D-IV  (4) A-III, B-I, C-IV, D-II
