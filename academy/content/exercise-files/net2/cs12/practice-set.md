# Practice set 2.4: programming the basic computer and microprogrammed control

Use Mano’s basic computer: 16-bit words, 12-bit addresses, and the codes AND 0/8, ADD 1/9, LDA 2/A, STA 3/B, BUN 4/C, BSA 5/D, ISZ 6/E. Clock cycles are LDA/ADD/AND 6, STA/BUN 5, BSA 6, ISZ 7, and 4 for register-reference or I/O. Time yourself: about 90 seconds per problem.

**1.** Assemble this program. Give the address symbol table, the hex code of every word, and the final content of D (hex and decimal).

    ORG 2A0
    LDA B
    CMA
    INC
    ADD A
    STA D
    HLT
    A, DEC 64
    B, DEC -29
    D, HEX 0
    END

**2.** The ISZ loop of Example 2 in the lesson (set-up LDA, STA, LDA, STA, CLA; body ADD PTR I, ISZ PTR, ISZ CTR, BUN LOP; exit STA, HLT) now adds N = 10 numbers. How many clock cycles does the program take?
(1) 250  (2) 275  (3) 280  (4) 300

**3.** Match List I with List II.

| List I | List II |
|---|---|
| A. CAR | I. Holds the microinstruction being executed |
| B. Control data register | II. Holds the return address of a microprogram subroutine |
| C. SBR | III. Holds the address of the next microinstruction |
| D. Control memory | IV. Stores the microprogram |

(1) A-III, B-I, C-II, D-IV  (2) A-I, B-III, C-II, D-IV  (3) A-III, B-II, C-I, D-IV  (4) A-III, B-I, C-IV, D-II

**4.** A microinstruction is 28 bits: a 14-bit control field, a select field for 8 status inputs, and a next-address field. Find the three field widths and the control-memory size.

**5.** Mapping rule 1 xxxx 000 (8-bit control address). Find the decimal start address of opcode 0101.

**6.** A CPU has mutually exclusive signal groups of 31, 12, 6, 3 and 1 signals. Each field keeps one "none" code. Give the horizontal and vertical control-field widths.

**7.** A microprogram has 1024 microinstructions of 120 bits, with 200 distinct control words. Compare single-level storage with nanoprogrammed storage.

**8.** Assertion (A): Microprogrammed control is common in CISC processors. Reason (R): The instruction set can be changed by changing the contents of the control memory. Choose from the four standard A–R options.

**9.** Statement I: The first pass of a two-pass assembler builds the address symbol table. Statement II: In the second pass, a symbol missing from every table is reported as an error. Choose from the four standard options.

**10.** The instruction BSA 5F0 is at location 3A7. Give M[5F0] and PC after it executes, and the instruction that returns.

**11.** Decode the instruction word E0A2 (hex).

**12.** AC = 8F20 (hex). Find AC after (a) CLE, CIR and (b) CLE, SPA, CME, CIR.

**13.** Arrange in order: A. ION; B. save AC and E; C. BUN 0 I; D. service the ready device; E. restore E and AC.

**14.** Which are correct? A. A writable control memory allows dynamic microprogramming. B. Hardwired control is easier to debug for large instruction sets. C. Horizontal microcode needs no field decoders. D. The mapping logic turns an opcode into a control-memory address. E. Microprogrammed control is faster than hardwired.

**15.** M[A] = 3C3C, M[B] = 00FF. Give M[R] after LDA A, CMA, STA T, LDA B, CMA, AND T, CMA, STA R.
