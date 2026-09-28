# Lab 0.1 - Hello Flutter

Your first contact with Flutter code. No install needed: you run everything in
**DartPad** (https://dartpad.dev), which runs Flutter apps in the browser.

## Files

| File | What it is |
|---|---|
| start/lib/main.dart | A small app that compiles and runs. It has TODO(1) to TODO(5). |
| solution/lib/main.dart | One possible finished version. Look only after trying. |

## Task

1. Open DartPad, delete the sample code and paste start/lib/main.dart. Press **Run**.
2. Complete the TODOs in order and run again after each one:
   - **TODO(1)** Change the seed colour (for example Colors.teal).
   - **TODO(2)** Put your name in the app bar.
   - **TODO(3)** Add your city under the text, styled with textTheme.titleMedium.
   - **TODO(4)** Add a FilledButton.icon that prints a greeting with debugPrint.
   - **TODO(5)** Add a dark theme from the same seed and switch themeMode to dark.

## Acceptance criteria

- The app bar shows your name instead of "Hello Flutter".
- The app bar, the background and the button use colours generated from your seed.
- Tapping **Say hello** prints Hello from <your name>! in DartPad's console.
- With themeMode: ThemeMode.dark the background is dark and the text is light.
- You did not write a single colour by hand except the seed.

## Think about it

- Which widgets could stay const, and why can the city Text not be const?
- Count the widgets in the tree from MaterialApp down to the button. Everything is a widget.
- What would you need to change for the button to show a message on screen
  instead of the console? (You will learn SnackBars in lesson 2.5.)