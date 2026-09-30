# Solutions: Practice set 7.4

**1. (3) Θ(n²).** Watershed n^(log₃ 9) = n². f(n) = n = O(n^(2−1)), case 1.

**2. (2) Θ(n log² n).** Watershed n = f(n)/log n, so f = Θ(n log¹ n). Extended case 2 with k = 1 gives Θ(n log² n). Trap: the basic master theorem does not cover this; do not answer Θ(n log n).

**3. (2) Θ(log² n).** a = 1, b = 2, watershed n⁰ = 1, f = log n = Θ(1·log¹ n). Case 2 with k = 1 gives Θ(log² n). Unrolling confirms it: log n + (log n − 1) + … + 1 = Θ(log² n).

**4. (2) 63.** i = 1, 2, 4, 8, 16, 32 and the inner loop runs i times: 1 + 2 + 4 + 8 + 16 + 32 = 63 = 2n − 1. Θ(n), not n log n.

**5. (1) B, C, A, E, D.** Take log₂ with L = log₂ n. B: √L. C: L + 2 log L. A: 1.5L. E: 2L. D: L·log L. So B < C < A < E < D. Trap: (log n)^(log n) = n^(log log n), which is super-polynomial.

**6. (1) A-II, B-I, C-IV, D-III.** A: case 1 → Θ(n). B: log 1 + … + log n = log(n!) = Θ(n log n). C: n = 2^m gives S(m) = 2S(m/2) + 1 = Θ(m) = Θ(log n). D: Karatsuba → Θ(n^(log₂ 3)).

**7. (1).** 3^n / 2^n = (1.5)^n → ∞, so 3^n = ω(2^n). R states the equivalent limit 2^n/3^n → 0, which is exactly why.

**8. (1) Both true.** Any positive power of n beats any fixed power of log n, eventually (for very large n). log(n^1000) = 1000 log n.

**9. (1) Θ(n).** Level sums shrink by the factor 1/5 + 7/10 = 9/10, a geometric series, so the total is at most 10n. This is the recurrence of median-of-medians selection.

**10. (3) 63.** Expansions happen at sizes 1, 2, 4, 8, 16 and 32: 1 + 2 + 4 + 8 + 16 + 32 = 63 copies. The 33rd append triggers the expansion from 32 to 64.

**11. (1) A, C and D only.** B is false. E is false: n log n = o(n²). C: n!/2^n → ∞. D: log n/√n → 0.

**12. (2) 5.** i takes 81, 27, 9, 3, 1, then 0 ends the loop: 5 iterations = ⌊log₃ 81⌋ + 1.

**13. (3) Θ(n).** There are n stack frames alive at the deepest point. The iterative version is Θ(1).

**14. (2) Θ(n² log² n).** Watershed n², f = n²·log¹ n, extended case 2 → Θ(n² log² n).

**15. (3) 210.** T(n) = n(n+1)/2, and 20 × 21 / 2 = 210.

## Error-log prompts
- Did you compute the watershed n^(log_b a) before reading options?
- Did you write the loop count as a sum before simplifying?
- Did you check whether the master theorem even applies (equal subproblems, a ≥ 1, division not subtraction)?
