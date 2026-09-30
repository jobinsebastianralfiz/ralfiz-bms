# Practice set 2.5: central processing unit

About 90 seconds per problem. Unless stated otherwise, the control word is SELA | SELB | SELD | OPR (3, 3, 3, 5 bits), R1–R7 = 001–111, and OPR codes are ADD 00010, SUB 00101, OR 01010, XOR 01100, SHLA 11000.

**1.** (a) Write the control word for R2 ← R5 − R6. (b) Which micro-operation does 001 100 110 01010 perform?

**2.** A two-word "load AC" instruction is stored at 500–501, and its address field is 300. R1 = 250 and XR = 100. Memory: M[300] = 820, M[820] = 120, M[802] = 460, M[400] = 390, M[250] = 700, M[249] = 55. Give the EA and the AC value for direct, immediate, indirect, relative, indexed, register, register indirect, autoincrement and autodecrement modes.

**3.** A 12-bit instruction set uses 4-bit address fields. There are 15 two-address and 14 one-address instructions. How many zero-address instructions are possible?

**4.** A 24-bit instruction has an opcode (60 instructions), one register field (32 registers) and an unsigned immediate field. Find the immediate width and its largest value.

**5.** Convert (A + B × C) × (D − E × F) to postfix. Find the maximum stack depth and the value for A = 2, B = 3, C = 4, D = 10, E = 2, F = 3.

**6.** Write X = A × B + C × D in three-, two-, one- and zero-address code. How many instructions does each need?

**7.** An 8-bit ALU computes E0 − 30 (hex) as A + B′ + 1. Give the result and C, S, Z, V. Which of BHI and BGT are taken?

**8.** (a) A 2-byte branch at address 1000 targets 1100. Find the offset. (b) A 4-byte branch at 2050 has offset −20. Find the target.

**9.** Register windows: G = 10, L = 8, C = 6, W = 5. Find the window size and the register-file size.

**10.** Mix: 40% ALU (1 cycle), 30% loads (3), 10% stores (2), 20% branches (2), with a clock of 950 MHz. Find CPI and MIPS.

**11.** Match List I with List II.

| List I (Mode) | List II (Typical use) |
|---|---|
| A. Immediate | I. Pointer variable |
| B. Register indirect | II. Array element |
| C. Indexed | III. Constant |
| D. Relative | IV. Branch inside a loop |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-II, C-I, D-IV  (4) A-III, B-I, C-IV, D-II

**12.** Assertion (A): Relative addressing lets branch instructions be shorter than those using absolute addresses. Reason (R): A branch offset usually needs fewer bits than a full memory address. Choose from the four standard A–R options.

**13.** Statement I: Zero-address instructions need a stack. Statement II: A zero-address program is always shorter, in instruction count, than a three-address program for the same expression. Choose from the four standard options.

**14.** What is the output?

    #include <stdio.h>
    int main(void) {
        int a[] = {2, 4, 6, 8, 10};
        int *p = a + 1;
        int u = *p++ + 1;
        int v = (*p)++;
        int w = *++p;
        printf("%d %d %d %d\n", u, v, w, a[2]);
        return 0;
    }

**15.** Which are correct? A. RISC relies on the compiler for pipeline scheduling. B. CISC control is usually hardwired. C. RISC uses fixed-length instructions. D. CISC has more addressing modes. E. RISC instructions can add two memory operands directly.
