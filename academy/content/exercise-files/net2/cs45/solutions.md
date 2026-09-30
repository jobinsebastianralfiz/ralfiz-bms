# Solutions cs45

1. R = 5 − (−4) + 1 = 10 rows, C = 9 − 2 + 1 = 8 columns. Offsets: row 1 − (−4) = 5, column 6 − 2 = 4.
   (a) Row-major k = 5 × 8 + 4 = 44 → 4000 + 44 × 8 = **4352**.
   (b) Column-major k = 4 × 10 + 5 = 45 → 4000 + 45 × 8 = **4360**.

2. Sizes 4, 4, 6; offsets 2, 2, 2. k = 2 × (4 × 6) + 2 × 6 + 2 = 48 + 12 + 2 = 62 → 1000 + 62 × 4 = **1248**.

3. Row r of an upper-triangular n × n matrix has n − r + 1 entries. Rows 1 and 2 hold 10 + 9 = 19. Row 3 starts at column 3, so A[3][7] has 4 entries before it in its row: index = 19 + 4 = **23**. Formula check: (i−1)n − (i−1)(i−2)/2 + (j−i) = 20 − 1 + 4 = 23.

4. (a) Postfix **AB*CDE*+F^G/−H+**. (b) Prefix **+−*AB/^+C*DEFGH**. Trace highlights: after A*B the * is popped by −; inside the bracket + then * are pushed (stack − ( + *, depth 4); ")" pops * and +; ^ is pushed above −; / pops ^ (higher) and is pushed; + pops / and − (left-associative). Maximum operator-stack size = **4** (counting the "(").

5. 8/2 = 4; 3+1 = 4; 4×4 = 16; 2^3 = 8; 16 − 8 = **8**.

6. Right to left: 2, 2 → ^ = 4; 6, 12 → / = 12/6 = 2; 4, 3 → * = 3 × 4 = 12; + = 12 + 2 = 14; − = 14 − 4 = **10**. Infix: (3×4 + 12/6) − 2^2.

7. Simulate each.
   (a) 2 1 5 4 3: push 1,2 pop 2,1; push 3,4,5 pop 5,4,3. Possible.
   (b) 3 1 2 5 4: after popping 3, the stack is 1 2 with 2 on top; 1 cannot come next. **Impossible.**
   (c) 5 4 3 2 1: push all, pop all. Possible.
   (d) 1 5 2 4 3: after popping 5, the stack is 2 3 4 with 4 on top; 2 cannot come next. **Impossible.**
   (e) 3 4 2 5 1: push 1,2,3 pop 3; push 4 pop 4; pop 2; push 5 pop 5; pop 1. Possible.
   Impossible: **(b) and (d)**.

8. Capacity is 5. A→slot 1, B→2, C→3, D→4 (rear 4). Two dequeues remove A and B (front 2). E→slot 5 (rear 5). F: (5+1) mod 6 = 0 ≠ 2, so F→slot 0 (rear 0). G: (0+1) mod 6 = 1 ≠ 2, so G→slot 1 (rear 1). **No enqueue fails.** Final front = 2, rear = 1, count = (1 − 2 + 6) mod 6 = **5** (C, D, E, F, G). The queue is now full.

9. Sorted-array insert shifts elements: O(n) (A-III). Doubly linked delete with the node pointer: O(1) (B-I). Heap insert sifts up: O(log n) (C-II). Checking all n(n−1)/2 pairs: O(n²) (D-IV). Answer **(1)**.

10. Both true, and R is the correct explanation: because operands never change order, they go straight to output and only operators need to wait on a stack for their precedence to be settled. Answer: **Both (A) and (R) are true and (R) is the correct explanation of (A)**.

11. Statement I is false: with two queues, either push or pop must move all elements through the other queue, costing O(n) for that operation. Statement II is true (each element is pushed and popped at most twice). Answer: **Statement I is false but Statement II is true**.

12. The list is 3 8 5 8 2 8. The pointer-to-pointer loop removes every node holding 8, including consecutive ones and the last one, without a special case for the head. Output: **3 5 2 | 3** (verified with gcc).

13. g reads the decimal digits and weights them by powers of 2. g(1) = 1, g(12) = 2 + 2 × 1 = 4, g(123) = 3 + 2 × 4 = 11. g(3) = 3, g(30) = 0 + 2 × 3 = 6, g(305) = 5 + 2 × 6 = 17. Output: **11 17**.

14. f is Fibonacci with f(0) = 0, f(1) = 1, so f(7) = **13**. calls(n) = 1 + calls(n−1) + calls(n−2), calls(0) = calls(1) = 1: 1, 1, 3, 5, 9, 15, 25, **41**. Check: 2F(8) − 1 = 2 × 21 − 1 = 41.

15. Output-restricted: we may insert at either end, but always remove the front.
   If 4 comes out first, nothing was removed before 4 went in, so 1, 2, 3 are all inside and 4 sits at the front. After that, only front removals happen, so the rest of the output is the front-to-back order of 1, 2, 3. Building that order: 1 goes in; 2 goes on either side (2 1 or 1 2); 3 goes on either end. The only possible orders are 3 2 1, 2 1 3, 3 1 2 and 1 2 3.
   (a) 4 1 3 2 needs 1 3 2: not in the list. **Impossible.**
   (b) 4 2 1 3 needs 2 1 3: 1 rear, 2 front, 3 rear, 4 front. **Possible.**
   (c) 4 2 3 1 needs 2 3 1: not in the list. **Impossible** (it is impossible for the input-restricted deque too).
   (d) 3 1 4 2: insert 1, 2 at the rear and 3 at the front (3 1 2); remove 3 and 1; insert 4 at the front (4 2); remove 4 and 2. **Possible.**
   Answer: **(b) and (d)**.
