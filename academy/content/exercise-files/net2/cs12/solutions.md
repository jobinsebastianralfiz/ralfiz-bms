# Solutions: practice set 2.4

**1.** LC = 2A0. The instructions take 2A0–2A5, so A = 2A6, B = 2A7 and D = 2A8 (symbol table 3 × 3 = 9 words).
Codes: LDA B 22A7, CMA 7200, INC 7020, ADD A 12A6, STA D 32A8, HLT 7001, A 0040, B FFE3 (−29), D 0000.
Run: AC = −29, and CMA + INC gives +29. Adding 64 gives 93, so **D = 005D hex = 93**.

**2.** Set-up 26. Body (6 + 7 + 7) × 10 = 200. BUN × 9 = 45. Exit 9. Total **280**, option (3). The formula is 25N + 30. Trap: counting BUN ten times gives 285.

**3.** CAR holds the next address (A-III). The CDR holds the current microinstruction (B-I). SBR holds the return address (C-II). The control memory stores the microprogram (D-IV). **Option (1).**

**4.** Select = log₂8 = 3 bits. Next address = 28 − 14 − 3 = 11 bits. **Control memory = 2¹¹ = 2048 words × 28 bits.**

**5.** 1 0101 000 = 10101000₂ = **168**.

**6.** Horizontal = 31 + 12 + 6 + 3 + 1 = **53 bits**. Vertical = ⌈log₂32⌉ + ⌈log₂13⌉ + ⌈log₂7⌉ + ⌈log₂4⌉ + ⌈log₂2⌉ = 5 + 4 + 3 + 2 + 1 = **15 bits**.

**7.** Single level: 1024 × 120 = **122,880 bits**. Nano: 1024 × ⌈log₂200⌉ = 1024 × 8 = 8,192, plus 200 × 120 = 24,000. Total **32,192 bits**, which saves 90,688 bits.

**8.** Both true, and R explains A: complex, changing instruction sets are easier to support when control is stored as data. **Option 1.**

**9.** Both true. The first pass records labels, and the second pass flags any unknown symbol. **Option 1.**

**10.** PC becomes 3A8 during fetch. BSA stores **M[5F0] = 3A8** and sets **PC = 5F1**. The return is **BUN 5F0 I**.

**11.** E = 1110: I = 1, opcode 110 = ISZ. So it is **ISZ indirect**: EA = M[0A2], then M[EA] is incremented, and the next instruction is skipped if the result is 0.

**12.** 8F20 = 1000 1111 0010 0000.
(a) E = 0 enters bit 15: 0100 0111 1001 0000 = **4790**.
(b) The sign is 1, so E becomes 1 and enters bit 15: **C790**, an arithmetic shift that keeps the value negative.

**13.** **B, D, E, A, C**: save, service, restore, ION, return.

**14.** **A, C and D.** B is false: microprogrammed control is easier to debug for large sets. E is false: microprogrammed control is slower.

**15.** The program computes A ∨ B = 3C3C ∨ 00FF = **3CFF**.
