# Practice set: Input–output organization (cs15)

Time: 24 minutes. Unless stated otherwise, 1 MB/s = 10^6 bytes per second and 1 KB = 1024 bytes.

**1. Match List I with List II**

| List I (Signal or register) | List II (Role) |
|---|---|
| A. BR | I. Holds the number of words still to transfer |
| B. BG | II. Raised by the DMA controller to ask for the buses |
| C. Word count register | III. Holds the next memory address for the DMA transfer |
| D. Address register | IV. Raised by the CPU when it releases the buses |

(1) A-II, B-IV, C-I, D-III (2) A-IV, B-II, C-I, D-III (3) A-II, B-IV, C-III, D-I (4) A-II, B-I, C-IV, D-III

**2. Assertion–Reason.**
Assertion (A): With interrupt-driven I/O, a device that is idle costs the CPU nothing.
Reason (R): Interrupts are raised only when the device has data or needs service.
Options: (1) both true, R explains A (2) both true, R does not explain A (3) A true, R false (4) A false, R true

**3.** A 1.5 GHz CPU polls a device delivering 12 MB/s in 32-byte chunks. Each poll costs 300 cycles. What percentage of CPU time does polling use?

**4.** The same device instead interrupts once per 32-byte chunk, costing 600 cycles per interrupt, and it is busy 40% of the time. Find the CPU fraction while the device is busy and the average fraction.

**5.** A 2 GHz CPU uses DMA for a disk delivering 40 MB/s in 4 KB blocks. Each block needs 2000 cycles of setup and a 1000-cycle completion interrupt. What percentage of CPU time is used?

**6.** A device moves 1,200,000 bytes per second by cycle stealing, one 16-bit word per stolen 125 ns memory cycle. What fraction of memory cycles is stolen?

**7.** A DMA controller has a 20-bit byte count register. How many times must it be initialised to transfer a 100 MB file (1 MB = 2^20 bytes)?

**8.** A serial line runs at 19,200 bps with frames of 1 start, 7 data, 1 parity and 1 stop bit. Find (a) characters per second, (b) the time to send 57,600 characters, (c) the data efficiency.

**9.** A UART has a 3.6864 MHz clock and 16× sampling. Find the divisors for 19,200 baud and 115,200 baud.

**10.** A device fills a 6000-byte buffer at 3 MB/s, then the DMA controller bursts it to memory over a 300 MB/s bus while the device waits. Find the percentage of time the CPU is blocked, using transfer ÷ (preparation + transfer).

**11.** In a 4-input parallel priority encoder (I0 highest), I2 and I3 request together. Give x, y and IST.

**12. Order.** Arrange the destination-initiated handshake:
A. Source places data on the bus and enables data valid
B. Destination enables ready for data
C. Source disables data valid and invalidates the data
D. Destination accepts data and disables ready for data
(1) B, A, D, C (2) A, B, D, C (3) B, D, A, C (4) B, A, C, D

**13. Which are correct?**
A. Memory-mapped I/O can use any memory-reference instruction on I/O registers.
B. Isolated I/O needs separate I/O read and I/O write control lines.
C. Memory-mapped I/O leaves the full address range for memory.
D. A multiplexer channel suits many slow devices.
(1) A, B and D only (2) A and C only (3) B, C and D only (4) A, B, C and D

**14. Two statements.**
Statement I: Transparent DMA never slows the CPU.
Statement II: A daisy chain lets software change device priorities at run time.
(1) both true (2) both false (3) I true, II false (4) I false, II true

**15.** List three reasons an interface is needed between a peripheral and the CPU, and name the four registers or commands an interface uses.
