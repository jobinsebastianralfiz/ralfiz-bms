# Practice set: Security, protection and virtual machines (Lesson 5.7)

Time: 24 minutes for all 15 (about 90 seconds each). No notes and no calculator, as in the real exam.

---

**1.** Match List I with List II.

| List I (Malware) | List II (Behaviour) |
|---|---|
| A. Virus | I. Hides the intruder by altering the kernel or system tools |
| B. Worm | II. Attaches to a host program and runs when the host runs |
| C. Rootkit | III. Fires only when a trigger condition becomes true |
| D. Logic bomb | IV. Standalone program that spreads itself over a network |

Options: (1) A-II, B-IV, C-I, D-III  (2) A-IV, B-II, C-I, D-III  (3) A-II, B-IV, C-III, D-I  (4) A-II, B-I, C-IV, D-III

**2.** The access matrix below is given.

| Domain | F1 | F2 | F3 |
|---|---|---|---|
| D1 | read | read, write | – |
| D2 | – | read* | execute |
| D3 | owner, write | – | read |

(a) Write the ACL of F2. (b) Write the capability list of D3. (c) Can D2 give D3 the read right on F2? (d) Can D3 grant D2 the read right on F1?

**3.** Given below are two statements.
Statement I: An access control list corresponds to one row of the access matrix.
Statement II: Capability-based systems make it easy to revoke a right from all domains at once.
Options: (1) Both true (2) Both false (3) I true, II false (4) I false, II true

**4.** The umask is 077. What modes do (a) a new file requested with 0666 and (b) a new directory requested with 0777 receive? Give octal and rwx form.

**5.** Write the ls -l permission strings for octal modes (a) 2755 (b) 1777 (c) 4711.

**6.** Passwords are 6 characters long, and each character is a lowercase letter or a digit. An attacker tests 5 × 10⁶ passwords per second. Find the worst-case time in seconds and the strength in bits.

**7.** Assertion (A): Salting stops an attacker from using one precomputed rainbow table for all users.
Reason (R): Salting makes brute-force search on a single user’s hash 2ⁿ times slower for an n-bit salt.
Options: (1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**8.** 40 employees must be able to exchange encrypted messages pairwise. How many keys are needed (a) with symmetric keys, one per pair, and (b) with public-key cryptography?

**9.** RSA with p = 3, q = 11 and e = 3. Find n, φ(n) and d. Encrypt M = 4.

**10.** Under Bell–LaPadula, subject S has clearance Confidential. Objects are O1 (Unclassified), O2 (Confidential) and O3 (Secret). For each object, say whether S may read and whether S may write.

**11.** Arrange the TCSEC classes from least to most secure: A. B3  B. C2  C. A1  D. C1  E. B1.

**12.** Which of the following are true?
A. A Type 1 hypervisor runs directly on the hardware.
B. VMware Workstation is a Type 2 hypervisor.
C. Paravirtualisation needs a modified guest kernel.
D. Hardware-assisted virtualisation needs the guest OS to be modified.
E. Binary translation rewrites sensitive guest kernel instructions at run time.
Options: (1) A, B and C only (2) A, B, C and E only (3) A, C, D and E only (4) B, C and E only

**13.** A face-recognition system accepted 45 of 15,000 impostor attempts and rejected 96 of 4,800 genuine attempts. Find FAR and FRR. If the threshold is made stricter, which way does each rate move?

**14.** What is the output of this C program?

    #include <stdio.h>
    #include <string.h>

    int main(void) {
        char buf[6];
        int n = snprintf(buf, sizeof buf, "%d-%s", 42, "root");
        printf("%s|%d|%zu\n", buf, n, strlen(buf));
        return 0;
    }

**15.** Twenty identical servers each average 6% CPU. They will be virtualised onto hosts of the same capacity with a 70% ceiling per host, and one extra host kept free for failover. How many hosts are needed in total?
