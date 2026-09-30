# Practice set 9.2: Network models and the physical view

15 exam-level problems. Every question has four options and one correct answer. Aim for about 90 seconds each.

**1.** A company links 15 routers in a full mesh. How many duplex links, and how many ports in total, are needed?
(1) 105 links, 210 ports (2) 210 links, 210 ports (3) 105 links, 105 ports (4) 225 links, 15 ports

**2.** Router R has two interfaces. Interface 1 goes to switch S1, which has 3 hosts and a second switch S2 on its ports. S2 has 5 hosts. Interface 2 goes to hub H with 6 hosts. How many collision domains and broadcast domains are there?
(1) 10 collision, 2 broadcast (2) 11 collision, 2 broadcast (3) 17 collision, 2 broadcast (4) 11 collision, 3 broadcast

**3.** A 2000-byte message passes down a five-layer stack. Each of the transport, network and data link layers adds a 20-byte header, and the data link layer also adds a 4-byte trailer. What fraction of the bits sent are headers and trailers (approximately)?
(1) 3.00% (2) 2.91% (3) 3.10% (4) 3.20%

**4.** Which of these MAC addresses is a broadcast, which is a multicast, and which is a unicast: P = FF:FF:FF:FF:FF:FF, Q = 01:00:5E:10:20:30, R = 6C:3B:E5:01:02:03?
(1) P broadcast, Q multicast, R unicast (2) P broadcast, Q unicast, R multicast (3) P multicast, Q multicast, R unicast (4) all three are unicast

**5.** Match List I with List II.

| List I (Layer) | List II (Delivery or job) |
|---|---|
| A. Data link | I. Source-to-destination (host-to-host) delivery |
| B. Network | II. Process-to-process delivery |
| C. Transport | III. Node-to-node delivery |
| D. Physical | IV. Transmission of individual bits over the medium |

(1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-II, C-I, D-IV (4) A-III, B-I, C-IV, D-II

**6.** Arrange the TCP/IP (five-layer) layers from top to bottom.
A. Transport B. Physical C. Application D. Data link E. Network
(1) C, A, E, D, B (2) C, E, A, D, B (3) A, C, E, D, B (4) C, A, D, E, B

**7.** Assertion (A): A layer-2 switch floods a frame whose destination MAC address is not yet in its table.
Reason (R): A switch learns MAC addresses from the destination field of incoming frames.
(1) Both (A) and (R) are true and (R) is the correct explanation of (A) (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A) (3) (A) is true but (R) is false (4) (A) is false but (R) is true

**8.** Statement I: VLANs allow one physical switch to be split into several broadcast domains.
Statement II: A bridge connects two LAN segments and forwards frames using MAC addresses.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**9.** A learning switch with hosts P, Q, R and S on ports 1–4 starts empty. The frames are P→Q, Q→P, R→P, P→S, S→R, Q→broadcast. How many frames are flooded?
(1) 2 (2) 3 (3) 4 (4) 1

**10.** Which of the following are correct?
A. Encryption is a presentation-layer function.
B. Dialog control is a session-layer function.
C. IP addresses are used for hop-to-hop delivery on a single link.
D. Port numbers identify processes.
E. The data link layer adds a trailer containing an error-detection code.
(1) A, B, D and E only (2) A, B and C only (3) B, D and E only (4) A, C and E only

**11.** How many bits does it take to transmit a minimum-size Ethernet frame, including the preamble and SFD, and how long does that take at 10 Mbps?
(1) 512 bits, 51.2 μs (2) 576 bits, 57.6 μs (3) 576 bits, 51.2 μs (4) 672 bits, 67.2 μs

**12.** Match List I with List II.

| List I (IEEE) | List II (Scope) |
|---|---|
| A. 802.2 | I. VLAN tagging |
| B. 802.1Q | II. Logical Link Control |
| C. 802.16 | III. Wireless personal area network |
| D. 802.15 | IV. Broadband wireless MAN (WiMAX) |

(1) A-II, B-I, C-IV, D-III (2) A-I, B-II, C-IV, D-III (3) A-II, B-I, C-III, D-IV (4) A-II, B-IV, C-I, D-III

**13.** In an 802.11 WLAN, stations X and Z are both in range of the access point but out of range of each other. Which problem does this describe, and what reduces it?
(1) Exposed station; CSMA/CD (2) Hidden station; RTS/CTS (3) Hidden station; token passing (4) Exposed station; RTS/CTS

**14.** A star topology has 20 devices connected to a central switch. How many cable links are there, and how many links fail if the cable of one device is cut?
(1) 190 links, 1 fails (2) 20 links, all fail (3) 20 links, 1 fails (4) 21 links, 1 fails

**15.** Statement I: In the OSI model, the network layer offers both connectionless and connection-oriented service, but the transport layer offers only connection-oriented service.
Statement II: In the TCP/IP suite, the network layer (IP) is connectionless.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true
