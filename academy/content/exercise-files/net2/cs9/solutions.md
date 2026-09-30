# Solutions: practice set 2.1

**1. Answer (2) 4.** XNOR is the dual of XOR. n1 = NOR(A, B); n2 = NOR(A, n1); n3 = NOR(B, n1); Y = NOR(n2, n3) = AB + A′B′. Four NOR gates. Five is the count for XOR with NOR gates (or XNOR with NAND gates).

**2. Answer (3) 21.** Level 1: 64/4 = 16 MUXes; level 2: 4; level 3: 1. Total 21 = (64 − 1)/(4 − 1). 63 is the 2-to-1 count.

**3. Answer (1).** Pair minterms by ABC; within each pair the first has D = 0, the second D = 1.
- ABC = 000 (m0, m1): only m1 → D
- 001 (m2, m3): only m3 → D
- 010 (m4, m5): only m4 → D′
- 011 (m6, m7): none → 0
- 100 (m8, m9): none → 0
- 101 (m10, m11): only m11 → D
- 110 (m12, m13): both → 1
- 111 (m14, m15): both → 1
So D, D, D′, 0, 0, D, 1, 1.

**4. Answer (2) 9.** Eight 3-to-8 decoders produce the 64 outputs using the three low bits; one more 3-to-8 decoder driven by the three high bits enables one of the eight. Total 9.

**5. Answer (3) 13.3 MHz.** Worst-case ripple time = 5 × 15 = 75 ns. f = 1/75 ns ≈ 13.33 MHz. 66.7 MHz uses a single flip-flop delay (synchronous rule).

**6. Answer (1) 35.7 MHz.** Minimum period = tpd(FF) + tpd(AND) + setup = 18 + 6 + 4 = 28 ns. f = 1/28 ns ≈ 35.71 MHz. Forgetting setup gives 41.7 MHz.

**7. Answer (2) 1100 and 4.** A mod-12 counter must count 0000 to 1011 and clear at the moment it reaches 12 = 1100 (detect Q3 and Q2 both 1 with a NAND gate driving the clear inputs). Unused states: 16 − 12 = 4.

**8. Answer (1) 1 and 4.** Start Q = 1 and write the trace as a table:

| Edge | J K | Action | Q after |
|---|---|---|---|
| 1 | 0 1 | reset | 0 |
| 2 | 1 1 | toggle | 1 |
| 3 | 0 0 | hold | 1 |
| 4 | 1 0 | set | 1 |
| 5 | 1 1 | toggle | 0 |
| 6 | 1 1 | toggle | 1 |

After the sixth edge Q = 1, and Q = 1 after edges 2, 3, 4 and 6: four edges. Option (4) comes from treating (0,0) as a toggle.

**9. Answer (3) 5.** Trace ABC with A+ = B, B+ = C, C+ = (A + B)′:
- 000 → A+ = 0, B+ = 0, C+ = 1 → 001
- 001 → 0, 1, 1 → 011
- 011 → 1, 1, 0 → 110
- 110 → 1, 0, 0 → 100
- 100 → 0, 0, 0 → 000
Five distinct states: mod-5.

**10. Answer (1) A-III, B-IV, C-II, D-I.** JK to T: tie J = K = T. JK to D: J = D, K = D′ gives DQ′ + DQ = D. D to T: D = T ⊕ Q. SR to D: S = D, R = D′ (never both 1).

**11. Answer (1).** Both statements are true and (R) explains (A). Because exactly one flip-flop is 1 in each state (1000, 0100, 0010, 0001), the output of flip-flop i is itself the “state i” signal: the counter is already a one-hot decoder. The price is that n flip-flops give only n states.

**12. Answer (1).** Both true. When the counter goes from 0111 to 1000, it passes through 0110, 0100 and 0000 for a few nanoseconds each; a decoder driven by these outputs can produce short spurious pulses. This is one reason synchronous counters are preferred for decoding.

**13. Answer (2) A, B, C and E only.** A: the enable acts as the data input, so a decoder with enable is a DEMUX. B: true (the V output). C: with A on the select line, I0 = 1 and I1 = 0 gives A′. D: false, a comparator is combinational. E: true, equality of each bit pair is XNOR.

**14. Answer (1) B, D, C, A.** With 4 flip-flops: ring 4, Johnson 8, decade 10, binary 16.

**15. Answer (3) 164 ns.** (n − 1) × tc + ts = 15 × 10 + 14 = 164 ns. 160 uses 16 × 10; 224 uses 16 × 14.
