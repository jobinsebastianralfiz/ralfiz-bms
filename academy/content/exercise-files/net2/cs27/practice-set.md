# Practice set 4.4: Normalization

Time yourself: problems 1–8 in 14 minutes, problems 9–15 in 12 minutes. Each carries 2 marks; there is no negative marking.

**1.** R(A, B, C, D, E, F, G) has F = {AB → C, C → DE, E → F, FG → A}. Find (AB)⁺ and (CG)⁺.

**2.** R(A, B, C, D, E, F) has F = {AB → C, C → D, D → E, E → F, F → B}. List all candidate keys.
(1) AB only (2) AB, AC (3) AB, AC, AD, AE, AF (4) AB, AF

**3.** For the relation in problem 2, how many superkeys does R have?
(1) 16 (2) 31 (3) 32 (4) 63

**4.** F = {A → B, B → A, A → C, B → C}. Give two different minimal covers of F.

**5.** R(A, B, C, D, E) has F = {AB → CD, D → A, BC → DE}. Find the candidate keys and the highest normal form.

**6.** R(A, B, C, D, E, F, G, H) has F = {AB → C, A → DE, B → F, F → GH}. What is the highest normal form?
(1) 1NF (2) 2NF (3) 3NF (4) BCNF

**7.** Decompose the relation of problem 6 into 3NF with the synthesis algorithm. How many relations do you get, and is any of them not in BCNF?

**8.** R(A, B, C, D, E) has F = {A → B, C → D, B → E}. Use the chase to decide whether {AB, CD, ACE} is lossless.

**9.** For problem 8, is the decomposition dependency preserving? If not, name a lost FD.

**10.** R(A, B, C, D, E) has F = {A → BC, CD → E, B → D, E → A}. Find all candidate keys, the highest normal form, and a BCNF decomposition. Is your decomposition dependency preserving?

**11.** Match List I with List II.

| List I (Normal form) | List II (What it forbids) |
|---|---|
| A. 2NF | I. Non-trivial MVD with a non-superkey left side |
| B. 3NF | II. Non-prime attribute depending on part of a key |
| C. BCNF | III. Non-prime attribute depending on a non-superkey |
| D. 4NF | IV. Any non-trivial FD with a non-superkey left side |

(1) A-II, B-III, C-IV, D-I (2) A-III, B-II, C-IV, D-I (3) A-II, B-IV, C-III, D-I (4) A-II, B-III, C-I, D-IV

**12.** Assertion (A): R(P, Q) with P → Q is in BCNF.
Reason (R): In a two-attribute relation, the determinant of any non-trivial FD is a candidate key.
Choose: (1) both true, R explains A (2) both true, R does not explain A (3) A true, R false (4) A false, R true

**13.** Statement I: BCNF decomposition is always lossless.
Statement II: For every relation there is a BCNF decomposition that is lossless and dependency preserving.
Choose: (1) both true (2) both false (3) I true, II false (4) I false, II true

**14.** R(Course, Teacher, Book) records that each teacher of a course uses every book of that course, independently. The course DBMS has 2 teachers and 3 books. (a) How many tuples does R hold for DBMS? (b) Which MVDs hold? (c) Give the 4NF decomposition and the number of tuples it stores for DBMS.

**15.** R(A, B, C, D, E, F) has exactly two candidate keys, AB and CD. How many superkeys does R have?
(1) 28 (2) 32 (3) 24 (4) 30
