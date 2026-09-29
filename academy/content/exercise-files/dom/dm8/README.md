# Lab 3.1 - Ralfiz Academy: enrolment form with validation

Build the validation and submit logic for a course enrolment form:

- built-in rules from HTML attributes (`required`, `type="email"`, `pattern`,
  `minlength`) read through each field's `validity` object
- custom rules with `setCustomValidity`: the password needs a letter and a number,
  and the confirm field must match
- your own accessible error messages (the form has `novalidate`): text in
  `#<name>-error`, linked with `aria-describedby`, plus `aria-invalid`
- validation when a field loses focus, then live while typing in touched fields
- on submit: an error summary and focus on the first invalid field, or a POST
  to JSONPlaceholder with a loading state and a success panel

## Run it

Open the `start` folder in VS Code with **Live Server**, or run `npx serve` in it
and open the address it prints. The HTML and CSS are finished, and `app.js` already
has `REQUIRED`, `controls()`, `setBusy()` and `showSuccess()`. Complete
TODO(1)-TODO(6) in `app.js`. The finished version is in `solution`.

## Acceptance criteria

1. Pressing **Enrol now** on the empty form shows an error under every field,
   the summary reads "Please fix 8 fields to continue." and focus moves to Full name.
2. Typing `12345` in Mobile number and leaving the field shows the mobile number
   message; the error disappears as soon as the number is valid.
3. The password checklist ticks live. `abcdefgh` shows "Include at least one letter
   and one number."; a different confirm value shows "Passwords do not match."
4. A valid form shows **Enrolling…** on the disabled button, then the success panel
   with the student details and the enrolment ID returned by the API.
5. With the network offline (DevTools > Network > Offline), submitting shows the
   "We could not enrol you" message and the button works again.
6. The password is never logged or sent.
