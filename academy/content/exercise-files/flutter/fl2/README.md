# Lab 0.2 - Set up your machine and run Tap Counter

## Part A - Setup checklist

Follow the install guide for your operating system on docs.flutter.dev.
Tick each line when it works. Run flutter doctor after every step.

- [ ] Flutter SDK installed in a simple path (for example C:\dev\flutter or ~/development/flutter)
- [ ] flutter --version prints a stable channel version in a **new** terminal
- [ ] Editor ready: VS Code + Flutter extension, or Android Studio + Flutter plugin
- [ ] Android Studio installed (for the Android SDK and emulator), licences accepted with
      flutter doctor --android-licenses
- [ ] One virtual device created in Device Manager, or a phone with USB debugging on
- [ ] flutter devices lists at least one device (emulator, phone, Chrome or desktop)
- [ ] Mac only (optional): Xcode installed and the iOS Simulator opens

Paste the summary lines of your flutter doctor here:

    (paste here)

## Part B - First project

    flutter create --org com.example hello_flutter
    cd hello_flutter
    flutter run

1. Tap **+** three times.
2. Change the text in lib/main.dart and save (or press r). The counter should still show 3.
3. Press R (hot restart). The counter goes back to 0.
4. Write down in one sentence why the two behave differently.

## Part C - Tap Counter

Replace lib/main.dart with start/lib/main.dart and complete TODO(1) to TODO(4).

## Acceptance criteria

- flutter doctor shows a tick for Flutter and for at least one target platform.
- The app bar says **Tap Counter** and uses a green colour scheme.
- The body reads **Taps so far:** with the number below it.
- The **-1** button is greyed out (disabled) at 0 and never makes the count negative.
- **Reset** sets the count to 0.
- flutter analyze reports No issues found!