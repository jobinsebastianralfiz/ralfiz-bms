# Practice set 9.4: Network layer

15 exam-level problems. Attempt 1–8 in 12 minutes and 9–15 in the next 12 minutes. Unless a problem says otherwise, usable hosts = 2^h − 2, all subnets (including the all-0s and all-1s subnets) are allowed, and IPv4 headers are 20 bytes.

**1.** For the host 130.50.77.200/20, find the subnet mask, the network address, the broadcast address and the number of usable hosts.

**2.** A company holds 150.40.0.0/16 and needs at least 25 subnets of equal size, with as many hosts per subnet as possible. What prefix should it use, and how many usable hosts does each subnet get?
(1) /20, 4094 (2) /21, 2046 (3) /21, 2048 (4) /22, 1022

**3.** Allocate 172.30.8.0/22 with VLSM, largest first, to L1 (400 hosts), L2 (200 hosts), L3 (60 hosts) and one point-to-point link P. Give each block and the first free address afterwards.

**4.** An ISP owns the sixteen contiguous blocks 60.20.32.0/24 to 60.20.47.0/24. What single route can it advertise? Would the same be possible for 60.20.40.0/24 to 60.20.55.0/24? Explain.

**5.** A router’s table is: 145.14.0.0/16 → A, 145.14.128.0/17 → B, 145.14.192.0/18 → C, default → D. Give the interface for each destination: (a) 145.14.200.9 (b) 145.14.100.1 (c) 145.14.130.7 (d) 145.15.0.1.

**6.** Which of the following can be assigned to a host in the same subnet as 192.168.4.70/27?
A. 192.168.4.64  B. 192.168.4.65  C. 192.168.4.95  D. 192.168.4.94  E. 192.168.4.96
(1) A, B, C and D only (2) B, C and D only (3) B and D only (4) B, D and E only

**7.** A datagram of total length 3820 bytes crosses a link with MTU 1006. Give, for every fragment, the data bytes carried, the total length, the offset field and MF.

**8.** A fragment arrives with offset field 370, HLEN 5, total length 1500 and MF = 0. Which data bytes does it carry, and what was the total length of the original datagram (with a 20-byte header)?

**9.** The first 32-bit word of an IPv4 header is 0x46000200. How long is the header, how many bytes of options are present, and how many data bytes does the datagram carry?

**10.** Match List I with List II.

| List I (address) | List II (meaning) |
|---|---|
| A. 127.0.0.1 | I. "This host", used as the source by a DHCP client with no address yet |
| B. 255.255.255.255 | II. Self-assigned link-local address |
| C. 169.254.3.4 | III. Loopback |
| D. 0.0.0.0 | IV. Limited broadcast, never forwarded by routers |

(1) A-III, B-IV, C-II, D-I (2) A-III, B-I, C-II, D-IV (3) A-IV, B-III, C-II, D-I (4) A-III, B-IV, C-I, D-II

**11.** Router X has links X–Y (cost 4), X–Z (cost 1) and X–W (cost 6). The vectors it receives, for destinations (X, Y, Z, W, V), are: from Y (3, 0, 2, 1, 4), from Z (1, 2, 0, 3, 6), from W (4, 1, 3, 0, 3). Give X’s new cost and next hop for Y, W and V.

**12.** Routers A – B – C form a line. Link A–B has cost 2 and link B–C has cost 1, so A reaches C at cost 3 through B. Link B–C fails. The routers use distance vector with infinity = 16 and no split horizon. B first believes A’s stale route, and then A and B update alternately. List the successive costs to C. After how many updates does B first record 16?

**13.** Run Dijkstra from S on the links S–T 7, S–U 2, U–T 3, T–W 1, U–W 8, U–X 5, X–W 2, W–Y 4, X–Y 7. Give the order in which nodes become permanent, each final distance, and S’s next hop to Y.

**14.** Given below are two statements.
Statement I: In IPv6, an intermediate router never fragments a packet.
Statement II: The IPv6 payload length field includes the 40-byte base header.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**15.** Which of the following statements about BGP are correct?
A. It is a path-vector protocol.
B. It runs over UDP port 179.
C. A router rejects a route whose AS path already contains its own AS number.
D. It is used between autonomous systems, and also inside one (iBGP).
E. It always chooses the path with the fewest routers.
(1) A, C and D only (2) A, B, C and D only (3) A and C only (4) A, C, D and E only
