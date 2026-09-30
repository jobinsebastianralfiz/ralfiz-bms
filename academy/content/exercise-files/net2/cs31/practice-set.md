# Practice set: System software (Paper 2, Unit 5.1)

Rules for the hypothetical machine: each imperative statement and DC takes one word; DS n takes n words; EQU takes none; literals are placed one word each at LTORG or END; ORIGIN sets the LC.

Program A (used in problems 1–4):

    PROG    START   500
            MOVER   AREG, ='6'
            MOVEM   AREG, SUM
    NEXT    ADD     AREG, ='1'
            COMP    AREG, LIM
            BC      LT, NEXT
            LTORG
            MOVER   BREG, ='6'
            MULT    BREG, ='3'
    HALF    EQU     NEXT+1
            ORIGIN  NEXT+12
            STOP
    SUM     DS      3
    LIM     DC      '9'
            END

1. What address does NEXT get?
2. At what addresses are =’6’ (first pool), =’1’, and the second-pool literals placed?
3. What value does HALF get, and what address does STOP get?
4. What addresses do SUM and LIM get, and what is the next free address after END?

5. SIC program: ALPHA START 2000; the first four statements are instructions; then X WORD 7; Y RESW 3; Z RESB 20; S BYTE C’HELLO’; T BYTE X’0A’; U RESW 1; END. Give the hexadecimal address of U and the program length.

6. A program translated with origin 0 is loaded at 4000. An instruction at translated address 120 has an operand address 350. Give the addresses of the instruction and the operand after loading.

7. Three modules are linked starting at 1000: A (size 120), B (size 75, translated origin 0) and C (size 60, translated origin 100). C defines an entry point GAMMA at translated address 140. Find the link origin of C and the link address of GAMMA.

8. A macro with 4 model statements is called 5 times in a 30-line source file whose definition occupies 7 lines (MACRO, prototype, 4 model statements, MEND). How many lines does the expanded file contain?

9. What does this print?

        #define DOUBLE(x) x + x
        int main(void) { printf("%d", 3 * DOUBLE(4)); return 0; }

10. What does this print?

        #define MUL(a, b) a * b
        int main(void) { printf("%d", MUL(2 + 3, 4 - 1)); return 0; }

11. Match List I with List II and choose A–?, B–?, C–?, D–?.

| List I | List II |
|---|---|
| A. ESD | I. Words to be relocated or linked |
| B. TXT | II. Symbols defined or referenced externally |
| C. RLD | III. End of the object deck and entry point |
| D. END | IV. Object code and data |

12. Assertion (A): A two-pass assembler needs a table of incomplete instructions. Reason (R): A one-pass assembler must fill in the address of a forward reference after the symbol is defined. Choose from the four standard A–R options.

13. Statement I: A macro call executes faster than an equivalent subroutine call. Statement II: A program using macros is usually smaller than one using subroutines. Choose from the four standard statement options.

14. Which of these belong to pass 1 of a two-pass assembler? A. Build the symbol table. B. Process LTORG. C. Generate the machine code. D. Update the LC. E. Build the literal table.

15. Arrange in order for a two-pass assembler handling ADD AREG, X where X is defined later: A. X is entered in SYMTAB with its address. B. The ADD statement is given its LC value. C. Pass 2 looks up X and writes its address into the instruction. D. Pass 1 reaches the definition of X.
