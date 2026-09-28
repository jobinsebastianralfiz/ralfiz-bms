import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightBlue)),
    home: const WaterHome(),
  ));
}

/// Shares today's water data with every widget below it.
class WaterScope extends InheritedWidget {
  const WaterScope({
    super.key,
    required this.glasses,
    required this.goal,
    required this.onAdd,
    required super.child,
  });

  final int glasses;
  final int goal;
  final VoidCallback onAdd;

  static WaterScope of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<WaterScope>();
    assert(scope != null, 'No WaterScope found above this context');
    return scope!;
  }

  @override
  bool updateShouldNotify(WaterScope oldWidget) =>
      glasses != oldWidget.glasses || goal != oldWidget.goal;
}

class WaterHome extends StatefulWidget {
  const WaterHome({super.key});
  @override
  State<WaterHome> createState() => _WaterHomeState();
}

class _WaterHomeState extends State<WaterHome> {
  static const _goal = 8;
  int _glasses = 0; // app state: several widgets need it, so it lives here

  void _add() => setState(() => _glasses++);

  void _remove() {
    if (_glasses == 0) return;
    setState(() => _glasses--);
  }

  @override
  Widget build(BuildContext context) {
    return WaterScope(
      glasses: _glasses,
      goal: _goal,
      onAdd: _add,
      child: Scaffold(
        appBar: AppBar(title: const Text('Water Tracker')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 16,
            children: [
              ProgressHeader(glasses: _glasses, goal: _goal), // data down
              AddButtons(onAdd: _add, onRemove: _remove), // events up
              const TodayCard(), // reads WaterScope, gets no parameters
              const TipCard(), // ephemeral state of its own
            ],
          ),
        ),
      ),
    );
  }
}

class ProgressHeader extends StatelessWidget {
  const ProgressHeader({super.key, required this.glasses, required this.goal});
  final int glasses;
  final int goal;

  @override
  Widget build(BuildContext context) {
    final progress = glasses >= goal ? 1.0 : glasses / goal;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, spacing: 8, children: [
      Text('$glasses of $goal glasses', style: Theme.of(context).textTheme.headlineSmall),
      LinearProgressIndicator(value: progress),
      if (glasses >= goal) const Text('Goal reached. Well done!'),
    ]);
  }
}

class AddButtons extends StatelessWidget {
  const AddButtons({super.key, required this.onAdd, required this.onRemove});
  final VoidCallback onAdd;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return Row(spacing: 12, children: [
      Expanded(
        child: OutlinedButton.icon(
            onPressed: onRemove, icon: const Icon(Icons.remove), label: const Text('Remove')),
      ),
      Expanded(
        child: FilledButton.icon(
            onPressed: onAdd, icon: const Icon(Icons.add), label: const Text('Add glass')),
      ),
    ]);
  }
}

class TodayCard extends StatelessWidget {
  const TodayCard({super.key});

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(padding: EdgeInsets.all(16), child: GlassGrid()),
    );
  }
}

class GlassGrid extends StatelessWidget {
  const GlassGrid({super.key});

  @override
  Widget build(BuildContext context) {
    final water = WaterScope.of(context); // registers a dependency
    final color = Theme.of(context).colorScheme.primary;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, spacing: 8, children: [
      const Text('Today'),
      Wrap(spacing: 4, children: [
        for (var i = 0; i < water.goal; i++)
          Icon(i < water.glasses ? Icons.water_drop : Icons.water_drop_outlined, color: color),
      ]),
      TextButton(onPressed: water.onAdd, child: const Text('Log a glass')),
    ]);
  }
}

class TipCard extends StatefulWidget {
  const TipCard({super.key});
  @override
  State<TipCard> createState() => _TipCardState();
}

class _TipCardState extends State<TipCard> {
  bool _expanded = false; // ephemeral: nobody else needs to know

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(children: [
        ListTile(
          leading: const Icon(Icons.lightbulb_outline),
          title: const Text('Hydration tip'),
          trailing: Icon(_expanded ? Icons.expand_less : Icons.expand_more),
          onTap: () => setState(() => _expanded = !_expanded),
        ),
        if (_expanded)
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Text('Keep a bottle on your desk and refill it after each meeting.'),
          ),
      ]),
    );
  }
}
