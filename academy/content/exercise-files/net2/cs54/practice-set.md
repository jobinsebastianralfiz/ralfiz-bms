# Practice set 8.2: Context-free languages and pushdown automata

15 exam-level problems. Target time: 24 minutes.

**1.** A grammar in Chomsky normal form derives a string of length 15. How many derivation steps does this take?
(1) 15 (2) 28 (3) 29 (4) 30

**2.** A grammar in Greibach normal form derives a string of length 15. How many derivation steps does this take?
(1) 14 (2) 15 (3) 16 (4) 29

**3.** Convert S → aSa | bSb | c to Chomsky normal form. How many steps does the derivation of abcba take in your CNF grammar?

**4.** How many parse trees does id * id + id * id have in the grammar E → E + E | E * E | id?
(1) 2 (2) 4 (3) 5 (4) 6

**5.** The CNF grammar is S → AB | BA | SS, A → a, B → b.
(a) Fill the CYK table for abba. Is abba accepted?
(b) Is aabb accepted?
(c) How many parse trees does ababab have?

**6.** Grammar: S → AaB | BB, A → aA | ε, B → bB | ε. (a) Which variables are nullable? (b) After ε-productions are removed, how many S-productions are there?

**7.** Grammar: S → AB | a, A → a, B → BC, C → c, D → d. Remove all useless symbols in the correct order. Which productions remain? What goes wrong if you remove unreachable symbols first?

**8.** A DPDA for {wcwᴿ | w ∈ {a, b}*} pushes A or B for each a or b, switches state on c, pops the matching symbol for each later input, and accepts when it sees Z0 at the end. Write the stack contents (top on the left) after each input symbol of abcba.

**9.** Match List I with List II.

| List I (operation) | List II |
|---|---|
| A. Complement | I. CFL closed, DCFL not closed |
| B. Intersection with a regular language | II. Both CFL and DCFL closed |
| C. Union | III. DCFL closed, CFL not closed |
| D. Intersection | IV. Neither closed |

(1) A-III, B-II, C-I, D-IV (2) A-I, B-II, C-III, D-IV (3) A-III, B-IV, C-I, D-II (4) A-III, B-II, C-IV, D-I

**10.** Assertion (A): Every context-free language over a one-letter alphabet is regular.
Reason (R): By Parikh’s theorem, the set of lengths of the strings in a unary CFL is eventually periodic.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**11.** Which of the following are undecidable for arbitrary CFGs?
A. Is L(G) = Σ*?  B. Is L(G) empty?  C. Is L(G1) ∩ L(G2) = ∅?  D. Is G ambiguous?  E. Is w ∈ L(G)?
(1) A, C and D only (2) A and D only (3) A, B, C and D only (4) C and D only

**12.** To prove that L = {aⁿbⁿcⁿ} is not context-free using the pumping lemma with constant p, which string is the best choice, and why does pumping fail?

**13.** Arrange these machines in increasing order of power: A. NPDA  B. Finite automaton  C. Turing machine  D. DPDA  E. Linear bounded automaton.
(1) B, D, A, E, C (2) B, A, D, E, C (3) D, B, A, E, C (4) B, D, E, A, C

**14.** For a CNF grammar and a string of length 16, what are the minimum and maximum heights (in edges) of the parse tree?
(1) 4 and 15 (2) 5 and 16 (3) 5 and 15 (4) 4 and 16

**15.** Which of these languages is inherently ambiguous?
(1) {aⁿbⁿcᵐdᵐ} ∪ {aⁿbᵐcᵐdⁿ} (2) {aⁿbⁿ} (3) {wcwᴿ} (4) balanced parentheses
