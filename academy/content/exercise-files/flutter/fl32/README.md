# Lab 5.3: Event Registration form

Build the registration desk app for "Flutter Meetup Kochi".

## Setup
1. flutter create event_registration   (the test file imports package:event_registration)
2. Replace lib/main.dart with start/lib/main.dart.
3. Copy test/validators_test.dart into the project's test folder (delete the default widget_test.dart).
No extra packages are needed: FilteringTextInputFormatter comes from package:flutter/services.dart.

## Tasks
- TODO(1) Wrap the fields in a Form with _formKey. Start with AutovalidateMode.disabled and
  switch to onUserInteraction after the first failed submit.
- TODO(2) Write validateName, validateEmail and validatePhone (return a message or null).
- TODO(3) Wire the validators. Email uses TextInputType.emailAddress; phone uses
  TextInputType.phone with digitsOnly and a 10 character limit. Name and email use
  TextInputAction.next; phone uses done and submits on the keyboard action.
- TODO(4) Add a FormField<bool> for the code-of-conduct checkbox.
- TODO(5) Implement _submit(): validate, show a spinner in the button for one second,
  show the confirmation dialog, then clear the form and focus Full name.
- TODO(6) Dispose every controller and the focus node.

## Acceptance criteria
- Tapping Register on the empty form shows: Enter your name, Enter your email,
  Enter a 10-digit phone number and Please accept the code of conduct.
- After that first attempt, each error disappears as soon as the field becomes valid.
- The phone field refuses letters and stops at 10 digits.
- A valid form shows a spinner, then a dialog "You are in!" with "Asha Nair · Student ticket".
- After Done, all fields are empty and the cursor is in Full name.
- flutter test reports All tests passed!
