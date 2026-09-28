# Lesson 7.4 lab: Chat app, part 1 - Firebase setup and sign-in

## 1. Create the Firebase project (once)
1. Open the Firebase console (console.firebase.google.com) and add a
   project named, for example, ralfiz-chat. Google Analytics is optional.
2. In Build > Authentication, click Get started, open the Sign-in method
   tab and enable Email/Password.

## 2. Install the tools (once per computer)
    npm install -g firebase-tools        # the Firebase CLI (needs Node.js)
    firebase login
    dart pub global activate flutterfire_cli

If flutterfire is "not found", add the pub cache bin folder to your PATH as
the activate command tells you.

## 3. Connect the Flutter app
    flutter create chat_app
    cd chat_app
    flutter pub add firebase_core firebase_auth
    flutterfire configure

Pick your project and the platforms you will run (Android, iOS...).
This writes lib/firebase_options.dart and the platform config files.
Run flutterfire configure again whenever you add a platform or a new
Firebase project. If the Android build asks for a higher minSdk, raise it in
android/app/build.gradle (or build.gradle.kts) as the error message says.

## 4. Code
Copy start/lib/main.dart to lib/main.dart and complete TODO(1) to TODO(6).
Compare with solution/lib/main.dart when you are done.

## Acceptance criteria
- A new user can create an account; the app switches to HomePage and shows
  "Signed in as <email>". The user appears in the console under
  Authentication > Users.
- Signing out returns to the sign-in page. Signing in again works.
- A wrong password shows "Wrong email or password." under the password field.
- Registering an existing email shows "An account already exists for that email."
- A 5-character password shows the weak password message.
- After a full restart, a signed-in user goes straight to HomePage.
