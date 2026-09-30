# Solutions: practice set 9.5

Every congestion trace, sequence number, wraparound time, window, RTT and HTTP count below was recomputed by the simulator in netv/cs62.py, using the convention stated at the top of the practice set.

**1. Answer (2) 16 and 17.** Rounds 1–9: 1, 2, 4, 8, 16, 32, 33, 34, 35. Timeout at 35: ssthresh = 17, cwnd = 1. Rounds 10–15: 1, 2, 4, 8, 16, then 17 (doubling 16 would overshoot 17). Option (1) forgets the new threshold.

**2.**

| Round | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cwnd | 1 | 2 | 4 | 8 | 12 | 13 | 14 | 7 | 8 | 9 | 10 | 11 | 1 | 2 | 4 |
| ssthresh | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 7 | 7 | 7 | 7 | 7 | 5 | 5 | 5 |

Round 5: doubling 8 would give 16 > 12, so cwnd = 12. Round 7: triple duplicate ACK at 14 → ssthresh 7, Reno sets cwnd = 7 (round 8). Round 12: timeout at 11 → ssthresh 5, cwnd = 1 even for Reno.

**3.** Rounds 1–4 (cwnd below 12) and rounds 13–15 (cwnd below 5, after the timeout). After the triple duplicate ACK, Reno goes straight to congestion avoidance, so rounds 8–12 are linear.

**4.** SYN uses 900, so data starts at 901.
- Client segment 1: seq 901 (bytes 901–1400), ack 4501.
- Client segment 2: seq 1401 (bytes 1401–1700), ack 4501.
- Server segment: seq 4501 (bytes 4501–4700), ack 1701.
- Client ACK: seq 1701, ack 4701.

**5.** (a) 2.5 Gbps = 312.5 × 10^6 bytes/s: 2^32 / (312.5 × 10^6) ≈ 13.74 s. (b) 40 Gbps = 5 × 10^9 bytes/s: ≈ 0.86 s. Both are far below 120 s, so both need PAWS (the timestamp option). Any rate above about 286 Mbps does.

**6. Answer (2) 10.** BDP = 10^10 × 0.03 / 8 = 37,500,000 bytes. 37,500,000 / 65,535 ≈ 572.2. 2^9 = 512 is too small; 2^10 = 1024 is enough. So S = 10.

**7. Answer (2) 8.19 Mbps.** 65,535 × 8 / 0.064 = 8,191,875 bps. Option (1) forgets the ×8; option (3) uses half the RTT.

**8.** (Update DevRTT with the old estimate first.)

| Sample | DevRTT | EstimatedRTT | Timeout |
|---|---|---|---|
| 100 | 0.75 × 8 + 0.25 × 20 = 11 | 0.875 × 80 + 0.125 × 100 = 82.5 | 82.5 + 44 = 126.5 |
| 70 | 0.75 × 11 + 0.25 × 12.5 = 11.375 | 80.9375 | 126.4375 |
| 90 | 0.75 × 11.375 + 0.25 × 9.0625 = 10.796875 | 82.0703125 | 125.2578125 |

**9.** (a) 2 + 12 × 2 = **26 RTT**. (b) 2 + 2 × ceil(12 / 3) = **10 RTT**. (c) 1 + 1 + 12 = **14 RTT**. (d) 1 + 1 + 1 = **3 RTT**.

**10. Answer (1) A-III, B-I, C-IV, D-II.** SSH TCP 22, TFTP UDP 69, DHCP server UDP 67, BGP TCP 179.

**11. Answer (1).** The separate control connection is exactly what "out of band" means here, so R explains A.

**12. Answer (1) A, C and D only.** B is false: MX names the mail exchanger for a domain (AAAA holds IPv6 addresses). E is false: root servers only refer queries to the TLD servers; DNS is distributed precisely so that no server holds everything.

**13. Answer (3).** I is true. II is false: POP3 uses port 110; 143 is IMAP.

**14.** 0x0035 = 53 (source port), 0xC350 = 50000 (destination port), 0x0044 = 68 bytes in total, so the data is 68 − 8 = 60 bytes. The source port is DNS’s well-known port and the destination is an ephemeral port, so this is a **DNS server’s reply** to a client.

**15. Answer (2) 7.** Rounds send 1, 2, 4, 8, 16 (cumulative 31), then 17 (48), then 18 (66). The 50th segment goes out in round 7.
