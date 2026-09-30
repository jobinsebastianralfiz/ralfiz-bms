# Solutions 8.5: Semantic analysis, runtime and code generation

Every value was recomputed by the verification script: an SDT evaluator, a DAG builder that uses value numbering, a leader and flow-graph builder with dominators, liveness analysis, Sethi–Ullman labelling, and gcc for the program.

**1.** Answer (1) 15. * is nearer the start symbol, so it has the lower precedence, and + binds tighter. Group the input as 4 * (2 + 3) * 5. By the rules, + multiplies: 2 + 3 means 2 × 3 = 6. Then * adds: 4 + 6 = 10, and 10 + 5 = 15. Trap: using the usual precedence gives (4 * 2) + (3 * 5) → (4 + 2) × (3 + 5) = 48.

**2.**
- Scheme P prints **31221**. The actions are at the end, so they run at reduction, innermost first: c (3), then a (1), b (2), b (2), a (1).
- Scheme Q prints **12213**. Each action comes before S, so it runs as soon as its terminal is matched, which gives the input order.

This contrast is exactly what NTA tests.

**3.** Answer (1): A, C and D only.
- A: C.i uses the left sibling B, and A.s is synthesized. Allowed.
- B: B.i uses C.s, the right sibling. Not L-attributed.
- C: D.i uses the left siblings B and C. Allowed.
- D: S-attributed, hence L-attributed.

**4.**
- (a) The code is t1 = b + c; t2 = b + c; t3 = t1 * t2; t4 = t3 − d; a = t4. That is **5 quadruples**.
- (b) Leaves b, c, d, plus one shared + node, the * node and the − node: **6 nodes**. a labels the − node.
- (c) t1 = b + c; t2 = t1 * t1; a = t2 − d. That is 3 instructions: the common sub-expression is computed once.

**5.** The leaves are q0, r0 and t0. The interior nodes are:
- n1 = * (q0, r0), labelled p;
- n2 = + (n1, t0), labelled s and later also q, because q = p + t builds the same node;
- n3 = * (n2, r0), labelled u. It uses the new value of q, so it is not n1.

That is 3 leaves and 3 interior nodes, **6 nodes** in all. The trap is reusing n1 for u = q * r: q has been redefined.

**6.** The leaders are:
- 1 (the first instruction);
- 3 and 9 and 10 (jump targets);
- 4 (after the jump in 3), 7 (after the jump in 6) and 9 (after the goto in 8).

Sorted: 1, 3, 4, 7, 9, 10. That gives **6 blocks**: B1 = 1–2, B2 = 3, B3 = 4–6, B4 = 7–8, B5 = 9, B6 = 10.

The edges are B1→B2, B2→B3, B2→B5, B3→B2, B3→B4, B4→B6 and B5→B6, which is **7 edges**. B2 dominates B3, so B3 → B2 is the only back edge: **1 back edge**, with the loop {B2, B3}.

**7.** Work backwards from {x}. The live sets are {a, b, c} at the start, then {a, c, t1}, {a, c, t1, t2}, {c, t1, t3}, {c, t4} and {x}. The maximum is **4** (a, c, t1 and t2 are all live after the second statement), so 4 registers are needed.

**8.**
- (a) a − b gets max(1, 0) = 1. c + d gets 1. e * (c + d): e is a left leaf (1) and c + d is 1, so they are equal and give 2. The root has max(1, 2) = **2**.
- (b) a − b gets 2, c + d gets 2, and e * (c + d) has children 1 and 2, so it gets 2. The root joins 2 and 2, giving **3**.

The two conventions differ here, so always read which one the question uses.

**9.** The activation tree for f(4) has **9** nodes (f(4) → f(3), f(2); f(3) → f(2), f(1); and so on). The longest chain is f(4), f(3), f(2), f(1), which gives a maximum of **4** records at once. For f(5) the numbers are 15 and 5.

**10.** Answer (2) 4 7 (run with gcc). c is static, so it is shared by every activation and never reset. g(3) makes 4 activations (n = 3, 2, 1, 0), so c = 4 when the outermost call returns. g(2) makes 3 more, so c = 7. Traps: (1) 4 3 restarts the count for the second top-level call. (3) 1 1 treats c as an automatic variable.

**11.** Answer (1): A-III, B-IV, C-II, D-I. Reaching definitions tell which constant assignment reaches a use. Liveness frees registers and finds dead assignments. Available expressions find global common sub-expressions. Very busy expressions allow hoisting.

**12.** Answer (3). A is true. R is false: the control link points to the caller. It is the access link that points to the lexically enclosing procedure.

**13.** Answer (3). Statement I is true: only the pointer list is permuted. Statement II is false: with no join points there is nothing to merge, so each assignment simply gets a new version and no φ is needed.

**14.** Answer (1): B, D, C, E, A. Code comes first, then static data. The heap grows upward into the free area, and the stack grows downward from the top.

**15.** **0 multiplications.**
- Strength reduction replaces t = 4 * i with t = t + 4 (100 additions, starting from t = 0).
- Induction-variable elimination rewrites the loop test in terms of t (t ≤ 400), so i is no longer needed.

Before the change the loop did 100 multiplications. Both transformations are machine-independent loop optimisations.
