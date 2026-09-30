# Solutions: Software quality (cs42)

**1.** A = MTTF ÷ (MTTF + MTTR) = 1200 ÷ 1230 = **97.56%**.

**2.** MTBF already includes MTTR. MTTF = 800 − 8 = 792 h. A = 792 ÷ 800 = **99%**. Trap: 800 ÷ 808 = 99.01% uses MTBF as MTTF.

**3.** 995 ÷ (995 + MTTR) ≥ 0.995 gives MTTR ≤ 995 × 0.005 ÷ 0.995 = **5 hours**.

**4.** Series: 0.98 × 0.97 × 0.99 = 0.941094 ≈ **0.941**.

**5.** Parallel pair: 1 − 0.2 × 0.2 = 0.96. In series with storage: 0.96 × 0.95 = **0.912**.

**6.** (a) MTTF = 1 ÷ 0.001 = **1000 hours**. (b) R(500) = e^(−0.5) = **0.6065**. Note that R(1000) = e^(−1) ≈ 0.368, so most runs do not reach the MTTF.

**7.** (a) λ = 15 × (1 − 60 ÷ 150) = **9** failures per CPU hour.
(b) Δμ = (ν₀ ÷ λ₀)(λP − λF) = (150 ÷ 15)(9 − 3) = **60 failures**.
(c) Δτ = (ν₀ ÷ λ₀) ln(λP ÷ λF) = 10 × ln 3 = **10.99 CPU hours**.

**8.** (1 − 0.9999) × 8760 × 60 = **52.56 minutes**.

**9.** DRE = 120 ÷ (120 + 30) = **0.8**.

**10.** DPMO = 24 × 10⁶ ÷ (800 × 5) = **6000**.

**11.** ACT = (6 + 10) ÷ 80 = 0.2. Annual maintenance effort = 0.2 × 400 = **80 person-months**.

**12.** Reported wrong totals: corrective (A-III). New cloud database: environment change, adaptive (B-I). PDF export on request: perfective (C-IV). Restructuring before problems: preventive (D-II). **Option (1).**

**13.** MTTR > 0, so MTTF + MTTR > MTTF; A is true and follows directly from R. **Option (1).**

**14.** Level 3 KPAs: organisation process focus, organisation process definition, training program, integrated software management, software product engineering, intergroup coordination and peer reviews. Quantitative process management is level 4. **Option (2): A, B, C and E only.**

**15.** Planning, preparation, meeting, rework, follow-up: **C, D, A, E, B, option (1).** Follow-up checks the rework, so it must come last.
