# Solutions 8.4: Lexical and syntax analysis

Every count and set below was recomputed by the verification script (grammar tools for FIRST/FOLLOW, LL(1) and LR item sets, a maximal-munch tokenizer, and gcc for the program).

**1.**
- (a) int, x, =, 1e-3, +, .5, ; gives **7**. 1e-3 and .5 are each one floating constant.
- (b) return, (, a, &&, b, ), ||, !, c, ; gives **10**.
- (c) x, +=, y, <<=, 2, ;, z, =, "a;b", ; gives **10**, option (1). <<= is a single operator, the comment disappears, and the semicolon inside the string does not end anything, because the string is one token.

**2.** Answer (4) 4. The scanner removes /*b*/, leaving a / b = 12 / 3 = 4 (run with gcc). Trap: thinking the comment hides /b, or that the slashes join into //.

**3.** Here α1 = a, α2 = b, β1 = c, β2 = d.

    S  → c S' | d S'
    S' → a S' | b S' | ε

A script checked that both grammars generate the same strings up to length 8.

**4.** A has no immediate left recursion. For B, substitute A into B → A b, which gives B → B a b | c b | d. Now remove the immediate left recursion from B:

    A  → B a | c
    B  → c b B' | d B'
    B' → a b B' | ε

The languages are equal up to length 10 (checked by script).

**5.** Factor out a, then b:

    A   → a A' | f
    A'  → b A'' | e
    A'' → c | d

Trap: factoring only ab and leaving a e as a separate alternative, so a is still a common prefix.

**6.**

| NT | FIRST | FOLLOW |
|---|---|---|
| S | { a } | { $ } |
| B | { c } | { g, f, h } |
| C | { b, ε } | { g, f, h } |
| D | { g, f, ε } | { h } |
| E | { g, ε } | { f, h } |
| F | { f, ε } | { h } |

FOLLOW(B) comes from S → aBDh: it gets FIRST(D) − {ε} = {g, f}, and h because D can vanish. C is at the right end of B's body, so it inherits FOLLOW(B). The filled cells are: S: a; B: c; C: b, f, g, h; D: f, g, h; E: g, f, h; F: f, h. That is **14 cells**, none with two entries, so the grammar is LL(1).

**7.** Answer (2).
- (a) M[S, a] = S → AaAb and M[S, b] = S → BbBa. A → ε goes under FOLLOW(A) = {a, b}, and B → ε likewise. There are no clashes, so the grammar **is LL(1)**.
- (b) In I0, both A → • and B → • are completed items. SLR reduces both on FOLLOW = {a, b}, which is a reduce–reduce conflict. So it is **not SLR(1)**.
- (c) In LR(1), the items are [A → •, a] and [B → •, b], with different lookaheads, so there is no conflict. The LR(1) collection has 10 states and so does LALR, so it **is LALR(1)**.

This is the standard proof that LL(1) does not imply SLR(1).

**8.** The LR(0) states are:

| State | Items |
|---|---|
| I0 | S'→•S, S→•AA, A→•aA, A→•b |
| I1 | S'→S• |
| I2 | S→A•A, A→•aA, A→•b |
| I3 | A→a•A, A→•aA, A→•b |
| I4 | A→b• |
| I5 | S→AA• |
| I6 | A→aA• |

There are **7 states**. Every completed item is alone in its state, so the grammar is **LR(0)**. The LR(1) collection has **10 states**: I3, I4 and I6 split into lookahead a/b and lookahead $ copies. The grammar has the same shape as S → CC.

**9.**
- (a) I0 = {A'→•A, A→•BC, B→•b, B→•} has the completed item B→• together with a shift on b. I2 = {A→B•C, C→•c, C→•} has C→• together with a shift on c. So **I0 and I2** have LR(0) shift–reduce conflicts.
- (b) SLR reduces B→ε only on FOLLOW(B) = {c, $}, which does not clash with the shift on b. It reduces C→ε only on FOLLOW(C) = {$}, which does not clash with c. **Yes, the grammar is SLR(1)**, with 6 states.

**10.** After a c, the two contexts give the items [A→c•, d], [B→c•, e] (after a) and [A→c•, e], [B→c•, d] (after b). Each state is conflict-free, so the grammar is **CLR(1)**, with **14** CLR states. The two states have the same core, so LALR merges them. The merged state reduces both A→c and B→c on d and on e: a reduce–reduce conflict. The grammar is **not LALR(1)**, with **13** LALR states. It is not SLR(1) either.

**11.** The trace is: shift id; reduce F→id; reduce T→F; shift *; shift (; shift id; reduce F→id; reduce T→F; reduce E→T; shift ); reduce F→(E); reduce T→T*F; reduce E→T; accept. That is **5 shifts** (one per token) and **8 reductions**.

**12.** Answer (1): A-II, B-IV, C-I, D-III. An unterminated string is a lexical error. A dangling else is a syntax error. Adding a struct to an int is a type error. A missing definition is found by the linker.

**13.** Answer (1). The standard example is S → Aa | bAc | Bc | bBa, A → d, B → d. It is CLR(1), but merging the two d-states gives a reduce–reduce conflict on a and c. R describes exactly the merge that causes it.

**14.** Answer (1). FOLLOW(S) gets $ as the start symbol, and z from W → S z. W is at the right end of S → x x W, so FOLLOW(W) contains FOLLOW(S) = {z, $}. The LR(0) automaton has 8 states (I0 to I7) and every completed item is alone in its state, so there are no conflicts.

**15.** Answer (2): A, B, D and E only. C is false: LEX always prefers the longest match, and rule order breaks ties only between lexemes of equal length.
