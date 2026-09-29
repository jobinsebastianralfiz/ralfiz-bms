// Lab 1.5 - Grade Book (solution)
// Run: node index.js
const students = require('./students.json');

const PASS_MARK = 40;

function gradeFor(score) {
  if (typeof score !== 'number' || !Number.isFinite(score)) return 'Invalid';
  if (score < 0 || score > 100) return 'Invalid';
  if (score >= 90) return 'A+';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  if (score >= 50) return 'D';
  return 'F';
}

function average(marks) {
  let total = 0;
  let count = 0;
  for (const mark of Object.values(marks)) {
    if (mark === null) continue;
    total += mark;
    count++;
  }
  return count === 0 ? null : total / count;
}

function remarkFor(grade) {
  switch (grade) {
    case 'A+':
    case 'A':
      return 'Excellent';
    case 'B':
    case 'C':
      return 'Good';
    case 'D':
      return 'Needs practice';
    case 'F':
      return 'Needs support';
    default:
      return '-';
  }
}

console.log('Name'.padEnd(8) + 'Avg'.padStart(6) + '  Grade  Remark');
console.log('-'.repeat(36));

const counts = { 'A+': 0, A: 0, B: 0, C: 0, D: 0, F: 0 };
let topper = null;
let sum = 0;
let graded = 0;

for (const student of students) {
  const avg = average(student.marks);
  if (avg === null) {
    console.log(student.name.padEnd(8) + 'Absent'.padStart(6));
    continue;
  }
  const grade = gradeFor(avg);
  console.log(
    student.name.padEnd(8) + avg.toFixed(1).padStart(6) +
    '  ' + grade.padEnd(5) + '  ' + remarkFor(grade)
  );
  if (topper === null || avg > topper.avg) {
    topper = { name: student.name, avg };
  }
  counts[grade]++;
  sum += avg;
  graded++;
}

console.log('-'.repeat(36));
console.log(`Topper: ${topper.name} (${topper.avg.toFixed(1)})`);
console.log(`Class average: ${(sum / graded).toFixed(1)} over ${graded} graded students`);

console.log('\nGrade chart');
for (const grade in counts) {
  console.log(grade.padEnd(3), '#'.repeat(counts[grade]), counts[grade]);
}

let needsSupport = null;
for (const student of students) {
  for (const [subject, mark] of Object.entries(student.marks)) {
    if (mark !== null && mark < PASS_MARK) {
      needsSupport = `${student.name} (${subject}: ${mark})`;
      break;
    }
  }
  if (needsSupport !== null) break;
}
console.log('\nFirst student who needs support:', needsSupport ?? 'none');
