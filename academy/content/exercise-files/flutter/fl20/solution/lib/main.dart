// Brew Lab menu - lesson 2.4 (SOLUTION)
// Needs the assets and font listed in pubspec.yaml (see README.md).
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
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Brew Lab',
          style: TextStyle(fontFamily: 'Pacifico', fontSize: 26),
        ),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.shopping_bag_outlined),
            tooltip: 'Cart',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          // Banner from the network, with loading and error states.
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.network(
              bannerUrl,
              height: 160,
              width: double.infinity,
              fit: BoxFit.cover,
              cacheWidth: 800,
              semanticLabel: 'Coffee cups on a wooden table',
              loadingBuilder: (context, child, progress) {
                if (progress == null) return child;
                return const SizedBox(
                  height: 160,
                  child: Center(child: CircularProgressIndicator()),
                );
              },
              errorBuilder: (context, error, stackTrace) => Container(
                height: 160,
                color: colors.surfaceContainerHighest,
                alignment: Alignment.center,
                child: const Icon(Icons.broken_image, size: 48),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 16, 8, 4),
            child: Text('Fresh coffee, slow mornings',
                style: text.headlineSmall),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 12),
            child: Text.rich(
              TextSpan(
                text: 'Open today ',
                style: text.bodyLarge,
                children: [
                  TextSpan(
                    text: 'until 9 pm',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: colors.primary,
                    ),
                  ),
                ],
              ),
            ),
          ),
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
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.asset(
            item.image,
            width: 56,
            height: 56,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) =>
                const SizedBox(width: 56, height: 56, child: Icon(Icons.image)),
          ),
        ),
        title: Text(item.name),
        subtitle: Text(item.priceLabel),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.star, color: Colors.amber, size: 18,
                semanticLabel: 'Rating'),
            const SizedBox(width: 4),
            Text(item.rating.toString()),
          ],
        ),
      ),
    );
  }
}
