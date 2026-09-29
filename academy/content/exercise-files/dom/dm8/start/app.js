const form = document.querySelector('#enrol');
const summary = document.querySelector('#summary');
const submitBtn = document.querySelector('#submit');
const success = document.querySelector('#success');
const API_URL = 'https://jsonplaceholder.typicode.com/users';

// Messages for empty required fields, by field name
const REQUIRED = {
  fullName: 'Enter your full name.',
  email: 'Enter your email address.',
  phone: 'Enter your mobile number.',
  course: 'Choose a course.',
  batch: 'Choose a batch.',
  password: 'Create a password.',
  confirm: 'Type your password again.',
  terms: 'Please accept the course terms.',
};

// Every control that takes part in validation (the button has no name)
const controls = () => [...form.elements].filter((el) => el.willValidate && el.name);

function setBusy(busy) {
  submitBtn.disabled = busy;
  submitBtn.textContent = busy ? 'Enrolling…' : 'Enrol now';
}

function showSuccess(student) {
  const rows = [
    ['Student', student.fullName],
    ['Email', student.email],
    ['Course', form.elements.course.selectedOptions[0].text],
    ['Batch', student.batch],
    ['Enrolment ID', `#${student.id}`],
  ];
  const details = document.querySelector('#success-details');
  details.replaceChildren();
  for (const [term, value] of rows) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = term;
    dd.textContent = value; // textContent: user input is never parsed as HTML
    details.append(dt, dd);
  }
  const first = student.fullName.split(' ')[0];
  document.querySelector('#success-title').textContent = `You are enrolled, ${first}!`;
  form.hidden = true;
  success.hidden = false;
  success.focus();
}

// TODO(1): return '' when field.validity.valid is true. Otherwise return a message:
// valueMissing -> REQUIRED[field.name], typeMismatch -> an email hint,
// patternMismatch -> the mobile number rule, tooShort -> "Use at least N characters.",
// anything else (your custom errors) -> field.validationMessage.
function messageFor(field) {
  return '';
}

// TODO(2): write messageFor(field) into the element with id `${field.name}-error`
// (use textContent), set aria-invalid to "true" or "false", and return true if valid.
function showError(field) {
  return true;
}

// TODO(3): tick the #password-rules items (length 8+, a letter, a digit) by toggling
// the ok class, then use setCustomValidity on password (needs a letter and a digit)
// and confirm (must match). Pass '' when a rule passes, or the field stays invalid.
function runCustomChecks() {}

// TODO(4): on focusout and change, mark the field as touched (field.dataset.touched = '')
// and validate it. On input, run the custom checks and re-validate touched fields only.

function validateAll() {
  runCustomChecks();
  return controls().filter((field) => !showError(field));
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  // TODO(5): call validateAll(). If anything is invalid, show "Please fix N fields to
  // continue." in #summary (count unique names), unhide it and focus the first bad field.

  // TODO(6): read the form with FormData + Object.fromEntries, delete password and
  // confirm, POST it as JSON to API_URL with setBusy(true), check res.ok, then call
  // showSuccess(await res.json()). On errors, show a message in #summary.
  // Always call setBusy(false) in finally.
  console.log('TODO(5): validate the form, then TODO(6): send it');
});

document.querySelector('#again').addEventListener('click', () => {
  form.reset();
  success.hidden = true;
  form.hidden = false;
});
