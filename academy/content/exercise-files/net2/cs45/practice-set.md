# Practice set cs45: arrays, stacks, queues and linked lists

Time: 23 minutes (about 90 seconds per problem). No calculator. Write your answer before looking at solutions.md.

1. A[−4..5][2..9] holds 8-byte values from base 4000. Find the address of A[1][6] in (a) row-major and (b) column-major order.

2. A[2..5][0..3][1..6] holds 4-byte integers in row-major order from base 1000. Find the address of A[4][2][3].

3. A 10 × 10 upper-triangular matrix (A[i][j] = 0 for j < i, indices from 1) is packed row by row into B[0..54]. At which index is A[3][7] stored?

4. Convert A * B − (C + D * E) ^ F / G + H to (a) postfix and (b) prefix. (^ is right-associative and highest; * and / next; + and − lowest.) What is the maximum size of the operator stack?

5. Evaluate the postfix expression 8 2 / 3 1 + * 2 3 ^ −.

6. Evaluate the prefix expression − + * 3 4 / 12 6 ^ 2 2 (operands are the space-separated numbers).

7. 1, 2, 3, 4, 5 are pushed in order; pops may happen at any time. Which of these outputs are impossible? (a) 2 1 5 4 3 (b) 3 1 2 5 4 (c) 5 4 3 2 1 (d) 1 5 2 4 3 (e) 3 4 2 5 1

8. A circular queue uses an array of 6 slots, front = rear = 0 initially, and the one-empty-slot rule (full when (rear+1) mod 6 = front). Perform: enqueue A, B, C, D; dequeue; dequeue; enqueue E, F, G. Which enqueue(s) fail, and what are the final front, rear and number of elements?

9. Match List I with List II.

| List I (Structure) | List II (Cost) |
|---|---|
| A. Sorted array, insert a new key | I. O(1) |
| B. Doubly linked list, delete a node given a pointer to it | II. O(log n) |
| C. Binary heap, insert | III. O(n) |
| D. Brute-force check of all pairs for a duplicate | IV. O(n²) |

Choose: (1) A-III, B-I, C-II, D-IV (2) A-II, B-I, C-III, D-IV (3) A-III, B-IV, C-II, D-I (4) A-I, B-III, C-II, D-IV

10. Assertion (A): Converting an infix expression to postfix requires a stack of operators, not of operands. Reason (R): Operands keep their relative order in postfix, so they can be written to the output as soon as they are read.
Choose from the four standard A–R options.

11. Statement I: A stack can be implemented with two queues so that both push and pop run in O(1) worst-case time. Statement II: A queue can be implemented with two stacks so that each operation runs in amortised O(1) time.
Choose from the four standard Statement I/II options.

12. What is the output of this C program?

    #include <stdio.h>
    #include <stdlib.h>
    struct node { int data; struct node *next; };
    int main(void) {
        struct node *h = NULL, *t, **pp;
        int v[] = {3, 8, 5, 8, 2, 8};
        for (int i = 5; i >= 0; i--) {
            t = malloc(sizeof *t); t->data = v[i]; t->next = h; h = t;
        }
        pp = &h;
        while (*pp) {
            if ((*pp)->data == 8) { t = *pp; *pp = t->next; free(t); }
            else pp = &(*pp)->next;
        }
        int n = 0;
        for (t = h; t; t = t->next) { printf("%d ", t->data); n++; }
        printf("| %d\n", n);
        return 0;
    }

13. What is the output of this C program?

    #include <stdio.h>
    int g(int n) {
        if (n == 0) return 0;
        return (n % 10) + 2 * g(n / 10);
    }
    int main(void) {
        printf("%d %d\n", g(123), g(305));
        return 0;
    }

14. The function "int f(int n){ calls++; if (n <= 1) return n; return f(n-1) + f(n-2); }" is called as f(7) with calls = 0. What are f(7) and the final value of calls?

15. With input 1, 2, 3, 4, which of these outputs can an output-restricted deque (insert at both ends, delete from the front only) produce? (a) 4 1 3 2 (b) 4 2 1 3 (c) 4 2 3 1 (d) 3 1 4 2
