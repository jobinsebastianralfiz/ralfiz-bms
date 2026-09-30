# Practice set 2.3: Register transfer and basic computer organization

Time yourself: problems 1–8 in 12 minutes, problems 9–15 in 12 minutes. Every question has four options; choose one. Unless stated, “the basic computer” is Mano’s basic computer, and all values are hexadecimal.

**1.** A common bus for 16 registers of 32 bits each is built with multiplexers. It needs:
(1) 16 multiplexers of 32 × 1, 5 select lines  (2) 32 multiplexers of 16 × 1, 4 select lines  (3) 32 multiplexers of 16 × 1, 16 select lines  (4) 4 multiplexers of 32 × 1, 4 select lines

**2.** The same bus (16 registers × 32 bits) is built with three-state buffers instead. It needs:
(1) 512 buffers and a 4 × 16 decoder  (2) 32 buffers and a 4 × 16 decoder  (3) 512 buffers and a 5 × 32 decoder  (4) 48 buffers and a 4 × 16 decoder

**3.** Registers R1 = 3A and R2 = C5 are edge-triggered. The statement T: R1 ← R2, R2 ← R1 is executed when T = 1. Afterwards:
(1) R1 = C5, R2 = C5  (2) R1 = 3A, R2 = 3A  (3) R1 = C5, R2 = 3A  (4) R1 = 3A, R2 = C5

**4.** A = 11010011 and B = 00111100. The results of selective complement and selective clear on A (each applied to the original A) are:
(1) 11101111 and 11000011  (2) 11111111 and 11000011  (3) 11101111 and 00010000  (4) 00010000 and 11000011

**5.** R = 11001011 (8 bits). The results of ashr R and cil R (each applied to the original R) are:
(1) 01100101 and 10010111  (2) 11100101 and 10010110  (3) 11100101 and 10010111  (4) 11100101 and 11100101

**6.** In Mano’s arithmetic circuit, A = 1010 and B = 0111. The outputs for S1 S0 Cin = 011 and 110 are:
(1) 0011 and 1001  (2) 0010 and 1001  (3) 0011 and 1011  (4) 0011 and 1010

**7.** Match List I (hex instruction) with List II (meaning).

| List I | List II |
|---|---|
| A. 7020 | I. Output a character (OUT) |
| B. B1A5 | II. Increment and skip if zero, direct address 012 |
| C. F400 | III. Increment AC (INC) |
| D. 6012 | IV. Store AC, indirect address 1A5 |

(1) A-III, B-IV, C-I, D-II  (2) A-III, B-I, C-IV, D-II  (3) A-II, B-IV, C-I, D-III  (4) A-III, B-IV, C-II, D-I

**8.** PC = 0A0, AC = 3F20, E = 0, M[0A0] = 10C4 and M[0C4] = D0E0. After the instruction at 0A0, AC, E and PC are:
(1) 1000, 0, 0A1  (2) 1000, 1, 0A1  (3) 11000, 0, 0A1  (4) 1000, 1, 0C4

**9.** AC = 8001 and E = 0. After CIL (7040), AC and E are:
(1) 0002, 1  (2) 0003, 0  (3) 0002, 0  (4) C000, 1

**10.** A subroutine starts at 300. The instruction at 045 is BSA 300 (5300). The subroutine ends with BUN 300 I (C300). After the BSA, M[300] and PC are ______, and after the BUN 300 I, PC is ______.
(1) 046, 301; 046  (2) 045, 301; 045  (3) 046, 300; 046  (4) 046, 301; 300

**11.** The program LDA X; ADD Y; STA Z; HLT uses direct addresses. Counting one clock pulse per timing signal, with a 50 ns clock, how long does it take?
(1) 800 ns  (2) 950 ns  (3) 1050 ns  (4) 1150 ns

**12.** An interrupt is pending (IEN = 1, FGO = 1) while the instruction at address 1F3 (not a branch or skip) executes. When the interrupt cycle ends, M[0] and PC are:
(1) 01F3, 001  (2) 01F4, 000  (3) 01F4, 001  (4) 01F5, 001

**13.** Assertion (A): The basic computer has 25 instructions although its operation code field has only 3 bits.
Reason (R): When the opcode is 111, the remaining 12 bits of the instruction specify one of several register-reference or input–output operations instead of an address.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**14.** Which statements about the common bus of the basic computer are correct?
A. It is 16 bits wide.
B. It has 3 select lines S2 S1 S0.
C. The memory unit is selected by code 7.
D. INPR places its contents directly on the bus.
E. When AR is placed on the bus, the 4 high-order bus lines carry 0.
(1) A, B, C and E only  (2) A, B and C only  (3) A, B, C, D and E  (4) B, C and E only

**15.** Arrange the micro-operations of an indirect AND instruction in the order of the timing signals.
A. AC ← AC ∧ DR, SC ← 0
B. AR ← M[AR]
C. IR ← M[AR], PC ← PC + 1
D. DR ← M[AR]
E. AR ← PC
(1) E, C, B, D, A  (2) E, C, D, B, A  (3) C, E, B, D, A  (4) E, B, C, D, A
