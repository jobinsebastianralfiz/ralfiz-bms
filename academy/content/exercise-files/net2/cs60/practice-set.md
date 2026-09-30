# Practice set 9.3: Data link layer

15 exam-level problems. Every question has four options and one correct answer. Aim for about 90 seconds each.

**1.** The data 1010001101 is sent with CRC using the generator 110101. What remainder is appended?
(1) 01110 (2) 1110 (3) 10110 (4) 01011

**2.** The data 10110011 is sent with CRC using the generator x⁴ + x + 1. What is the transmitted codeword?
(1) 101100111011 (2) 10110011010 (3) 101100110010 (4) 101100110100

**3.** Using 16-bit one's complement arithmetic, what is the Internet checksum of the words 0x1A2B, 0xC3D4 and 0x8F10?
(1) 0x6D10 (2) 0x92EF (3) 0x92F0 (4) 0x6D0F

**4.** A code must correct up to 3 bit errors in any codeword. What is the minimum Hamming distance it needs?
(1) 4 (2) 6 (3) 7 (4) 3

**5.** The data 1001 is encoded with Hamming(7,4) (even parity; check bits at positions 1, 2, 4). The codeword is received with bit 6 flipped. What syndrome does the receiver compute?
(1) 3 (2) 5 (3) 7 (4) 6

**6.** A 2 Mbps link carries 4000-bit frames over a path with a one-way propagation delay of 10 ms. Stop-and-wait is used. What are the efficiency and the throughput?
(1) 9.09%, 181.8 kbps (2) 16.7%, 333 kbps (3) 10%, 200 kbps (4) 4.76%, 95.2 kbps

**7.** For the link in problem 6, what is the smallest window that gives 100% utilisation, and how many sequence-number bits does Go-Back-N need for it?
(1) 6 frames, 3 bits (2) 11 frames, 5 bits (3) 11 frames, 4 bits (4) 21 frames, 5 bits

**8.** Go-Back-N with a window of 3 sends 10 frames. Every 5th transmission is lost. Use the batch model: the full window is sent, and after a loss the sender resends from the lost frame. How many transmissions are needed?
(1) 12 (2) 14 (3) 16 (4) 18

**9.** For problem 8's loss pattern, how many transmissions does Selective Repeat need?
(1) 10 (2) 12 (3) 13 (4) 16

**10.** In pure ALOHA, the offered load is G = 1 frame per frame time. What fraction of frame times carries a successful frame?
(1) 0.368 (2) 0.184 (3) 0.135 (4) 0.5

**11.** A 10 Mbps CSMA/CD bus is 2.5 km long, with a signal speed of 2 × 10⁸ m/s. What is the minimum frame size?
(1) 125 bits (2) 250 bits (3) 500 bits (4) 512 bits

**12.** Match List I with List II.

| List I (Requirement) | List II (Minimum Hamming distance) |
|---|---|
| A. Detect up to 5 errors | I. 9 |
| B. Correct up to 4 errors | II. 5 |
| C. Correct up to 2 errors | III. 3 |
| D. Correct 1 error | IV. 6 |

(1) A-IV, B-I, C-II, D-III (2) A-I, B-IV, C-II, D-III (3) A-IV, B-II, C-I, D-III (4) A-IV, B-I, C-III, D-II

**13.** Assertion (A): Go-Back-N wastes bandwidth on noisy links.
Reason (R): After a single lost frame, Go-Back-N retransmits all the outstanding frames that follow it, even if they were received correctly.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A) (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A) (3) (A) is true but (R) is false (4) (A) is false but (R) is true

**14.** HDLC bit stuffing is applied to 01111110111110. What is sent between the flags?
(1) 01111101011111 (2) 011111101111100 (3) 0111110101111110 (4) 0111110101111100

**15.** Which of the following are correct?
A. A CRC with an r-bit remainder detects all burst errors of length at most r.
B. In slotted ALOHA, the vulnerable time is twice the frame time.
C. CSMA/CA uses RTS/CTS to reduce the hidden-station problem.
D. PPP uses LCP to establish and configure the link.
E. The Selective Repeat receiver window is 1.
(1) A, C and D only (2) A, B and C only (3) C, D and E only (4) A, C, D and E only
