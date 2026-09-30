# Solutions: practice set 2.5

**1.** (a) SELA = R5 = 101, SELB = R6 = 110, SELD = R2 = 010, SUB = 00101, giving **101 110 010 00101**. (b) SELA = R1, SELB = R4, SELD = R6, OPR = OR, so **R6 ← R1 ∨ R4**.

**2.** PC after fetch = 502.

| Mode | EA | AC |
|---|---|---|
| Direct | 300 | 820 |
| Immediate | 501 | 300 |
| Indirect | 820 | 120 |
| Relative | 502 + 300 = 802 | 460 |
| Indexed | 100 + 300 = 400 | 390 |
| Register | none | 250 |
| Register indirect | 250 | 700 |
| Autoincrement | 250 (R1 becomes 251) | 700 |
| Autodecrement | 249 | 55 |

**3.** Two-address opcode = 12 − 8 = 4 bits, which is 16 patterns; 15 are used, leaving 1. One-address patterns = 1 × 2⁴ = 16; 14 are used, leaving 2. Zero-address = 2 × 2⁴ = **32**.

**4.** Opcode ⌈log₂60⌉ = 6 and register ⌈log₂32⌉ = 5, so immediate = 24 − 11 = **13 bits**, with a maximum of **8191**.

**5.** **A B C × + D E F × − ×**. The maximum depth is **4**, reached when D E F are pushed on top of the first partial result. Value (2 + 12) × (10 − 6) = **56**.

**6.**
- Three-address: MUL R1, A, B; MUL R2, C, D; ADD X, R1, R2 (**3**).
- Two-address: MOV R1, A; MUL R1, B; MOV R2, C; MUL R2, D; ADD R1, R2; MOV X, R1 (**6**).
- One-address: LOAD A; MUL B; STORE T; LOAD C; MUL D; ADD T; STORE X (**7**).
- Zero-address: PUSH A; PUSH B; MUL; PUSH C; PUSH D; MUL; ADD; POP X (**8**).
With A = 6, B = 4, C = 9, D = 2 every version gives 42.

**7.** 30′ + 1 = D0, and E0 + D0 = 1 B0. The result is **B0**, with **C = 1, S = 1, Z = 0, V = 0**.
- Unsigned 224 > 48 with C = 1 and Z = 0, so **BHI is taken**.
- Signed −32 − 48 = −80, so A < B. S ⊕ V = 1, so **BGT is not taken**.

**8.** (a) 1100 − (1000 + 2) = **+98**. (b) 2050 + 4 − 20 = **2034**.

**9.** Window = 8 + 12 + 10 = **30**. File = (8 + 6) × 5 + 10 = **80**.

**10.** CPI = 0.4 + 0.9 + 0.2 + 0.4 = **1.9**. MIPS = 950 / 1.9 = **500**.

**11.** **Option (1)**: constant, pointer, array, loop branch.

**12.** Both true, and R explains A. **Option 1.**

**13.** I is true: operands are implied at the top of the stack. II is false: zero-address programs need more instructions (8 against 3 for our examples), though each instruction is shorter. **Statement I true, Statement II false.**

**14.** u = a[1] + 1 = 5, and p moves to a[2]. v = a[2] = 6, and then a[2] becomes 7. w: p moves to a[3], so w = 8. Output **5 6 8 7** (verified with gcc).

**15.** **A, C and D.** B is false: CISC is usually microprogrammed. E is false: RISC is load/store.
