# Practice set 8.3: Turing machines and computability

15 exam-level problems. Target time: 24 minutes.

**1.** The binary-increment TM (scan right to the blank, step left, turn 1s into 0s moving left, turn the first 0 or blank into 1 and halt without moving) is run on 1111. How many moves does it make, and what is the final tape?
(1) 9, 10000 (2) 10, 10000 (3) 10, 1111 (4) 11, 10000

**2.** The X/Y marking TM for {aⁿbⁿ} (from the lesson) is run on aaabbb. How many moves does it make before accepting?
(1) 18 (2) 21 (3) 25 (4) 36

**3.** The unary-addition TM (0 → 1, run right to the blank, step left, erase one 1) is run on 111011. How many moves does it make, and what is the result?

**4.** Find a solution of the PCP instance 1 = (aa, aaa), 2 = (a, b), 3 = (aba, a), written as (top, bottom). What is the shortest solution?

**5.** Show that the PCP instance 1 = (ab, a), 2 = (bba, bb) has no solution.

**6.** Match List I with List II.

| List I (grammar type) | List II (form of productions) |
|---|---|
| A. Type 0 | I. A → aB or A → a |
| B. Type 1 | II. A → γ, with a single variable on the left |
| C. Type 2 | III. α → β with length(α) ≤ length(β) |
| D. Type 3 | IV. α → β with no restriction (α contains a variable) |

(1) A-IV, B-III, C-II, D-I (2) A-III, B-IV, C-II, D-I (3) A-IV, B-II, C-III, D-I (4) A-IV, B-III, C-I, D-II

**7.** Assertion (A): "Does a TM M accept the string 0110?" is undecidable.
Reason (R): It is a non-trivial property of L(M).
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**8.** Which are decidable?
A. Does a given TM have a transition that moves left?
B. Is L(M) context-free, for a TM M?
C. Is w ∈ L(G), for a context-sensitive grammar G?
D. Does a TM M halt on blank tape within 50 moves?
E. Is L(G1) ∩ L(G2) = ∅ for two CFGs?
(1) A, C and D only (2) A and D only (3) A, C, D and E only (4) C and D only

**9.** Classify each language as recursive, RE-but-not-recursive, or not RE:
(a) {⟨M⟩ | M accepts ⟨M⟩}  (b) {⟨M⟩ | L(M) is finite}  (c) {⟨D⟩ | D is a DFA and L(D) = Σ*}  (d) {⟨M⟩ | M halts on at least one input}

**10.** You know that P is undecidable, and you want to show that Q is undecidable. Which reduction do you need, P ≤m Q or Q ≤m P? What would the other direction prove?

**11.** Given below are two statements.
Statement I: RE languages are closed under intersection.
Statement II: RE languages are closed under set difference.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**12.** An LBA has 4 states and the tape alphabet {0, 1}. On inputs of length 5, what is the maximum number of configurations (the head is counted on the 5 input cells)?
(1) 40 (2) 160 (3) 640 (4) 1280

**13.** Arrange in increasing order of inclusion: A. Recursive  B. Context-free  C. Recursively enumerable  D. Regular  E. Context-sensitive.
(1) D, B, E, A, C (2) D, E, B, A, C (3) D, B, A, E, C (4) B, D, E, A, C

**14.** Given below are two statements.
Statement I: A 3-tape TM that runs in time n² can be simulated by a single-tape TM in time O(n⁴).
Statement II: Multi-tape TMs accept more languages than single-tape TMs.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**15.** Why do non-RE languages exist? Choose the best reason.
(1) Some TMs loop forever. (2) The set of TMs is countable, while the set of languages is uncountable. (3) The halting problem is undecidable. (4) PCP is undecidable.
