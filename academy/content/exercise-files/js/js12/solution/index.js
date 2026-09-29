// js12 lab: Student Records Analyser. Run with: node index.js
import { readFileSync } from 'node:fs';

const students = JSON.parse(
  readFileSync(new URL('../students.json', import.meta.url), 'utf8'),
);
const SUBJECTS = ['JavaScript', 'DOM', 'SQL'];
const round1 = (n) => Math.round(n * 10) / 10;
const average = (nums) => nums.reduce((a, b) => a + b, 0) / nums.length;

console.log('Students loaded:', students.length);

// 1. map + spread: a new object per student, originals untouched
const withAvg = students.map((s) => ({ ...s, average: round1(average(s.marks)) }));

// 2. filter + every
const isPassing = (s) => s.marks.every((m) => m >= 40) && s.attendance >= 0.75;
const passed = withAvg.filter(isPassing);
console.log(`Passed: ${passed.length} of ${students.length}`);
console.log('Needs help:', withAvg.filter((s) => !isPassing(s)).map((s) => s.name));

// 3. toSorted + slice
const ranked = withAvg.toSorted((a, b) => b.average - a.average);
const top3 = ranked.slice(0, 3);
console.log('Top 3:', top3.map((s) => `${s.name} (${s.average})`).join(', '));

// 4a. reduce to one number
const classAverage = round1(
  withAvg.reduce((sum, s) => sum + s.average, 0) / withAvg.length,
);
console.log('Class average:', classAverage);

// 4b. reduce to an object, then finish the averages
const totals = withAvg.reduce((acc, s) => {
  acc[s.batch] ??= { count: 0, sum: 0 };
  acc[s.batch].count += 1;
  acc[s.batch].sum += s.average;
  return acc;
}, {});
const byBatch = Object.fromEntries(
  Object.entries(totals).map(([batch, { count, sum }]) =>
    [batch, { count, average: round1(sum / count) }]),
);
console.log('By batch:', byBatch);

// 5. find, findLast, some
const firstUnder40 = students.find((s) => s.marks.some((m) => m < 40));
const lastLowAttendance = students.findLast((s) => s.attendance < 0.8);
const anyone95 = students.some((s) => s.marks.some((m) => m >= 95));
console.log('First mark under 40:', firstUnder40?.name);
console.log('Last attendance under 80%:', lastLowAttendance?.name);
console.log('Anyone scored 95 or more:', anyone95);

// 6a. flatMap + spread into Math.max
const highest = Math.max(...students.flatMap((s) => s.marks));
console.log('Highest single mark:', highest);

// 6b. map over subjects, reduce over students
const toppers = SUBJECTS.map((subject, i) => {
  const best = students.reduce((a, b) => (b.marks[i] > a.marks[i] ? b : a));
  return `${subject}: ${best.name} (${best.marks[i]})`;
});
console.log('Subject toppers:', toppers);

// 7. destructuring in the callback
console.table(ranked.map(({ name, batch, average: avg }, i) =>
  ({ rank: i + 1, name, batch, average: avg })));

console.log('Originals unchanged:', !('average' in students[0]));