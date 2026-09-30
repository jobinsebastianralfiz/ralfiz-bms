# Practice set 8.1: Regular languages and finite automata

15 exam-level problems. Target time: 24 minutes (about 90 seconds each). All DFA counts are for the **minimal complete DFA** (the dead state is counted) unless a problem says otherwise.

**1.** Strings over {0, 1} are read as binary numbers, most significant bit first. ε counts as 0. How many states does the minimal DFA for "value divisible by 9" have?
(1) 4 (2) 8 (3) 9 (4) 10

**2.** How many states does the minimal DFA over {a, b} for "the 5th symbol from the left is b" have?
(1) 5 (2) 6 (3) 7 (4) 32

**3.** How many states does the minimal DFA over {a, b} for "strings ending in abb" have?
(1) 3 (2) 4 (3) 5 (4) 8

**4.** An NFA over {a, b} has start state q0 (loops on a and b), a move q0 → q1 on a, a move q1 → q2 on b, and a final state q2 that loops on a and b. (a) How many reachable DFA states does the subset construction produce? (b) How many states does the minimal DFA have?
(1) 4 and 4 (2) 4 and 3 (3) 8 and 3 (4) 3 and 3

**5.** Minimise this DFA over {a, b}. The start state is 1 and the only final state is 6.

| State | a | b |
|---|---|---|
| →1 | 2 | 3 |
| 2 | 4 | 5 |
| 3 | 4 | 5 |
| 4 | 4 | 6 |
| 5 | 4 | 6 |
| *6 | 4 | 6 |

How many states does the minimal DFA have, and what language does it accept?

**6.** Given below are two statements.
Statement I: (ab)*a = a(ba)*
Statement II: (a*b)* = ε + (a + b)*b
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**7.** A DFA over {a, b} has start state q0 and final state q1. From q0: a → q0, b → q1. From q1: a → q0, b → q1. Use Arden’s theorem to find a regular expression for the language, and simplify it.

**8.** Match List I with List II.

| List I | List II |
|---|---|
| A. Arden’s theorem | I. NFA to DFA |
| B. Myhill–Nerode theorem | II. Regular expression to ε-NFA |
| C. Thompson’s construction | III. Automaton to regular expression |
| D. Subset construction | IV. Characterises regularity and gives the minimal DFA |

(1) A-III, B-IV, C-II, D-I (2) A-IV, B-III, C-II, D-I (3) A-III, B-IV, C-I, D-II (4) A-II, B-IV, C-III, D-I

**9.** A Moore machine over {0, 1} prints the parity (number of 1s mod 2) of the input read so far. The start state prints 0. What is the output for the input 10110?

**10.** A Mealy machine has states A (start) and B. A on 0 → B/0, A on 1 → A/0, B on 0 → B/0, B on 1 → A/1. What is the output for the input 0010110?

**11.** How many DFAs are there with 2 states, the input alphabet {a, b, c} and a fixed start state?
(1) 64 (2) 128 (3) 256 (4) 512

**12.** Assertion (A): If a language satisfies the pumping lemma for regular languages, it is regular.
Reason (R): The pumping lemma gives a necessary condition for regularity.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**13.** Which of the following languages are regular?
A. {aⁿbᵐ | n + m is even}
B. {aⁿbⁿcⁿ | n ≥ 0}
C. {w ∈ {a, b}* | (#a − #b) mod 5 = 0}
D. {ww | w ∈ {a, b}*}
E. {aⁿ | n = 3k + 1, k ≥ 0}
(1) A, C and E only (2) A and E only (3) A, B, C and E only (4) C and E only

**14.** How many states does the minimal DFA over {a, b} for "an even number of a’s AND ending in b" have?
(1) 2 (2) 3 (3) 4 (4) 6

**15.** Arrange these languages over {a, b} in increasing order of minimal DFA states.
A. |w| ≤ 2  B. contains abab  C. #a ≡ 0 (mod 2) and #b ≡ 0 (mod 3)  D. 3rd symbol from the right is b  E. |w| ≡ 0 (mod 3)
(1) E, A, B, C, D (2) A, E, B, C, D (3) E, A, C, B, D (4) E, B, A, C, D
