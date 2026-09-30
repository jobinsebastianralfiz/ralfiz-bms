# Practice set cs46: trees and heaps

Time: 24 minutes. Height is counted in edges (a single node has height 0) unless stated otherwise. Draw the tree after every insertion.

1. A binary tree has 12 leaves and 5 nodes with exactly one child. How many nodes does it have?

2. Preorder: P Q S W T X R U V Y. Inorder: S W Q X T P U R V Y. Find the postorder and the level order, and the height.

3. Postorder: B A D F E C J H L K G. Inorder: A B C D E F G H J K L. Find the preorder.

4. Insert 45, 20, 65, 10, 30, 55, 90, 25, 35, 60 into an empty BST. Give the preorder and the height. Then delete 45 using the inorder predecessor and give the new preorder.

5. Insert 30, 20, 10, 40, 50, 45, 35, 33 into an empty AVL tree. Name every rotation and give the final preorder.

6. Insert 50, 40, 30, 20, 10, 5, 25, 27 into an empty AVL tree. Give the final preorder and height.

7. Insert 5, 15, 25, 35, 45, 55, 65, 75, 85, 95, 12, 22, 32 into an empty B-tree of order 5 (max 4 keys; on overflow the median goes up). How many splits occur, and what is the final tree?

8. Insert 1, 2, …, 10 into an empty B-tree of order 3 (on overflow the middle of the 3 keys goes up). Give the final tree, its height and its number of nodes.

9. Apply bottom-up build-max-heap to [20, 35, 15, 50, 40, 10, 45, 30, 25]. Then build a heap from the same keys by repeated insertion. Give both arrays and the number of swaps for each.

10. How many distinct max-heaps can be formed from 6 distinct keys?

11. Match List I with List II.

| List I | List II |
|---|---|
| A. Minimum nodes in an AVL tree of height 4 | I. 15 |
| B. Maximum nodes in a binary tree of height 3 | II. 12 |
| C. Nodes in a full binary tree with 7 leaves | III. 14 |
| D. BSTs on 4 distinct keys | IV. 13 |

Choose: (1) A-II, B-I, C-IV, D-III (2) A-II, B-IV, C-I, D-III (3) A-III, B-I, C-IV, D-II (4) A-II, B-I, C-III, D-IV

12. Assertion (A): Inserting keys in sorted order into a plain BST produces a tree of height n − 1. Reason (R): Each new key is larger than all existing keys, so it always becomes the right child of the current maximum.
Choose from the four standard A–R options.

13. Statement I: In an AVL tree, a single insertion can require rotations at several ancestors. Statement II: In a red–black tree, a deletion needs at most three rotations.
Choose from the four standard Statement I/II options.

14. What is the output of this C program?

    #include <stdio.h>
    #include <stdlib.h>
    struct node { int key; struct node *left, *right; };
    struct node *ins(struct node *r, int k) {
        if (!r) {
            r = malloc(sizeof *r);
            r->key = k; r->left = r->right = NULL;
        } else if (k < r->key) r->left = ins(r->left, k);
        else r->right = ins(r->right, k);
        return r;
    }
    int one(struct node *r) {
        if (!r) return 0;
        int me = (r->left == NULL) != (r->right == NULL);
        return me + one(r->left) + one(r->right);
    }
    void mirror(struct node *r) {
        if (!r) return;
        struct node *t = r->left; r->left = r->right; r->right = t;
        mirror(r->left); mirror(r->right);
    }
    void in(struct node *r) {
        if (!r) return;
        in(r->left); printf("%d ", r->key); in(r->right);
    }
    int main(void) {
        int k[] = {50, 30, 70, 20, 60, 80, 65, 10};
        struct node *r = NULL;
        for (int i = 0; i < 8; i++) r = ins(r, k[i]);
        printf("%d | ", one(r));
        mirror(r);
        in(r);
        printf("\n");
        return 0;
    }

15. A B+ tree uses 512-byte blocks, 8-byte keys, 6-byte block pointers and 6-byte record pointers. Find the maximum number of child pointers in an internal node and the maximum number of keys in a leaf (each leaf also has one next-leaf pointer).
