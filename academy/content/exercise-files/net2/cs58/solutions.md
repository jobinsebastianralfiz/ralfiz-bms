# Solutions: Practice set 9.1

**1. Answer (2) 48 kbps.** Nyquist: C = 2B log₂ L = 2 × 6000 × log₂ 16 = 12,000 × 4 = 48 kbps. Option (1) forgets the factor 2. Option (3) uses 16 bits per level.

**2. Answer (2) 26.6 kbps.** Convert first: 20 dB means SNR = 10² = 100. C = 4000 × log₂ 101 = 4000 × 6.658 ≈ 26.6 kbps. Option (1) uses 4000 × 20 (dB put straight into the formula). Option (3) doubles the result.

**3. Answer (3) 64.** 120,000 = 2 × 10,000 × log₂ L, so log₂ L = 6 and L = 2⁶ = 64. Option (1) gives the bits per level, not the number of levels.

**4. Answer (2) 25 mW.** Cable loss = 0.5 × 12 = 6 dB. Net = −6 + 3 = −3 dB. P = 50 × 10^(−0.3) ≈ 50 × 0.501 ≈ 25 mW, so the power is halved. Option (1) forgets the amplifier: 50 × 10^(−0.6) ≈ 12.6 mW. Option (3) subtracts the amplifier gain instead of adding it: 50 × 10^(−0.9) ≈ 6.3 mW.

**5. Answer (3) 20 dB.** For voltage, gain = 20 log₁₀(V₂/V₁) = 20 log₁₀ 10 = 20 dB. Option (1) wrongly uses 10 log, the power formula. (The power ratio is 100, which is also 20 dB.)

**6. Answer (1) 24 kbps.** 32-QAM carries log₂ 32 = 5 bits per symbol: 4800 × 5 = 24,000 bps. Option (2) multiplies by 32.

**7. Answer (2) 14.** The waveform is LH LH LH LH HL HL HL HL, or as one string LHLHLHLHHLHLHLHL. Between two equal bits (1 1 or 0 0) there is a boundary transition. Between the 1 and the 0 in the middle there is none (H followed by H). So there are 8 mid-bit transitions + 6 boundary transitions = 14. Option (3) assumes a boundary transition everywhere.

**8. Answer (1) + 0 − + 0 0 −.** In AMI, 0 is zero volts and the 1s alternate: first 1 → +, next 1 → −, next 1 → +, last 1 → −. Option (3) is pseudoternary, the mirror scheme.

**9. Answer (1) A-II, B-I, C-IV, D-III.** 10 Mbps Ethernet uses Manchester. Token Ring (802.5) uses differential Manchester. 100BASE-TX uses 4B/5B with MLT-3. 1000BASE-X uses 8B/10B.

**10. Answer (3) 660 kHz.** 4 × 150 + 3 guard bands × 20 = 600 + 60 = 660 kHz. Option (2) counts 4 guard bands.

**11. Answer (2).** Both statements are true. Statistical TDM is more efficient because idle sources get no slot, so no capacity is wasted. The address in each slot is a *cost* of that design, not the reason it is efficient. So R does not explain A.

**12. Answer (3).** Statement I is true: a circuit is a reserved physical path. Statement II is false: virtual-circuit packets carry only a short virtual-circuit identifier. Datagrams are the ones that carry the full destination address.

**13. Answer (2) 2.02 s.** Transmission = 8 × 10⁶ / 4 × 10⁶ = 2 s. Propagation = 4 × 10⁶ m / 2 × 10⁸ m/s = 0.02 s. Total = 2.02 s. Option (1) ignores propagation.

**14. Answer (1) B, C and E only.** A is false: hertz measures a frequency range and bps measures a data rate. B is true: T = 1/50 s = 20 ms. C is true: 2 × 4000 × 8 = 64 kbps. D is false: 16-QAM carries 4 bits per symbol. E is true: 32 × 8 × 8000 = 2.048 Mbps.

**15. Answer (1) C, B, D, A.** Category 3 twisted pair (about 16 MHz) < coaxial cable (hundreds of MHz) < multimode fibre < single-mode fibre (the lowest dispersion, the highest bandwidth over distance).
