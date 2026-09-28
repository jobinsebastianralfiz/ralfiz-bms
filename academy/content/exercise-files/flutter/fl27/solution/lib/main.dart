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
    final explore = ListView(
      padding: const EdgeInsets.all(16),
      children: [
        SearchAnchor.bar(
          barHintText: 'Search destinations',
          suggestionsBuilder: (context, controller) {
            final query = controller.text.toLowerCase();
            return destinations
                .where((d) => d.name.toLowerCase().contains(query))
                .map((d) => ListTile(
                      leading: const Icon(Icons.place_outlined),
                      title: Text(d.name),
                      subtitle: Text(d.place),
                      onTap: () => controller.closeView(d.name),
                    ));
          },
        ),
        const SizedBox(height: 12),
        Wrap(spacing: 8, runSpacing: 4, children: [
          for (final type in types)
            FilterChip(
              label: Text(type),
              selected: _types.contains(type),
              onSelected: (on) =>
                  setState(() => on ? _types.add(type) : _types.remove(type)),
            ),
        ]),
        const SizedBox(height: 12),
        SegmentedButton<Budget>(
          segments: const [
            ButtonSegment(value: Budget.budget, label: Text('Budget')),
            ButtonSegment(value: Budget.mid, label: Text('Mid')),
            ButtonSegment(value: Budget.luxury, label: Text('Luxury')),
          ],
          selected: {if (_budget case final b?) b},
          emptySelectionAllowed: true,
          onSelectionChanged: (set) =>
              setState(() => _budget = set.isEmpty ? null : set.first),
        ),
        const SizedBox(height: 16),
        if (visible.isEmpty) const Center(child: Text('No destinations match')),
        for (final d in visible)
          DestinationCard(
            destination: d,
            saved: _saved.contains(d.name),
            onToggleSaved: () => _toggleSaved(d),
          ),
      ],
    );
    final savedList = ListView(children: [
      if (_saved.isEmpty) const ListTile(title: Text('Nothing saved yet')),
      for (final d in destinations.where((d) => _saved.contains(d.name)))
        ListTile(leading: Icon(iconFor(d.type)), title: Text(d.name), subtitle: Text(d.subtitle)),
    ]);
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Explorer')),
      body: _tab == 0 ? explore : savedList,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [
          const NavigationDestination(
              icon: Icon(Icons.explore_outlined), selectedIcon: Icon(Icons.explore), label: 'Explore'),
          NavigationDestination(
            icon: Badge.count(
              count: _saved.length,
              isLabelVisible: _saved.isNotEmpty,
              child: const Icon(Icons.favorite_border),
            ),
            selectedIcon: const Icon(Icons.favorite),
            label: 'Saved',
          ),
        ],
      ),
    );
  }
}

class DestinationCard extends StatelessWidget {
  const DestinationCard(
      {super.key, required this.destination, required this.saved, required this.onToggleSaved});
  final Destination destination;
  final bool saved;
  final VoidCallback onToggleSaved;
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(children: [
        Container(
          height: 110,
          color: scheme.primaryContainer,
          alignment: Alignment.center,
          child: Icon(iconFor(destination.type), size: 44, color: scheme.onPrimaryContainer),
        ),
        ListTile(
          title: Text(destination.name),
          subtitle: Text(destination.subtitle),
          trailing: IconButton(
            tooltip: saved ? 'Remove from saved' : 'Save',
            isSelected: saved,
            icon: const Icon(Icons.favorite_border),
            selectedIcon: const Icon(Icons.favorite),
            onPressed: onToggleSaved,
          ),
        ),
      ]),
    );
  }
}
