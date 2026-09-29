// js12 lab: Student Records Analyser. Run with: node index.js
import { readFileSync } from 'node:fs';

const students = JSON.parse(
  readFileSync(new URL('../students.json', import.meta.url), 'utf8'),
);
const SUBJECTS = ['JavaScript', 'DOM', 'SQL'];
const round1 = (n) => Math.round(n * 10) / 10;
const average = (nums) => nums.reduce((a, b) => a + b, 0) / nums.length;

console.log('Students loaded:', students.length);

// TODO(1): map each student to a COPY with an extra field
// average: round1(average(s.marks)). Do not change the originals.
const withAvg = students;

// TODO(2): passed = all marks >= 40 AND attendance >= 0.75 (filter + every)
const passed = [];
console.log(`Passed: ${passed.length} of ${students.length}`);

// TODO(3): top 3 by average, highest first (toSorted + slice)
const top3 = [];
console.log('Top 3:', top3.map((s) => `${s.name} (${s.average})`).join(', '));

// TODO(4a): class average of the student averages (reduce), 1 decimal place
const classAverage = 0;
console.log('Class average:', classAverage);

// TODO(4b): per-batch summary with reduce: { A: { count, average }, B: {...} }
const byBatch = {};
console.log('By batch:', byBatch);

// TODO(5): answer with find, findLast and some
const firstUnder40 = undefined;   // first student with any mark < 40
const lastLowAttendance = undefined; // last student with attendance < 0.8
const anyone95 = false;           // did anyone score 95 or more in a subject?
console.log('First mark under 40:', firstUnder40?.name);
console.log('Last attendance under 80%:', lastLowAttendance?.name);
console.log('Anyone scored 95 or more:', anyone95);

// TODO(6a): highest single mark across all students (flatMap + Math.max)
const highest = 0;
console.log('Highest single mark:', highest);

// TODO(6b): for each subject, the student with the best mark (map + reduce)
const toppers = [];
console.log('Subject toppers:', toppers);

// TODO(7): console.table of rank, name, batch and average, best first.
// Use destructuring in the callback: ({ name, batch, average }, i) => ...

console.log('Originals unchanged:', !('average' in students[0]));