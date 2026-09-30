# Solutions: Practice set 9.3

**1. Answer (1) 01110.** The generator 110101 has 6 bits, so r = 5. Append 5 zeros: 101000110100000. Dividing modulo 2 by 110101 leaves 01110, and the codeword is 101000110101110. The remainder always has exactly r = 5 bits, so the leading 0 must be kept. Option (2) drops it.

**2. Answer (4) 101100110100.** x⁴ + x + 1 = 10011 (r = 4). Dividing 101100110000 by 10011 leaves 0100. The codeword is the data followed by 0100. Option (2) appends only 3 bits.

**3. Answer (2) 0x92EF.** 0x1A2B + 0xC3D4 = 0xDDFF. Adding 0x8F10 gives 0x16D0F. Wrap the carry: 0x6D0F + 1 = 0x6D10. The complement is 0xFFFF − 0x6D10 = 0x92EF. Option (1) is the sum before complementing. Option (4) forgets the end-around carry.

**4. Answer (3) 7.** Correcting t errors needs d(min) ≥ 2t + 1 = 7. Option (1), 4, would only be enough to *detect* 3 errors.

**5. Answer (4) 6.** Data 1001 gives d3 = 1, d5 = 0, d6 = 0, d7 = 1. So p1 = 1 ⊕ 0 ⊕ 1 = 0, p2 = 1 ⊕ 0 ⊕ 1 = 0 and p4 = 0 ⊕ 0 ⊕ 1 = 1, and the codeword is 0011001. Flipping bit 6 gives 0011011. Its 1s are at positions 3, 4, 6 and 7, and 3 ⊕ 4 ⊕ 6 ⊕ 7 = 6. The syndrome always names the flipped position.

**6. Answer (1) 9.09%, 181.8 kbps.** T(t) = 4000 / 2 × 10⁶ = 2 ms, so a = 10 / 2 = 5. η = 1 / (1 + 10) = 1/11 = 9.09%, and the throughput = 2 Mbps / 11 ≈ 181.8 kbps. Option (2) uses 1/(1 + a).

**7. Answer (3) 11 frames, 4 bits.** W = 1 + 2a = 11. GBN needs 2ᵏ − 1 ≥ 11, so k = 4 (15 ≥ 11). Selective Repeat would need 2ᵏ⁻¹ ≥ 11, so k = 5. Option (2) mixes GBN's window with SR's bit count.

**8. Answer (3) 16.** Transmissions 1–3 carry frames 1–3. Transmissions 4–6 carry 4, 5, 6, and #5 (frame 5) is lost, so frame 6 is discarded. Transmissions 7–9 carry 5, 6, 7. Transmissions 10–12 carry 8, 9, 10, and #10 (frame 8) is lost. Transmissions 13–15 carry 8, 9, 10, and #15 (frame 10) is lost. Transmission 16 carries frame 10. Total 16.

**9. Answer (2) 12.** Selective Repeat resends only the lost frames. Every 5th transmission is lost, and 10 frames must get through. After 12 transmissions, 12 − 2 = 10 have succeeded (#5 and #10 were lost). The retransmissions are at #11 and #12, and neither of them is a 5th, so 12 is enough.

**10. Answer (3) 0.135.** S = G e^(−2G) = e^(−2) ≈ 0.135. Option (2), 0.184, is the maximum, reached at G = 0.5. Option (1), 0.368, is slotted ALOHA at G = 1.

**11. Answer (2) 250 bits.** T(p) = 2500 / 2 × 10⁸ = 12.5 μs. L(min) = 2 × 12.5 × 10⁻⁶ × 10⁷ = 250 bits. Option (1) uses T(p) instead of 2T(p). Option (4) quotes the Ethernet standard's 512 bits, which is not what this question asks.

**12. Answer (1) A-IV, B-I, C-II, D-III.** Detecting s errors needs s + 1, so 6 for s = 5. Correcting t errors needs 2t + 1: 9 for t = 4, 5 for t = 2 and 3 for t = 1.

**13. Answer (1).** Both statements are true, and R is the reason for A. Resending correctly received frames is exactly the waste, and Selective Repeat avoids it.

**14. Answer (4) 0111110101111100.** 0 11111 → insert 0 → 1 0 (the sixth 1 and the next 0) → 11111 → insert 0 → 0. Result: 011111 0 10 11111 0 0 = 0111110101111100. Unstuffing gives back the original.

**15. Answer (1) A, C and D only.** B is false: slotted ALOHA's vulnerable time is one frame time. E is false: the SR receiver window equals the sender window (up to 2ᵏ⁻¹). It is the GBN receiver whose window is 1.
