# Solutions: practice set 2.3

**1. Answer (2).** One multiplexer per bus bit: 32. Each has one input per register: 16 × 1. Select lines: log₂ 16 = 4.

**2. Answer (1).** One buffer per register bit: 16 × 32 = 512. A 4 × 16 decoder enables one register’s 32 buffers.

**3. Answer (3) R1 = C5, R2 = 3A.** The comma means both transfers use the same clock edge. Edge-triggered flip-flops sample their inputs before any output changes, so the registers swap.

**4. Answer (1).** Selective complement A ⊕ B = 11010011 ⊕ 00111100 = 11101111. Selective clear A ∧ B′ = 11010011 ∧ 11000011 = 11000011.

**5. Answer (3).** ashr copies the sign bit: 1 1100101 = 11100101. cil moves bit 7 (1) round to bit 0: 1001011 1 = 10010111.

**6. Answer (1).** 011: A + B′ + 1 = A − B = 10 − 7 = 3 = 0011. 110: A − 1 = 9 = 1001.

**7. Answer (1) A-III, B-IV, C-I, D-II.** 7020 = INC. B1A5: B = 1011, so I = 1 and opcode 011 (STA), address 1A5. F400 = OUT. 6012: I = 0, opcode 110 (ISZ), address 012.

**8. Answer (2) 1000, 1, 0A1.** 10C4 is ADD direct, EA = 0C4. DR = D0E0. 3F20 + D0E0 = 1 1000: AC = 1000, E = 1. PC was incremented to 0A1 at T1. Option (3) shows a 17-bit AC, which is impossible.

**9. Answer (1) 0002, 1.** 8001 = 1000 0000 0000 0001. Shift left: 0000 0000 0000 0010, bit 0 takes E = 0. The old bit 15 (1) goes to E. AC = 0002, E = 1.

**10. Answer (1).** BSA: M[300] ← 046 (PC after fetch), PC ← 301. BUN 300 I: EA = M[300] = 046, so PC ← 046, back after the call.

**11. Answer (3) 1050 ns.** LDA: T0–T5 = 6 pulses. ADD: 6. STA: T0–T4 = 5. HLT: T0–T3 = 4. Total 21 pulses × 50 ns = 1050 ns.

**12. Answer (3) 01F4, 001.** During the fetch of the instruction at 1F3, PC became 1F4. The interrupt cycle saves PC as it is (TR ← PC, then M[0] ← TR), so M[0] = 01F4. PC ← 0 and then PC ← 1.

**13. Answer (1).** Both true, and (R) explains (A): opcodes 000–110 give 7 memory-reference instructions; opcode 111 with I = 0 gives 12 register-reference instructions and with I = 1 gives 6 I/O instructions, using bits 0–11: 7 + 12 + 6 = 25.

**14. Answer (1) A, B, C and E only.** D is false: INPR feeds the adder and logic circuit, which loads AC; it is not a bus source. The bus sources are AR, PC, DR, AC, IR, TR and memory (codes 1–7).

**15. Answer (1) E, C, B, D, A.** T0: AR ← PC. T1: IR ← M[AR], PC ← PC + 1. (T2: decode.) T3: AR ← M[AR] (indirect). T4: DR ← M[AR]. T5: AC ← AC ∧ DR, SC ← 0.
