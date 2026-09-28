import 'package:flutter/material.dart';

void main() => runApp(const TravelApp());

enum Budget { budget, mid, luxury }

class Destination {
  const Destination(this.name, this.place, this.type, this.budget);
  final String name;
  final String place;
  final String type;
  final Budget budget;
  String get subtitle => '$place · $type';
}

const destinations = [
  Destination('Munnar', 'Kerala, India', 'Mountains', Budget.mid),
  Destination('Alleppey', 'Kerala, India', 'Backwaters', Budget.mid),
  Destination('Goa', 'India', 'Beach', Budget.budget),
  Destination('Jaipur', 'Rajasthan, India', 'Heritage', Budget.budget),
  Destination('Dubai', 'UAE', 'City', Budget.luxury),
  Destination('Banff', 'Alberta, Canada', 'Mountains', Budget.luxury),
];

const types = ['Beach', 'Mountains', 'City', 'Heritage', 'Backwaters'];

IconData iconFor(String type) => switch (type) {
      'Beach' => Icons.beach_access,
      'Mountains' => Icons.landscape,
      'City' => Icons.location_city,
      'Heritage' => Icons.account_balance,
      _ => Icons.kayaking,
    };

class TravelApp extends StatelessWidget {
  const TravelApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Travel Explorer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      home: const ExplorerHome(),
    );
  }
}

class ExplorerHome extends StatefulWidget {
  const ExplorerHome({super.key});
  @override
  State<ExplorerHome> createState() => _ExplorerHomeState();
}

class _ExplorerHomeState extends State<ExplorerHome> {
  int _tab = 0;
  final _types = <String>{};
  Budget? _budget;
  final _saved = <String>{};
  List<Destination> get _visible => destinations
      .where((d) => _types.isEmpty || _types.contains(d.type))
      .where((d) => _budget == null || d.budget == _budget)
      .toList();
  void _toggleSaved(Destination d) => setState(() {
        if (!_saved.remove(d.name)) _saved.add(d.name);
      });
  @override
  Widget build(BuildContext context) {
    final visible = _visible;
    debugPrint('Tab $_tab, saved: $_saved');
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Explorer')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // TODO(1): SearchAnchor.bar with barHintText 'Search destinations'.
          //          suggestionsBuilder: filter destinations whose lower-case name
          //          contains controller.text.toLowerCase(); each ListTile calls
          //          controller.closeView(d.name) on tap.
          // TODO(2): Wrap(spacing: 8) of FilterChip for each type in types,
          //          selected: _types.contains(type), onSelected adds or removes it.
          // TODO(3): SegmentedButton<Budget> with three ButtonSegments,
          //          selected: {if (_budget case final b?) b},
          //          emptySelectionAllowed: true, and onSelectionChanged that sets
          //          _budget to null when the set is empty, otherwise set.first.
          if (visible.isEmpty) const Center(child: Text('No destinations match')),
          for (final d in visible)
            DestinationCard(
              destination: d,
              saved: _saved.contains(d.name),
              onToggleSaved: () => _toggleSaved(d),
            ),
        ],
      ),
      // TODO(5): bottomNavigationBar: NavigationBar with Explore and Saved.
      //          Wrap the Saved icon in Badge.count(count: _saved.length,
      //          isLabelVisible: _saved.isNotEmpty, ...). When _tab == 1,
      //          show a list of saved destinations instead of the explorer.
    );
  }
}

class DestinationCard extends StatelessWidget {
  const DestinationCard({
    super.key,
    required this.destination,
    required this.saved,
    required this.onToggleSaved,
  });
  final Destination destination;
  final bool saved;
  final VoidCallback onToggleSaved;
  @override
  Widget build(BuildContext context) {
    // TODO(4): Card(clipBehavior: Clip.antiAlias) with a Column:
    //          a 110-high Container in primaryContainer with iconFor(type),
    //          then a ListTile (title, subtitle) whose trailing is an IconButton
    //          with isSelected: saved, icon favorite_border, selectedIcon favorite.
    return ListTile(
      title: Text(destination.name),
      subtitle: Text(destination.subtitle),
      onTap: onToggleSaved,
    );
  }
}
