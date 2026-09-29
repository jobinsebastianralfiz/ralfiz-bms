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

// TODO(1) solution: a friendly message for each kind of problem
function messageFor(field) {
  const v = field.validity;
  if (v.valid) return '';
  if (v.valueMissing) return REQUIRED[field.name];
  if (v.typeMismatch) return 'Enter an email address like asha@example.com.';
  if (v.patternMismatch) return 'Enter a 10-digit mobile number starting with 6, 7, 8 or 9.';
  if (v.tooShort) return `Use at least ${field.minLength} characters.`;
  return field.validationMessage; // customError: our own messages
}

// TODO(2) solution: write the message next to the field
function showError(field) {
  const message = messageFor(field);
  field.setAttribute('aria-invalid', String(message !== ''));
  document.getElementById(`${field.name}-error`).textContent = message;
  return message === '';
}

// TODO(3) solution: rules HTML attributes cannot express
function runCustomChecks() {
  const { password, confirm } = form.elements;
  const pw = password.value;
  const rules = {
    length: pw.length >= 8,
    letter: /[a-z]/i.test(pw),
    digit: /\d/.test(pw),
  };
  for (const li of document.querySelectorAll('#password-rules [data-rule]')) {
    li.classList.toggle('ok', rules[li.dataset.rule]);
  }
  password.setCustomValidity(
    pw && !(rules.letter && rules.digit) ? 'Include at least one letter and one number.' : '');
  confirm.setCustomValidity(
    confirm.value && confirm.value !== pw ? 'Passwords do not match.' : '');
}

// TODO(4) solution: validate on leave, then live for touched fields
function touch(field) {
  if (!field.name) return;
  field.dataset.touched = '';
  runCustomChecks();
  showError(field);
}
form.addEventListener('focusout', (event) => touch(event.target));
form.addEventListener('change', (event) => touch(event.target)); // radios, select, checkbox
form.addEventListener('input', () => {
  runCustomChecks();
  for (const field of controls()) {
    if ('touched' in field.dataset) showError(field);
  }
});

function validateAll() {
  runCustomChecks();
  const invalid = [];
  for (const field of controls()) {
    field.dataset.touched = '';
    if (!showError(field)) invalid.push(field);
  }
  return invalid;
}

// TODO(5) and TODO(6) solution
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (submitBtn.disabled) return; // ignore double submits

  const invalid = validateAll();
  if (invalid.length) {
    const count = new Set(invalid.map((field) => field.name)).size;
    summary.textContent = `Please fix ${count} ${count === 1 ? 'field' : 'fields'} to continue.`;
    summary.hidden = false;
    invalid[0].focus();
    return;
  }
  summary.hidden = true;

  const data = Object.fromEntries(new FormData(form));
  delete data.password; // never log, echo or send passwords to a test API
  delete data.confirm;

  setBusy(true);
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`the server replied ${res.status}`);
    const saved = await res.json();
    console.log('Enrolled:', saved);
    showSuccess(saved);
  } catch (err) {
    summary.textContent = `We could not enrol you: ${err.message}. Please try again.`;
    summary.hidden = false;
  } finally {
    setBusy(false);
  }
});

document.querySelector('#again').addEventListener('click', () => {
  form.reset();
  for (const field of controls()) {
    delete field.dataset.touched;
    field.removeAttribute('aria-invalid');
    document.getElementById(`${field.name}-error`).textContent = '';
  }
  runCustomChecks();
  success.hidden = true;
  form.hidden = false;
  form.elements.fullName.focus();
});
