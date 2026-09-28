// Brew Lab menu - lesson 2.4 (STARTER)
// Compiles as it is. Complete TODO(1) to TODO(3).
// Add the assets and font from README.md before you run it.
import 'package:flutter/material.dart';

void main() => runApp(const BrewLabApp());

class BrewLabApp extends StatelessWidget {
  const BrewLabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Brew Lab',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.brown),
      ),
      home: const MenuPage(),
    );
  }
}

class MenuItem {
  const MenuItem(this.name, this.price, this.rating, this.image);
  final String name;
  final int price;
  final double rating;
  final String image;

  String get priceLabel => '₹$price';
}

const menu = [
  MenuItem('Leaf latte', 180, 4.8, 'assets/images/latte.jpg'),
  MenuItem('Cold brew', 160, 4.6, 'assets/images/cold_brew.jpg'),
  MenuItem('Masala chai', 90, 4.9, 'assets/images/chai.jpg'),
  MenuItem('Banana cake', 120, 4.4, 'assets/images/cake.jpg'),
];

const bannerUrl = 'https://picsum.photos/seed/brewlab/800/400';

class MenuPage extends StatelessWidget {
  const MenuPage({super.key});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        // TODO(1): give this title the Pacifico font (fontSize 26).
        title: const Text('Brew Lab'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          // TODO(2): show bannerUrl with Image.network: height 160,
          // full width, BoxFit.cover, rounded with ClipRRect, plus a
          // loadingBuilder (spinner) and an errorBuilder (broken_image icon).
          const SizedBox(height: 160, child: Placeholder()),
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 16, 8, 4),
            child: Text('Fresh coffee, slow mornings',
                style: text.headlineSmall),
          ),
          // TODO(1): add a Text.rich line: "Open today " in bodyLarge,
          // followed by "until 9 pm" in bold primary colour.
          for (final item in menu) MenuTile(item: item),
        ],
      ),
    );
  }
}

class MenuTile extends StatelessWidget {
  const MenuTile({super.key, required this.item});

  final MenuItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        // TODO(3): show item.image with Image.asset (56 x 56, BoxFit.cover)
        // inside a ClipRRect with a radius of 8.
        leading: const Icon(Icons.local_cafe),
        title: Text(item.name),
        subtitle: Text(item.priceLabel),
        // TODO(3): replace this with a Row (mainAxisSize: min) holding an
        // amber star Icon (size 18) and the rating text.
        trailing: Text(item.rating.toString()),
      ),
    );
  }
}
