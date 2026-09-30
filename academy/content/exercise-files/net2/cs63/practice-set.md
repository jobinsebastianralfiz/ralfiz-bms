# Practice set: Network security (cs63)

15 problems. Target: 24 minutes. Use A = 0, …, Z = 25 for all classical ciphers.

**1.** In RSA, p = 13, q = 17 and e = 5. Find d, and then the ciphertext for M = 10.
(1) d = 77, C = 108  (2) d = 77, C = 10  (3) d = 173, C = 108  (4) d = 29, C = 100

**2.** Diffie–Hellman with p = 19 and g = 3. Alice's secret is a = 4 and Bob's secret is b = 7. Find the values exchanged and the shared key.
(1) 5, 2, key 2  (2) 5, 2, key 16  (3) 81, 2187, key 16  (4) 2, 5, key 5

**3.** Build the Playfair square for the keyword SECURITY (I/J together, filler X) and encrypt MEET ME.
(1) VT TF VT  (2) TV FT TV  (3) VT TF VT X  (4) LF EF LF

**4.** The ciphertext DNETEEDHESFTA was produced by a 3-rail rail fence cipher. Recover the plaintext.

**5.** The ciphertext DEDFRF was produced by a Vigenère cipher with the key LAB. Find the plaintext.

**6.** Encrypt MEETMEATNOON with a columnar transposition under the key 3142. Write the text in rows of 4, and read column 1 first, then 2, 3 and 4 (the numbers give the reading order).

**7.** A team of 20 users uses pairwise symmetric keys. (a) How many keys are needed? (b) How many extra keys are needed when 5 more users join? (c) How many keys would 25 users need with public-key cryptography?

**8.** A system uses a 256-bit hash. (a) About how many hashes does a birthday attack need? (b) About how many does a preimage search need?

**9.** Match List I with List II.

| List I (attack) | List II (description) |
|---|---|
| A. Traffic analysis | I. Active attack aimed at availability |
| B. Replay | II. Passive attack that studies patterns of communication |
| C. Distributed denial of service | III. Active attack in which one entity pretends to be another |
| D. Masquerade | IV. Active attack that resends a captured valid message |

(1) A-II, B-IV, C-I, D-III  (2) A-II, B-III, C-I, D-IV  (3) A-IV, B-II, C-I, D-III  (4) A-II, B-IV, C-III, D-I

**10.** Assertion (A): Encrypting a bitmap image with AES in ECB mode can leave the outline of the image visible. Reason (R): ECB encrypts equal plaintext blocks to equal ciphertext blocks under the same key.
(1) Both true, and R explains A  (2) Both true, but R does not explain A  (3) A true, R false  (4) A false, R true

**11.** Statement I: TLS 1.3 removed static RSA key exchange, so every full handshake uses an ephemeral (Diffie–Hellman) key exchange. Statement II: In IPSec tunnel mode, a new outer IP header is added in front of the protected original packet.
(1) Both true  (2) Both false  (3) I true, II false  (4) I false, II true

**12.** Which of the following can provide non-repudiation?
A. HMAC-SHA256  B. RSA signature  C. DSA  D. AES in CBC mode  E. ECDSA
(1) B, C and E only  (2) A, B and C only  (3) B and E only  (4) A, B, C and E only

**13.** Arrange the steps PGP follows when a message is both signed and encrypted.
A. Compress the signed message
B. Compute the hash of the message
C. Encrypt the session key with the receiver's public key
D. Sign the hash with the sender's private key
E. Encrypt the compressed message with a one-time session key
(1) B, D, A, E, C  (2) B, D, E, A, C  (3) A, B, D, E, C  (4) B, A, D, E, C

**14.** RSA keys: n = 33, e = 3 and d = 7. Sign the message value M = 5, then show how the receiver verifies it.

**15.** For AES-128, AES-192 and AES-256, give (a) the number of rounds, (b) the number of round keys and (c) the number of 32-bit words produced by key expansion.
