# Solutions 3.1: Language design and translation issues

**1. Answer (1) A-II, B-IV, C-I, D-III.** The meaning of * is fixed by the language designers. The range of float depends on the implementation (the compiler and machine). A static variable gets its absolute address when the program is loaded. Parameters are bound to arguments at each call, at run time.

**2.** Start with x = 3, y = 4.

| Method | Trace | Output |
|---|---|---|
| Value | a = 3, b = 4 are copies; b = 7, a = 21 locally; global x = 4 | **4 4** |
| Reference | b is y: y = 4 + 3 = 7; a is x: x = 3 × 7 = 21; x = 22 | **22 7** |
| Value-result | a = 3, b = 4; b = 7, a = 21; global x = 4; copy back x = 21, y = 7 | **21 7** |
| Name | plain variables as actuals, so the same as reference | **22 7** |

The value-result copy-back overwrites the x = 4 set inside the procedure.

**3.** Static: p always uses the globals. r → q → p prints 1 + 2 = 3. q then sets the global b = q’s a = 10. r prints its own b = 20. main’s p prints 1 + 10 = 11. Output: **3 20 11**.
Dynamic: p finds a in q (10) and b in r (20), so it prints 30. q sets b = a, and the nearest b is r’s, so r’s b = 10. r prints 10. main’s p uses the globals: 1 + 2 = 3. Output: **30 10 3**.

**4.** By name: t = i = 0; i = a[i] = a[0] = 1; a[i] = t, which is now a[1] = 0. Output: **1 1 0 3**.
By reference: y is fixed as a[0] at the call. t = 0; i = a[0] = 1; a[0] = 0. Output: **1 0 2 3** (a correct swap).

**5.** e is re-evaluated each time as a[i] × a[i]: 4 + 9 + 25 + 49 = **87**. (By value it would be 4 × 4 = 16.)

**6. Answer (1) A-III, B-I, C-II, D-IV.**

**7. Answer (1).** Both are true, and the re-evaluation in R is exactly what breaks swap(i, a[i]) (see problem 4).

**8.** 6 − 3 = **3** static links. With a display, the record is found in one step (read display[3]), independent of depth.

**9.** Copy in x = 0, y = 0; then x = 1, y = 2. Left to right: k = 1, then k = 2, so **2**. Right to left: k = 2, then k = 1, so **1**. By reference: both are k; k = 1 then k = 2, so **2**.

**10.**
| Variable | Scope | Lifetime |
|---|---|---|
| (a) global | From its declaration to the end of the file (other files with extern) | Whole program |
| (b) static local | Its function only | Whole program |
| (c) automatic local of f | Only f (not visible in g) | Alive during g’s execution, until f returns |
| (d) malloc block | No name; reached only through pointers | Until free, or program end (a leak if all pointers are lost) |

**11. Answer (4).** A pure interpreter produces no object file. The hybrid statement is true (Java bytecode and the JVM).

**12.** The count is Catalan(n − 1) for n operands. (a) n = 3: **2**. (b) n = 5: **14**.

**13.**
- Value: x = 2, c = 1 + 2 = 3, returns 2. Output **2 3**.
- Reference: x is c, so c = 2, then c = 2 + 2 = 4; returns 4. Output **4 4**.
- Value-result: x = 2, c = 3, returns 2, then the copy-back sets c = 2. Output **2 2**.

**14. Answer (1).** B is wrong: dynamic scope follows the dynamic chain. E is wrong: standard C has no nested functions (gcc allows them only as an extension).

**15.** D, B, E, A, C: lexical analysis, syntax analysis, code generation, linking, loading.
