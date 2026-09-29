// Ralfiz lead cleaner (solution). Run: node index.js

const raw = `
Anu Thomas | anu.thomas@ralfiz.dev | +91 98470 12345 | 673001
Ravi K | ravi@ralfiz | 09847012346 | 600 042
Sara Mathew | Sara.M@Example.in | 98470-12347 | 079001
Tom | tom@shop.ralfiz.dev | 5847012348 | 560001
Meera Nair |  meera.nair@ralfiz.dev  | +91-94470-55555 | 682 016
`;

// (1) Anchored, simple, named patterns
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE = /^\+91[6-9]\d{9}$/;      // checked after normalising
const PIN = /^[1-9]\d{5}$/;

// (2) One regex handles "|", " | " and "  |  "
const parseLine = line => line.split(/\s*\|\s*/);

// (3) Normalise before validating
function normalise(lead) {
  const digits = lead.phone.replace(/[\s-]/g, '').replace(/^(?:\+91|0)/, '');
  return {
    name: lead.name.trim(),
    email: lead.email.trim().toLowerCase(),
    phone: `+91${digits}`,
    pin: lead.pin.replace(/\s/g, ''),
  };
}

function validate(lead) {
  const problems = [];
  if (lead.email.length > 254 || !EMAIL.test(lead.email)) problems.push('email');
  if (!MOBILE.test(lead.phone)) problems.push('phone');
  if (!PIN.test(lead.pin)) problems.push('PIN');
  return problems;
}

const leads = raw.trim().split('\n').map(parseLine).map(([name, email, phone, pin]) =>
  normalise({ name, email, phone, pin }));

console.log('Lead check');
for (const lead of leads) {
  const problems = validate(lead);
  const status = problems.length ? `INVALID ${problems.join(', ')}` : 'ok';
  console.log(' ', lead.name.padEnd(12), lead.phone.padEnd(14), status);
}
const valid = leads.filter(l => validate(l).length === 0);
console.log(`Valid leads: ${valid.length} of ${leads.length}`);

// (4) matchAll with named groups
const log = 'ORD-1001 paid ₹1,215.00; ORD-1002 refunded ₹240.00; ORD-1004 paid ₹2,539.00';
const entry = /(?<id>ORD-\d+) (?<status>\w+) ₹(?<amount>[\d,]+\.\d{2})/g;
let paidTotal = 0;
for (const { groups } of log.matchAll(entry)) {
  if (groups.status === 'paid') paidTotal += Number(groups.amount.replaceAll(',', ''));
}
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
console.log('Paid total:', inr.format(paidTotal));

// (5) A replacer function keeps the last 4 digits
const message = 'Call Anu on +91 98470 12345 or Meera on 94470 55555 today.';
const PHONE_IN_TEXT = /(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}/g;
const redacted = message.replace(PHONE_IN_TEXT, match => {
  const digits = match.replace(/\D/g, '');
  return `****${digits.slice(-4)}`;
});
console.log('Redacted:', redacted);

// (6) Escape special characters (RegExp.escape where the runtime has it)
function escapeRegExp(text) {
  if (typeof RegExp.escape === 'function') return RegExp.escape(text);
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
const term = 'C++ (basics)';
const courses = ['C++ (basics) batch', 'C++ advanced', 'Python (basics)'];
const re = new RegExp(escapeRegExp(term), 'i');
console.log('Search results:', courses.filter(c => re.test(c)));

// (7) Named groups in the replacement string
const DMY = /^(?<d>\d{2})\/(?<m>\d{2})\/(?<y>\d{4})$/;
const dates = ['28/09/2026', '01/10/2026'];
console.log('ISO dates:', dates.map(d => d.replace(DMY, '$<y>-$<m>-$<d>')));