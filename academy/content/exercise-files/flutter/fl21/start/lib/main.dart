// Habit Tracker - lesson 2.5 (STARTER)
// Compiles and runs as it is. Complete TODO(1) to TODO(5).
import 'package:flutter/material.dart';

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
  final _habits = [
    Habit('Drink water'),
    Habit('Read 10 pages'),
    Habit('Walk after lunch'),
    Habit('Stretch'),
  ];

  // TODO(1): write _toggle(Habit habit) that flips habit.done inside setState.

  // TODO(2): write _delete(int index):
  //  - remember the removed habit, remove it inside setState
  //  - hide the current SnackBar, then show SnackBar(content: Text('Deleted $name'))
  //    with a SnackBarAction labelled Undo that inserts it back at index.

  // TODO(3): write _showOptions(Habit habit) that calls showModalBottomSheet
  // with showDragHandle: true and a Column (mainAxisSize: min) holding the
  // habit name and ListTiles Rename, Set reminder and Delete.
  // Each option first calls Navigator.pop(context).

  // TODO(4): write Future<void> _confirmReset() that awaits
  // showDialog<bool>(...) with an AlertDialog (Cancel / Reset).
  // Only when the result is true and the State is still mounted,
  // set every habit.done to false inside setState.

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Habits'),
        // TODO(4): add an IconButton (Icons.restart_alt, tooltip Reset)
        // that calls _confirmReset.
      ),
      body: ListView(
        children: [
          for (final (i, habit) in _habits.indexed)
            ListTile(
              leading: Icon(
                habit.done ? Icons.check_circle : Icons.radio_button_unchecked,
              ),
              title: Text(habit.name),
              // TODO(1): onTap: toggle this habit.
              // TODO(3): onLongPress: show the options sheet.
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                tooltip: 'Delete',
                // TODO(2): call _delete(i) instead of doing nothing.
                onPressed: () => debugPrint('Delete tapped at $i'),
              ),
            ),
        ],
      ),
      // TODO(5): add bottomNavigationBar: a padded FilledButton.icon
      // "Mark all done" (Icons.done_all). Its onPressed is null when
      // every habit is already done.
    );
  }
}
