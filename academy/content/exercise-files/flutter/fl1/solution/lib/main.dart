// Lesson 0.1 - Hello Flutter (SOLUTION)
// Runs in dartpad.dev or as lib/main.dart in any Flutter project.
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
      // TODO(1) done: a new seed colour drives the whole Material 3 palette.
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
      ),
      // TODO(5) done: the same seed, generated for a dark background.
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.teal,
          brightness: Brightness.dark,
        ),
      ),
      themeMode: ThemeMode.dark,
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // TODO(2) done
      appBar: AppBar(title: const Text('Asha Menon')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.flutter_dash, size: 64),
            const SizedBox(height: 12),
            const Text('Everything here is a widget'),
            // TODO(3) done: not const, because it reads the theme at build time.
            const SizedBox(height: 8),
            Text(
              'Kochi, Kerala',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            // TODO(4) done: the button receives a function to call later.
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => debugPrint('Hello from Asha!'),
              icon: const Icon(Icons.waving_hand),
              label: const Text('Say hello'),
            ),
          ],
        ),
      ),
    );
  }
}