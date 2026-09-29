// Ralfiz lead cleaner. Run: node index.js
// Partners paste leads as "name | email | phone | PIN". Clean and validate them.

const raw = `
Anu Thomas | anu.thomas@ralfiz.dev | +91 98470 12345 | 673001
Ravi K | ravi@ralfiz | 09847012346 | 600 042
Sara Mathew | Sara.M@Example.in | 98470-12347 | 079001
Tom | tom@shop.ralfiz.dev | 5847012348 | 560001
Meera Nair |  meera.nair@ralfiz.dev  | +91-94470-55555 | 682 016
`;

// TODO(1): anchored patterns. email: loose shape; mobile: optional +91 or 0,
// then 10 digits starting 6-9; pin: 6 digits, first digit 1-9.
const EMAIL = /./;
const MOBILE = /./;
const PIN = /./;

// TODO(2): split each non-empty line on a pipe with any spaces around it.
function parseLine(line) {
  return line.split('|');
}

// TODO(3): normalise: email trimmed + lowercased; phone and PIN without
// spaces or dashes. Phone should end up as +91 followed by 10 digits.
function normalise(lead) {
  return lead;
}

function validate(lead) {
  const problems = [];
  if (!EMAIL.test(lead.email)) problems.push('email');
  if (!MOBILE.test(lead.phone)) problems.push('phone');
  if (!PIN.test(lead.pin)) problems.push('PIN');
  return problems;
}

const leads = raw.trim().split('\n').map(parseLine).map(([name, email, phone, pin]) =>
  normalise({ name, email, phone, pin }));

console.log('Lead check');
for (const lead of leads) {
  const problems = validate(lead);
  const status = problems.length ? 'INVALID ' + problems.join(', ') : 'ok';
  console.log(' ', String(lead.name).padEnd(12), String(lead.phone).padEnd(14), status);
}

// TODO(4): use matchAll with named groups (id, amount) to total paid orders.
const log = 'ORD-1001 paid ₹1,215.00; ORD-1002 refunded ₹240.00; ORD-1004 paid ₹2,539.00';
let paidTotal = 0;
console.log('Paid total:', paidTotal);

// TODO(5): redact phone numbers, keeping only the last 4 digits (****2345).
const message = 'Call Anu on +91 98470 12345 or Meera on 94470 55555 today.';
console.log('Redacted:', message);

// TODO(6): escape the search term so special characters are literal.
function escapeRegExp(text) {
  return text;
}
const term = 'C++ (basics)';
const courses = ['C++ (basics) batch', 'C++ advanced', 'Python (basics)'];
let found = [];
try {
  const re = new RegExp(escapeRegExp(term), 'i');
  found = courses.filter(c => re.test(c));
} catch (err) {
  console.log('Search failed:', err.message);
}
console.log('Search results:', found);

// TODO(7): convert "28/09/2026" style dates to ISO "2026-09-28" with named groups.
const dates = ['28/09/2026', '01/10/2026'];
console.log('ISO dates:', dates);