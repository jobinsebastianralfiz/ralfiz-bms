# Practice set 4.5: Transactions, concurrency, recovery and indexing

Time yourself: problems 1–8 in 14 minutes, problems 9–15 in 12 minutes. Each carries 2 marks; there is no negative marking.

**1.** S: R1(X) R2(Z) R3(X) W1(X) W2(Z) R3(Y) W3(Y) R2(Y). Draw the precedence graph. Is S conflict serializable? How many conflict-equivalent serial schedules exist?

**2.** S: R2(B) W1(B) W2(B) W3(B). Is S conflict serializable? Is it view serializable? If so, give the serial order.

**3.** Classify each schedule as not recoverable, recoverable only, cascadeless (not strict) or strict.
(a) R1(A) W1(A) R2(A) W2(B) C2 C1
(b) W1(A) R2(B) W2(A) C1 C2
(c) R1(A) W1(A) R2(B) C1 R2(A) W2(A) C2

**4.** T1 has 3 operations and T2 has 4. How many schedules are possible, and how many are non-serial?
(1) 35, 33 (2) 35, 34 (3) 70, 68 (4) 12, 10

**5.** T1: lock-X(A); read(A); lock-X(B); unlock(A); write(B); unlock(B).
T2: lock-S(A); read(A); unlock(A); lock-X(B); write(B); unlock(B).
Which of T1 and T2 follow two-phase locking?

**6.** TS(T1) = 10, TS(T2) = 20, TS(T3) = 30, all item timestamps start at 0. S: R1(A) W2(A) R3(B) W1(A) W2(B). Under basic TO, what happens to each operation? What changes with the Thomas write rule?

**7.** Assertion (A): The Thomas write rule never rolls back a transaction.
Reason (R): It ignores writes whose timestamp is below the item’s write timestamp.
Choose: (1) both true, R explains A (2) both true, R does not explain A (3) A true, R false (4) A false, R true

**8.** T5 (TS 5) and T9 (TS 9). (a) T5 requests an item held by T9. (b) T9 requests an item held by T5. What happens in wait-die and in wound-wait?

**9.** Immediate-update log, crash after the last record:
[T1 start] [T1, A, 100, 150] [T2 start] [T2, B, 200, 250] [T1 commit] [checkpoint {T2}] [T3 start] [T3, C, 300, 350] [T2, D, 400, 450] [T4 start] [T4, A, 150, 175] [T3 commit]
Give the redo list, the undo list and the final values of A, B, C, D.

**10.** Block 1,024 bytes, key 10 bytes, block pointer 6 bytes. What is the order of a B+-tree internal node?
(1) 63 (2) 64 (3) 65 (4) 102

**11.** Same sizes, with an 8-byte record pointer. Find the leaf capacity, and the number of record pointers a completely full 3-level B+-tree (root, one internal level, leaves) holds.

**12.** A B-tree of order 5 has 3 levels. What are the minimum and maximum numbers of keys?
(1) 17 and 124 (2) 8 and 124 (3) 17 and 125 (4) 26 and 124

**13.** An ordered file has 30,000 records of 100 bytes in 1,024-byte blocks (unspanned). The primary key is 9 bytes and a block pointer 6 bytes. Find the number of block accesses for (a) binary search on the file, (b) binary search on a single-level primary index, (c) a multilevel index.

**14.** Insert 10, 20, 30, 40, 50, 60, 70, 80 into an empty B+-tree whose nodes hold at most 3 keys. Show the tree after each split and give the final number of leaves.

**15.** Match List I with List II.

| List I (Isolation level) | List II (Weakest anomaly still possible) |
|---|---|
| A. READ UNCOMMITTED | I. None of the three |
| B. READ COMMITTED | II. Phantom |
| C. REPEATABLE READ | III. Dirty read |
| D. SERIALIZABLE | IV. Unrepeatable read |

(1) A-III, B-IV, C-II, D-I (2) A-IV, B-III, C-II, D-I (3) A-III, B-II, C-IV, D-I (4) A-III, B-IV, C-I, D-II
