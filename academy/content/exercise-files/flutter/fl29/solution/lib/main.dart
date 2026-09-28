import 'package:flutter/material.dart';

void main() => runApp(MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      home: const HomePage(),
    ));

class Destination {
  const Destination(this.name, this.place, this.icon, this.price);
  final String name;
  final String place;
  final IconData icon;
  final String price;
}

const destinations = [
  Destination('Munnar', 'Kerala · Mountains', Icons.landscape, '₹4,200'),
  Destination('Goa', 'India · Beach', Icons.beach_access, '₹3,500'),
  Destination('Dubai', 'UAE · City', Icons.location_city, 'AED 650'),
];

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _rating = 3;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Explorer')),
      body: ListView(
        children: [
          SectionHeader(title: 'Popular', actionLabel: 'See all', onAction: () {}),
          for (final d in destinations)
            DestinationCard(destination: d, onTap: () {}, trailing: const Icon(Icons.favorite_border)),
          const SectionHeader(title: 'Deals'),
          for (final d in destinations)
            DestinationCard(
              destination: d,
              trailing: d.name == 'Goa' ? const StarRating(value: 4) : Text(d.price),
            ),
          const SectionHeader(title: 'Rate Munnar'),
          Center(
            child: StarRating(value: _rating, onChanged: (v) => setState(() => _rating = v)),
          ),
          Center(child: Text('$_rating of 5')),
          const SectionHeader(title: 'Packing list'),
          const PackingList(),
        ],
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  const SectionHeader({super.key, required this.title, this.actionLabel, this.onAction});
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final label = actionLabel;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 8, 4),
      child: Row(children: [
        Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
        if (label != null && onAction != null) TextButton(onPressed: onAction, child: Text(label)),
      ]),
    );
  }
}

class DestinationCard extends StatelessWidget {
  const DestinationCard({super.key, required this.destination, this.onTap, this.trailing});
  final Destination destination;
  final VoidCallback? onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: scheme.primaryContainer,
          child: Icon(destination.icon, color: scheme.onPrimaryContainer),
        ),
        title: Text(destination.name),
        subtitle: Text(destination.place),
        trailing: trailing,
      ),
    );
  }
}

class StarRating extends StatelessWidget {
  const StarRating({super.key, required this.value, this.max = 5, this.onChanged});
  final int value;
  final int max;
  final ValueChanged<int>? onChanged;

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;
    final onChanged = this.onChanged;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (var i = 1; i <= max; i++)
          if (onChanged == null)
            Icon(i <= value ? Icons.star : Icons.star_border, color: color, size: 18)
          else
            IconButton(
              onPressed: () => onChanged(i),
              icon: Icon(i <= value ? Icons.star : Icons.star_border, color: color),
            ),
      ],
    );
  }
}

class PackingList extends StatefulWidget {
  const PackingList({super.key});

  @override
  State<PackingList> createState() => _PackingListState();
}

class _PackingListState extends State<PackingList> {
  final _items = ['Passport', 'Tickets', 'Charger'];

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      for (final item in _items)
        PackingTile(
          key: ValueKey(item),
          label: item,
          onRemove: () => setState(() => _items.remove(item)),
        ),
    ]);
  }
}

class PackingTile extends StatefulWidget {
  const PackingTile({super.key, required this.label, required this.onRemove});
  final String label;
  final VoidCallback onRemove;

  @override
  State<PackingTile> createState() => _PackingTileState();
}

class _PackingTileState extends State<PackingTile> {
  bool _packed = false;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Checkbox(value: _packed, onChanged: (v) => setState(() => _packed = v ?? false)),
      title: Text(widget.label),
      trailing: IconButton(icon: const Icon(Icons.close), onPressed: widget.onRemove),
    );
  }
}
