# Solutions: practice set 9.4

Every address, aggregation, fragmentation and routing answer here was recomputed in netv/cs61.py (Python ipaddress module for addressing, networkx and a Bellman–Ford/Dijkstra implementation for routing).

**1.** /20 = 8 + 8 + 4, so the mask is 255.255.240.0 and the block size in the third octet is 16. The multiple of 16 at or below 77 is 64. Network 130.50.64.0, broadcast 130.50.79.255, usable hosts 2^12 − 2 = 4094 (range 130.50.64.1 to 130.50.79.254).

**2. Answer (2) /21, 2046.** 25 subnets need 5 bits (2^5 = 32 ≥ 25; 4 bits give only 16). /16 + 5 = /21, leaving 11 host bits: 2^11 − 2 = 2046. Option (3) forgets the −2; option (1) has only 16 subnets.

**3.** L1 (400) needs /23 (510 hosts): 172.30.8.0/23 (8.0 to 9.255). L2 (200) needs /24 (254): 172.30.10.0/24. L3 (60) needs /26 (62): 172.30.11.0/26. P needs /30: 172.30.11.64/30. The first free address is 172.30.11.68.

**4.** 16 = 2^4 blocks, so the prefix shortens by 4: /20. The third octet 32 is a multiple of 16, so the route is 60.20.32.0/20 (it covers 32–47 exactly). For 40–55: 40 is not a multiple of 16, so no single /20 fits. 40–47 and 48–55 form two aligned /21s: 60.20.40.0/21 and 60.20.48.0/21, advertised as two routes.

**5.** (a) 200 lies in 192–255, so the /18 matches and wins: **C**. (b) 100 is in the /16 only (the /17 starts at 128): **A**. (c) 130 is in 128–255 (the /17) but not 192–255: **B**. (d) 145.15 matches nothing but the default: **D**.

**6. Answer (3) B and D only.** The subnet is 192.168.4.64/27 (block 32): .64 is the network address and .95 is the broadcast address, so the usable hosts are .65 to .94. .96 is in the next subnet.

**7.** Data = 3800 bytes. 1006 − 20 = 986, rounded down to a multiple of 8 gives 984.

| Fragment | Data bytes | Total length | Offset | MF |
|---|---|---|---|---|
| 1 | 0 – 983 | 1004 | 0 | 1 |
| 2 | 984 – 1967 | 1004 | 123 | 1 |
| 3 | 1968 – 2951 | 1004 | 246 | 1 |
| 4 | 2952 – 3799 | 868 | 369 | 0 |

The trap is using 986: 986 is not a multiple of 8, so the second fragment’s start could not be written in the offset field.

**8.** First byte = 370 × 8 = 2960. Data = 1500 − 20 = 1480. Last byte = 2960 + 1480 − 1 = 4439. MF = 0, so this is the last fragment: the original data was 4440 bytes and the original total length was 4460.

**9.** 0x46 gives version 4 and HLEN 6, so the header is 24 bytes, with 4 bytes of options. 0x0200 = 512 is the total length, so the data is 512 − 24 = 488 bytes.

**10. Answer (1) A-III, B-IV, C-II, D-I.**

**11.** Bellman–Ford with link costs Y 4, Z 1, W 6:
- Y: via Y 4 + 0 = 4, via Z 1 + 2 = 3, via W 6 + 1 = 7. **3 via Z.**
- W: via Y 4 + 1 = 5, via Z 1 + 3 = 4, via W 6 + 0 = 6. **4 via Z.**
- V: via Y 4 + 4 = 8, via Z 1 + 6 = 7, via W 6 + 3 = 9. **7 via Z.**
The direct links to Y and W are not the best routes. (Z is at cost 1 via Z.)

**12.** B: 3 + 2 = 5 (via A, a loop), then A: 5 + 2 = 7, B: 9, A: 11, B: 13, A: 15, B: 17, capped at 16. B first records 16 on the **7th** update; A reaches 16 on the next one. Because each round trip adds 2 × 2 = 4, the counting is faster than with cost-1 links (where it takes 14 updates), but packets still loop during the whole period.

**13.** Permanent order: S 0, U 2 (S), T 5 (via U: 2 + 3 beats 7), W 6 (via T: 5 + 1 beats 2 + 8), X 7 (via U: 2 + 5 beats 6 + 2 = 8), Y 10 (via W: 6 + 4 beats 7 + 7). The path to Y is S–U–T–W–Y, so S’s next hop to Y is **U**.

**14. Answer (3).** I is true: only the source fragments in IPv6; routers send ICMPv6 Packet Too Big. II is false: the payload length counts everything after the 40-byte base header (extension headers plus data).

**15. Answer (1) A, C and D only.** BGP runs over TCP port 179, not UDP (B false). Its route choice is driven by policy and path attributes, not by the number of routers (E false).
