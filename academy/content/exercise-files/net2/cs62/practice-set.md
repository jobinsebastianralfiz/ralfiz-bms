# Practice set 9.5: Transport and application layers

15 exam-level problems. Attempt 1–8 in 12 minutes and 9–15 in the next 12 minutes. Congestion convention for every problem: round 1 uses cwnd = 1 MSS; slow start doubles cwnd each round but never jumps above ssthresh; at or above ssthresh cwnd grows by 1 MSS per round; on a loss the new ssthresh is floor(cwnd / 2).

**1.** A TCP Tahoe sender has initial ssthresh = 32 MSS. A timeout is detected in round 9. What is cwnd in round 14 and in round 15?
(1) 16 and 32 (2) 16 and 17 (3) 17 and 18 (4) 8 and 16

**2.** A TCP Reno sender has initial ssthresh = 12 MSS. Three duplicate ACKs arrive in round 7, and a timeout occurs in round 12. Give cwnd and ssthresh for rounds 1 to 15.

**3.** In problem 2, in which rounds is the sender in slow start?

**4.** A client (ISN 900) connects to a server (ISN 4500). After the handshake the client sends two segments carrying 500 and 300 bytes. The server then sends one segment carrying 200 bytes, which also acknowledges everything received. Finally the client sends a pure ACK. Give the sequence and acknowledgement numbers of the two client data segments, the server segment and the final ACK.

**5.** How long does the TCP sequence space take to wrap around at (a) 2.5 Gbps and (b) 40 Gbps? Which of these needs PAWS if MSL = 120 s?

**6.** A 10 Gbps path has RTT 30 ms. What window-scale shift count is needed to keep it full with one connection?
(1) 9 (2) 10 (3) 11 (4) 14

**7.** Without window scaling, what is the maximum throughput of one TCP connection over a path with RTT 64 ms?
(1) 1.02 Mbps (2) 8.19 Mbps (3) 16.38 Mbps (4) 65.5 Mbps

**8.** EstimatedRTT = 80 ms and DevRTT = 8 ms. Samples of 100, 70 and 90 ms arrive in that order. With α = 1/8 and β = 1/4, give EstimatedRTT, DevRTT and the timeout after each sample.

**9.** A page has a base file and 12 embedded objects on one server. Ignoring transmission times and DNS, find the RTTs for: (a) non-persistent, serial; (b) non-persistent with 3 parallel connections; (c) persistent without pipelining; (d) persistent with pipelining.

**10.** Match List I with List II.

| List I (protocol) | List II (port and transport) |
|---|---|
| A. SSH | I. UDP 69 |
| B. TFTP | II. TCP 179 |
| C. DHCP server | III. TCP 22 |
| D. BGP | IV. UDP 67 |

(1) A-III, B-I, C-IV, D-II (2) A-III, B-IV, C-I, D-II (3) A-II, B-I, C-IV, D-III (4) A-III, B-I, C-II, D-IV

**11.** Assertion (A): FTP is said to send its control information out of band.
Reason (R): FTP uses a separate TCP connection for commands (port 21) and opens a new data connection for each file transferred.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**12.** Which of the following statements about DNS are correct?
A. In an iterative query, a server that does not know the answer returns a referral to another server.
B. An MX record gives the IPv6 address of a host.
C. Zone transfers between DNS servers use TCP.
D. Resolvers cache answers for the TTL given in the record.
E. Root servers store the address of every host on the Internet.
(1) A, C and D only (2) A, B, C and D only (3) A and D only (4) A, C, D and E only

**13.** Given below are two statements.
Statement I: IMAP keeps messages and folders on the server, so the same mailbox looks the same from several devices.
Statement II: POP3 uses TCP port 143.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**14.** A UDP header, in hexadecimal, is 0035 C350 0044 xxxx (the last field is the checksum). Give the source port, the destination port, the total UDP length and the data length. Which side sent this datagram, the client or the server of which protocol?

**15.** With ssthresh = 16 MSS and no losses, in which round is the 50th segment sent?
(1) 6 (2) 7 (3) 8 (4) 50
