// Tip Calculator - lesson 2.3 (STARTER)
// Compiles and runs as it is. Complete TODO(1) to TODO(4).
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
  // TODO(1): Add a final TextEditingController field named _billController,
  // pass it to the TextField below, and dispose it in dispose().

  int _tipPercent = 15;

  // TODO(2): Add an int _people field that starts at 1.
  // Add a method _changePeople(int delta) that updates it inside setState
  // and never lets it go below 1 (tip: use clamp(1, 20)).

  @override
  void dispose() {
    // TODO(1): dispose the controller here, before super.dispose().
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // TODO(3): Read the bill from the controller with double.tryParse(...) ?? 0.
    // Compute tip, total and perPerson, then format each one into a local
    // String with toStringAsFixed(2), for example: final tipText = ...
    const bill = 0.0;
    final billText = bill.toStringAsFixed(2);

    return Scaffold(
      appBar: AppBar(title: const Text('Tip Calculator')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
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
          // TODO(2): Add a Row: Text('People'), Spacer, a minus
          // IconButton.filledTonal, the count, and a plus IconButton.filledTonal.
          // Disable minus (onPressed: null) when _people is 1.

          // TODO(4): Replace this card with three Cards holding ListTiles:
          // Tip, Total and Each person pays (use the primaryContainer colour
          // for the last one).
          Card(
            child: ListTile(
              title: const Text('Bill'),
              trailing: Text('₹$billText'),
            ),
          ),
        ],
      ),
    );
  }
}
