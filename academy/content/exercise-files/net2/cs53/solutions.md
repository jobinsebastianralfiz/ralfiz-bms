# Solutions: practice set 8.1

Every count below was checked by code (netv/cs53.py), using Myhill–Nerode class counting and brute force over all strings up to length 12.

**1. Answer (3) 9.** The states are the remainders r = 0…8, and a bit b moves r to (2r + b) mod 9. 9 is odd, so 2 is invertible mod 9. Every remainder is reachable, and no two remainders are equivalent. So there are 9 states. Trap: option (4) 10 is the answer when ε must be rejected.

**2. Answer (3) 7.** We need positions 0, 1, 2, 3, 4 (5 states, counting symbols read so far), then an accepting sink for "5th symbol was b" and a dead state for "5th symbol was a". That is 5 + 2 = 7. The "right-end" version would need 2⁵ = 32.

**3. Answer (2) 4.** The states track the longest suffix that is a prefix of abb: ε, a, ab, abb. That gives k + 1 = 4 states. There is no dead state, because failure falls back to an earlier state.

**4. Answer (2) 4 and 3.** The reachable subsets are {q0}, {q0,q1}, {q0,q2} and {q0,q1,q2}. The last two are both final, and both stay final forever (q2 loops), so they are equivalent. The minimal DFA has 3 states: "no progress", "seen a", "found ab".

**5. Answer: 4 states.** 0-equivalence: {1,2,3,4,5}, {6}. 1-equivalence: 4 and 5 go to 6 on b, so they split off. Result {1,2,3}, {4,5}, {6}. 2-equivalence: 2 and 3 go into {4,5}, but 1 goes into {1,2,3}. Result {1}, {2,3}, {4,5}, {6}. This is stable, so there are 4 states. The DFA accepts strings of length at least 3 that end in b. (After 2 symbols it is in {4,5}, and from then on it tracks "last symbol is b".)

**6. Answer (1) Both true.** I: both sides are a(ba)ⁿ = (ab)ⁿa, the alternating strings that start and end with a. II: (a*b)* is ε or any string ending in b. Both were checked on every string up to length 12.

**7.** The equations are q0 = ε + q0 a + q1 a and q1 = q0 b + q1 b. Arden on q1 gives q1 = q0 bb*. Substituting: q0 = ε + q0(a + bb*a), so q0 = (a + bb*a)*. The language is q1 = (a + bb*a)* bb*, which simplifies to **(a + b)*b**: all strings ending in b. The equivalence was checked by brute force.

**8. Answer (1) A-III, B-IV, C-II, D-I.** Arden gives a regular expression from the state equations. Myhill–Nerode characterises regularity and the minimal DFA. Thompson builds an ε-NFA from a regex. The subset construction turns an NFA into a DFA. Option (3) swaps C and D.

**9. Output 0 1 1 0 1 1.** The prefixes ε, 1, 10, 101, 1011, 10110 have 0, 1, 1, 2, 3, 3 ones. Their parities are 0 1 1 0 1 1. That is six outputs for five inputs, the Moore n + 1 rule.

**10. Output 0 0 1 0 1 0 0.** A 1 is printed only on the transition B → A on input 1, that is, when "01" has just been completed. That happens at input positions 3 and 5. Seven outputs for seven inputs.

**11. Answer (3) 256.** Each of the 2 × 3 = 6 transitions has 2 choices: 2⁶ = 64. There are 2² = 4 choices of final set. 64 × 4 = 256. Trap: (4) 512 lets the start state vary.

**12. Answer (4).** A is false. Some non-regular languages satisfy the pumping condition, for example L = {a⁺bⁿcⁿ | n ≥ 0} ∪ {bʲcᵏ | j, k ≥ 0}. Every long string can be pumped on its first symbol, yet L ∩ ab*c* = {abⁿcⁿ} is not regular, so L is not regular. The lemma is only necessary, which is exactly what R says. R is true.

**13. Answer (1) A, C and E only.** A: n + m even just means the length is even. It is a*b* ∩ ((a + b)(a + b))*, so it is regular. B: not context-free, let alone regular. C: 5 states tracking the difference mod 5. D: not regular (not even context-free). E: a(aaa)*.

**14. Answer (2) 3.** We might expect 2 × 2 = 4 (parity × last symbol). But when the parity is odd, the last symbol does not matter, because another a must still come and it will change the last symbol. So "odd, ends in b" and "odd, ends in a" are equivalent. That leaves 3 states. Always check whether the product states are all distinguishable.

**15. Answer (1) E, A, B, C, D.** E = 3, A = 2 + 2 = 4, B = 4 + 1 = 5, C = 2 × 3 = 6, D = 2³ = 8.
