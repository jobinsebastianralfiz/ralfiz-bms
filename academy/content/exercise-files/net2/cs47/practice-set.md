# Practice set cs47: searching, sorting and hashing

Time: 24 minutes. Sort into ascending order. A "pass" of bubble sort is one left-to-right sweep; a pass of selection sort places one element; pass i of insertion sort inserts a[i].

1. Bubble sort (with an early-exit flag) is applied to [41, 7, 33, 19, 2, 25]. Give the array after each pass, the number of passes and the number of swaps.

2. Insertion sort is applied to the same array [41, 7, 33, 19, 2, 25]. Give the array after pass 3 and the total number of comparisons.

3. Selection sort is applied to [41, 7, 33, 19, 2, 25]. How many swaps are made, and what is the array after pass 2?

4. Quick sort with the Lomuto partition (pivot = last element) is applied to [36, 12, 58, 7, 44, 21, 63, 30]. What is the array after the first partition, and where is the pivot?

5. Bottom-up merge sort is applied to [36, 12, 58, 7, 44, 21, 63, 30]. Give the array after each pass and the total number of comparisons.

6. LSD radix sort (base 10) is applied to [305, 42, 919, 17, 580, 263, 8, 71]. Give the array after each of the three passes.

7. Counting sort is applied to [2, 5, 3, 0, 2, 3, 0, 3] (keys 0..5). Give the count array, the cumulative array and the output.

8. (a) In the sorted array 5, 11, 18, 24, 30, 37, 45, 52, 60, 68, 77, which elements does binary search compare with 60? (b) For a sorted array of 10 elements, what is the average number of comparisons for a successful search?

9. Insert 43, 36, 92, 87, 11, 4, 71, 13, 14 into a table of size 10 with h(k) = k mod 10 and linear probing. Give the final table and the number of probes for 71, 13 and 14.

10. Repeat problem 9 with quadratic probing h(k, i) = (k mod 10 + i²) mod 10.

11. Insert 20, 46, 33, 59, 72, 11, 85, 24 into a table of size 13 with double hashing h(k, i) = (k mod 13 + i·(7 − k mod 7)) mod 13. Give the final table.

12. For α = 0.9, compute the expected number of probes for (a) an unsuccessful and (b) a successful search with linear probing, and (c) an unsuccessful and (d) a successful search under uniform hashing. (ln 10 ≈ 2.303)

13. Match List I with List II.

| List I (Algorithm) | List II (Worst-case comparisons or time) |
|---|---|
| A. Binary search, n = 1000 | I. 7 comparisons |
| B. Sorting 5 elements (optimal comparison sort) | II. Θ(n²) |
| C. Selection sort | III. 10 comparisons |
| D. Min and max of 10 elements | IV. 13 comparisons |

Choose: (1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-IV, C-II, D-I (4) A-III, B-I, C-IV, D-II

14. Assertion (A): Quick sort with the last element as pivot takes Θ(n²) time on an already sorted array. Reason (R): Each partition then puts all remaining elements on one side of the pivot.
Choose from the four standard A–R options.

15. What is the output of this C program?

    #include <stdio.h>
    int main(void) {
        int x[] = {3, 8, 12, 20}, y[] = {5, 9, 10, 25, 30};
        int out[9], i = 0, j = 0, k = 0, cmp = 0;
        while (i < 4 && j < 5) {
            cmp++;
            if (x[i] <= y[j]) out[k++] = x[i++];
            else out[k++] = y[j++];
        }
        while (i < 4) out[k++] = x[i++];
        while (j < 5) out[k++] = y[j++];
        printf("%d %d %d\n", cmp, out[4], out[7]);
        return 0;
    }
