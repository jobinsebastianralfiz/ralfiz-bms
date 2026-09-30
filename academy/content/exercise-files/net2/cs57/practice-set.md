# Practice set 8.5: Semantic analysis, runtime and code generation

15 exam-level problems. Pace: about 90 seconds for each problem, and allow up to 3 minutes each for problems 4, 5 and 6. Write the answer, then check it with solutions.md.

Conventions: basic blocks use the three leader rules. DAG node counts include the leaves. Sethi–Ullman labels are asked for under both conventions where stated.

---

**1.** Evaluate 4 * 2 + 3 * 5 using this SDD:

    E → E1 * T   { E.val = E1.val + T.val }
    E → T        { E.val = T.val }
    T → T1 + F   { T.val = T1.val × F.val }
    T → F        { T.val = F.val }
    F → num      { F.val = num.lexval }

(1) 15 (2) 48 (3) 23 (4) 26

**2.** Two translation schemes. What does each print for the input a b b a c?

    Scheme P:  S → a S { print 1 } | b S { print 2 } | c { print 3 }
    Scheme Q:  S → a { print 1 } S | b { print 2 } S | c { print 3 }

**3.** Which of these SDDs are L-attributed?

- A. A → B C { B.i = A.i; C.i = B.s; A.s = C.s }
- B. A → B C { C.i = A.i; B.i = C.s }
- C. A → B C D { D.i = B.s + C.s }
- D. A → B C { A.s = B.s × C.s }

(1) A, C and D only (2) A and D only (3) A, B and D only (4) all four

**4.** For a = (b + c) * (b + c) − d:

- (a) write the three-address code with a new temporary for every operator, and count the quadruples (count the final copy a = t as a quadruple);
- (b) count the nodes in the DAG;
- (c) write the three-address code produced from the DAG.

**5.** How many nodes does the DAG of this basic block have? Which variables label each interior node?

    p = q * r
    s = q * r + t
    q = p + t
    u = q * r

**6.** For the code below, find the leaders, the basic blocks, the number of flow-graph edges and the number of back edges.

    (1)  f = 1
    (2)  i = 2
    (3)  if i > n goto (9)
    (4)  f = f * i
    (5)  i = i + 1
    (6)  if f < 1000 goto (3)
    (7)  f = 0
    (8)  goto (10)
    (9)  print f
    (10) print i

**7.** Only x is live at the end, and a, b, c are live at the start. What is the minimum number of registers needed with no spilling?

    t1 = a * b
    t2 = t1 + c
    t3 = a - t2
    t4 = t3 * t1
    x  = t4 + c

**8.** Find the Sethi–Ullman label (minimum number of registers) for (a − b) + e * (c + d):

- (a) when a left-child leaf is labelled 1 and a right-child leaf 0;
- (b) when every leaf is labelled 1.

**9.** For int f(int n) { return n < 2 ? n : f(n−1) + f(n−2); }, how many activations does f(4) create, and what is the maximum number of activation records of f on the stack at one time?

**10.** What is the output?

    #include <stdio.h>
    int g(int n) {
        static int c = 0;
        c++;
        if (n > 0) g(n - 1);
        return c;
    }
    int main(void) {
        printf("%d ", g(3));
        printf("%d", g(2));
        return 0;
    }

(1) 4 3 (2) 4 7 (3) 1 1 (4) 3 5

**11.** Match List I with List II.

| List I (Analysis) | List II (Main use) |
|---|---|
| A. Reaching definitions | I. Code hoisting |
| B. Live variables | II. Global common sub-expression elimination |
| C. Available expressions | III. Constant propagation |
| D. Very busy expressions | IV. Register allocation and dead-code elimination |

(1) A-III, B-IV, C-II, D-I (2) A-IV, B-III, C-II, D-I (3) A-III, B-II, C-IV, D-I (4) A-III, B-IV, C-I, D-II

**12.** Assertion (A): Access links are needed to implement non-local references in a language with nested procedures under static scoping.
Reason (R): The control link of an activation record always points to the record of the lexically enclosing procedure.

(1) Both true, and R explains A (2) Both true, but R does not explain A (3) A true, R false (4) A false, R true

**13.** Statement I: Indirect triples allow instructions to be reordered without changing the triples themselves.
Statement II: SSA form needs φ-functions even in straight-line code with no branches.

(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**14.** Arrange the regions of a typical run-time memory layout from the lowest address to the highest.

- A. Stack
- B. Code
- C. Heap
- D. Static data
- E. Free memory between the heap and the stack

(1) B, D, C, E, A (2) B, C, D, E, A (3) D, B, C, E, A (4) B, D, A, E, C

**15.** A loop runs for i = 1 to 100 and computes t = 4 * i on each iteration to index an array. After strength reduction (t = t + 4) and induction-variable elimination, how many multiplications does the loop execute? Name the two transformations and what each does.
