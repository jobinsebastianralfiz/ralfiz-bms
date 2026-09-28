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

  // TODO(1): Replace _buildHeader with a SectionHeader widget class.
  Widget _buildHeader(String title, String? actionLabel) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 8, 4),
      child: Row(children: [
        Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
        if (actionLabel != null) TextButton(onPressed: () {}, child: Text(actionLabel)),
      ]),
    );
  }

  // TODO(2): Replace _buildCard with a DestinationCard widget class that has
  //          required destination, VoidCallback? onTap and Widget? trailing.
  Widget _buildCard(Destination d, Widget? trailing) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: scheme.primaryContainer,
          child: Icon(d.icon, color: scheme.onPrimaryContainer),
        ),
        title: Text(d.name),
        subtitle: Text(d.place),
        trailing: trailing,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Explorer')),
      body: ListView(
        children: [
          _buildHeader('Popular', 'See all'),
          for (final d in destinations) _buildCard(d, const Icon(Icons.favorite_border)),
          _buildHeader('Deals', null),
          for (final d in destinations) _buildCard(d, Text(d.price)),
          _buildHeader('Rate Munnar', null),
          // TODO(3): Replace this Row with StarRating(value: _rating,
          //          onChanged: (v) => setState(() => _rating = v)).
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              for (var i = 1; i <= 5; i++)
                IconButton(
                  onPressed: () => setState(() => _rating = i),
                  icon: Icon(i <= _rating ? Icons.star : Icons.star_border),
                ),
            ],
          ),
          Center(child: Text('$_rating of 5')),
          _buildHeader('Packing list', null),
          const PackingList(),
        ],
      ),
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
        // TODO(4): add key: ValueKey(item) and test removing a ticked item.
        PackingTile(label: item, onRemove: () => setState(() => _items.remove(item))),
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
