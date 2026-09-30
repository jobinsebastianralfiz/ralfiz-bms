# Solutions: Network security (cs63)

**1. Answer (1): d = 77, C = 108.**
n = 13 × 17 = 221 and φ(n) = 12 × 16 = 192. Extended Euclid for 5 mod 192:
192 = 38 × 5 + 2, 5 = 2 × 2 + 1, so 1 = 5 − 2 × 2 = 5 − 2 × (192 − 38 × 5) = 77 × 5 − 2 × 192.
So d = 77. Check: 5 × 77 = 385 = 2 × 192 + 1.
C = 10^5 mod 221 = 100000 mod 221 = 108 (221 × 452 = 99892, and 100000 − 99892 = 108). Decryption: 108^77 mod 221 = 10.
Trap: option (3) fails the check, since 5 × 173 = 865 ≡ 97 (mod 192), not 1; option (2) forgets to encrypt at all.

**2. Answer (2): 5, 2, key 16.**
A = 3^4 mod 19 = 81 mod 19 = 5. B = 3^7 mod 19 = 2187 mod 19 = 2 (19 × 115 = 2185).
Alice computes B^a = 2^4 = 16. Bob computes A^b = 5^7 mod 19 = 16. The key is 16 = 3^28 mod 19.
Option (3) forgets to reduce mod p. Option (1) reports Bob's public value as the key.

**3. Answer (1): VT TF VT.**
The square is:
    S E C U R
    I T Y A B
    D F G H K
    L M N O P
    Q V W X Z
The pairs are ME ET ME (no double letters inside a pair, even length).
ME: M and E are in the same column (column 2), so take the letter below each: M→V and E→T, giving VT.
ET: same column, so E→T and T→F, giving TF.
ME again gives VT. The ciphertext is VT TF VT. Option (2) reverses the letters inside each pair.

**4. Plaintext: DEFENDTHEEAST.**
There are 13 letters with period 2(3 − 1) = 4. Rail 1 holds positions 1, 5, 9 and 13, which is 4 letters. Rail 2 holds positions 2, 4, 6, 8, 10 and 12, which is 6 letters. Rail 3 holds positions 3, 7 and 11, which is 3 letters.
Split the ciphertext 4 / 6 / 3: DNET | EEDHES | FTA. Then read the zig-zag:
    D . . . N . . . E . . . T
    . E . E . D . H . E . S .
    . . F . . . T . . . A . .
Reading along the zig-zag gives DEFENDTHEEAST.

**5. Plaintext: SECURE.**
The key LABLAB gives shifts 11, 0, 1, 11, 0, 1. Subtract them:
D(3) − 11 = −8 → 18 S; E(4) − 0 = 4 E; D(3) − 1 = 2 C; F(5) − 11 = −6 → 20 U; R(17) − 0 = 17 R; F(5) − 1 = 4 E.

**6. Ciphertext: EEOTTNMMNEAO.**
    key:  3 1 4 2
          M E E T
          M E A T
          N O O N
Read column 1 (the second column) EEO, then column 2 (the fourth) TTN, column 3 (the first) MMN and column 4 (the third) EAO. The result is EEO TTN MMN EAO.

**7. (a) 190, (b) 110, (c) 50.**
(a) 20 × 19 ÷ 2 = 190. (b) 25 × 24 ÷ 2 = 300, so 300 − 190 = 110 more keys (each new user pairs with every other user). (c) 25 key pairs make 2 × 25 = 50 keys.

**8. (a) About 2^128, (b) about 2^256.**
The birthday bound is 2^(n/2) = 2^128. A preimage needs about 2^n = 2^256 tries (2^255 on average).

**9. Answer (1): A-II, B-IV, C-I, D-III.**
Traffic analysis only observes (passive). Replay resends captured messages. DDoS attacks availability. Masquerade is impersonation.

**10. Answer (1).**
Identical plaintext blocks, such as large areas of one colour, give identical ciphertext blocks. The structure of the picture therefore survives encryption. R is the direct cause of A. CBC or CTR with a fresh IV or nonce hides this.

**11. Answer (1): both true.**
TLS 1.3 (RFC 8446) keeps only forward-secret key exchange (ECDHE or DHE, or PSK with (EC)DHE). Tunnel mode wraps the whole original packet inside a new outer IP header.

**12. Answer (1): B, C and E only.**
Non-repudiation needs a private key that only the signer holds: RSA signatures, DSA and ECDSA. HMAC uses a shared secret, so either party could have made the tag. AES-CBC gives confidentiality only.

**13. Answer (1): B, D, A, E, C.**
PGP signs first (hash, then sign with the private key), then compresses, then encrypts with a fresh session key, and finally encrypts that session key with the receiver's public key. Signing before compressing means the signature does not depend on the compression algorithm.

**14. Signature S = 14.**
S = 5^7 mod 33. 5^2 = 25, 5^4 = 625 mod 33 = 31, and 5^7 = 31 × 25 × 5 = 3875 mod 33 = 14 (33 × 117 = 3861).
To verify, the receiver computes S^e = 14^3 mod 33 = 2744 mod 33 = 5 (33 × 83 = 2739). This equals M, so the signature is valid. Signing used the private exponent 7, and verifying used the public exponent 3.

**15.**
| Variant | Rounds | Round keys | Key-expansion words |
|---|---|---|---|
| AES-128 | 10 | 11 | 44 |
| AES-192 | 12 | 13 | 52 |
| AES-256 | 14 | 15 | 60 |

Round keys = rounds + 1, because of the initial AddRoundKey. Each round key is 4 words of 32 bits, so the word count is 4 × (rounds + 1).
