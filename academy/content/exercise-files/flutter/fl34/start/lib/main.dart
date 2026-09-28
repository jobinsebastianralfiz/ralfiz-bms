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
    // TODO(4): look up the nearest WaterScope with
    //          context.dependOnInheritedWidgetOfExactType<WaterScope>(),
    //          assert it is not null, and return it.
    throw UnimplementedError('WaterScope.of');
  }

  // TODO(4): return true only when glasses or goal changed.
  @override
  bool updateShouldNotify(WaterScope oldWidget) => true;
}

class WaterHome extends StatefulWidget {
  const WaterHome({super.key});
  @override
  State<WaterHome> createState() => _WaterHomeState();
}

class _WaterHomeState extends State<WaterHome> {
  static const _goal = 8;
  // TODO(1): the count lives inside AddButtons, so ProgressHeader cannot see it.
  //          Move it here as int _glasses = 0 with _add() and _remove() methods
  //          that call setState (never go below 0).

  @override
  Widget build(BuildContext context) {
    // TODO(5): wrap the Scaffold in WaterScope(glasses: ..., goal: _goal, onAdd: _add, child: ...).
    return Scaffold(
      appBar: AppBar(title: const Text('Water Tracker')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 16,
          children: const [
            ProgressHeader(glasses: 0, goal: _goal), // TODO(3): pass _glasses
            AddButtons(), // TODO(2): pass onAdd: _add, onRemove: _remove
            // TODO(6): add const TodayCard() once WaterScope works.
            TipCard(),
          ],
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

// TODO(2): turn this into a StatelessWidget with required VoidCallback onAdd and
//          onRemove fields, and call them from the buttons.
class AddButtons extends StatefulWidget {
  const AddButtons({super.key});
  @override
  State<AddButtons> createState() => _AddButtonsState();
}

class _AddButtonsState extends State<AddButtons> {
  int _count = 0; // wrong place: only this widget knows the value

  @override
  Widget build(BuildContext context) {
    return Row(spacing: 12, children: [
      Expanded(
        child: OutlinedButton.icon(
            onPressed: () => setState(() => _count = _count > 0 ? _count - 1 : 0),
            icon: const Icon(Icons.remove),
            label: const Text('Remove')),
      ),
      Expanded(
        child: FilledButton.icon(
            onPressed: () => setState(() => _count++),
            icon: const Icon(Icons.add),
            label: Text('Add glass ($_count)')),
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
