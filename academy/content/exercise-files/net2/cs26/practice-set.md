# Practice set 4.3: SQL

Time: 24 minutes. No notes. Standard SQL semantics.

Problems 1–10 and 15 use these tables (NULL means a missing value):

    STUDENT                       COURSE                   ENROLL
    sid  sname  city   age        cid  title  credits      sid  cid  marks
    1    Ravi   Kochi  21         C1   DBMS   4            1    C1   80
    2    Sita   Delhi  22         C2   OS     4            1    C2   70
    3    Manu   Kochi  NULL       C3   CN     3            1    C3   NULL
    4    Tara   Pune   23         C4   AI     3            2    C1   90
    5    Joel   NULL   21                                  2    C3   60
                                                           3    C1   50
                                                           4    C2   85
                                                           4    C1   75

**1.** SELECT COUNT(*), COUNT(marks), SUM(marks) FROM ENROLL;
(1) 8, 8, 510  (2) 8, 7, 510  (3) 7, 7, 510  (4) 8, 7, 580

**2.** SELECT cid, COUNT(*) FROM ENROLL GROUP BY cid HAVING AVG(marks) > 70;
(1) C1 4 and C2 2  (2) C1 4 only  (3) C1 4, C2 2 and C3 2  (4) C2 2 only

**3.** SELECT sname FROM STUDENT WHERE sid NOT IN (SELECT sid FROM ENROLL);
(1) No rows  (2) Joel  (3) Manu and Joel  (4) Joel and Tara

**4.** What does this query return?

    SELECT s.sname FROM STUDENT s
    WHERE NOT EXISTS (SELECT * FROM COURSE c WHERE c.credits = 4
          AND NOT EXISTS (SELECT * FROM ENROLL e
                          WHERE e.sid = s.sid AND e.cid = c.cid));

(1) Ravi only  (2) Ravi and Tara  (3) Ravi, Sita and Tara  (4) Joel

**5.** How many rows does SELECT city, COUNT(*) FROM STUDENT GROUP BY city; return?
(1) 3  (2) 4  (3) 5  (4) 2

**6.** SELECT COUNT(*) FROM STUDENT WHERE age > 21 OR age <= 21;
(1) 5  (2) 4  (3) 3  (4) 0

**7.** How many rows does SELECT * FROM STUDENT s LEFT JOIN ENROLL e ON s.sid = e.sid; return?
(1) 8  (2) 9  (3) 13  (4) 40

**8.** SELECT MAX(marks) FROM ENROLL WHERE marks < (SELECT MAX(marks) FROM ENROLL);
(1) 90  (2) 85  (3) 80  (4) NULL

**9.** How many rows does this query return?

    SELECT s.sname, SUM(c.credits)
    FROM STUDENT s JOIN ENROLL e ON s.sid = e.sid JOIN COURSE c ON c.cid = e.cid
    GROUP BY s.sname HAVING SUM(c.credits) >= 7;

(1) 2  (2) 3  (3) 4  (4) 1

**10.** SELECT title FROM COURSE WHERE cid NOT IN (SELECT cid FROM ENROLL);
(1) No rows  (2) AI  (3) CN and AI  (4) DBMS

**11.** Match List I with List II.

| List I | List II |
|---|---|
| A. COMMIT | I. DCL |
| B. GRANT | II. DDL |
| C. DROP | III. TCL |
| D. MERGE | IV. DML |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-I, C-IV, D-II  (4) A-III, B-II, C-I, D-IV

**12.** Assertion (A): A correlated subquery is logically evaluated once for each row of the outer query.
Reason (R): A correlated subquery refers to a column of a table in the outer query.
(1) Both true, R explains A  (2) Both true, R does not explain A  (3) A true, R false  (4) A false, R true

**13.** Statement I: A view with WITH CHECK OPTION rejects an insert through the view whose new row does not satisfy the view’s WHERE condition.
Statement II: DROP TABLE removes all rows but keeps the table definition for reuse.
(1) Both true  (2) Both false  (3) I true, II false  (4) I false, II true

**14.** Which are true?
A. x > ANY (S) is equivalent to x > MIN(S) when S has no NULLs.
B. x > ALL (empty set) is TRUE.
C. x IN (S) is equivalent to x = ALL (S).
D. EXISTS can evaluate to UNKNOWN.
(1) A and B only  (2) A, B and C only  (3) B and D only  (4) A only

**15.** SELECT sname FROM STUDENT WHERE age > ALL (SELECT age FROM STUDENT WHERE city = 'Kochi');
(1) Sita and Tara  (2) Tara only  (3) No rows  (4) Sita, Tara and Joel
