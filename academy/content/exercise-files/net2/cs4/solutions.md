# Solutions: Practice set 1.4

**1.** Sum 8 has 5 equally likely outcomes: (2,6), (3,5), (4,4), (5,3), (6,2). Both even: (2,6), (4,4), (6,2), which is 3 outcomes. P = 3/5. Trap: 5/36 is P(sum = 8), and 1/4 is the unconditional P(both even). **Answer: (1) 3/5**

**2.** Tree: P(C ∩ +) = 0.2 × 0.9 = 0.18; P(C̄ ∩ +) = 0.8 × 0.1 = 0.08; P(+) = 0.26. P(C | +) = 0.18/0.26 = 9/13 ≈ 0.692. Trap: 0.90 is P(+ | C), 0.26 is P(+), 0.18 is the joint probability. **Answer: (3) 9/13**

**3.** Binomial: C(4,2)(0.6)²(0.4)² = 6 × 0.36 × 0.16 = 0.3456. Trap: forgetting the C(4,2) factor gives 0.0576; 0.1536 is P(exactly 1 head) = 4 × 0.6 × 0.064. **Answer: (1) 0.3456**

**4.** Glue A and B into a block: 4! arrangements of 4 units × 2 internal orders = 48 out of 5! = 120. P = 48/120 = 2/5. Check: there are 4 adjacent seat pairs out of C(5,2) = 10 pairs of seats, 4/10 = 2/5. **Answer: (2) 2/5**

**5.** E[X] = −0.3 + 0 + 1.0 = 0.7. E[X²] = 0.3 + 0 + 2.0 = 2.3. Var = 2.3 − 0.49 = 1.81. Trap: 2.3 is E[X²]; 0.7 is the mean. **Answer: (3) 1.81**

**6.** P(0) = e^−3 × 3⁰/0! = e^−3 ≈ 0.0498. Trap: 0.1494 is P(1) = 3e^−3; 0.9502 is P(at least one error); 0.2240 is P(2) = 4.5e^−3. **Answer: (1) 0.0498**

**7.** P(A ∩ B̄) + P(Ā ∩ B) = 0.4 × 0.5 + 0.6 × 0.5 = 0.2 + 0.3 = 0.5. Trap: 0.9 adds P(A) + P(B); 0.7 is P(A ∪ B) = 0.4 + 0.5 − 0.2, which also counts “both”. **Answer: (3) 0.5**

**8.** Geometric, trials version: mean = 1/p = 3. Trap: 2 = (1 − p)/p is the expected number of tails before the first head. **Answer: (1) 3**

**9.** By the hypothesis, 1 + … + k = k(k + 1)/2; adding the next term k + 1 gives k(k + 1)/2 + (k + 1) = (k + 1)(k/2 + 1) = (k + 1)(k + 2)/2. Trap: option 1 adds k instead of k + 1. **Answer: (2) k(k + 1)/2 + (k + 1)**

**10.** A: binomial mean np = 12 × ½ = 6 (II). B: geometric with p = ½, mean 1/p = 2 (IV). C: success = rolling 1 or 2, so p = 1/3 and the mean is 3 (I). D: linearity, 12 × 7/2 = 42 (III). Trap: option 3 swaps A and B by confusing the count of successes with the waiting time. **Answer: (1) A-II, B-IV, C-I, D-III**

**11.** R is the algebra that proves A: expand the complement of the union with inclusion–exclusion and use P(A ∩ B) = P(A)P(B); the result factorises as P(Ā)P(B̄). **Answer: (1) Both (A) and (R) are true and (R) is the correct explanation of (A)**

**12.** Statement I: a step that uses two earlier cases needs two base cases (as in Fibonacci proofs), so it is true. Statement II: P(X > s + t | X > s) = (1 − p)^(s+t)/(1 − p)^s = (1 − p)^t = P(X > t), so it is true. **Answer: (1) Both Statement I and Statement II are true**

**13.** A is inclusion–exclusion for three events. B: if exclusive, P(A ∪ B) = 1.3 > 1, impossible, so true. C: A ∩ B = A, so P(B | A) = P(A)/P(A) = 1. D: conditioning on B is still a probability measure, so the complement rule holds. E is false: with A = S both terms are 1 and the sum is 2. **Answer: (1) A, B, C and D only**

**14.** P(R) = ½ × ⅓ + ¼ × ⅔ + ¼ × ½ = 1/6 + 1/6 + 1/8 = 11/24. P(U₂ | R) = (1/6)/(11/24) = 4/11 ≈ 0.364. Trap: 1/4 is the prior for U₂ and 2/3 is P(R | U₂). **Answer: (2) 4/11**

**15.** Fixed points: expected 1 for every n. Inversions: C(6,2)/2 = 15/2 = 7.5. Total = 8.5 by linearity. Trap: 7.5 forgets the fixed points; 16 uses the maximum 15 inversions. **Answer: (1) 8.5**