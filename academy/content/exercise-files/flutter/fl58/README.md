# Lesson 11.1 lab: TaskFlow secure session

You will move TaskFlow's tokens out of plain storage into the platform keystore,
read build settings from a config file, and stop credentials leaking into logs.
The app signs in to https://dummyjson.com with the public demo user
emilys / emilyspass.

## Setup

1. In your TaskFlow project run:
       flutter pub add dio flutter_secure_storage
   (or copy pubspec.yaml from this folder and run flutter pub get).
2. Android: open android/app/src/main/AndroidManifest.xml and set
   android:allowBackup="false" on the <application> tag, so Keystore-bound
   data is not restored onto another device (where the key no longer exists).
3. Create config/dev.json in the project root:
       { "API_BASE_URL": "https://dummyjson.com", "ENV": "dev" }
   and config/staging.json with "ENV": "staging".
   These files hold settings, not secrets. Everything in them ends up inside the app.
4. Copy start/lib/main.dart over lib/main.dart and run
       flutter run --dart-define-from-file=config/dev.json
   on an emulator or device (secure storage is a plugin, so DartPad cannot run it).

## Tasks

- TODO(1) AppConfig reads API_BASE_URL and ENV with String.fromEnvironment.
- TODO(2) to TODO(4) TokenStorage writes, reads and deletes both tokens with FlutterSecureStorage.
- TODO(5) _redact replaces authorization, password, accessToken and refreshToken values with ***.
- TODO(6) ApiClient adds the Bearer header from TokenStorage and logs only in debug builds.

## Acceptance criteria

- After **Sign in as emilys**, the Access token row shows the first 6 characters followed by ... (N chars), never the whole token.
- **Who am I?** shows Emily Johnson.
- Stop the app completely and start it again: the Access token row still shows the masked token.
- **Sign out** sets the Access token row back to none, and **Who am I?** then shows Server said 401 (or another 4xx code).
- The debug console shows password: *** and accessToken: ***, and no full token appears anywhere in the log.
- Running with --dart-define-from-file=config/staging.json shows staging | https://dummyjson.com.

## Stretch: an obfuscated release build

    flutter build apk --release --obfuscate --split-debug-info=build/debug-info

Keep the build/debug-info folder (do not commit it to a public repo). You need it to
read crash stack traces later with flutter symbolize. Then unzip the APK, find
lib/arm64-v8a/libapp.so (your compiled Dart code) and run strings on it, searching
for dummyjson: config values are still in plain sight, which is exactly why no
secret may ever go into config/*.json.