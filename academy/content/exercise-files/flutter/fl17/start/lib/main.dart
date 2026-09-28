// Widget Tree Explorer - STARTER (lesson 2.1)
// This file runs as it is. Fill in TODO(1) to TODO(5), then do the
// experiments in README.md while watching the Debug Console.
import 'package:flutter/material.dart';

void main() => runApp(const TreeExplorerApp());

class TreeExplorerApp extends StatelessWidget {
  const TreeExplorerApp({super.key});

  @override
  Widget build(BuildContext context) {
    debugPrint('build TreeExplorerApp');
    return MaterialApp(
      title: 'Widget Tree Explorer',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
      home: const CounterPage(),
    );
  }
}

class CounterPage extends StatefulWidget {
  const CounterPage({super.key});

  @override
  State<CounterPage> createState() => _CounterPageState();
}

class _CounterPageState extends State<CounterPage> {
  int _count = 0;

  // TODO(1): Override initState, call super.initState() first, then
  //   debugPrint('initState CounterPage').

  void _increment() => setState(() => _count++);

  @override
  Widget build(BuildContext context) {
    debugPrint('build CounterPage (count $_count)');
    return Scaffold(
      appBar: AppBar(title: const Text('Tree Explorer')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // TODO(2): Make this first Label const and compare the console.
            Label('I am const'),
            Label('Count is $_count'),
            const SizedBox(height: 16),
            // TODO(3): Add const ThemeReader() here.
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _increment,
        tooltip: 'Add one',
        child: const Icon(Icons.add),
      ),
    );
  }
}

/// A tiny widget that should log every time its build method runs.
class Label extends StatelessWidget {
  const Label(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    // TODO(4): debugPrint('build Label($text)');
    return Text(text, style: Theme.of(context).textTheme.titleLarge);
  }
}

/// Should show that BuildContext looks UP the tree for Theme and Navigator.
class ThemeReader extends StatelessWidget {
  const ThemeReader({super.key});

  @override
  Widget build(BuildContext context) {
    // TODO(5): Read Theme.of(context).colorScheme.primary and check
    //   Navigator.maybeOf(context) != null. Return a Chip with a palette
    //   Icon in the primary colour and the label
    //   'Navigator above me: <true or false>'.
    return const Placeholder(fallbackHeight: 40, fallbackWidth: 200);
  }
}
