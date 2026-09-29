// Lesson 0.1: your first program (solution)
// Run it from this folder with:  node index.js

const learnerName = 'Asha';
const city = 'Perinthalmanna';

const daysPerWeek = 5;
const minutesPerDay = 45;

console.log(`Hello, I am ${learnerName} from ${city}.`);

const weeklyMinutes = daysPerWeek * minutesPerDay;
console.log(`I will study ${weeklyMinutes} minutes a week.`);

const lessons = 31;
const weeks = Math.ceil(lessons / daysPerWeek);
console.log(`At one lesson a day I finish the JavaScript track in ${weeks} weeks.`);

// process is a Node.js host object: it does not exist in browsers
console.log('Running on Node.js', process.version, 'on', process.platform);

// The event loop: the script finishes first, then microtasks, then tasks
console.log('A: start');
setTimeout(() => console.log('D: timer'), 0);
Promise.resolve().then(() => console.log('C: promise'));
console.log('B: end');
