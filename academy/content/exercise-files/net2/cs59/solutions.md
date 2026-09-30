# Solutions: Practice set 9.2

**1. Answer (1) 105 links, 210 ports.** Links = 15 × 14 / 2 = 105. Each router needs 14 ports, so 15 × 14 = 210 ports. Option (2) doubles the links.

**2. Answer (2) 11 collision, 2 broadcast.** On the switch side, every switch port starts a new collision domain. That gives the R–S1 link (1), S1's 3 hosts (3), the S1–S2 link (1) and S2's 5 hosts (5): 10 in all. The hub side is 1. Total 11. There are 2 router interfaces, so 2 broadcast domains. Option (3) counts the 6 hub hosts separately. Option (4) treats the second switch as a new broadcast domain, but switches do not split broadcasts.

**3. Answer (3) 3.10%.** Overhead = 3 × 20 + 4 = 64 bytes. Total sent = 2000 + 64 = 2064 bytes. 64 / 2064 = 3.10%. Option (4) divides by 2000 instead of by the total. Options (1) and (2) forget the trailer.

**4. Answer (1).** FF:FF:FF:FF:FF:FF is the broadcast address. 0x01 = 0000 0001 has its LSB set, so Q is multicast (01:00:5E is the IPv4 multicast block). 0x6C = 0110 1100 has LSB 0, so R is unicast.

**5. Answer (1) A-III, B-I, C-II, D-IV.** Data link: node-to-node. Network: host-to-host. Transport: process-to-process. Physical: bits.

**6. Answer (1) C, A, E, D, B.** Top to bottom: Application, Transport, Network, Data link, Physical.

**7. Answer (3).** A is true: an unknown destination is flooded out of every port except the incoming one. R is false: the switch learns from the *source* address of each frame. The destination may not have sent anything yet.

**8. Answer (1).** Both statements are true. A VLAN is a separate broadcast domain on shared switch hardware. A bridge is a layer-2 device that filters on MAC addresses.

**9. Answer (2) 3.** P→Q: Q unknown, so flooded (learn P). Q→P: forwarded (learn Q). R→P: forwarded (learn R). P→S: S unknown, so flooded. S→R: forwarded (learn S). Q→broadcast: flooded. That is 3 floods. Option (1) forgets that P→S is still unknown at that point.

**10. Answer (1) A, B, D and E only.** C is false: hop-to-hop delivery uses MAC addresses. IP addresses stay the same end to end.

**11. Answer (2) 576 bits, 57.6 μs.** 64 + 8 = 72 bytes = 576 bits. 576 / 10⁷ s = 57.6 μs. Option (1) excludes the preamble. The 51.2 μs slot time corresponds to 512 bits.

**12. Answer (1) A-II, B-I, C-IV, D-III.** 802.2 is LLC. 802.1Q is VLAN tagging. 802.16 is WiMAX (broadband wireless MAN). 802.15 is WPAN.

**13. Answer (2).** X and Z cannot hear each other, so they are *hidden* from each other. The AP's CTS reaches both, so RTS/CTS reduces the problem. CSMA/CD is not usable in wireless.

**14. Answer (3) 20 links, 1 fails.** A star needs one link per device: 20. A cut cable isolates only that one device. Option (1) is the mesh count 20 × 19 / 2 = 190.

**15. Answer (1).** Both statements are true. This is the standard OSI versus TCP/IP contrast in Tanenbaum. TCP/IP supplies both services at the transport layer (TCP and UDP) and only connectionless IP at the network layer.
