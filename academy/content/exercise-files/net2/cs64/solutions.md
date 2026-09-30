# Solutions: Mobile technology, cloud computing and IoT (cs64)

**1. Answer (2): N = 13, D/R ≈ 6.24.**
N = i² + ij + j² = 9 + 3 + 1 = 13. D/R = √(3 × 13) = √39 ≈ 6.24.
Option (3) uses √N ≈ 3.61. Option (1) uses i² + j² = 10, which is not a valid cluster size.

**2. Answer (4): 10.**
The valid sizes from i² + ij + j² are 1, 3, 4, 7, 9, 12, 13, 16 … There is no pair (i, j) that gives 10: the candidates 9 (3, 0), 7 (2, 1) and 12 (2, 2) jump over it.

**3. (a) 150, (b) 50.**
A duplex channel takes 2 × 25 = 50 kHz, so there are 30 MHz ÷ 50 kHz = 600 duplex channels.
(a) 600 ÷ 4 = 150 per cell. (b) 600 ÷ 12 = 50 per cell.
The larger cluster gives better S/I but only a third of the channels per cell.

**4. 6000 calls.**
70 ÷ 7 = 10 clusters, and every cluster reuses all 600 channels. So the capacity is 10 × 600 = 6000 simultaneous calls. This is why frequency reuse, and cell splitting to get more clusters, raise capacity.

**5. A silent, B sent 1, C sent 0, D silent.**
Divide each inner product by 4:
S·A = 0 − 2 + 2 + 0 = 0, so A was silent.
S·B = 0 + 2 + 2 + 0 = 4, giving +1, so B sent 1.
S·C = 0 − 2 − 2 + 0 = −4, giving −1, so C sent 0.
S·D = 0 + 2 − 2 + 0 = 0, so D was silent.
Check: B − C = (0, −2, 2, 0).

**6. About 4.38 hours = 262.8 minutes.**
(1 − 0.9995) × 365 × 24 = 0.0005 × 8760 = 4.38 hours, and 4.38 × 60 = 262.8 minutes.

**7. (a) About 99.79%, (b) about 99.89%.**
(a) In series: 0.999 × 0.999 × 0.9999 = 0.9979012, about 99.79%.
(b) The doubled application tier has availability 1 − (0.001)² = 0.999999. The new total is 0.999 × 0.999999 × 0.9999 ≈ 0.998899, about 99.89%. The remaining weak links are the single web server and the database.

**8. Answer (1): A and D only.**
Each + matches exactly one level, so the filter needs exactly four levels: campus / something / something / light.
A and D fit. B has only three levels. C has five, and + cannot absorb the extra level (only # can). E fails because topics are case-sensitive, so Campus is not campus.

**9. Answer (1): A-III, B-IV, C-I, D-II.**
AMPS is analog FDMA. GSM uses TDMA slots on FDMA carriers of 200 kHz. UMTS uses WCDMA on 5 MHz carriers. LTE uses OFDMA in the downlink and SC-FDMA in the uplink.

**10. Answer (1).**
A radio's own signal swamps what it receives, so it cannot "listen while talking" the way Ethernet does. Hidden stations cannot hear each other at all. So collisions are avoided (backoff, ACKs, optional RTS/CTS) rather than detected. R is the reason for A.

**11. Answer (4).**
In PaaS the provider manages the OS and runtime, and the consumer deploys only the application and data, so Statement I is false. Statement II is the NIST definition of a hybrid cloud (for example cloud bursting from private to public).

**12. Answer (1): A, C and D only.**
ESXi, Xen and Hyper-V run on bare metal. VirtualBox and VMware Workstation are hosted (Type 2) and run as applications on a desktop OS.

**13. Answer (3): B, D, A, C.**
PUBLISH (sender to receiver), then PUBREC (receiver: "received"), then PUBREL (sender: "release"), then PUBCOMP (receiver: "complete"). This four-way handshake gives exactly-once delivery.

**14.**
(a) 15 × 2³ = 120 kHz.
(b) 1 ÷ 2³ ms = 0.125 ms.
(c) 10 ÷ 0.125 = 80 slots per frame.
(d) 12 × 120 kHz = 1440 kHz = 1.44 MHz.

**15. 374 carriers and 2992 slots.**
75 MHz ÷ 200 kHz = 375, and one carrier is lost to guard bands, which leaves 374 usable carrier pairs. Each has 8 time slots: 374 × 8 = 2992 full-rate slots.
