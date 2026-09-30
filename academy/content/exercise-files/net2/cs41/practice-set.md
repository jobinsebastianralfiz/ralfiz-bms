# Practice set: Software design (Lesson 6.3)

Time: 24 minutes. Each question carries 2 marks. There is no negative marking.

**1.** Arrange the following from the lowest to the highest cohesion:
A. Sequential B. Temporal C. Coincidental D. Communicational E. Procedural F. Logical

**2.** Arrange the following from the lowest to the highest coupling:
A. Stamp B. Common C. Content D. Data E. Control F. External

**3.** Name the cohesion of each module.
(a) A module that validates a date, prints a banner and converts inches to centimetres.
(b) A module that reads a transaction, then validates it, then posts the valid transaction to the ledger, each step using the previous step’s output.
(c) A module that, from one sales record, updates the stock level and also updates the salesperson’s commission.
(d) A module that closes all files, releases memory and writes the shutdown log when the program ends.

**4.** Name the coupling between the modules in each case.
(a) A function receives an entire Employee record but reads only the employee’s ID.
(b) A function receives a flag that decides whether it deletes or archives a file.
(c) Two modules both update a global array of orders.
(d) Two modules must follow the same fixed file format imposed by a government portal.

**5.** Match List I with List II.

| List I (Architectural style) | List II (Characteristic) |
|---|---|
| A. Blackboard | I. Each layer uses only the layer below it |
| B. Layered | II. Independent filters connected by pipes transform a data stream |
| C. Pipe and filter | III. A central data store notifies clients when data of interest changes |
| D. Client–server | IV. Clients request services from servers over a network |

(1) A-III, B-I, C-II, D-IV (2) A-I, B-III, C-II, D-IV (3) A-III, B-II, C-I, D-IV (4) A-III, B-I, C-IV, D-II

**6.** A structure chart has modules with (fan-out, input/output variables): Main (4, 3), A (2, 6), B (0, 5), C (1, 2). Compute S, D and C for each module using Card and Glass, and name the most complex module.

**7.** A module has 50 lines of code, fan-in 2 and fan-out 5. Compute its Henry–Kafura complexity.

**8.** A class has five methods using instance variables M1 {x}, M2 {x, y}, M3 {z}, M4 {w}, M5 {z, w}. Compute P, Q and LCOM (original CK definition).

**9.** Class Shape is the root. Circle, Polygon and Line derive from Shape; Triangle and Quadrilateral derive from Polygon; Square derives from Quadrilateral. Find DIT(Square), NOC(Shape) and NOC(Polygon).

**10.** Assertion (A): Logical cohesion is better than temporal cohesion.
Reason (R): In logical cohesion, the tasks are selected by a control flag passed from outside.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**11.** Statement I: In UML, a hollow diamond at the whole end of an association denotes aggregation.
Statement II: In UML, realisation is drawn as a solid line with a filled arrowhead.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**12.** Which of the following are structural design patterns?
A. Adapter B. Proxy C. Observer D. Facade E. Command

(1) A, B and D only (2) A, B, D and E only (3) A and D only (4) B, C and D only

**13.** A payroll DFD is: read timesheet → validate → compute gross pay → compute deductions → format payslip → print. Identify the incoming flow, the transform centre and the outgoing flow, and draw the first-level factoring.

**14.** Which of Mandel’s golden rules is violated in each case? (a) A form clears all entered data when one field is wrong. (b) The Save command is Ctrl+S in one screen and F2 in another. (c) The user must remember a 6-digit product code typed on the previous screen.

**15.** A structure chart has 9 modules and 11 call arcs. Compute size and the arc-to-node ratio. Is the chart a pure tree?
