# Practice set 10.3: Planning, NLP and multi-agent systems

15 exam-level problems. Pace: about 90 seconds per problem, and up to 3 minutes for problems 3, 8 and 10. Keep probabilities as exact fractions.

Conventions: the blocks-world schemas are the standard four from the lesson:

| Action | PRE | ADD | DEL |
|---|---|---|---|
| Pickup(x) | Clear(x), OnTable(x), HandEmpty | Holding(x) | Clear(x), OnTable(x), HandEmpty |
| Putdown(x) | Holding(x) | Clear(x), OnTable(x), HandEmpty | Holding(x) |
| Stack(x,y) | Holding(x), Clear(y) | On(x,y), Clear(x), HandEmpty | Holding(x), Clear(y) |
| Unstack(x,y) | On(x,y), Clear(x), HandEmpty | Holding(x), Clear(y) | On(x,y), Clear(x), HandEmpty |

---

**1.** The initial state is On(A,B), On(B,C), OnTable(C), Clear(A), HandEmpty. Apply Unstack(A,B), Putdown(A), Unstack(B,C) and Stack(B,A) in that order. Write the state after every action. Which atoms hold at the end?

**2.** Regress the goal {On(B,C), Clear(A)} through Stack(B,C). Then say whether Unstack(B,C) is relevant to the same goal, and why.

**3.** For the tower C at the bottom, B on C and A on top, the goal is On(C,B) ∧ On(B,A) (turn the tower upside down). What is the length of the shortest plan? Write one such plan.

(1) 4 (2) 5 (3) 6 (4) 8

**4.** A partial-order plan has (a) two independent chains of three actions each, and (b) three independent chains of two actions each. How many linearisations does each have?

**5.** Given below are two statements: one is labelled as Assertion (A) and the other is labelled as Reason (R).

- Assertion (A): When a step C threatens the causal link A →p B, the planner may resolve the threat by adding the ordering C ≺ A.
- Reason (R): Once C is ordered before A, C can no longer fall between A and B, so it cannot delete p while the link is being protected.

(1) Both (A) and (R) are true and (R) is the correct explanation of (A) (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A) (3) (A) is true but (R) is false (4) (A) is false but (R) is true

**6.** Match List I with List II.

| List I (GraphPlan mutex) | List II (condition) |
|---|---|
| A. Inconsistent effects | I. One action deletes a precondition of the other |
| B. Interference | II. The preconditions are mutex at the previous level |
| C. Competing needs | III. Every way of achieving the two literals is pairwise mutex |
| D. Inconsistent support | IV. One action negates an effect of the other |

(1) A-IV, B-I, C-II, D-III (2) A-I, B-IV, C-II, D-III (3) A-IV, B-I, C-III, D-II (4) A-IV, B-II, C-I, D-III

**7.** (a) Arrange in order from lowest to highest: A. Discourse B. Syntactic C. Morphological D. Pragmatic E. Semantic.
(b) Name the type of ambiguity in each: (i) “The chicken is ready to eat.” (ii) “He went to the bank.” (iii) “Every student saw a film.” (iv) “Meena told Priya that she had passed.”

**8.** Use the CNF grammar S → NP VP; VP → V NP | VP PP; NP → Det N | NP PP | I; PP → P NP; V → saw; Det → the; N → man | hill; P → on. For “I saw the man on the hill”: (a) how many cells does the CYK table have? (b) which non-terminals are in the cell for “saw the man on the hill”, and with how many derivations? (c) how many parse trees does S have?

**9.** A bigram model is trained on: “<s> agents plan tasks </s>”, “<s> agents share tasks </s>”, “<s> robots plan routes </s>”, “<s> agents plan routes </s>”.
(a) Find P(<s> agents plan routes </s>) and P(<s> robots share tasks </s>) without smoothing.
(b) Repeat both with add-one smoothing, taking V = 7 (the six words plus </s>).

**10.** Four documents: D1 “nlp parses text”, D2 “agents plan tasks plan”, D3 “agents negotiate”, D4 “text retrieval ranks text”. Use w = tf × log₁₀(N/df).
(a) Give the weights of the terms in D2 and D4.
(b) The query is “plan text”, weighted by idf only. Rank the documents by cosine similarity.

**11.** A system returns a ranked list whose relevance judgements are R N R R N N R N (R = relevant). The collection holds 5 relevant documents. Find precision and recall at rank 5 and at rank 8, and F₁ at rank 8.

**12.** Find the Levenshtein distance (unit costs) for (a) “planning” → “planting” and (b) “agents” → “argent”.

**13.** (a) The row player chooses Up or Down, the column player Left or Right. Payoffs (row, column): (Up, Left) = (2, 3), (Up, Right) = (4, 1), (Down, Left) = (1, 2), (Down, Right) = (3, 4). Find the pure Nash equilibrium and say whether it is Pareto optimal.
(b) In a sealed-bid auction the bids are 45, 60, 52 and 38. What does the winner pay under first-price rules and under Vickrey rules?

**14.** (a) Fifteen voters rank four candidates: 6 voters A ≻ B ≻ C ≻ D, 5 voters B ≻ C ≻ D ≻ A, 4 voters C ≻ B ≻ D ≻ A. Find the plurality winner, the Borda winner (3, 2, 1, 0 points) and the Condorcet winner.
(b) Under the Zeuthen strategy, A’s offer gives A 10 and B 5, and B’s offer gives A 7 and B 8. Who concedes?

**15.** Which of the following statements are correct?

- A. KQML performatives such as tell and ask-if carry content written in a language such as KIF.
- B. In the contract net protocol, the manager bids for tasks announced by the contractors.
- C. A Nash equilibrium is always Pareto optimal.
- D. The perlocutionary act of an utterance is its effect on the hearer.
- E. A blackboard system lets independent knowledge sources cooperate through a shared data structure.

(1) A, D and E only (2) A, B and D only (3) A, C, D and E only (4) D and E only
