// Lesson 0.2 - Tap Counter (STARTER)
// Replace lib/main.dart in your new hello_flutter project with this file.
// It is a trimmed copy of the flutter create template and runs as it is.
// Complete TODO(1) to TODO(4), using hot reload (save or press r) after each.
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      // TODO(1): Change both titles to 'Tap Counter' and the seed to Colors.green.
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }

  // TODO(2): Add _decrementCounter (never below 0) and _reset (back to 0).
  //          Both must change _counter inside setState.

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // TODO(3): Change this text to 'Taps so far:'.
            const Text('You have pushed the button this many times:'),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            // TODO(4): Add a SizedBox(height: 16) and a centred Row with an
            //          OutlinedButton '-1' (disabled when _counter is 0: pass
            //          null to onPressed) and a TextButton 'Reset'.
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}