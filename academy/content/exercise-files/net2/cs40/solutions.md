# Solutions: Software requirements (Lesson 6.2)

**1.** (a) F: a service (fee calculation). (b) NF, organisational (operational environment fixed by the organisation). (c) NF, product (efficiency / performance). (d) NF, external (legislative).
Trap: (a) contains a number, but the number is a business rule, not a quality limit.

**2. Answer (1): A-III, B-I, C-II, D-IV.**
Black hole: in but not out. Miracle: out but not in. Grey hole: inputs cannot produce the outputs. Unbalanced: parent and child boundary flows differ.

**3.** (a) 2⁵ = 32 rules.
(b) Covered = 4 × 4 + 3 × 2 + 5 × 1 = 16 + 6 + 5 = 27. Since 27 is less than 32, the table is **incomplete**: 5 combinations have no rule.

**4.** 2 × 2 × 4 × 3 = 48 rules.

**5.** [T | P] gives 2 choices; 2{digit}2 gives 10² = 100; (letter) is optional, so 1 + 26 = 27 choices (absent, or one of 26). Total = 2 × 100 × 27 = 5,400.
Trap: forgetting the “absent” case and getting 5,200.

**6.** n_r = 70 + 30 = 100. Q1 = 88 ÷ 100 = 0.88.
Q2 = 63 ÷ (9 × 10) = 63 ÷ 90 = 0.70.
Q3 = 72 ÷ (72 + 28) = 72 ÷ 100 = 0.72.

**7.** Inputs: coupon is extra at the child level. Outputs: shipment is missing at the child level. Two balancing errors. Fix: add coupon to the parent’s inputs and make the child produce shipment.

**8. Answer (1): A, C and E only.**
A skips a process (store to entity). C is a black hole. E links two entities directly. D is normal.

**9. Order: E, C, F, A, D, B.**
Inception, elicitation, elaboration, negotiation, specification, validation (then management).

**10. Answer (4).** A is false: an extension runs only when its condition holds at the extension point. R is true.

**11. Answer (3).** I is true (test-case generation is a validation technique precisely because untestable requirements are suspect). II is false: the context diagram shows no stores.

**12. Answer (1): A-II, B-IV, C-III, D-I.**
Timing diagrams are interaction diagrams; deployment diagrams show hardware nodes; state machines are behaviour diagrams; package diagrams are structure diagrams.

**13.** For example: “95% of search requests shall complete within 2 seconds with 500 concurrent users.” “The system shall have a mean time to failure of at least 1,000 hours of operation.” Each can be tested.

**14.** (a) Normal (stated). (b) Expected (unstated but basic; its absence causes dissatisfaction). (c) Exciting (beyond expectations).

**15. Answer (2).** Both notations show conditions and actions; the table is better for completeness checks, the tree for readability of sequential tests.
