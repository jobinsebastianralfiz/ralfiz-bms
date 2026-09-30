# Practice set 10.5: Genetic algorithms

15 exam-level problems. Positions in strings are counted from the left, starting at 1. In roulette-wheel problems, an individual is selected when its cumulative probability is strictly greater than r for the first time. Give answers to 4 decimal places where they are not exact.

**1.** Four 5-bit chromosomes are 01011, 10100, 00111 and 11010, with fitness f(x) = x², where x is the decoded integer. Find each selection probability and the expected number of copies of each in a mating pool of 4.

**2.** Five individuals have fitness 8, 22, 14, 36 and 20. Build the cumulative probability table and find which individuals are selected by the random numbers 0.07, 0.31, 0.44, 0.93 and 0.66.

**3.** For the same five individuals, stochastic universal sampling uses 5 pointers 0.2 apart, the first at 0.05. Which individuals are selected?

**4.** Parents P1 = 1100101101 and P2 = 0011010110. Find the children of one-point crossover with the cut after bit 6.

**5.** For the same parents, find the children of two-point crossover with cuts after bit 2 and after bit 7.

**6.** For the same parents, apply uniform crossover with the mask 1010011001 (1 = child 1 copies P1). Find both children.

**7.** For L = 8 and the schema H = 0**11*1*, find (a) the order, (b) the defining length, (c) the number of matching strings, (d) the lower bound on crossover survival for pc = 0.8, (e) the exact mutation survival for pm = 0.005.

**8.** A schema of order 2 and defining length 2 (L = 10) has 20 instances. Its average fitness is 15 and the population average is 10. With pc = 0.9 and pm = 0.01, find the schema theorem’s lower bound on the number of instances in the next generation.

**9.** (a) An 8-bit chromosome 11001000 encodes x ∈ [2, 5] linearly, with 00000000 → 2 and 11111111 → 5. Find x. (b) How many bits are needed to encode x ∈ [−2, 3] to 2 decimal places?

**10.** Convert the binary number 0110 to Gray code, and the Gray code 1011 to binary.

**11.** Match List I with List II.

| List I (operator) | List II (main role) |
|---|---|
| A. Selection | I. Keeps the best individual unchanged |
| B. Crossover | II. Restores lost alleles and keeps diversity |
| C. Mutation | III. Gives fitter individuals more offspring |
| D. Elitism | IV. Combines parts of two parents |

(1) A-III, B-IV, C-II, D-I  (2) A-IV, B-III, C-II, D-I  (3) A-III, B-II, C-IV, D-I  (4) A-III, B-IV, C-I, D-II

**12.** Assertion (A): A GA that uses selection alone, with no crossover and no mutation, can never produce a string that was not in the initial population.
Reason (R): Selection only copies strings that already exist in the population.

(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**13.** A population has 20 individuals with distinct fitness values. In a tournament of size 3 (with replacement), find the probability that (a) the best individual wins, (b) the worst individual wins.

**14.** P1 = 2 4 6 8 1 3 5 7 and P2 = 1 2 3 4 5 6 7 8, with cut points after positions 2 and 5. (a) Find the OX child that keeps P1’s segment. (b) Find the PMX child that keeps P1’s segment.

**15.** Which of the following statements are correct?

- A. The schema theorem shows that a GA always finds the global optimum.
- B. Short, low-order, above-average schemata receive exponentially increasing trials.
- C. The mutation term in the schema theorem grows with the order of the schema.
- D. The crossover term in the schema theorem grows with the defining length of the schema.
- E. The theorem counts schemata created by crossover as well as those destroyed.

(1) B, C and D only  (2) A, B and C only  (3) B and D only  (4) B, C, D and E only
