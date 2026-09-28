// Tip Calculator - lesson 2.3 (SOLUTION)
// Paste into lib/main.dart of a new project, or into DartPad.
import 'package:flutter/material.dart';

void main() => runApp(const TipApp());

class TipApp extends StatelessWidget {
  const TipApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tip Calculator',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
      ),
      home: const TipCalculator(),
    );
  }
}

class TipCalculator extends StatefulWidget {
  const TipCalculator({super.key});

  @override
  State<TipCalculator> createState() => _TipCalculatorState();
}

class _TipCalculatorState extends State<TipCalculator> {
  // State: the three things the user can change.
  final _billController = TextEditingController();
  int _tipPercent = 15;
  int _people = 1;

  @override
  void dispose() {
    _billController.dispose(); // release the controller
    super.dispose();
  }

  void _changePeople(int delta) {
    setState(() {
      _people = (_people + delta).clamp(1, 20);
    });
  }

  @override
  Widget build(BuildContext context) {
    // Derived values: computed on every build, never stored.
    final bill = double.tryParse(_billController.text) ?? 0;
    final tip = bill * _tipPercent / 100;
    final total = bill + tip;
    final perPerson = total / _people;

    final tipText = tip.toStringAsFixed(2);
    final totalText = total.toStringAsFixed(2);
    final perPersonText = perPerson.toStringAsFixed(2);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Tip Calculator')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _billController,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Bill amount',
              prefixIcon: Icon(Icons.receipt_long),
              border: OutlineInputBorder(),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 10, label: Text('10%')),
              ButtonSegment(value: 15, label: Text('15%')),
              ButtonSegment(value: 20, label: Text('20%')),
            ],
            selected: {_tipPercent},
            onSelectionChanged: (selection) {
              setState(() => _tipPercent = selection.first);
            },
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Text('People', style: textTheme.titleMedium),
              const Spacer(),
              IconButton.filledTonal(
                onPressed: _people > 1 ? () => _changePeople(-1) : null,
                icon: const Icon(Icons.remove),
                tooltip: 'One less person',
              ),
              SizedBox(
                width: 48,
                child: Text(
                  '$_people',
                  textAlign: TextAlign.center,
                  style: textTheme.titleLarge,
                ),
              ),
              IconButton.filledTonal(
                onPressed: () => _changePeople(1),
                icon: const Icon(Icons.add),
                tooltip: 'One more person',
              ),
            ],
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              title: const Text('Tip'),
              trailing: Text('₹$tipText'),
            ),
          ),
          Card(
            child: ListTile(
              title: const Text('Total'),
              trailing: Text('₹$totalText'),
            ),
          ),
          Card(
            color: Theme.of(context).colorScheme.primaryContainer,
            child: ListTile(
              title: const Text('Each person pays'),
              trailing: Text('₹$perPersonText', style: textTheme.titleLarge),
            ),
          ),
        ],
      ),
    );
  }
}
