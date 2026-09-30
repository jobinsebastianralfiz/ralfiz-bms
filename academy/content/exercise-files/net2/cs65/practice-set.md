# Practice set 10.1: AI approaches and search

15 exam-level problems. Pace: about 90 seconds per problem, and up to 3 minutes for the traces (problems 3, 4 and 7). Write your answer, then check it with solutions.md.

Conventions (use them in every trace): graph search, successors in alphabetical order, ties in a priority queue broken alphabetically, goal test when a node is expanded (unless the problem says otherwise). Alpha–beta works left to right.

Problems 1 to 6 use this undirected graph. Start S, goal G.

    Edges (cost): S–A 3   S–B 1   B–A 1   A–C 2   A–E 6
                  B–D 5   C–D 1   C–G 6   D–G 2   E–G 1
    Heuristic h:  S 5   A 4   B 5   C 3   D 2   E 1   G 0

---

**1.** Give the order in which BFS expands the nodes, the path it returns, and that path’s cost.

**2.** Give the order in which recursive DFS visits the nodes and the cost of the path it returns.

(1) S, A, C, G; cost 11 (2) S, A, B, D, G; cost 11 (3) S, A, B, D, C, G; cost 16 (4) S, B, D, G; cost 8

**3.** Trace uniform-cost search. Show the frontier after each expansion and give the path and its cost.

**4.** (a) Is h admissible? Is it consistent? (b) Trace A*. How many nodes does it expand, including G?

**5.** What path does greedy best-first search return, and how much more does it cost than the optimal path?

**6.** Iterative deepening search (with no repeated states on the current path) finds the goal at which depth limit? Count all node visits over all iterations.

(1) limit 2; 12 visits (2) limit 3; 16 visits (3) limit 3; 19 visits (4) limit 4; 25 visits

**7.** A MAX root has four MIN children. Their leaves, left to right, are (8, 3, 5), (2, 9, 4), (6, 7, 1) and (4, 8, 6). Find the root value and the number of leaves alpha–beta prunes.

**8.** A three-ply tree (MAX, MIN, MAX, leaves) has leaves grouped as ((6, 4), (2, 8)), ((7, 3), (1, 5)), ((9, 2), (6, 3)). Find the minimax value. How many leaves does alpha–beta prune? Explain the result.

**9.** Match List I with List II.

| List I (Task environment) | List II (Property that best describes it) |
|---|---|
| A. Poker | I. Episodic |
| B. Image classification | II. Continuous |
| C. Crossword puzzle | III. Partially observable |
| D. Taxi driving | IV. Static and single-agent |

(1) A-I, B-III, C-IV, D-II (2) A-III, B-I, C-II, D-IV (3) A-III, B-IV, C-I, D-II (4) A-III, B-I, C-IV, D-II

**10.** Assertion (A): Random-restart hill climbing finds a global optimum with probability approaching 1 as the number of restarts grows. Reason (R): Every restart begins from a new randomly generated state.

(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**11.** Which of the following statements are correct?

- A. MRV chooses the variable with the fewest legal values remaining.
- B. The degree heuristic is used to break ties in MRV.
- C. Forward checking detects every inconsistency that arc consistency detects.
- D. AC-3 runs in O(cd³) time for c binary constraints and domain size d.
- E. A tree-structured CSP can be solved in O(nd²) time.

(1) A, B and C only (2) A, B, D and E only (3) A, D and E only (4) B, C and E only

**12.** A map has regions V, W, X, Y and Z. The adjacent pairs are W–X, W–Y, X–Y, X–Z, Y–Z, Z–V and Y–V. (a) How many proper 3-colourings are there? (b) After W = red and X = green, which variable does MRV choose next, and why?

**13.** For b = 5 and a goal at depth d = 3 (the last node at that depth), how many nodes do BFS (goal test at generation) and IDS generate? What is IDS’s percentage overhead?

**14.** In simulated annealing, a move is worse by ΔE = 5. What is the acceptance probability at T = 10 and at T = 1?

**15.** Take b = 10, the shallowest goal depth d = 5 and the maximum depth m = 8. Arrange by worst-case memory, smallest first: A. BFS, B. DFS, C. IDS, D. Depth-limited search with l = 3.

(1) C, D, B, A (2) D, C, B, A (3) D, B, C, A (4) B, D, C, A
