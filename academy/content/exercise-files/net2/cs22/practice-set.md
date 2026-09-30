# Practice set: Computer graphics output primitives (UGC NET Paper 2, Unit 3)

Time: 22 minutes. Use ROUND(v) = floor(v + 0.5) wherever rounding is needed. Region codes are written T B R L (above, below, right, left).

**1.** A raster system has resolution 800 × 600 and 16 bits per pixel. (a) What is the frame-buffer size in bytes? (b) How many colours can a pixel show?

**2.** A system shows 1280 × 1024 pixels at 60 frames per second. Ignoring retrace, what is the time available per pixel (to 3 significant figures)?

**3.** Use DDA to list the pixels from (2, 3) to (10, 8).

**4.** Use Bresenham to draw the line from (5, 8) to (15, 14). Give p₀ to p₄ and all pixels.

**5.** For the line from (0, 0) to (4, 9), how many pixels does DDA plot, and which axis is the major axis?

**6.** Use the midpoint circle algorithm for r = 7 (centre at the origin). List the first-octant points and the decision parameters.

**7.** Assertion (A): The midpoint ellipse algorithm computes one quadrant in two regions. Reason (R): An ellipse has 4-way symmetry and the slope of its curve passes through −1 within each quadrant.

**8.** Match List I with List II.

| List I | List II |
|---|---|
| A. DVST | I. Emissive flat panel |
| B. LCD | II. No refresh needed; picture held on a storage grid |
| C. Plasma panel | III. Refreshes from a display file |
| D. Random-scan CRT | IV. Non-emissive flat panel |

(1) A-II, B-IV, C-I, D-III  (2) A-II, B-I, C-IV, D-III  (3) A-III, B-IV, C-I, D-II  (4) A-IV, B-II, C-I, D-III

**9.** Window (10, 10)–(50, 40). Give the region codes of (0, 5), (30, 50), (5, 45) and (30, 60). Which of the lines (0,5)–(30,50) and (5,45)–(30,60) are trivially rejected?

**10.** Clip the line from (0, 20) to (60, 50) against the window of problem 9 with Cohen–Sutherland.

**11.** Clip the line from (−5, 3) to (15, 9) against the window (0, 0)–(10, 10) with Liang–Barsky. Give all pₖ, qₖ, u₁ and u₂.

**12.** Clip the line from (0, 5) to (30, 50) against the window of problem 9. Give the visible segment.

**13.** Clip the triangle (3, 3), (15, 3), (3, 15) against the window (0, 0)–(10, 10) with Sutherland–Hodgman. Give the vertex count after each window edge (left, right, bottom, top) and the final polygon.

**14.** Which of these are true? A. Flood fill can handle a boundary drawn in several colours. B. A 4-connected fill visits diagonal neighbours. C. The odd–even rule and the non-zero winding rule always agree for a simple (non-self-intersecting) polygon. D. Boundary fill needs a seed point inside the region.

**15.** A window (0, 0)–(100, 50) is mapped to a viewport (200, 100)–(400, 300). Map the point (30, 20), and say whether a circle keeps its shape.
