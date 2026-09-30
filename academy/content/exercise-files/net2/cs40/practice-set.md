# Practice set: Software requirements (Lesson 6.2)

Time: 24 minutes. Each question carries 2 marks. There is no negative marking.

**1.** Classify each requirement as functional (F) or non-functional (NF), and give the Sommerville group for every NF one.
(a) The system shall calculate late fees at ₹5 per day.
(b) The system shall run on the college’s existing Linux servers.
(c) The system shall process 200 transactions per second at peak.
(d) Student records shall be kept according to the national data protection rules.

**2.** Match List I with List II.

| List I (DFD fault) | List II (Description) |
|---|---|
| A. Black hole | I. A process with outputs but no inputs |
| B. Miracle | II. A process whose inputs are insufficient to produce its outputs |
| C. Grey hole | III. A process with inputs but no outputs |
| D. Unbalanced diagram | IV. A child diagram whose boundary flows differ from its parent process |

(1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-II, C-I, D-IV (4) A-III, B-I, C-IV, D-II

**3.** A limited-entry decision table has 5 conditions. (a) How many rules does the full table have? (b) Its simplified form has 4 rules with two dashes, 3 rules with one dash and 5 rules with no dash, and no rules overlap. Is it complete?

**4.** A decision table has 2 Y/N conditions, one condition with 4 values and one with 3 values. How many rules does the complete table have?

**5.** In a data dictionary: emp-code = [T | P] + 2{digit}2 + (letter), where letter is one of 26 letters. How many distinct employee codes are possible?

**6.** An SRS has 70 functional and 30 non-functional requirements; reviewers agreed on the interpretation of 88. There are 63 unique functional requirements, 9 inputs and 10 states. 72 requirements are validated as correct and 28 are not yet validated. Compute Q1, Q2 and Q3.

**7.** Parent process 2 has inputs {order, payment} and outputs {receipt, shipment}. Its child diagram receives {order, payment, coupon} and sends {receipt}. List the balancing errors.

**8.** Which of the following are illegal in a DFD?
A. A flow from a data store to an external entity
B. A flow from an external entity to a process
C. A process with only input flows
D. A flow between two processes
E. A flow from one external entity to another

(1) A, C and E only (2) A and E only (3) C and E only (4) A, C, D and E only

**9.** Arrange Pressman’s requirements engineering tasks in order: A. Negotiation B. Validation C. Elicitation D. Specification E. Inception F. Elaboration.

**10.** Assertion (A): An «extend» use case is performed every time its base use case is performed.
Reason (R): In an «extend» relationship, the base use case is complete without the extension.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**11.** Statement I: A requirement that no test case can be designed for is probably not verifiable.
Statement II: The context diagram contains the system’s data stores.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**12.** Match List I with List II.

| List I (UML diagram) | List II (Category) |
|---|---|
| A. Timing diagram | I. Structure diagram |
| B. Deployment diagram | II. Interaction diagram |
| C. State machine diagram | III. Behaviour diagram (not interaction) |
| D. Package diagram | IV. Structure diagram showing hardware nodes |

(1) A-II, B-IV, C-III, D-I (2) A-III, B-IV, C-II, D-I (3) A-II, B-I, C-III, D-IV (4) A-II, B-IV, C-I, D-III

**13.** Rewrite “The system shall be fast and reliable” as two measurable non-functional requirements.

**14.** In QFD, classify: (a) The customer asks for online fee payment. (b) The app works on the customer’s existing phones without any setup. (c) The app predicts which students may fail and alerts mentors, which nobody asked for.

**15.** Which of the following best describes the difference between a decision table and a decision tree?
(1) A tree cannot show actions. (2) A table makes completeness and contradictions easy to check; a tree is easier to read when conditions are tested in a natural sequence. (3) A table is used only for extended-entry conditions. (4) A tree always has fewer leaves than the table has rules.
