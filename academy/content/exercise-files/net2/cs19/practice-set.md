# Practice set 3.2: Elementary data types and programming in C

15 exam-level problems. Pace: about 90 seconds for each problem. Predict every output on paper before you check it.

Assume x86-64 Linux with gcc: char 1 byte, int 4 bytes, long 8, pointers 8, double 8, ASCII characters. Every program compiles cleanly with gcc -Wall -Wextra and has no undefined behaviour.

---

**1.** What is the output?

    #include <stdio.h>
    int main(void) {
        int i, s = 0;
        for (i = 0; i < 5; i++);
        s = s + i;
        printf("%d %d", i, s);
        return 0;
    }

(1) 5 10 (2) 5 5 (3) 4 4 (4) 0 0

**2.** What is the output?

    #include <stdio.h>
    void swap1(int a, int b) { int t = a; a = b; b = t; }
    void swap2(int *a, int *b) { int t = *a; *a = *b; *b = t; }
    int main(void) {
        int x = 1, y = 2;
        swap1(x, y);
        printf("%d %d ", x, y);
        swap2(&x, &y);
        printf("%d %d", x, y);
        return 0;
    }

**3.** What is the output?

    #include <stdio.h>
    int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }
    int fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
    int main(void) {
        printf("%d %d", fact(5), fib(7));
        return 0;
    }

How many calls to fib (including the first) does fib(7) make?

**4.** What is the output?

    #include <stdio.h>
    int main(void) {
        int i = 0, n = 0;
        do {
            n++;
        } while (i > 0);
        while (i < 10) {
            i += 3;
            if (i == 6) continue;
            n += 10;
        }
        printf("%d %d", i, n);
        return 0;
    }

**5.** What is the output?

    #include <stdio.h>
    int main(void) {
        int x = 5;
        int y = x++ * 2;
        int z = ++x * 2;
        printf("%d %d %d", x, y, z);
        return 0;
    }

**6.** What is the output?

    #include <stdio.h>
    int main(void) {
        const char *p = "program";
        p += 3;
        printf("%s %c %c", p, *p + 1, p[2]);
        return 0;
    }

**7.** What is the output?

    #include <stdio.h>
    int sum(int n) { return n == 0 ? 0 : n % 10 + sum(n / 10); }
    int rev(int n, int r) { return n == 0 ? r : rev(n / 10, r * 10 + n % 10); }
    int main(void) {
        printf("%d %d", sum(4096), rev(1230, 0));
        return 0;
    }

**8.** What is the output?

    #include <stdio.h>
    int main(void) {
        char str[] = "UGCNET";
        int k;
        for (k = 5; k >= 0; k -= 2)
            putchar(str[k]);
        return 0;
    }

Why would the pointer version while (p >= str) { putchar(*p); p -= 2; } be wrong, even if it happens to print the same thing?

**9.** What is the output?

    #include <stdio.h>
    int main(void) {
        int i, j, c = 0;
        for (i = 1; i <= 4; i++)
            for (j = i; j <= 4; j++)
                c++;
        printf("%d", c);
        return 0;
    }

**10.** What is the output?

    #include <stdio.h>
    typedef struct node { int v; struct node *next; } Node;
    int main(void) {
        Node c = {3, NULL}, b = {2, &c}, a = {1, &b};
        Node *p = &a;
        int s = 0;
        while (p != NULL) {
            s = s * 10 + p->v;
            p = p->next;
        }
        printf("%d %d", s, a.next->next->v);
        return 0;
    }

**11.** A float array x[4][6] is stored in column-major order starting at address 500, with 4 bytes per element. Find the address of x[2][3]. What would it be in row-major order?

**12.** Assume the sizes above. What is sizeof for each?

    struct A { char c; double d; int i; };
    struct B { double d; int i; char c; };
    union U { char s[10]; int i; };

**13.** What is the output?

    #include <stdio.h>
    #include <string.h>
    int main(void) {
        char a[20] = "net";
        char b[] = "jrf";
        strcat(a, b);
        strcpy(b, "ok");
        printf("%s %zu %s %d", a, strlen(a), b, strcmp("abc", "abd") < 0);
        return 0;
    }

**14.** Which of these statements have undefined behaviour? (int i = 2, a[5] = {0};)

- A. a[i] = i++;
- B. i = i++;
- C. i = (i = 3) + 1;
- D. a[i++] = 7;
- E. i++, i++;

**15.** What is the output?

    #include <stdio.h>
    int main(void) {
        int x = 10, y = 20;
        int *const p = &x;
        const int *q = &x;
        *p = 15;
        q = &y;
        printf("%d %d", x, *q);
        return 0;
    }

Which of these lines, if added before the printf, would fail to compile: (a) p = &y; (b) *q = 5; (c) x = 1; (d) q = p;
