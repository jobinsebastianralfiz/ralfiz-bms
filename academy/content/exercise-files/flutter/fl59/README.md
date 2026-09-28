# Lesson 11.2 lab: TaskFlow network and app security

The starter app runs, but it trusts everything: plain HTTP goes through, any
link opens a task, and the lock screen unlocks without asking anyone. You will
fix all three.

## Setup

1. Run:

       flutter pub add dio local_auth

   (or copy pubspec.yaml from this folder and run flutter pub get).

2. Android, android/app/src/main/kotlin/.../MainActivity.kt: local_auth needs a
   FlutterFragmentActivity.

       import io.flutter.embedding.android.FlutterFragmentActivity

       class MainActivity : FlutterFragmentActivity()

3. Android, android/app/src/main/AndroidManifest.xml: add the permission above
   the application tag, and turn cleartext traffic off for platform code
   (WebViews, native SDKs):

       <uses-permission android:name="android.permission.USE_BIOMETRIC"/>
       <application
           android:usesCleartextTraffic="false"
           ... >

   If the build complains, check that your LaunchTheme's parent is an AppCompat
   theme and that minSdk in android/app/build.gradle(.kts) meets the plugin's
   current requirement (see the local_auth page on pub.dev).

4. iOS, ios/Runner/Info.plist: explain Face ID to the user. Do not add
   NSAllowsArbitraryLoads; App Transport Security should stay on.

       <key>NSFaceIDUsageDescription</key>
       <string>TaskFlow uses Face ID to unlock your tasks.</string>

5. Emulator: set a screen lock (PIN) in Settings, then add a fingerprint.
   In the Android emulator's extended controls (the ... button) open
   Fingerprint and press Touch sensor when the prompt appears.
   On the iOS Simulator use Features > Face ID > Enrolled, then Matching Face.

6. Copy start/lib/main.dart over lib/main.dart and run it.

## Tasks

- TODO(1) HttpsOnlyInterceptor rejects every non-HTTPS request.
- TODO(2) parseTaskLink accepts only https://taskflow.example.com/tasks/<digits>.
- TODO(3) and TODO(4) _unlock uses local_auth and maps LocalAuthException codes to messages.
- TODO(5) the app locks again when it goes to the background.

## Acceptance criteria

- Launch shows "TaskFlow is locked". Unlock shows the system prompt; cancelling it shows "Unlock cancelled." and the app stays locked.
- A successful fingerprint, face or device PIN opens "Security checks".
- "Fetch over HTTPS" shows "Loaded 3 todos over HTTPS".
- "Try plain HTTP" shows "Blocked insecure URL: http://dummyjson.com/todos?limit=3" and no request leaves the device.
- The link list shows "Open task 42", "Rejected: Unknown page" and "Rejected: Unknown link source".
- Press Home, then return to the app: it is locked again.

## Remember

The lock screen proves that someone who can unlock this phone is holding it.
It does not prove to the TaskFlow server who they are. The server still checks
the access token on every request.