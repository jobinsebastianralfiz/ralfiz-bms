// Lesson 0.1 - Hello Flutter (STARTER)
// Paste this whole file into dartpad.dev and press Run.
// It compiles as it is. Complete TODO(1) to TODO(5), running after each one.
import 'package:flutter/material.dart';

void main() {
  runApp(const HelloApp());
}

class HelloApp extends StatelessWidget {
  const HelloApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      // TODO(1): Change the seed colour to your favourite, e.g. Colors.teal.
      //          Watch how every colour in the app follows it.
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
      // TODO(5): Add a darkTheme built with the same seed and
      //          brightness: Brightness.dark, then set
      //          themeMode: ThemeMode.dark to try it.
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // TODO(2): Put your own name in the app bar title.
      appBar: AppBar(title: const Text('Hello Flutter')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.flutter_dash, size: 64),
            const SizedBox(height: 12),
            const Text('Everything here is a widget'),
            // TODO(3): Add const SizedBox(height: 8) and a Text with your city,
            //          styled with Theme.of(context).textTheme.titleMedium.
            // TODO(4): Add const SizedBox(height: 24) and a FilledButton.icon
            //          with icon Icons.waving_hand and label 'Say hello'.
            //          Its onPressed should call debugPrint('Hello from <your name>!').
          ],
        ),
      ),
    );
  }
}