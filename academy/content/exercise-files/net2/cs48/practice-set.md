# Practice set 7.4: Performance analysis and recurrences

Time: 25 minutes. Each question has one correct option. No negative marking.

**1.** What is the solution of T(n) = 9T(n/3) + n?
(1) Θ(n) (2) Θ(n log n) (3) Θ(n²) (4) Θ(n² log n)

**2.** What is the solution of T(n) = 2T(n/2) + n log n?
(1) Θ(n log n) (2) Θ(n log² n) (3) Θ(n²) (4) Θ(n log log n)

**3.** What is the solution of T(n) = T(n/2) + log n?
(1) Θ(log n) (2) Θ(log² n) (3) Θ(n) (4) Θ(log log n)

**4.** How many times does x++ execute when n = 32?

    for (i = 1; i <= n; i = i * 2)
        for (j = 1; j <= i; j++)
            x++;

(1) 32 (2) 63 (3) 160 (4) 192

**5.** Arrange in increasing order of growth: A. n^(3/2), B. 2^(√(log₂ n)), C. n log² n, D. (log n)^(log n), E. n².
(1) B, C, A, E, D (2) C, B, A, E, D (3) B, C, A, D, E (4) B, A, C, E, D

**6.** List I / List II. Match each recurrence with its solution.

| List I | List II |
|---|---|
| A. T(n) = 2T(n/2) + 1 | I. Θ(n log n) |
| B. T(n) = T(n − 1) + log n | II. Θ(n) |
| C. T(n) = 2T(√n) + 1 | III. Θ(n^(log₂ 3)) |
| D. T(n) = 3T(n/2) + n | IV. Θ(log n) |

(1) A-II, B-I, C-IV, D-III (2) A-IV, B-I, C-II, D-III (3) A-II, B-III, C-IV, D-I (4) A-II, B-I, C-III, D-IV

**7.** Assertion (A): 3^n = ω(2^n). Reason (R): lim (n → ∞) 2^n / 3^n = 0.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**8.** Statement I: n^0.001 = ω(log¹⁰⁰⁰ n). Statement II: log(n^1000) = Θ(log n).
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**9.** What is the solution of T(n) = T(n/5) + T(7n/10) + n?
(1) Θ(n) (2) Θ(n log n) (3) Θ(n²) (4) Θ(log n)

**10.** An array starts with capacity 1 and doubles when full, copying all elements. How many element copies are made in 33 appends?
(1) 32 (2) 33 (3) 63 (4) 64

**11.** Which are correct? A. n = O(n²) B. n² = O(n) C. 2^n = o(n!) D. log n = o(√n) E. n log n = Ω(n²)
(1) A, C and D only (2) A and D only (3) A, B and C only (4) C, D and E only

**12.** What is printed?

    int n = 81, c = 0;
    for (int i = n; i >= 1; i = i / 3) c++;
    printf("%d", c);

(1) 4 (2) 5 (3) 27 (4) 3

**13.** The recursive factorial function fact(n) = n × fact(n − 1) uses how much auxiliary space?
(1) Θ(1) (2) Θ(log n) (3) Θ(n) (4) Θ(n²)

**14.** What is the solution of T(n) = 4T(n/2) + n²·log n?
(1) Θ(n² log n) (2) Θ(n² log² n) (3) Θ(n³) (4) Θ(n²)

**15.** What is the exact value of T(n) = T(n − 1) + n with T(1) = 1, for n = 20?
(1) 190 (2) 200 (3) 210 (4) 400
