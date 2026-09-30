# Solutions: Practice set 4.3

**1. Answer: (2) 8, 7, 510.** There are 8 rows. One marks value is NULL, so COUNT(marks) = 7. SUM = 80 + 70 + 90 + 60 + 50 + 85 + 75 = 510.

**2. Answer: (1) C1 4 and C2 2.** C1 has marks 80, 90, 50 and 75, so AVG = 73.75. C2 has 70 and 85, so AVG = 77.5. C3 has 60 and NULL, so AVG = 60 (the NULL is ignored). COUNT(*) still counts every row of the group.

**3. Answer: (2) Joel.** ENROLL.sid has no NULLs, so NOT IN behaves normally. Students 1–4 are enrolled and 5 (Joel) is not.

**4. Answer: (2) Ravi and Tara.** The 4-credit courses are C1 and C2. Ravi has both, Tara has both (C2 and C1), Sita lacks C2, Manu lacks C2 and Joel has neither.

**5. Answer: (2) 4.** The groups are Kochi (2), Delhi, Pune and one NULL group (Joel).

**6. Answer: (2) 4.** Manu’s age is NULL, so both comparisons are UNKNOWN and his row is dropped.

**7. Answer: (2) 9.** Ravi 3 + Sita 2 + Manu 1 + Tara 2 matched rows = 8, plus Joel with NULLs = 9.

**8. Answer: (2) 85.** The maximum is 90, and the largest mark below it is 85.

**9. Answer: (2) 3.** Credit totals: Ravi 4 + 4 + 3 = 11, Sita 4 + 3 = 7, Manu 4, Tara 4 + 4 = 8. Three students have 7 or more: Ravi, Sita and Tara.

**10. Answer: (2) AI.** No one takes C4. ENROLL.cid has no NULLs, so NOT IN works.

**11. Answer: (1) A-III, B-I, C-II, D-IV.**

**12. Answer: (1).** Both are true, and R explains A: because it depends on the outer row, it must be recomputed (logically) for each outer row.

**13. Answer: (3).** I is true. II is false: DROP removes the definition too. TRUNCATE keeps the table.

**14. Answer: (1) A and B only.** C is false: IN is = ANY. D is false: EXISTS is always TRUE or FALSE.

**15. Answer: (3) No rows.** The Kochi ages are 21 and NULL (Manu). For every student, the comparison with NULL is UNKNOWN, so “> ALL” is never TRUE. Without the NULL it would be ages > 21, giving Sita and Tara.

## Recreate the tables

    CREATE TABLE STUDENT(sid INT PRIMARY KEY, sname VARCHAR(20), city VARCHAR(20), age INT);
    CREATE TABLE COURSE(cid VARCHAR(5) PRIMARY KEY, title VARCHAR(20), credits INT);
    CREATE TABLE ENROLL(sid INT, cid VARCHAR(5), marks INT, PRIMARY KEY(sid, cid));
    INSERT INTO STUDENT VALUES (1,'Ravi','Kochi',21),(2,'Sita','Delhi',22),(3,'Manu','Kochi',NULL),
                               (4,'Tara','Pune',23),(5,'Joel',NULL,21);
    INSERT INTO COURSE VALUES ('C1','DBMS',4),('C2','OS',4),('C3','CN',3),('C4','AI',3);
    INSERT INTO ENROLL VALUES (1,'C1',80),(1,'C2',70),(1,'C3',NULL),(2,'C1',90),(2,'C3',60),
                              (3,'C1',50),(4,'C2',85),(4,'C1',75);
