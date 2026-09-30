# Solutions: System software practice set

**Program A, with the LC beside each line**

    PROG    START   500
            MOVER   AREG, ='6'     500
            MOVEM   AREG, SUM      501
    NEXT    ADD     AREG, ='1'     502
            COMP    AREG, LIM      503
            BC      LT, NEXT       504
            LTORG                  ='6' at 505, ='1' at 506
            MOVER   BREG, ='6'     507
            MULT    BREG, ='3'     508
    HALF    EQU     NEXT+1         HALF = 503
            ORIGIN  NEXT+12        LC = 514
            STOP                   514
    SUM     DS      3              515-517
    LIM     DC      '9'            518
            END                    ='6' at 519, ='3' at 520

1. **NEXT = 502.**
2. Pool 1 (LTORG): **='6' at 505, ='1' at 506**. Pool 2 (END): the second ='6' is a new pool, so it gets its own word: **='6' at 519, ='3' at 520**.
3. **HALF = 503** (EQU uses no LC). ORIGIN NEXT+12 sets the LC to 514, so **STOP is at 514**.
4. **SUM = 515** (515–517), **LIM = 518**. The literals occupy 519–520, so the next free address is **521**.

5. The instructions are at 2000, 2003, 2006 and 2009. X at 200C, Y at 200F (RESW 3 = 9 bytes), Z at 2018 (RESB 20 = 20 decimal = 14 hex), S at 202C (5 bytes), T at 2031 (1 byte), **U at 2032**. U takes 3 bytes, so the next free address is 2035 and the **length is 35 hex = 53 bytes**.

6. r = 4000 − 0 = 4000. The **instruction is at 4120** and the **operand address becomes 4350**.

7. A occupies 1000–1119 and B 1120–1194, so **C's link origin = 1195**. GAMMA = 1195 + (140 − 100) = **1235**.

8. 30 − 7 (definition) − 5 (calls) + 5 × 4 (expansions) = **38 lines**.

9. 3 * 4 + 4 = **16** (not 24): the body is not bracketed.

10. 2 + 3 * 4 - 1 = 2 + 12 − 1 = **13** (not 15).

11. A-II, B-IV, C-I, D-III.

12. A is false: a two-pass assembler already knows every address when pass 2 starts, so it needs no TII. R is true: it describes backpatching in a one-pass assembler. **(A) is false but (R) is true.**

13. I is true (no call and return linkage at run time). II is false (every call inserts a copy, so the program grows). **Statement I is true but Statement II is false.**

14. **A, B, D and E.** Code generation (C) is pass 2.

15. **B, D, A, C.** The forward reference is first met and given its LC (B), pass 1 later reaches the definition (D) and enters X in SYMTAB (A), and pass 2 fills in the address (C).
