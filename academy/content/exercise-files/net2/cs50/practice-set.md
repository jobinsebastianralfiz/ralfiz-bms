# Practice set 7.6: Graph algorithms

Time: 26 minutes. Each question has one correct option. No negative marking. Neighbours are taken in alphabetical or numeric order unless stated.

Graph G1 (undirected, weighted): P–Q 6, P–R 1, P–S 5, Q–R 5, Q–T 3, R–S 5, R–T 6, R–U 4, S–U 2, T–U 6.

**1.** What is the weight of the MST of G1?
(1) 16 (2) 15 (3) 17 (4) 18

**2.** G1 has three edges of weight 5. Which of them belongs to its MST?
(1) P–S (2) R–S (3) Q–R (4) None of them

**3.** In Prim’s algorithm started from P on G1, which edge is added second?
(1) P–R (2) S–U (3) R–U (4) Q–T

Graph G2 (directed): a→b 3, a→c 8, b→c 2, b→d 7, c→d 1, c→e 9, d→e 2, e→b 1.

**4.** What is the shortest distance from a to e in G2?
(1) 8 (2) 10 (3) 12 (4) 9

**5.** In what order does Dijkstra’s algorithm, started from a, finalise the vertices of G2?
(1) a, b, d, c, e (2) a, c, b, d, e (3) a, b, c, e, d (4) a, b, c, d, e

**6.** How many strongly connected components does G2 have (ignore the weights)?
(1) 1 (2) 2 (3) 3 (4) 5

**7.** BFS from vertex 1 on the undirected graph with edges 1–2, 1–3, 2–4, 3–4, 3–5, 4–6, 5–6. What is the visiting order?
(1) 1 2 4 3 5 6 (2) 1 2 3 4 5 6 (3) 1 3 2 5 4 6 (4) 1 2 3 5 4 6

**8.** DFS from vertex 1 on the same graph. What is the visiting order?
(1) 1 2 3 4 5 6 (2) 1 2 4 6 5 3 (3) 1 2 4 3 5 6 (4) 1 3 5 6 4 2

**9.** How many topological orders does the DAG with edges 1→2, 1→3, 2→4, 3→4, 4→5 have?
(1) 1 (2) 2 (3) 4 (4) 6

**10.** A network has capacities s→x 7, s→y 5, x→y 3, x→t 4, y→t 8. What is the maximum flow from s to t?
(1) 11 (2) 10 (3) 9 (4) 12

**11.** Floyd–Warshall is run on the edges 1→2 5, 2→3 −2, 3→1 4, 1→3 6. What is the final D[1][3]?
(1) 6 (2) 4 (3) 3 (4) 2

**12.** Match List I with List II.

| List I | List II |
|---|---|
| A. Prim (array implementation) | I. O(V + E) |
| B. Kruskal | II. O(E log E) |
| C. DAG shortest paths | III. O(V²) |
| D. Edmonds–Karp | IV. O(VE²) |

(1) A-III, B-II, C-I, D-IV (2) A-II, B-III, C-I, D-IV (3) A-III, B-II, C-IV, D-I (4) A-III, B-I, C-II, D-IV

**13.** Assertion (A): A DFS of an undirected graph produces no cross edges. Reason (R): If the edge {u, v} were first explored from u after v had finished, then v would already have explored {v, u} while u was undiscovered, making it a tree edge.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**14.** Statement I: Bellman–Ford can report a negative cycle reachable from the source. Statement II: Floyd–Warshall reveals a negative cycle when some diagonal entry becomes negative.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**15.** Which algorithms correctly find single-source shortest paths in a DAG that has some negative edges? A. Dijkstra B. Bellman–Ford C. Relaxation in topological order D. Floyd–Warshall (then read the source’s row) E. BFS
(1) B and C only (2) C only (3) B, C and D only (4) A, B, C and D only
