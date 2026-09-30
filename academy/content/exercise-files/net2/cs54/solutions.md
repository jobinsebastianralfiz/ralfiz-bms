# Solutions: practice set 8.2

All counts, tables and language equalities were checked by code (netv/cs54.py).

**1. Answer (3) 29.** 2n − 1 = 2 × 15 − 1. There are 14 steps of the form A → BC and 15 of the form A → a.

**2. Answer (2) 15.** Each GNF step emits exactly one terminal.

**3.** Replace the terminals: A → a, B → b. The rule S → c is already in CNF. Break the long bodies: S → AX | BY | c, X → SA, Y → SB. Derivation of abcba (n = 5): S ⇒ AX ⇒ aX ⇒ aSA ⇒ aBYA ⇒ abYA ⇒ abSBA ⇒ abcBA ⇒ abcbA ⇒ abcba. That is **9 = 2 × 5 − 1** steps. The grammar generates exactly {wcwᴿ}, checked up to length 9.

**4. Answer (3) 5.** There are three operators and no precedence in the grammar, so the answer is the Catalan number C₃ = 5. For example, (id * id) + (id * id) is one tree and id * (id + (id * id)) is another.

**5.** Row by length (cells left to right):

| Length | abba |
|---|---|
| 1 | A, B, B, A |
| 2 | S (ab), ∅ (bb), S (ba) |
| 3 | ∅, ∅ |
| 4 | S (ab · ba via S → SS) |

(a) abba is accepted. (b) aabb is rejected: the only length-2 S is at "ab" in the middle, and the length-4 cell stays empty. (c) ababab has **2** parse trees: SS can split it as (ab)(abab) or (abab)(ab), and each 4-symbol half splits in only one way. The grammar generates the concatenations of ab and ba blocks.

**6.** (a) A and B are nullable (A → ε, B → ε), and so is S (S → BB). (b) From S → AaB we get AaB, aB, Aa and a. From S → BB we get BB and B (B alone appears once, because dropping either copy gives the same body). That is **6** S-productions: S → AaB | aB | Aa | a | BB | B.

**7.** B → BC never terminates, so B is non-generating. Delete B and S → AB. Now A and C are unreachable from S, and D always was. Only **S → a** remains. If you remove unreachable symbols first, only D is deleted (A, B and C are all reachable through S → AB). Then deleting B leaves A → a and C → c in the grammar as useless leftovers.

**8.** Z0 → AZ0 (after a) → BAZ0 (after b) → BAZ0 (after c; only the state changes) → AZ0 (after b, pop B) → Z0 (after a, pop A). Then it accepts on Z0. The switch on c is what makes the machine deterministic.

**9. Answer (1) A-III, B-II, C-I, D-IV.** Complement: DCFL yes, CFL no. Intersection with a regular language: both yes. Union: CFL yes, DCFL no. Intersection: neither.

**10. Answer (1).** Parikh’s theorem gives semilinear length sets, which for one letter means eventually periodic lengths, and every such unary language is regular. R explains A.

**11. Answer (1) A, C and D only.** Universality, emptiness of an intersection and ambiguity are undecidable (all reduce from PCP or from Turing machine computations). Emptiness uses the generating-symbols test and membership uses CYK, so B and E are decidable.

**12.** Choose z = aᵖbᵖcᵖ. Since |vwx| ≤ p, the window cannot touch both the a-block and the c-block. With i = 2, at most two of the three counts grow, and at least one grows because |vx| ≥ 1. So the counts become unequal, or the symbols fall out of order if v or x straddles a boundary. Either way the string leaves L.

**13. Answer (1) B, D, A, E, C.** FA < DPDA < NPDA < LBA < TM. Each inclusion is proper: aⁿbⁿ, then wwᴿ, then aⁿbⁿcⁿ, then a recursive language that is not context-sensitive.

**14. Answer (2) 5 and 16.** The minimum is log₂ 16 + 1 = 5 (a balanced tree plus the terminal edge). The maximum is (16 − 1) + 1 = 16 (a chain).

**15. Answer (1).** Strings of the form aⁿbⁿcⁿdⁿ are in both parts and get two structurally different trees under every grammar. This is a classical inherently ambiguous language. The other three have deterministic (hence unambiguous) grammars.
