# Solutions: Input–output organization (cs15)

**1. Answer (1): A-II, B-IV, C-I, D-III.** BR is the controller’s request; BG is the CPU’s grant; the word count register holds how many words remain; the address register holds the next memory address. Option (3) swaps the two registers.

**2. Answer (1).** Both true, and R explains A: since the device interrupts only when it needs service, an idle device generates no interrupts and costs no CPU time (unlike polling, which runs whether or not data is ready).

**3. 7.5%.** Polls per second = 12×10^6 ÷ 32 = 375,000. Cycles = 375,000 × 300 = 1.125×10^8. Fraction = 1.125×10^8 ÷ 1.5×10^9 = 0.075.

**4. 15% while busy, 6% average.** Interrupts per second while busy = 375,000. Cycles = 375,000 × 600 = 2.25×10^8, which is 2.25×10^8 ÷ 1.5×10^9 = 15%. Average = 15% × 0.4 = 6%.

**5. About 1.465%.** Blocks per second = 40×10^6 ÷ 4096 = 9765.625. Cycles = 9765.625 × (2000 + 1000) = 29,296,875. Fraction = 29,296,875 ÷ 2×10^9 = 0.01465.

**6. 7.5%.** Words per second = 1,200,000 ÷ 2 = 600,000. Stolen time = 600,000 × 125 ns = 0.075 s per second.

**7. 100.** One initialisation moves 2^20 bytes = 1 MB. 100 MB ÷ 1 MB = 100 exactly, so no rounding is needed.

**8.** Frame = 1 + 7 + 1 + 1 = 10 bits. (a) 19,200 ÷ 10 = 1920 characters per second. (b) 57,600 ÷ 1920 = 30 s. (c) Data bits 7 of 10 = 70%.

**9. 12 and 2.** 3,686,400 ÷ (16 × 19,200) = 12. 3,686,400 ÷ (16 × 115,200) = 2.

**10. About 0.99%.** Preparation = 6000 ÷ 3×10^6 = 2 ms. Transfer = 6000 ÷ 300×10^6 = 20 μs. Blocked = 20 ÷ (2000 + 20) = 0.0099.

**11. x = 1, y = 0, IST = 1.** The highest active input is I2 (code 10); I3 is ignored; IST = 1 because a request exists.

**12. Answer (1): B, A, D, C.** In a destination-initiated transfer the destination first says it is ready; the source then puts data and raises data valid; the destination accepts and drops ready for data; the source drops data valid.

**13. Answer (1): A, B and D only.** C is false: memory-mapped I/O uses up part of the memory address range.

**14. Answer (3).** Transparent (hidden) DMA uses only cycles in which the CPU does not need the bus, so it never slows the CPU (true). A daisy chain has fixed priority set by wiring position (II false); a parallel scheme with a mask register allows software changes.

**15.** Reasons: differences in signal type (electromechanical versus electronic), speed, data format (serial or other codes) and operating modes. Registers/commands: data register (data input and data output), status register (status command), control register (control command).
