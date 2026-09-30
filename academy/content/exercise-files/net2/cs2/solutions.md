# Solutions 1.2: Sets, relations and functions

**1. Answer: (3)**
A relation is any subset of A × A, which has 16 elements: 2¹⁶ = 65536.

**2. Answer: (2)**
4 diagonal cells free (2⁴) and C(4, 2) = 6 off-diagonal pairs, each both-in or both-out (2⁶): 2^10 = 1024 = 2^(n(n+1)/2).

**3. Answer: (2)**
3⁶ − 3·2⁶ + 3·1⁶ = 729 − 192 + 3 = 540. Check: 3!·S(6, 3) = 6 × 90 = 540.

**4. Answer: (1)**
6 × 5 × 4 × 3 = 360 = 6!/2!. 1296 = 6⁴ counts all functions.

**5. Answer: (3)**
Bell number B₅ = S(5,1) + S(5,2) + S(5,3) + S(5,4) + S(5,5) = 1 + 15 + 25 + 10 + 1 = 52.

**6. Answer: (1)**
S(6, 3) = S(5, 2) + 3·S(5, 3) = 15 + 3 × 25 = 90. 540 is the number of onto functions, which also orders the blocks (3! = 6 times more).

**7. Answer: (3)**
The digraph is a 3-cycle, so every vertex reaches every vertex, including itself (1 → 2 → 3 → 1). The transitive closure is all of A × A: 9 pairs.

**8. Answer: (1)**
D30 ≅ P({2, 3, 5}): Boolean, 8 elements (II). P({a, b}): Boolean, 4 elements (IV). {1, 2, 4, 8} is a chain (I). D12 is distributive, not complemented (2 and 6 have no complement) and not a chain (III).

**9. Answer: (3)**
72 = 2³·3², so the divisors form a 4 × 3 grid of exponents (12 elements). Edges that raise the power of 2: 3 per row × 3 rows = 9. Edges that raise the power of 3: 2 per column × 4 columns = 8. Total 17.

**10. Answer: (1)**
A complement b of 6 needs lcm(6, b) = 36, so 4 | b and 9 | b, so b = 36, but gcd(6, 36) = 6 ≠ 1. So 6 has no complement and D36 is not complemented; the non-square-free factorisation is what creates such an element. R explains A.

**11. Answer: (1)**
(f ∘ g)(3) = f(9) = 19. (g ∘ f)(1) = g(3) = 9. Difference 10.

**12. Answer: (1)**
R is reflexive, symmetric and transitive (check (1,2), (2,1) → (1,1) ✓, and (2,1), (1,2) → (2,2) ✓), so it is an equivalence with classes {1, 2} and {3}. It is not antisymmetric: (1, 2) and (2, 1) with 1 ≠ 2.

**13. Answer: (1)**
2⁴ × 3⁶ = 16 × 729 = 11664.

**14. Answer: (2)**
A commutative operation is fixed by its values on the diagonal (3 cells) and on one cell of each of the 3 off-diagonal pairs: 3^(3 + 3) = 3⁶ = 729. 19683 = 3⁹ counts all binary operations.

**15. Answer: (1)**
Start anywhere and keep stepping down to a strictly smaller element; in a finite poset this must stop at a minimal element, so Statement I is true. In a finite lattice, the join of all elements is the greatest element and the meet of all elements is the least, so Statement II is true.
