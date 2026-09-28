# Lesson 12.1 lab: TaskFlow on Supabase Auth

TaskFlow moves from DummyJSON to its own Supabase project. In this lab you add
sign-up, sign-in, magic links and sign-out, with an AuthCubit that listens to
onAuthStateChange and a go_router redirect that guards every screen.

## 1. Create the Supabase project

1. Sign in at supabase.com, create a new project (for example taskflow-dev),
   choose a region near your users and save the database password somewhere safe.
2. Open the project's API keys settings and copy:
   - the Project URL (https://<project-ref>.supabase.co)
   - the publishable key (older projects and tutorials call it the anon key).
   Do NOT copy the secret key (formerly service_role) into the app. It bypasses
   Row Level Security and belongs only on servers.
3. In Authentication, open URL Configuration and add this Redirect URL:

       io.supabase.taskflow://login-callback/

4. Leave "Confirm email" on (the default). The built-in email sender is meant
   for testing and is rate limited; production projects configure their own SMTP.

## 2. Configure the Flutter app

1. Run:

       flutter pub add supabase_flutter flutter_bloc go_router

2. Create config/supabase.json (the publishable key is public by design, but
   keeping per-environment files out of Git keeps projects tidy):

       {
         "SUPABASE_URL": "https://<project-ref>.supabase.co",
         "SUPABASE_PUBLISHABLE_KEY": "<your publishable key>"
       }

3. Android: inside the MainActivity activity tag in
   android/app/src/main/AndroidManifest.xml add:

       <intent-filter>
         <action android:name="android.intent.action.VIEW" />
         <category android:name="android.intent.category.DEFAULT" />
         <category android:name="android.intent.category.BROWSABLE" />
         <data android:scheme="io.supabase.taskflow" android:host="login-callback" />
       </intent-filter>

4. iOS: in ios/Runner/Info.plist add:

       <key>CFBundleURLTypes</key>
       <array>
         <dict>
           <key>CFBundleTypeRole</key>
           <string>Editor</string>
           <key>CFBundleURLSchemes</key>
           <array>
             <string>io.supabase.taskflow</string>
           </array>
         </dict>
       </array>

5. Copy start/lib/main.dart over lib/main.dart and run:

       flutter run --dart-define-from-file=config/supabase.json

## Tasks

- TODO(1) AuthRepository calls signInWithPassword, signUp, signInWithOtp and signOut.
- TODO(2) AuthCubit starts in SessionUnknown and follows onAuthStateChange.
- TODO(3) The go_router redirect guards /tasks and moves signed-in users off /sign-in.
- TODO(4) AuthException messages appear under the password field.
- TODO(5) The logout button signs out through the cubit.

## Acceptance criteria

- A fresh install opens on "Sign in to TaskFlow", not on the tasks screen.
- Signing in with a wrong password shows "Invalid login credentials" under the password field.
- Create account with a new email shows the SnackBar "Check your email to confirm your account."
  and the user appears in Authentication > Users as waiting for verification.
- After confirming (or signing in with a confirmed user) the app shows "Signed in as <email>".
- Fully restart the app: it goes straight to the tasks screen, because the session was persisted.
- The logout button returns to the sign-in screen, and a restart stays signed out.
- Email me a magic link shows "Magic link sent to <email>"; opening the link on the device signs you in.