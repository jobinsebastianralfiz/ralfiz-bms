import 'dart:collection';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class Product {
  const Product(this.id, this.name, this.price);
  final int id;
  final String name;
  final int price;
  String get priceLabel => '₹$price';
}

const catalog = [
  Product(1, 'Canvas Tote', 499), Product(2, 'Steel Bottle', 799),
  Product(3, 'Desk Lamp', 1299), Product(4, 'Wireless Mouse', 999),
];

/// App state: plain Dart, no widgets, easy to unit test.
class CartModel extends ChangeNotifier {
  final List<Product> _items = [];

  UnmodifiableListView<Product> get items => UnmodifiableListView(_items);
  int get count => _items.length;
  int get total => _items.fold<int>(0, (sum, p) => sum + p.price);
  bool contains(Product p) => _items.contains(p);

  void add(Product p) {
    if (contains(p)) return;
    _items.add(p);
    notifyListeners();
  }

  void remove(Product p) {
    if (_items.remove(p)) notifyListeners();
  }
  void clear() {
    _items.clear();
    notifyListeners();
  }
}

void main() {
  runApp(ChangeNotifierProvider(
    create: (context) => CartModel(),
    child: MaterialApp(
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange)),
      home: const CatalogPage(),
    ),
  ));
}

class CatalogPage extends StatelessWidget {
  const CatalogPage({super.key});
  @override
  Widget build(BuildContext context) {
    // Watches nothing: only CartButton and each ProductTile subscribe.
    return Scaffold(
      appBar: AppBar(title: const Text('Shop')),
      body: ListView(children: [for (final p in catalog) ProductTile(product: p)]),
      floatingActionButton: const CartButton(),
    );
  }
}

class CartButton extends StatelessWidget {
  const CartButton({super.key});
  @override
  Widget build(BuildContext context) {
    // Rebuilds only when the number of items changes.
    final count = context.select<CartModel, int>((cart) => cart.count);
    return FloatingActionButton.extended(
      onPressed: () => Navigator.push(
          context, MaterialPageRoute<void>(builder: (context) => const CartPage())),
      icon: const Icon(Icons.shopping_cart),
      label: Text('Cart ($count)'),
    );
  }
}

class ProductTile extends StatelessWidget {
  const ProductTile({super.key, required this.product});
  final Product product;

  @override
  Widget build(BuildContext context) {
    final inCart = context.select<CartModel, bool>((cart) => cart.contains(product));
    return ListTile(
      leading: const Icon(Icons.shopping_bag),
      title: Text(product.name),
      subtitle: Text(product.priceLabel),
      trailing: inCart
          ? const Icon(Icons.check_circle)
          : FilledButton.tonal(
              // read: we only call a method, we do not want to rebuild.
              onPressed: () => context.read<CartModel>().add(product),
              child: const Text('Add'),
            ),
    );
  }
}

class CartPage extends StatelessWidget {
  const CartPage({super.key});
  Future<void> _confirmClear(BuildContext context) async {
    final cart = context.read<CartModel>();
    final count = cart.count;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear cart?'),
        content: Text('Remove all $count items?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Clear')),
        ],
      ),
    );
    if (ok ?? false) cart.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your cart'), actions: [
          IconButton(icon: const Icon(Icons.delete_sweep), onPressed: () => _confirmClear(context)),
        ]),
      body: Column(children: [
        Expanded(
          child: Consumer<CartModel>(
            builder: (context, cart, child) {
              if (cart.items.isEmpty) return const Center(child: Text('Your cart is empty'));
              return ListView(children: [
                for (final p in cart.items)
                  ListTile(
                    title: Text(p.name),
                    subtitle: Text(p.priceLabel),
                    trailing: IconButton(
                        icon: const Icon(Icons.remove_circle_outline),
                        onPressed: () => cart.remove(p)),
                  ),
              ]);
            },
          ),
        ),
        const TotalBar(),
      ]),
    );
  }
}

class TotalBar extends StatelessWidget {
  const TotalBar({super.key});
  void _checkout(BuildContext context, int total) {
    context.read<CartModel>().clear();
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('Order placed: ₹$total')));
  }

  @override
  Widget build(BuildContext context) {
    final total = context.watch<CartModel>().total;
    return Container(
      color: Theme.of(context).colorScheme.surfaceContainer,
      padding: const EdgeInsets.all(16),
      child: SafeArea(
        top: false,
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('Total: ₹$total', style: Theme.of(context).textTheme.titleMedium),
          FilledButton(
            onPressed: total == 0 ? null : () => _checkout(context, total),
            child: const Text('Checkout'),
          ),
        ]),
      ),
    );
  }
}
