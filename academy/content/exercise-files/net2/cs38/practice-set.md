# Practice set: OS case studies and distributed systems (Lesson 5.8)

Time: 24 minutes for all 15 (about 90 seconds each). No notes and no calculator, as in the real exam.

---

**1.** Three processes use Lamport clocks, all starting at 0; every event adds 1, and a receive sets the clock to max(local, timestamp) + 1.

- P1: p1 (internal), p2 (send m1 to P3), p3 (internal), p4 (receive m2)
- P2: q1 (internal), q2 (internal), q3 (send m2 to P1), q4 (receive m3)
- P3: r1 (receive m1), r2 (send m3 to P2), r3 (internal)

Find the Lamport timestamp of every event.

**2.** For the system in problem 1, find the vector timestamps of p4, q4 and r3.

**3.** For the system in problem 1, which of these pairs are concurrent? (a) p3 and q3 (b) p2 and q4 (c) r3 and q4 (d) p1 and q1

**4.** Given below are two statements.
Statement I: If a → b, then the Lamport timestamps satisfy C(a) < C(b).
Statement II: If the vector timestamps satisfy V(a) < V(b), then a → b.
Options: (1) Both true (2) Both false (3) I true, II false (4) I false, II true

**5.** Match List I with List II.

| List I (Algorithm) | List II (Messages per entry, N processes) |
|---|---|
| A. Ricart–Agrawala | I. 3 |
| B. Centralised | II. 3(N − 1) |
| C. Lamport | III. 1 to ∞ |
| D. Token ring | IV. 2(N − 1) |

Options: (1) A-IV, B-I, C-II, D-III (2) A-II, B-I, C-IV, D-III (3) A-IV, B-III, C-II, D-I (4) A-I, B-IV, C-II, D-III

**6.** An NTP client records T1 = 200, T2 = 260, T3 = 263, T4 = 225 (milliseconds; T1 and T4 on the client clock, T2 and T3 on the server clock). Find the offset and the round-trip delay.

**7.** Using Cristian’s algorithm, a client sends its request at 08:30:10.100 and gets the reply at 08:30:10.160 (client clock). The server reports 08:30:12.000 and says it spent 20 ms handling the request. What time should the client set?

**8.** In a Berkeley round, the master reads 3:00 and the slaves read 3:25, 2:50 and 3:05. Ignoring delays, what adjustment does each machine receive?

**9.** Clocks drift at most 2 × 10⁻⁶ seconds per second. How often must they resynchronise to stay within 10 ms of each other?

**10.** Processes with IDs 1 to 7 use the bully algorithm. Process 7 (the coordinator) crashes and process 3 notices. (a) To which processes does 3 send ELECTION? (b) Who becomes coordinator? (c) If 6 is also down, who wins?

**11.** What is the output of this C program? Count characters printed by all processes.

    #include <stdio.h>
    #include <unistd.h>

    int main(void) {
        if (fork() == 0)
            fork();
        printf("x");
        return 0;
    }

**12.** Arrange from the bottom (hardware) to the top: A. Cocoa Touch B. Core OS C. Media D. Core Services

**13.** Which of the following are true?
A. Windows threads have 32 priority levels, with 16–31 the real-time class.
B. Linux nice values run from −20 (highest priority) to +19 (lowest).
C. Android runs each app under its own Linux user ID.
D. A symbolic link shares the inode of its target.
E. NTFS keeps a record for every file in the Master File Table.
Options: (1) A, B and C only (2) A, B, C and E only (3) B, C, D and E only (4) A, B, C, D and E

**14.** A file has N = 9 replicas. (a) With W = 5, what is the smallest valid R? (b) Is W = 4, R = 6 a valid quorum configuration? Why?

**15.** Assertion (A): Ricart–Agrawala needs fewer messages per critical-section entry than Lamport’s algorithm.
Reason (R): In Ricart–Agrawala, the release message is replaced by sending the deferred replies on exit.
Options: (1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true
