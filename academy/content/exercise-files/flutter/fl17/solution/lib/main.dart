// Widget Tree Explorer - SOLUTION (lesson 2.1)
// Watch the Debug Console while you tap, hot reload and hot restart.
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

  @override
  void initState() {
    super.initState();
    // Runs once when the element is created. Hot reload does not repeat it.
    debugPrint('initState CounterPage');
  }

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
            const Label('I am const'),
            Label('Count is $_count'),
            const SizedBox(height: 16),
            const ThemeReader(),
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

/// A tiny widget that logs every time its build method runs.
class Label extends StatelessWidget {
  const Label(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    debugPrint('build Label($text)');
    return Text(text, style: Theme.of(context).textTheme.titleLarge);
  }
}

/// Shows that BuildContext looks UP the tree for Theme and Navigator.
class ThemeReader extends StatelessWidget {
  const ThemeReader({super.key});

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    final hasNavigator = Navigator.maybeOf(context) != null;
    return Chip(
      avatar: Icon(Icons.palette, color: primary),
      label: Text('Navigator above me: $hasNavigator'),
    );
  }
}
