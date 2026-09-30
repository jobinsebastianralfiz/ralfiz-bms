# Solutions: Transformations, 3D and curves practice set

**1.** M = T(2, 2)·R(90°)·T(−2, −2) = [0 −1 4; 1 0 0; 0 0 1]. Image: **(1, 4)**.

**2.** M = [2 0 −1; 0 3 −2; 0 0 1]. Corners: **(1, 1), (5, 1), (5, 4), (1, 4)**. Area grows from 2 to 12 (factor 6 = det).

**3.** M = [0 1 −2; 1 0 2; 0 0 1], i.e. (x, y) → (y − 2, x + 2). Image: **(−1, 5)**.

**4.** Corners **(0, 0), (1, 0), (3, 1), (2, 1)**. Area stays **1** (det = 1).

**5.** Original area = ½ × 4 × 3 = 6. |det| of the composite = 1 × (2 × 2) = 4. New area = **24**.

**6.** R·T: translate first, then rotate: **(0, 4)**. T·R: rotate first, then translate: **(3, 1)**.

**7.** (1, 0, 0) → **(0, 0, −1)** about y. (0, 1, 0) → **(0, 0, 1)** about x (y′ = y cos θ − z sin θ = 0, z′ = y sin θ + z cos θ = 1).

**8.** Perspective: x = 6 × 3/12 = 1.5, y = 4 × 3/12 = 1, so **(1.5, 1)**. Orthographic: **(6, 4)**.

**9.** t = 1/2: **(4, 3)**. t = 1/4: **(1.8125, 2.25)**. Tangent at 0: 3(P₁ − P₀) = **(6, 12)**.

**10. Option (1): A-II, B-I, C-IV, D-III.**

**11.** n + 1 = 10, so n = 9, d = 4. Knots = n + d + 1 = **14**. Segments = n − 2 = **7**.

**12.** Yellow (0.9 < 1.0) is stored, then red (0.3 < 0.9) replaces it, then green (0.5 is not < 0.3) is rejected: **red** is shown. The painter's algorithm sorts from far to near (0.9, 0.5, 0.3) and draws **red last**, so the result is the same.

**13.** CMY = (1 − 0.2, 1 − 0.4, 1 − 0.6) = **(0.8, 0.6, 0.4)**. K = min = 0.4, so CMYK = **(0.4, 0.2, 0, 0.4)**. V = max = **0.6**; S = (0.6 − 0.2)/0.6 = **0.667** (2/3). H = 210°.

**14. Option 1: both true, and R explains A.** Transposing needs no division, unlike the general inverse (adjugate ÷ determinant).

**15.** Each buffer = 1024 × 768 × 3 bytes = 2,359,296 bytes = 2.25 MB. Together **4.5 MB**.
