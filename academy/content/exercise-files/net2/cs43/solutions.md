# Solutions: Estimation and scheduling (cs43)

**1.** UFP = 20×4 + 12×7 + 8×3 + 6×10 + 4×10 = 80 + 84 + 24 + 60 + 40 = **288**. VAF = 0.65 + 0.45 = 1.10. FP = 288 × 1.10 = **316.8**.

**2.** 316.8 × 50 = 15,840 LOC = **15.84 KLOC**.

**3.** E = 2.4 × 20^1.05 = **55.76 person-months**. D = 2.5 × 55.76^0.38 = **11.52 months**.

**4.** E = 3.6 × 100^1.20 = **904.28 person-months**. D = 2.5 × 904.28^0.32 = 22.08 months. Staff = 904.28 ÷ 22.08 = **40.96 persons**.

**5.** E₂ ÷ E₁ = 2^1.20 = **2.297**. Effort more than doubles because b > 1.

**6.** EAF = 1.40 × 1.08 × 0.86 × 0.91 = **1.1833**. Nominal E = 3.2 × 60^1.05 = 235.62. Adjusted E = 235.62 × 1.18329 = **278.80 person-months**. Trap: using the basic a = 2.4 instead of 3.2.

**7.** Effort ∝ 1 ÷ t⁴: 120 × (15 ÷ 12)⁴ = 120 × 2.4414 = **292.97 person-months**.

**8.** tₑ = (3 + 24 + 15) ÷ 6 = **7 days**. σ = 12 ÷ 6 = 2, σ² = **4**.

**9.** Forward: A 0–5, B 0–3, C 5–9, D starts at max(5, 3) = 5, ends 11; E 9–11; F starts at max(11, 11) = 11, ends 14. **Duration 14 days.** Paths: A-C-E-F = 14, A-D-F = 14, B-D-F = 12. **Two critical paths: A-C-E-F and A-D-F.** C and E are critical, so their total and free floats are **0**. (B has total float 2 and free float 2.)

**10.** σ = 3. Z = (33 − 30) ÷ 3 = 1, P = Φ(1) = **0.8413**. For 97.72% we need Z = 2, so the deadline is 30 + 2 × 3 = **36 weeks**.

**11.** SV = 200 − 250 = **−₹50 lakh**; CV = 200 − 250 = **−₹50 lakh**; SPI = 200 ÷ 250 = **0.8**; CPI = 200 ÷ 250 = **0.8**; EAC = 500 ÷ 0.8 = **₹625 lakh**.

**12.** RE before = 0.4 × 10 = **₹4 lakh**; after = 0.1 × 10 = **₹1 lakh**; RRL = (4 − 1) ÷ 1 = **3**. The mitigation is worth it.

**13.** PV = BCWS, EV = BCWP, AC = ACWP, ETC = EAC − AC: **option (1)**.

**14.** A is true because the EAF depends on each project’s ratings; R states exactly that mechanism. **Option (1).**

**15.** The five scale factors are precedentedness, development flexibility, architecture/risk resolution, team cohesion and process maturity. Required reliability (RELY) is an effort multiplier. **Option (1): A, B, D and E only.**
