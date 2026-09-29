// Lab 1.5 - Grade Book (starter)
// Run: node index.js
const students = require('./students.json');

const PASS_MARK = 40;

// TODO(1): guard clauses for invalid scores, then an if / else if ladder.
function gradeFor(score) {
  return '?';
}

// TODO(2): for...of over Object.values(marks); skip null with continue.
// Return null when there are no marks at all.
function average(marks) {
  return null;
}

// TODO(3): switch (grade) with grouped cases:
// A+ and A -> 'Excellent', B and C -> 'Good', D -> 'Needs practice',
// F -> 'Needs support', default -> '-'
function remarkFor(grade) {
  return '-';
}

console.log('Name'.padEnd(8) + 'Avg'.padStart(6) + '  Grade  Remark');
console.log('-'.repeat(36));

const counts = { 'A+': 0, A: 0, B: 0, C: 0, D: 0, F: 0 };
let topper = null;
let sum = 0;
let graded = 0;

// TODO(4): loop over students with for...of. For each one, work out the
// average. If it is null print the name and 'Absent' and continue.
// Otherwise print name, avg.toFixed(1), grade and remark in columns.
// TODO(5): inside the same loop, update topper ({ name, avg }), counts[grade],
// sum and graded.
for (const student of students) {
  console.log(student.name.padEnd(8) + '...'.padStart(6));
}

console.log('-'.repeat(36));
console.log('Topper:', topper);
console.log('Class average:', graded ? (sum / graded).toFixed(1) : 'n/a');

// TODO(6): for...in over counts, print grade, '#'.repeat(count) and count.

// TODO(7): nested loops: find the first student with any mark below
// PASS_MARK (ignore null). Use break to stop both loops early.
let needsSupport = null;
console.log('First student who needs support:', needsSupport ?? 'none');
