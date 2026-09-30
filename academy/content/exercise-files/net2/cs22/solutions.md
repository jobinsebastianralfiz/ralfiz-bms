# Solutions: Output primitives practice set

**1.** (a) 800 × 600 × 16 = 7,680,000 bits = **960,000 bytes** (about 937.5 KB). (b) 2¹⁶ = **65,536 colours**.

**2.** 60 × 1280 × 1024 = 78,643,200 pixels per second, so 1/78,643,200 s ≈ **12.7 ns** per pixel.

**3.** Δx = 8, Δy = 5, y increases by 0.625. y = 3, 3.625, 4.25, 4.875, 5.5, 6.125, 6.75, 7.375, 8 → pixels **(2, 3), (3, 4), (4, 4), (5, 5), (6, 6), (7, 6), (8, 7), (9, 7), (10, 8)**. The tie at 5.5 rounds up to 6.

**4.** Δx = 10, Δy = 6, p₀ = 2. p₀ to p₄: **2, −6, 6, −2, 10**. Full list of pₖ: 2, −6, 6, −2, 10, 2, −6, 6, −2, 10. Pixels: **(5, 8), (6, 9), (7, 9), (8, 10), (9, 10), (10, 11), (11, 12), (12, 12), (13, 13), (14, 13), (15, 14)**.

**5.** |Δy| = 9 > |Δx| = 4, so **y is the major axis** and DDA plots 9 + 1 = **10 pixels**.

**6.** p₀ = 1 − 7 = −6. Parameters: **−6, −3, 2, −3, 6**. Points: **(0, 7), (1, 7), (2, 7), (3, 6), (4, 6), (5, 5)**; the octant ends at x = y = 5.

**7. Option 1: both true and R explains A.** Because of 4-way symmetry only one quadrant is needed, and because the slope passes through −1, x is the better step variable before that point (region 1) and y after it (region 2).

**8. Option (1): A-II, B-IV, C-I, D-III.**

**9.** (0, 5): left and below → **0101**. (30, 50): above → **1000**. (5, 45): above and left → **1001**. (30, 60): above → **1000**. Line (0,5)–(30,50): 0101 AND 1000 = 0000 → not rejected, must be clipped. Line (5,45)–(30,60): 1001 AND 1000 = 1000 → **trivially rejected**.

**10.** Codes 0001 and 1010. Left edge x = 10 gives y = 25; top edge y = 40 gives x = 40. Visible segment **(10, 25) to (40, 40)**.

**11.** Δx = 20, Δy = 6. p = (−20, 20, −6, 6), q = (−5, 15, 3, 7), ratios 1/4, 3/4, −1/2, 7/6. u₁ = **1/4**, u₂ = **3/4**. Segment **(0, 4.5) to (10, 7.5)**.

**12.** m = 45/30 = 1.5. P = (0, 5), code 0101. Clipping at the bottom edge first gives (3.33, 10), which is still left of the window (code 0001); clipping that at x = 10 gives y = 5 + 1.5 × 10 = 20, so P becomes (10, 20) with code 0000. (Taking the left edge first reaches the same point.) Q = (30, 50), code 1000: y = 40 gives x = (40 − 5)/1.5 = 23.33. Visible segment **(10, 20) to (23.33, 40)** (x = 70/3).

**13.** Counts: left **3**, right **4**, bottom **4**, top **5**. Final polygon: **(3, 3), (10, 3), (10, 8), (8, 10), (3, 10)**.

**14. A, C and D.** B is false: 4-connected means left, right, up and down only.

**15.** sₓ = 2, s_y = 4, so (30, 20) → **(260, 180)**. Because sₓ ≠ s_y, a circle becomes an ellipse.
