# Solutions: practice set 4.5

**1.** Conflicts: R3(X) … W1(X) gives T3 → T1, and W3(Y) … R2(Y) gives T3 → T2. R1(X) and R3(X) are both reads; W2(Z) conflicts only with R2(Z) of the same transaction. Graph: T3 → T1, T3 → T2. Acyclic, so **conflict serializable**. Topological orders: T3 T1 T2 and T3 T2 T1, which makes **2** serial schedules.

**2.** R2(B) … W1(B) gives T2 → T1; W1(B) … W2(B) gives T1 → T2: a cycle, **not conflict serializable**. View test with T2 T1 T3: T2 reads the initial B in both, and the final writer is T3 in both. **View serializable, equivalent to T2 → T1 → T3.** The blind writes of T1 and T3 make this possible.

**3.** (a) T2 reads A from uncommitted T1 and commits first: **not recoverable**. (b) No transaction reads a value written by another, but T2 writes A before T1 commits: **cascadeless, not strict**. (c) T2 reads and writes A only after C1: **strict**.

**4.** Answer (1). 7!/(3! 4!) = 35 schedules; 2 are serial; 33 are non-serial.

**5.** T1 acquires lock-X(B) before releasing A, and releases nothing before its last lock: **T1 follows 2PL** (lock point at lock-X(B)). T2 releases A and then acquires lock-X(B): **T2 violates 2PL**.

**6.** R1(A) allowed (R-TS(A) = 10). W2(A) allowed (W-TS(A) = 20). R3(B) allowed (R-TS(B) = 30). W1(A): 10 ≥ R-TS(A) = 10 but 10 < W-TS(A) = 20: **basic TO rolls back T1**; with the **Thomas write rule the write is ignored** and T1 continues. W2(B): 20 < R-TS(B) = 30: **T2 is rolled back** under both rules.

**7.** Answer (4). A is false: a write with TS(T) < R-TS(X), or a read with TS(T) < W-TS(X), still rolls T back (problem 6 shows T2 being rolled back). R is true.

**8.** (a) T5 is older. Wait-die: **T5 waits**. Wound-wait: **T5 wounds T9** (T9 is rolled back). (b) T9 is younger. Wait-die: **T9 dies** (restarts with TS 9). Wound-wait: **T9 waits**.

**9.** T1 committed before the checkpoint: no action. **Redo: T3** (C = 350). **Undo: T2 and T4**, scanning backward: A = 150, D = 400, B = 200. Final: **A = 150, B = 200, C = 350, D = 400**.

**10.** Answer (2). 6p + 10(p − 1) ≤ 1024, so 16p ≤ 1034 and p = 64.

**11.** Leaf: 18 p_leaf + 6 ≤ 1024, so p_leaf = 56. Full 3-level tree: 64 × 64 = 4,096 leaves × 56 = **229,376** record pointers.

**12.** Answer (1). Minimum: root 1 key; level 2 has 2 nodes of 2 keys; level 3 has 6 nodes of 2 keys: 1 + 4 + 12 = 17 = 2 × 3² − 1. Maximum: 31 nodes × 4 keys = 124 = 5³ − 1.

**13.** bfr = 10, b = 3,000 blocks. (a) ⌈log₂ 3000⌉ = **12**. (b) fo = ⌊1024/15⌋ = 68, index blocks = ⌈3000/68⌉ = 45, accesses ⌈log₂ 45⌉ + 1 = **7**. (c) Second level ⌈45/68⌉ = 1 block, so 2 levels + 1 = **3**.

**14.** After 40: root [30], leaves [10 20] [30 40]. After 60: root [30 50], leaves [10 20] [30 40] [50 60]. After 80: root [30 50 70], leaves [10 20] [30 40] [50 60] [70 80]. **4 leaves**, 5 nodes, 2 levels.

**15.** Answer (1). READ UNCOMMITTED allows dirty reads (III); READ COMMITTED prevents them but allows unrepeatable reads (IV); REPEATABLE READ still allows phantoms (II); SERIALIZABLE allows none (I).
