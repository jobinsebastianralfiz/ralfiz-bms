# Practice set 3.1: Language design and translation issues

15 exam-level problems. Pace: about 90 seconds for each problem, and allow 3 minutes each for the trace problems (2, 3, 4 and 5). Write the answer, then check it with solutions.md.

Conventions: the pseudo-code uses C syntax. print writes its values separated by spaces. Scoping is static unless a problem says otherwise. Under value-result, results are copied back from left to right, and the address of each actual is fixed at the call.

---

**1.** Match List I with List II.

| List I (Binding) | List II (Time) |
|---|---|
| A. Meaning of the symbol * in C | I. Load time |
| B. Range of values of float in a C compiler | II. Language design time |
| C. A C static variable to its absolute address | III. Run time |
| D. A formal parameter to its actual parameter | IV. Language implementation time |

(1) A-II, B-IV, C-I, D-III (2) A-IV, B-II, C-I, D-III (3) A-II, B-IV, C-III, D-I (4) A-II, B-I, C-IV, D-III

**2.** For the program below, give the output for call by value, by reference, by value-result and by name.

    int x = 3, y = 4;
    void p(int a, int b) { b = b + a; a = a * b; x = x + 1; }
    main() { p(x, y); print(x, y); }

**3.** Give the output under static scoping and under dynamic scoping.

    int a = 1, b = 2;
    void p() { print(a + b); }
    void q() { int a = 10; p(); b = a; }
    void r() { int b = 20; q(); print(b); }
    main() { r(); p(); }

**4.** What is printed by call by name, and what by call by reference?

    int i = 0;
    int a[3] = {1, 2, 3};
    void swap(int x, int y) { int t = x; x = y; y = t; }
    main() { swap(i, a[i]); print(i, a[0], a[1], a[2]); }

**5.** Parameters are passed by name. What is printed?

    int i = 0;
    int a[4] = {2, 3, 5, 7};
    int total(int e) { int s = 0; i = 0; while (i < 4) { s = s + e; i = i + 1; } return s; }
    main() { print(total(a[i] * a[i])); }

**6.** Match List I with List II.

| List I | List II |
|---|---|
| A. Operational semantics | I. {P} S {Q} and weakest preconditions |
| B. Axiomatic semantics | II. Functions from states to states |
| C. Denotational semantics | III. Execution on an abstract machine |
| D. Attribute grammar | IV. Type rules attached to productions |

(1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-II, C-I, D-IV (4) A-III, B-I, C-IV, D-II

**7.** Assertion (A): A general swap(x, y) procedure that works for every pair of actual parameters cannot be written using call by name.
Reason (R): Under call by name, an actual such as a[i] is re-evaluated at every use, so it can denote a different element after i changes.

(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**8.** Procedures nest, and the main program is at depth 1. A procedure at depth 6 uses a variable declared at depth 3. How many static links are followed? How many memory accesses does a display need to find the record?

**9.** What is printed for call by value-result with left-to-right copy-back? What if the copy-back is right to left? What for call by reference?

    int k = 0;
    void f(int x, int y) { x = 1; y = 2; }
    main() { f(k, k); print(k); }

**10.** State the scope and the lifetime of each: (a) a C global variable, (b) a C static local variable, (c) an automatic local variable of a function f while f is calling g, (d) a block obtained with malloc inside f and never freed.

**11.** Statement I: A pure interpreter produces an object file that can be run later without the interpreter.
Statement II: A hybrid implementation translates the source into an intermediate code that is then interpreted.

(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**12.** For the grammar E → E + E | E * E | id, how many parse trees do (a) id + id * id and (b) id * id + id * id + id have?

**13.** What is printed for call by value, by reference and by value-result?

    int c = 1;
    int inc(int x) { x = x + 1; c = c + x; return x; }
    main() { int r = inc(c); print(r, c); }

**14.** Which of the following are correct? A. Static scope is resolved from the program text. B. Dynamic scope follows the static chain. C. Perl local variables are dynamically scoped. D. A display gives constant-time non-local access. E. C allows nested function definitions in standard C.

(1) A, C and D only (2) A, B and D only (3) A, C, D and E only (4) B and E only

**15.** Arrange in order: A. Linking B. Syntax analysis C. Loading D. Lexical analysis E. Code generation.
