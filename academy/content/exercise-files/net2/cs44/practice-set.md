# Practice set: Software testing (cs44)

Time: 22 minutes.

1. A function has 5 integer inputs, each with a valid range. How many test cases do (a) basic BVA, (b) robustness testing, (c) worst-case testing need?

2. A function takes x in [10, 50] and y in [1, 9]. Using integer midpoints (rounded down) as nominal values, list the basic BVA test cases.

3. An input has valid classes: account type ∈ {savings, current} (2 classes), amount ∈ {≤ 10,000, 10,001–1,00,000, > 1,00,000} (3), channel ∈ {branch, ATM, online, mobile} (4). How many tests do weak normal and strong normal equivalence class testing need?

4. A decision table has 4 binary conditions. How many rules does the full table have? If two rules are merged into one rule with a single don’t-care entry, how many rules remain?

5. A flow graph has 17 edges and 13 nodes. Find V(G). How many predicate nodes does it have, if every predicate node has exactly two outgoing edges?

6. Find the cyclomatic complexity of:

    int f(int a, int b, int c) {
        int r = 0;
        if (a > 0 || b > 0)
            r = 1;
        while (c > 0) {
            if (c % 2 == 0)
                r = r + c;
            c = c - 1;
        }
        return r;
    }

7. A program has a main function and 3 procedures, drawn as separate flow graphs with 40 edges and 34 nodes in total. Find V(G).

8. What is the minimum number of tests for MC/DC of the decision (A || B || C)? Give one such set.

9. 80 mutants are generated; 8 are equivalent; the tests kill 54. Find the mutation score. How many more non-equivalent mutants must be killed to reach 90%?

10. What is the output of this program?

    #include <stdio.h>
    int inrange(int x) { return x > 18 && x <= 60; }
    int main(void) {
        int t[] = {17, 18, 19, 60, 61};
        for (int i = 0; i < 5; i++) printf("%d", inrange(t[i]));
        printf("\n");
        return 0;
    }

    The specification says ages 18 to 60 inclusive are valid. Which boundary test exposes the fault?

11. 30 defects are seeded. Testing finds 24 of them and 72 original defects. Estimate the original defects remaining.

12. Match List I with List II.

| List I | List II |
|---|---|
| A. Driver | I. Stand-in for a called module |
| B. Stub | II. Calls the module under test and passes it data |
| C. Test oracle | III. Decides whether an output is correct |
| D. Mutant | IV. Program with one small deliberate change |

Options: (1) A-II, B-I, C-III, D-IV (2) A-I, B-II, C-III, D-IV (3) A-II, B-I, C-IV, D-III (4) A-II, B-III, C-I, D-IV

13. Assertion (A): Two consecutive if–else statements give a cyclomatic complexity of 3.
Reason (R): Such a function has exactly 3 complete entry-to-exit paths.
Options: (1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

14. Which of the following are black-box techniques?
A. Equivalence partitioning  B. Decision table testing  C. Data flow testing  D. Cause–effect graphing  E. Loop testing
Options: (1) A, B and D only (2) A, B, C and D only (3) A and D only (4) B, C and E only

15. Arrange the following test levels of the V-model in the order in which they are executed: A. Acceptance, B. Integration, C. Unit, D. System.
Options: (1) C, B, D, A (2) B, C, D, A (3) C, D, B, A (4) C, B, A, D
