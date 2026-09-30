# Practice set: Mobile technology, cloud computing and IoT (cs64)

15 problems. Target: 24 minutes.

**1.** In a hexagonal cellular layout, the shift parameters are i = 3 and j = 1. Find the cluster size N and the co-channel reuse ratio D/R.
(1) N = 10, D/R ≈ 5.48  (2) N = 13, D/R ≈ 6.24  (3) N = 13, D/R ≈ 3.61  (4) N = 12, D/R = 6

**2.** Which of the following cannot be a cluster size for a hexagonal cellular system?
(1) 3  (2) 4  (3) 7  (4) 10

**3.** An operator has 30 MHz of spectrum, and each duplex channel uses two 25 kHz simplex channels. How many duplex channels does each cell get with (a) N = 4 and (b) N = 12?

**4.** A city is covered by 70 cells using a 7-cell cluster, and the operator has 600 duplex channels in total. How many calls can the system carry at the same time (every channel busy)?

**5.** CDMA chip codes: A = (+1 +1 +1 +1), B = (+1 −1 +1 −1), C = (+1 +1 −1 −1), D = (+1 −1 −1 +1). The received sum is S = (0 −2 +2 0). What did each station send?

**6.** A cloud SLA promises 99.95% availability. What is the maximum downtime per 365-day year, in hours and in minutes?

**7.** A three-tier application has web 99.9%, application server 99.9% and database 99.99% availability, all needed and independent. (a) Find the overall availability. (b) The application tier is doubled with an independent second server, so either one is enough. Find the new overall availability.

**8.** A client subscribes to the MQTT filter campus/+/+/light. Which of these topics does it receive?
A. campus/b1/f2/light  B. campus/b1/light  C. campus/b1/f2/light/on  D. campus/b2/f1/light  E. Campus/b1/f2/light
(1) A and D only  (2) A, C and D only  (3) A, D and E only  (4) A, B and D only

**9.** Match List I with List II.

| List I (system) | List II (main multiple-access method) |
|---|---|
| A. AMPS (1G) | I. Wideband CDMA |
| B. GSM (2G) | II. OFDMA in the downlink |
| C. UMTS (3G) | III. FDMA |
| D. LTE (4G) | IV. TDMA within FDMA carriers |

(1) A-III, B-IV, C-I, D-II  (2) A-IV, B-III, C-I, D-II  (3) A-III, B-IV, C-II, D-I  (4) A-III, B-I, C-IV, D-II

**10.** Assertion (A): IEEE 802.11 uses CSMA/CA rather than CSMA/CD. Reason (R): A wireless station cannot reliably detect a collision while it is transmitting, and it may not hear a hidden terminal at all.
(1) Both true, and R explains A  (2) Both true, but R does not explain A  (3) A true, R false  (4) A false, R true

**11.** Statement I: In PaaS, the consumer manages the operating system and the language runtime. Statement II: A hybrid cloud is a composition of two or more distinct cloud infrastructures bound together so that data and applications can move between them.
(1) Both true  (2) Both false  (3) I true, II false  (4) I false, II true

**12.** Which of the following are Type 1 (bare-metal) hypervisors?
A. VMware ESXi  B. Oracle VirtualBox  C. Xen  D. Microsoft Hyper-V  E. VMware Workstation
(1) A, C and D only  (2) A and C only  (3) A, B, C and D only  (4) C, D and E only

**13.** Arrange the MQTT QoS 2 packets in the order they are sent for one message.
A. PUBREL  B. PUBLISH  C. PUBCOMP  D. PUBREC
(1) B, A, D, C  (2) B, D, C, A  (3) B, D, A, C  (4) D, B, A, C

**14.** For 5G NR numerology μ = 3, find (a) the subcarrier spacing, (b) the slot duration, (c) the number of slots in a 10 ms frame and (d) the bandwidth of one resource block (12 subcarriers).

**15.** The GSM-1800 (DCS) band has 75 MHz in each direction. With 200 kHz carriers and one carrier lost to guard bands, how many carrier pairs are usable, and how many full-rate TDMA slots do they provide?
