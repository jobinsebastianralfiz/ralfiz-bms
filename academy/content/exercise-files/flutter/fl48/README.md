# Lesson 8.5 lab: release the Notes app

You prepare a small Notes app for release: identity, icons, version,
dev/prod configuration and a signed Android App Bundle. Store upload is
optional (it needs a Google Play developer account).

## Setup

    flutter create --org academy.ralfiz notes
    cd notes

The --org flag makes the ids academy.ralfiz.notes instead of com.example.notes.
Copy pubspec.yaml from this folder (keep your project name if it differs) and
replace lib/main.dart with start/lib/main.dart. Then:

    flutter pub get

## Tasks

1. Code (TODOs in lib/main.dart)
   - TODO(1) Read FLAVOR, API_URL and APP_VERSION with String.fromEnvironment
     (defaults: dev, https://jsonplaceholder.typicode.com, dev build).
   - TODO(2) Title "Notes DEV" when not prod; orange DEV BUILD strip when not prod.
   - TODO(3) Show the flavor and API in two ListTiles.
   - TODO(4) Info button opens showAboutDialog with applicationVersion.

2. Icons
   - Put a square 1024 x 1024 PNG at assets/icon/icon.png (any simple logo).
   - Run: dart run flutter_launcher_icons
   - Check the icon on an emulator home screen.

3. Version
   - pubspec.yaml already says version: 1.0.0+1. Keep it for the first build.

4. Dev and prod runs

       flutter run --dart-define=FLAVOR=dev
       flutter run --release --dart-define=FLAVOR=prod --dart-define=API_URL=https://api.example.com --dart-define=APP_VERSION=1.0.0+1

5. Android signing
   - Create an upload keystore (macOS/Linux):

         keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -storetype JKS -keysize 2048 -validity 10000 -alias upload

   - Create android/key.properties (and add it to .gitignore):

         storePassword=<your password>
         keyPassword=<your password>
         keyAlias=upload
         storeFile=/Users/<you>/upload-keystore.jks

   - In android/app/build.gradle.kts load key.properties and add the release
     signingConfig exactly as shown in the lesson (section 4).
   - Build:

         flutter build appbundle --dart-define=FLAVOR=prod --dart-define=APP_VERSION=1.0.0+1

6. Optional: upload the .aab to an internal testing track in the Play Console
   and install it from the tester link.

7. Next update: change the build to 1.0.1+2 and build again.

## Acceptance criteria

- A dev run shows the orange DEV BUILD strip, "Flavor: dev" and the
  jsonplaceholder API.
- The prod release run has no strip and shows https://api.example.com.
- The About dialog shows 1.0.0+1 in the prod build and "dev build" in a plain run.
- The emulator home screen shows your icon instead of the Flutter logo.
- flutter build appbundle succeeds and creates an .aab under
  build/app/outputs/bundle/release/.
- git status does not list key.properties or any .jks file.
