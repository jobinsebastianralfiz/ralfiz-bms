# Practice set 10.6: Artificial neural networks and machine learning basics

15 exam-level problems. Pace: about 90 seconds per problem, and up to 4 minutes for problems 2 and 6. Give answers to 4 decimal places where they are not exact. σ(z) = 1/(1 + e^−z) is the logistic sigmoid.

---

**1.** A perceptron has w = (0.5, −0.4, 0.2), b = −0.1 and η = 0.1, and outputs y = 1 if net ≥ 0, else 0. For x = (1, 0, 1) with target t = 0, find net, y and the new weights and bias.

**2.** Train a perceptron on NAND with binary inputs presented in the order (0,0), (0,1), (1,0), (1,1) and targets 1, 1, 1, 0. Start from w1 = w2 = b = 0 with η = 1, and use y = 1 if net > 0, else 0. Give the weights and bias at the end of every epoch, and the epoch in which training stops.

**3.** Given below are two statements:

- Statement I: A perceptron with w = (3, 2) and b = −6 has a decision boundary that crosses the x1 axis at x1 = 2 and the x2 axis at x2 = 3.
- Statement II: Of the 16 Boolean functions of two inputs, exactly two cannot be computed by a single perceptron.

(1) Both Statement I and Statement II are true (2) Both Statement I and Statement II are false (3) Statement I is true but Statement II is false (4) Statement I is false but Statement II is true

**4.** A neuron has inputs x = (2, −1, 0.5), weights w = (0.3, 0.4, −0.2) and bias 0.1. Find its net input and its output with (a) the binary step (threshold 0), (b) the logistic sigmoid, (c) tanh and (d) ReLU.

**5.** A McCulloch–Pitts neuron has three binary inputs with weights 2, 1 and 1 and fires when the weighted sum is at least 3. For which input combinations does it fire? Write the function it computes as a Boolean expression.

**6.** A 2-2-1 network with sigmoid units has hidden unit h1 with weights (0.2, 0.4) and bias −0.3, hidden unit h2 with weights (−0.3, 0.1) and bias 0.2, and an output unit with weights (0.6, −0.5) from h1 and h2 and bias 0.1. For x = (0, 1), target t = 0 and η = 1, do one full backpropagation step: forward pass, error E = ½(t − o)², all deltas, and every updated weight and bias.

**7.** A network has two sigmoid output units with outputs o = (0.8, 0.4) and targets t = (1, 0). Hidden unit h1 (output 0.5) connects to them with weights 0.3 and −0.2; hidden unit h2 (output 0.9) with weights 0.6 and 0.4. Find both output deltas and both hidden deltas.

**8.** Learn NAND with the Hebb rule using bipolar inputs (1,1), (1,−1), (−1,1), (−1,−1), bipolar targets −1, 1, 1, 1, a bias input of 1, η = 1 and zero initial weights. Give the final weights and bias, and check that sign(net) reproduces NAND.

**9.** An ADALINE has w = (0.2, −0.1), b = 0.1 and η = 0.1, and is trained with Δw = η(t − net)x, Δb = η(t − net). Present x = (1, 1) with t = 1, then x = (1, −1) with t = −1. Give net, the weights and the bias after each step.

**10.** A 4-unit Hopfield network stores p1 = (1, 1, −1, −1) and p2 = (1, −1, 1, −1) with W = p1p1ᵀ + p2p2ᵀ − 2I.
(a) Write W. (b) Check that both patterns are stable. (c) The probe is s = (1, 1, −1, 1). Update unit 4 only: what is its net input and the new state? (d) Find the energy E = −½ sᵀWs before and after the update.

**11.** A 1-D Kohonen chain has four units with weights w1 = (0.1, 0.9), w2 = (0.4, 0.6), w3 = (0.7, 0.3), w4 = (0.9, 0.1). The input is x = (0.6, 0.4). The winner and its immediate chain neighbours are updated with η = 0.4. Find the winner and all the new weight vectors.

**12.** Match List I with List II.

| List I (network or rule) | List II (property) |
|---|---|
| A. Hopfield network | I. Unsupervised, competitive, topology-preserving |
| B. Kohonen SOM | II. Error-correction on the thresholded output |
| C. Perceptron rule | III. Recurrent, symmetric weights, energy function |
| D. Delta (LMS) rule | IV. Gradient descent on the squared error of the linear output |

(1) A-III, B-I, C-IV, D-II (2) A-III, B-I, C-II, D-IV (3) A-I, B-III, C-II, D-IV (4) A-III, B-II, C-I, D-IV

**13.** (a) In Q-learning with α = 0.2 and γ = 0.9, Q(s, a) starts at 0. The agent takes a in s twice. The first time it gets reward 5 and max Q(s′, ·) = 10; the second time it gets reward −1 and max Q(s′, ·) is still 10. Find Q(s, a) after each update.
(b) Given below are two statements: one is labelled as Assertion (A) and the other is labelled as Reason (R).

- Assertion (A): Reinforcement learning needs no labelled input–output pairs.
- Reason (R): A reinforcement learning agent learns from scalar rewards that it receives for its actions.

(1) Both (A) and (R) are true and (R) is the correct explanation of (A) (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A) (3) (A) is true but (R) is false (4) (A) is false but (R) is true

**14.** (a) Run k-means with k = 2 on the points (1,1), (2,1), (1,2), (6,5), (7,6), (5,6), starting from the centroids (1,1) and (5,6). Give the centroids after one iteration, and say whether a second iteration changes anything.
(b) A classifier has TP = 45, FP = 5, FN = 15, TN = 35. Find accuracy, precision, recall, F1 and specificity TN/(TN + FP).

**15.** Which of the following statements are correct?

- A. A network with any number of layers but only linear activations computes a linear function of its input.
- B. The maximum value of the derivative of the logistic sigmoid is 0.25.
- C. In a Hopfield network, every self-connection weight wᵢᵢ is 1.
- D. Early stopping on a validation set is a way to reduce overfitting.
- E. A fully connected 784-128-10 network with biases has 101,770 trainable parameters.

(1) A, B and D only (2) A, B, D and E only (3) B, D and E only (4) A, B, C and D only
