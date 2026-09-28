// Habit Tracker - lesson 2.5 (SOLUTION)
// Paste into lib/main.dart of a new project, or into DartPad.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() => runApp(const HabitApp());

class HabitApp extends StatelessWidget {
  const HabitApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Habit Tracker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
      ),
      home: const HabitsPage(),
    );
  }
}

class Habit {
  Habit(this.name);
  final String name;
  bool done = false;
}

class HabitsPage extends StatefulWidget {
  const HabitsPage({super.key});

  @override
  State<HabitsPage> createState() => _HabitsPageState();
}

class _HabitsPageState extends State<HabitsPage> {
  final _habits = [Habit('Drink water'), Habit('Read 10 pages'),
      Habit('Walk after lunch'), Habit('Stretch')];

  bool get _allDone => _habits.every((h) => h.done);

  void _toggle(Habit habit) {
    HapticFeedback.selectionClick();
    setState(() => habit.done = !habit.done);
  }

  void _delete(int index) {
    final removed = _habits[index];
    final name = removed.name;
    setState(() => _habits.removeAt(index));
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text('Deleted $name'),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () {
              // The list may be shorter now, so keep the index in range.
              final at = index.clamp(0, _habits.length);
              setState(() => _habits.insert(at, removed));
            },
          ),
        ),
      );
  }

  void _showOptions(Habit habit) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(habit.name, style: Theme.of(context).textTheme.titleMedium),
            ListTile(
              leading: const Icon(Icons.edit),
              title: const Text('Rename'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.notifications_outlined),
              title: const Text('Set reminder'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline),
              title: const Text('Delete'),
              onTap: () {
                Navigator.pop(context);
                _delete(_habits.indexOf(habit));
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmReset() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.restart_alt),
        title: const Text('Reset today?'),
        content: const Text('All habits will be marked as not done.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Reset'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    _setAll(false);
  }

  void _setAll(bool done) {
    setState(() {
      for (final habit in _habits) {
        habit.done = done;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Habits'),
        actions: [
          IconButton(
            onPressed: _confirmReset,
            tooltip: 'Reset',
            icon: const Icon(Icons.restart_alt),
          ),
        ],
      ),
      body: ListView(
        children: [
          for (final (i, habit) in _habits.indexed)
            ListTile(
              leading: Icon(
                habit.done ? Icons.check_circle : Icons.radio_button_unchecked,
                color: habit.done ? Theme.of(context).colorScheme.primary : null,
              ),
              title: Text(habit.name),
              onTap: () => _toggle(habit),
              onLongPress: () => _showOptions(habit),
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                tooltip: 'Delete',
                onPressed: () => _delete(i),
              ),
            ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _allDone ? null : () => _setAll(true),
            icon: const Icon(Icons.done_all),
            label: const Text('Mark all done'),
          ),
        ),
      ),
    );
  }
}
