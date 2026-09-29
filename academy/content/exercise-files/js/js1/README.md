# Lesson 0.1 lab: your first program

## Task
Finish `start/index.js` so it introduces you, calculates your weekly study
time, prints information about the host (Node.js) and shows the order in
which the event loop runs code.

## How to run
1. Install Node.js LTS (22 or newer) from https://nodejs.org and check it:
   `node -v`
2. Open a terminal in `javascript/js1/start` and run: `node index.js`
3. After each TODO, run the file again.
4. Compare with `javascript/js1/solution` (`node index.js` there).

## Acceptance criteria
- The first line prints your own name and city.
- A line reads `I will study 225 minutes a week.` (with the default numbers).
- A line prints the Node.js version, such as `v22.12.0`, and your platform
  (`win32`, `darwin` or `linux`).
- The last four lines appear in the order A, B, C, D, and you can explain why.

## Think about it
- Why would `process.version` fail if you pasted this code into the browser
  console, while `Math.ceil` works in both places?
- What would change in the output if you replaced the 0 in setTimeout with 1000?
