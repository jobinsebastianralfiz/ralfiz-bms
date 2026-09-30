# Practice set 8.4: Lexical and syntax analysis

15 exam-level problems. Pace: about 90 seconds for each problem, and allow 3 minutes each for the construction problems (8, 9 and 11). Write the answer, then check it with solutions.md.

Conventions: tokens are counted after comments and white space are removed. State counts include the state that contains the augmented item S' → •S. $ is the end marker.

---

**1.** How many tokens are there in each C line?

    (a)  int x = 1e-3 + .5;
    (b)  return (a&&b)||!c;
    (c)  x += y<<=2; /* shift */ z = "a;b";

Options for (c): (1) 10 (2) 12 (3) 13 (4) 16

**2.** What is the output of the following program?

    #include <stdio.h>
    int main(void) {
        int a = 12, b = 3;
        int c = a/*b*/ /b;
        printf("%d", c);
        return 0;
    }

(1) 36 (2) Compilation error (3) 12 (4) 4

**3.** Remove the left recursion from S → S a | S b | c | d.

**4.** Remove the left recursion (it is indirect) from

    A → B a | c
    B → A b | d

Take the order A, B.

**5.** Left-factor A → a b c | a b d | a e | f.

**6.** For the grammar below, find FIRST and FOLLOW of every non-terminal, and say how many cells of the LL(1) table are filled.

    S → a B D h
    B → c C
    C → b C | ε
    D → E F
    E → g | ε
    F → f | ε

**7.** Consider the grammar S → A a A b | B b B a, A → ε, B → ε.

- (a) Is it LL(1)?
- (b) Is it SLR(1)?
- (c) Is it LALR(1)?

Choose: (1) LL(1) and SLR(1) (2) LL(1) but not SLR(1) (3) SLR(1) but not LL(1) (4) neither LL(1) nor LALR(1)

**8.** Build the canonical LR(0) collection for S → A A, A → a A | b. How many states are there? Is the grammar LR(0)? How many states does its canonical LR(1) collection have?

**9.** For A → B C, B → b | ε, C → c | ε:

- (a) Which LR(0) states have conflicts?
- (b) Does SLR(1) remove them?

**10.** Classify S → a A d | b B d | a B e | b A e, A → c, B → c. Give the number of LALR(1) states and CLR(1) states.

**11.** Using the SLR(1) table for E → E + T | T, T → T * F | F, F → ( E ) | id, count the shifts and the reductions made while parsing id * ( id ).

**12.** Match List I with List II.

| List I (Error) | List II (Phase) |
|---|---|
| A. Unterminated string literal "abc | I. Semantic analysis |
| B. else without a matching if | II. Lexical analysis |
| C. Adding a struct to an int | III. Linking |
| D. Undefined reference to a function never defined | IV. Syntax analysis |

(1) A-II, B-IV, C-I, D-III (2) A-IV, B-II, C-I, D-III (3) A-II, B-I, C-IV, D-III (4) A-II, B-IV, C-III, D-I

**13.** Assertion (A): An LALR(1) parser may report a reduce–reduce conflict for a grammar that is CLR(1).
Reason (R): LALR(1) merges canonical LR(1) states that have identical LR(0) cores and unions their lookaheads.

(1) Both true, and R explains A (2) Both true, but R does not explain A (3) A true, R false (4) A false, R true

**14.** Statement I: For S → x x W | y, W → S z, FOLLOW(S) = FOLLOW(W) = { z, $ }.
Statement II: The grammar has an LR(0) automaton with 8 states and no conflicts.

(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**15.** Which of the following are correct?

- A. YACC resolves a shift–reduce conflict by shifting.
- B. YACC resolves a reduce–reduce conflict in favour of the production that appears first in the grammar.
- C. LEX prefers the rule listed first even when a later rule matches a longer lexeme.
- D. %left and %right declarations declared later in a YACC file have higher precedence.
- E. yyparse() calls yylex() whenever it needs the next token.

(1) A, B and D only (2) A, B, D and E only (3) A, C and E only (4) B, C, D and E only
