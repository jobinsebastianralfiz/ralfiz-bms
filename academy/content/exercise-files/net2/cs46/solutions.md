# Solutions cs46

1. n₂ = n₀ − 1 = 11. Total = 12 + 5 + 11 = **28**.

2. Root P. Inorder left S W Q X T, right U R V Y. Left subtree (preorder Q S W T X): root Q, left S W (S with right child W), right X T (T with left child X). Right subtree (preorder R U V Y): root R, left U, right V Y (V with right child Y).
   Postorder **W S X T Q U Y V R P**; level order **P Q R S T U V W X Y**; height **3** (P→Q→S→W).

3. Root G (last in postorder). Inorder left A B C D E F, right H J K L. Left postorder B A D F E C: root C; its left A B (postorder B A → root A, right child B); its right D E F (postorder D F E → root E with children D, F). Right postorder J H L K: root K; left H J (postorder J H → root H, right child J); right L.
   Preorder **G C A B E D F K H J L**.

4. Tree 45(20(10, 30(25, 35)), 65(55(—, 60), 90)). Preorder **45 20 10 30 25 35 65 55 60 90**, height **3**. Predecessor of 45 is 35 (rightmost in the left subtree, a leaf). New preorder **35 20 10 30 25 65 55 60 90**.

5. 10 → LL at 30 (root 20). 50 → RR at 30 (40 moves up: 20(10, 40(30, 50))). 45 → RR at 20 (root 40: 40(20(10, 30), 50(45))). 35 → no rotation. 33 → RL at 30 (inserted into the left subtree of 30’s right child 35): 33 moves up.
   Rotations **LL, RR, RR, RL**. Final preorder **40 20 10 33 30 35 50 45**, height 3.

6. 30 → LL at 50. 10 → LL at 30. 5 → LL at 40 (root becomes 20). 25 → none. 27 → LR at 30 (27 moves up between 25 and 30).
   Final preorder **20 10 5 40 27 25 30 50**, height **3**.

7. 45 overflows [5 15 25 35 45] → 25 up. 75 overflows [35 45 55 65 75] → 55 up. Later keys fit: 85, 95 → [65 75 85 95]; 12, 22 → [5 12 15 22]; 32 → [32 35 45].
   **2 splits.** Final: root **[25 55]** with leaves [5 12 15 22], [32 35 45], [65 75 85 95]. Height 1.

8. Splits happen when inserting 3, 5, 7 (leaf and then root), and 9. Final tree:
   root [4]; children [2] and [6 8]; leaves [1], [3], [5], [7], [9 10]. **Height 2, 8 nodes, 5 splits** (counting the two at key 7 separately).

9. Build-heap (sift down at positions 4, 3, 2, 1): **50 40 45 35 20 10 15 30 25** with **4 swaps**.
   Repeated insertion: **50 40 45 30 35 10 15 20 25** with **6 swaps**. Both are valid heaps; they differ at positions 4, 5 and 8.

10. The 6-node complete tree has a left subtree of 3 nodes and a right subtree of 2. H(6) = C(5, 3)·H(3)·H(2) = 10 × 2 × 1 = **20**.

11. A: N(4) = 12 (II). B: 2⁴ − 1 = 15 (I). C: a full binary tree has n = 2n₀ − 1 = 13 nodes (IV). D: C₄ = 14 (III). Answer **(1)**.

12. Both true, and R explains A: each new key goes to the right of the previous maximum, so the tree is a right chain of n nodes with height n − 1. Answer: **Both (A) and (R) are true and (R) is the correct explanation of (A)**.

13. Statement I is false: after an AVL insertion, one single or double rotation at the lowest unbalanced node restores that subtree’s old height, so no higher rotation is needed. Statement II is true. Answer: **Statement I is false but Statement II is true**.

14. The BST is 50(30(20(10)), 70(60(—, 65), 80)). Nodes with exactly one child: 30, 20, 60 → 3. Mirroring swaps every left and right, so the inorder becomes descending. Output: **3 | 80 70 65 60 50 30 20 10** (verified with gcc).

15. Internal: 6p + 8(p − 1) ≤ 512 → 14p ≤ 520 → p = **37**. Leaf: q(8 + 6) + 6 ≤ 512 → 14q ≤ 506 → q = **36**.
