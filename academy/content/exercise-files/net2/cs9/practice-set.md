# Practice set 2.1: Digital logic circuits and components

Time yourself: problems 1–8 in 12 minutes, problems 9–15 in 12 minutes. Every question has four options; choose one.

**1.** The minimum number of 2-input NOR gates needed to implement a 2-input XNOR function is:
(1) 3  (2) 4  (3) 5  (4) 6

**2.** The minimum number of 4-to-1 multiplexers needed to build a 64-to-1 multiplexer is:
(1) 16  (2) 20  (3) 21  (4) 63

**3.** F(A, B, C, D) = Σm(1, 3, 4, 11, 12, 13, 14, 15) is implemented with an 8-to-1 multiplexer whose select lines are A, B, C (A is the MSB). The data inputs I0 to I7 must be:
(1) D, D, D′, 0, 0, D, 1, 1
(2) D, D, D, 0, 0, D′, 1, 1
(3) D′, D, D′, 0, 0, D, 1, 1
(4) D, D, D′, 1, 0, D, 1, 1

**4.** The minimum number of 3-to-8 decoders (each with an enable input) needed to build a 6-to-64 decoder is:
(1) 8  (2) 9  (3) 10  (4) 16

**5.** A 5-bit ripple counter uses flip-flops with a propagation delay of 15 ns. Its maximum reliable clock frequency is closest to:
(1) 66.7 MHz  (2) 26.7 MHz  (3) 13.3 MHz  (4) 6.67 MHz

**6.** A synchronous counter uses flip-flops with a propagation delay of 18 ns and a setup time of 4 ns. The AND gates between stages have a delay of 6 ns. The maximum clock frequency is closest to:
(1) 35.7 MHz  (2) 41.7 MHz  (3) 45.5 MHz  (4) 55.6 MHz

**7.** A 4-bit binary ripple counter is made into a mod-12 counter by clearing all flip-flops when a particular state appears. The state to detect and the number of unused states are:
(1) 1011 and 4  (2) 1100 and 4  (3) 1100 and 3  (4) 1011 and 5

**8.** A JK flip-flop starts with Q = 1. The (J, K) inputs at six successive clock edges are (0,1), (1,1), (0,0), (1,0), (1,1), (1,1). The value of Q after the sixth edge, and the number of edges after which Q = 1, are:
(1) 1 and 4  (2) 0 and 3  (3) 1 and 3  (4) 0 and 4

**9.** A synchronous counter has three D flip-flops A, B, C (A is the MSB) with DA = B, DB = C and DC = (A + B)′. Starting from 000, its modulus is:
(1) 3  (2) 4  (3) 5  (4) 6

**10.** Match List I (conversion) with List II (connection).

| List I | List II |
|---|---|
| A. JK to T | I. S = D, R = D′ |
| B. JK to D | II. D = T ⊕ Q |
| C. D to T | III. J = K = T |
| D. SR to D | IV. J = D, K = D′ |

(1) A-III, B-IV, C-II, D-I  (2) A-IV, B-III, C-II, D-I  (3) A-III, B-IV, C-I, D-II  (4) A-III, B-II, C-IV, D-I

**11.** Assertion (A): The states of a ring counter can be identified directly from the flip-flop outputs, without any decoding gates.
Reason (R): In every state of a ring counter, exactly one flip-flop holds a 1.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A)
(2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A)
(3) (A) is true but (R) is false
(4) (A) is false but (R) is true

**12.** Statement I: In a ripple counter, the outputs can briefly pass through wrong intermediate states (glitches) while a change ripples through the stages.
Statement II: A decoder driven by a ripple counter can produce spurious output pulses because of these intermediate states.
(1) Both Statement I and Statement II are true
(2) Both Statement I and Statement II are false
(3) Statement I is true but Statement II is false
(4) Statement I is false but Statement II is true

**13.** Which of the following statements are correct?
A. A decoder with an enable input can be used as a demultiplexer.
B. A priority encoder has a valid output to show that at least one input is active.
C. A 2-to-1 multiplexer can implement the NOT function if the constants 0 and 1 are available.
D. A magnitude comparator is a sequential circuit.
E. A 4-bit comparator checks equality with an XNOR gate per bit.
(1) A, B and C only  (2) A, B, C and E only  (3) B, C, D and E only  (4) A, C and E only

**14.** Arrange the following 4-flip-flop counters in increasing order of the number of states:
A. Binary counter  B. Ring counter  C. Decade counter  D. Johnson counter
(1) B, D, C, A  (2) D, B, C, A  (3) B, C, D, A  (4) B, D, A, C

**15.** A 16-bit ripple-carry adder is built from full adders with a carry delay of 10 ns and a sum delay of 14 ns (both measured from carry-in). Its worst-case addition time is:
(1) 150 ns  (2) 160 ns  (3) 164 ns  (4) 224 ns
