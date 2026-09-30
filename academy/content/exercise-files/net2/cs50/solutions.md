# Solutions: Practice set 7.6

**1. (2) 15.** Kruskal on G1: P–R 1 (take), S–U 2 (take), Q–T 3 (take), R–U 4 (take). Among the weight-5 edges, P–S closes the cycle P–R–U–S and R–S closes R–U–S, but Q–R joins {Q, T} to the rest (take). Five edges for six vertices: 1 + 2 + 3 + 4 + 5 = 15.

**2. (3) Q–R.** See problem 1. P–S and R–S would each close a cycle, because P, R, S and U are already connected. Even though weights tie, this MST is unique: no other weight-5 edge can connect {Q, T}. (Rule: distinct weights guarantee a unique MST; ties only make several MSTs possible.)

**3. (3) R–U.** Prim from P: first P–R 1 (tree {P, R}); the cheapest edge leaving {P, R} is then R–U 4 (P–S, Q–R and R–S weigh 5; R–T and P–Q weigh 6). S–U 2 is added third, once U is in the tree. Then Q–R 5 and Q–T 3.

**4. (1) 8.** a→b 3, b→c 2 (5), c→d 1 (6), d→e 2 (8). The alternatives are longer: b→d→e = 12, c→e = 14, a→c→d→e = 11.

**5. (4) a, b, c, d, e.** Distances: b 3, c 5, d 6, e 8. Dijkstra finalises in increasing distance.

**6. (2) 2.** b→c→d→e→b is a cycle, so {b, c, d, e} is one SCC. Nothing leads back to a, so {a} is the other. Trap: counting every vertex separately gives 5.

**7. (2) 1 2 3 4 5 6.** Level 1: 2, 3. Level 2: 4 (from 2), then 5 (from 3). Level 3: 6.

**8. (3) 1 2 4 3 5 6.** 1 → 2 → 4 (2’s only new neighbour) → 3 (4’s smallest unvisited neighbour) → 5 → 6.

**9. (2) 2.** 1 must be first and 4, 5 last (in that order); only 2 and 3 can swap: 1 2 3 4 5 and 1 3 2 4 5.

**10. (4) 12.** Augment s→x→t by 4, s→x→y→t by 3 and s→y→t by 5: total 12. The cut ({s}, {x, y, t}) has capacity 7 + 5 = 12, so no larger flow exists.

**11. (3) 3.** 1→2→3 = 5 − 2 = 3, shorter than the direct edge 6. The only cycle, 1→2→3→1, weighs 5 − 2 + 4 = 7 > 0, so the diagonal stays 0 and the answer is well defined.

**12. (1) A-III, B-II, C-I, D-IV.**

**13. (1).** The reason is exactly the argument of the proof: the edge would be explored first from the vertex that is discovered first.

**14. (1) Both true.** Bellman–Ford does an extra V-th pass; Floyd–Warshall shows D[i][i] < 0 for a vertex on a negative cycle.

**15. (3) B, C and D only.** Bellman–Ford and Floyd–Warshall allow negative edges, and topological-order relaxation handles them in O(V + E). Dijkstra may fail with negative edges, and BFS ignores weights altogether.

## Answer key
1-(2), 2-(3), 3-(3), 4-(1), 5-(4), 6-(2), 7-(2), 8-(3), 9-(2), 10-(4), 11-(3), 12-(1), 13-(1), 14-(1), 15-(3)
