# js12 lab: Student Records Analyser

A Ralfiz Academy coordinator needs quick answers about one batch. Load
`students.json` and answer every question with **array methods** (no
`for` loops except where the file says so).

## Run it

```bash
cd javascript/js12/start
node index.js
```

Node.js 22 or newer. `package.json` in the lab folder sets `"type": "module"`,
so `index.js` can use `import` (you will study modules properly in js23).
The data is read from `../students.json`.

## Tasks

Complete `TODO(1)` to `TODO(7)` in `start/index.js`: averages (`map`),
pass list (`filter` + `every`), top 3 (`toSorted` + `slice`), class and batch
averages (`reduce`), questions (`find`, `findLast`, `some`), highest mark and
subject toppers (`flatMap`, `reduce`), and a ranked table (`console.table`
with destructuring).

## Acceptance criteria

- `Students loaded: 12` and `Passed: 9 of 12`.
- Top 3: Fathima Nazar (91.7), Nikhil Varghese (91), Aisha Rahman (85).
- `Class average: 71.2`; batch A averages 68.3 and batch B 74.1 (6 students each).
- First mark under 40: Arjun Das. Last attendance under 80%: Ananya Joseph.
- `Highest single mark: 95`; toppers: JavaScript Fathima Nazar (92), DOM Nikhil Varghese (94), SQL Fathima Nazar (95).
- The original records do not gain an `average` property.

Compare with `solution/index.js` when you are done.