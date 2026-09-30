# Practice set 4.6: enhanced data models, data warehousing and data mining

Time: 24 minutes (about 90 seconds per problem). No notes. Each problem has four options; choose one.

Problems 1, 2 and 4 use this stationery-shop database (6 transactions):

| TID | Items |
|---|---|
| T1 | Pen, Ink, Paper |
| T2 | Pen, Paper |
| T3 | Ink, Paper, Stapler |
| T4 | Pen, Ink, Paper |
| T5 | Pen, Stapler |
| T6 | Pen, Ink, Paper, Stapler |

**1.** What are the support of {Ink, Paper} and the confidence of Paper → Ink?
(1) 66.7% and 100%  (2) 66.7% and 80%  (3) 80% and 66.7%  (4) 50% and 80%

**2.** Run Apriori with minimum support count 3. How many frequent itemsets (of all sizes) are found?
(1) 6  (2) 7  (3) 8  (4) 9

**3.** How many association rules (both sides non-empty) can be formed from 6 distinct items?
(1) 63  (2) 602  (3) 665  (4) 729

**4.** What is the lift of Ink → Paper, and what does it indicate?
(1) 1.2, positive correlation  (2) 1.0, independence  (3) 0.8, negative correlation  (4) 1.5, positive correlation

**5.** A cube has dimensions Time (hierarchy day < month < year), Product (product < category) and Region (city < state). How many cuboids are there, counting "all" levels?
(1) 8  (2) 12  (3) 24  (4) 36

**6.** Match List I with List II.

| List I (Design) | List II (Feature) |
|---|---|
| A. Star schema | I. Several fact tables share dimension tables |
| B. Snowflake schema | II. One fact table with denormalised dimension tables |
| C. Fact constellation | III. Records events and has no numeric measure |
| D. Factless fact table | IV. Dimension tables normalised into sub-tables |

(1) A-II, B-IV, C-I, D-III  (2) A-IV, B-II, C-I, D-III  (3) A-II, B-IV, C-III, D-I  (4) A-II, B-I, C-IV, D-III

**7.** Assertion (A): A data warehouse keeps several years of history and includes time in the key of fact records.
Reason (R): A data warehouse is time-variant.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)  (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)  (3) (A) is true but (R) is false  (4) (A) is false but (R) is true

**8.** 8 records have 5 Yes and 3 No. Attribute Weather splits them into Sunny (1 Yes, 3 No) and Cloudy (4 Yes, 0 No). What is the information gain of Weather (to 3 decimals)?
(1) 0.406  (2) 0.549  (3) 0.954  (4) 0.811

**9.** Run k-means (k = 2) on the points 1, 2, 5, 6, 11, 12 with initial centroids 1 and 12. What are the final centroids?
(1) 1.5 and 8.5  (2) 3.5 and 11.5  (3) 2.67 and 9.67  (4) 3 and 11

**10.** A classifier gives TP = 45, FN = 5, FP = 15, TN = 135. What are its precision, recall and F1 score?
(1) 0.90, 0.75, 0.818  (2) 0.75, 0.90, 0.900  (3) 0.75, 0.90, 0.818  (4) 0.75, 0.90, 0.825

**11.** R (5,000 tuples × 200 bytes) is at site A. S is at site B, and its join column has 300 distinct values of 10 bytes each. 1,000 tuples of R match S, and the result is needed at B. How many bytes does the semijoin plan transfer, and how many does shipping all of R transfer?
(1) 200,000 and 1,000,000  (2) 203,000 and 1,000,000  (3) 203,000 and 1,003,000  (4) 230,000 and 1,000,000

**12.** A data item has N = 5 replicas and W = 3. What is the minimum read quorum R? And how many messages does 2PC with 4 participants use (PREPARE, vote, decision, ACK)?
(1) 2 and 12  (2) 3 and 12  (3) 3 and 16  (4) 2 and 16

**13.** Arrange Fayyad’s KDD steps in order: A. Transformation  B. Interpretation/evaluation  C. Selection  D. Data mining  E. Preprocessing
(1) C, E, A, D, B  (2) E, C, A, D, B  (3) C, A, E, D, B  (4) C, E, D, A, B

**14.** Which of the following are object-relational features added to SQL by SQL:1999 or SQL:2003?
A. User-defined structured types  B. REF types that point to row objects  C. Table inheritance using UNDER  D. The MULTISET collection type  E. Abolishing the SELECT statement
(1) A, B and C only  (2) A, B, C and D only  (3) B, C, D and E only  (4) A, C and E only

**15.** Statement I: An R-tree indexes spatial objects using nested minimum bounding rectangles.
Statement II: A quadtree splits every internal node into exactly eight children.
(1) Both Statement I and Statement II are true  (2) Both Statement I and Statement II are false  (3) Statement I is true but Statement II is false  (4) Statement I is false but Statement II is true
