# Solutions 3.2: Elementary data types and programming in C

**1. Answer (2).** The semicolon after the for header is an empty body. The loop only runs i up to 5; then s = 0 + 5. Output: **5 5**

**2.** swap1 swaps its own copies, so x and y are unchanged. swap2 works through the addresses. Output: **1 2 2 1**

**3.** fact(5) = 120. fib(7) = 13 (0, 1, 1, 2, 3, 5, 8, 13). Output: **120 13**
The call count C(n) satisfies C(n) = 1 + C(n − 1) + C(n − 2) with C(0) = C(1) = 1, which gives C(n) = 2·fib(n + 1) − 1. For n = 7: 2 × 21 − 1 = **41** calls.

**4.** The do-while body runs once even though i > 0 is false: n = 1. The while loop takes i through 3, 6, 9, 12. At i = 6 the continue skips n += 10; at 3, 9 and 12 it adds 10. n = 1 + 30 = 31. Output: **12 31**

**5.** y = 5 × 2 = 10, then x = 6. ++x makes x = 7 and z = 14. Output: **7 10 14**

**6.** p points to "gram". *p is g, and g + 1 is h. p[2] is a. Output: **gram h a**

**7.** sum adds the digits: 4 + 0 + 9 + 6 = 19. rev reverses 1230 into 321 (the trailing 0 becomes a leading zero and disappears). Output: **19 321**

**8.** k takes the values 5, 3 and 1: str[5] = T, str[3] = N, str[1] = G. Then k = −1 ends the loop. Output: **TNG**
The pointer version would finally compute str − 1 to make the test p >= str fail. A pointer may point into an array or one past its end, but not before its start, so merely computing str − 1 is undefined behaviour. With an int index, −1 is just a number and nothing is computed outside the array.

**9.** For i = 1 to 4 the inner loop runs 4, 3, 2, 1 times: 4 + 3 + 2 + 1 = 10. Output: **10**

**10.** The loop visits a, b, c: s = 1, 12, 123. a.next->next is c, whose v is 3. Output: **123 3**

**11.** Column-major: 500 + (j × rows + i) × 4 = 500 + (3 × 4 + 2) × 4 = 500 + 56 = **556**. Row-major: 500 + (2 × 6 + 3) × 4 = 500 + 60 = **560**.

**12.** struct A: c at 0, 7 bytes of padding, d at 8–15, i at 16–19, then tail padding to a multiple of 8: **24**. struct B: d at 0–7, i at 8–11, c at 12, tail padding: **16**. union U: the largest member is 10 bytes; rounded up to the int alignment of 4 gives **12**.

**13.** strcat makes a = "netjrf" (length 6). strcpy puts "ok" into b (b has room for 4 chars). strcmp("abc", "abd") is negative, so the comparison gives 1. Output: **netjrf 6 ok 1**

**14.** A and B are undefined: in A, i is read for the index and modified by i++ without ordering; in B, i is modified twice. C is also undefined in C11: i is assigned by the inner assignment and by the outer one, and the two side effects are unsequenced. D is fine (one modification of i, and a[i++] uses the old value 2). E is fine (the comma operator is a sequence point). Undefined: **A, B and C**.

**15.** *p = 15 changes x through the constant pointer. q may be pointed elsewhere, so q = &y is fine. Output: **15 20**
(a) fails, because p is a const pointer. (b) fails, because q points to const int. (c) is fine, because x is not const. (d) is fine: an int * converts to a const int * implicitly.
