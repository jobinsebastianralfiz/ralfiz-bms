# Practice set: Estimation and scheduling (cs43)

Time: 25 minutes. Use Boehm’s coefficients: basic organic (2.4, 1.05), semi-detached (3.0, 1.12), embedded (3.6, 1.20); c = 2.5 with d = 0.38, 0.35, 0.32; intermediate a = 3.2, 3.0, 2.8. FP weights (simple/average/complex): EI 3/4/6, EO 4/5/7, EQ 3/4/6, ILF 7/10/15, EIF 5/7/10.

1. A system has 20 average EIs, 12 complex EOs, 8 simple EQs, 6 average ILFs and 4 complex EIFs. The 14 general system characteristics add up to 45. Find UFP and FP.

2. The project in problem 1 will be written at 50 LOC per function point. Estimate its size in KLOC (two decimals).

3. Using basic COCOMO, find the effort and development time of a 20 KLOC organic project (two decimals).

4. Using basic COCOMO, find the effort of a 100 KLOC embedded project, and the average staff size (two decimals).

5. By what factor does basic COCOMO effort grow when an embedded project’s size doubles? (Three decimals.)

6. A 60 KLOC organic project is rated: RELY very high (1.40), DATA high (1.08), PCAP high (0.86), TOOL high (0.91). All other drivers are nominal. Find the EAF (four decimals) and the intermediate COCOMO effort (two decimals).

7. Under the Putnam model, a project needs 120 person-months over 15 months. Estimate the effort if the schedule is cut to 12 months (two decimals).

8. An activity has a = 3, m = 6, b = 15 days. Find tₑ and σ².

9. Activities (days; predecessors): A 5 (none), B 3 (none), C 4 (A), D 6 (A, B), E 2 (C), F 3 (D, E). Find the project duration, the critical path, and the total and free float of C and E.

10. A PERT critical path has Tₑ = 30 weeks and σ² = 9. Find the probability (four decimals) of finishing within 33 weeks, and the deadline that gives about 97.72% confidence.

11. BAC = ₹500 lakh. At the review: PV = ₹250 lakh, EV = ₹200 lakh, AC = ₹250 lakh. Find SV, CV, SPI, CPI and EAC.

12. A risk has probability 0.4 and impact ₹10 lakh. A ₹1 lakh mitigation would cut the probability to 0.1. Find RE before and after, and the RRL.

13. Match List I with List II.

| List I (EVM term) | List II (Also called) |
|---|---|
| A. Planned value | I. ACWP |
| B. Earned value | II. BCWS |
| C. Actual cost | III. BCWP |
| D. Estimate to complete | IV. EAC − AC |

Options: (1) A-II, B-III, C-I, D-IV (2) A-III, B-II, C-I, D-IV (3) A-II, B-I, C-III, D-IV (4) A-II, B-III, C-IV, D-I

14. Assertion (A): Two projects of the same size can get different effort estimates in intermediate COCOMO even when both are organic.
Reason (R): Intermediate COCOMO multiplies the nominal effort by the product of 15 cost-driver multipliers.
Options: (1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

15. Which of the following are scale factors in COCOMO II?
A. Precedentedness  B. Development flexibility  C. Required reliability  D. Team cohesion  E. Process maturity
Options: (1) A, B, D and E only (2) A, B and C only (3) C, D and E only (4) A, B, C, D and E
