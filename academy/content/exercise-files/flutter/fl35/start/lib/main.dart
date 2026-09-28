// Lab 6.2: Shopping Cart with Provider
// Setup: flutter create shopping_cart, flutter pub add provider, replace
// lib/main.dart with this file and copy cart_model_test.dart into test/.
// Goal: the catalog, the Cart button, the cart list and the total all share one
// CartModel. Done when:
//  - flutter test reports All tests passed!
//  - Adding Canvas Tote and Steel Bottle shows Cart (2) and two check icons.
//  - The cart page lists both and shows Total: ₹1298; removing one updates it.
//  - The delete icon asks "Clear cart?" and empties the cart after Clear.
//  - Checkout shows the snack bar Order placed: ₹1298 and empties the cart.
import 'dart:collection';

import 'package:flutter/material.dart';
// TODO(3): import 'package:provider/provider.dart';

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

class CartModel extends ChangeNotifier {
  final List<Product> _items = [];

  UnmodifiableListView<Product> get items => UnmodifiableListView(_items);
  int get count => _items.length;
  // TODO(1): return the sum of the prices with fold<int>.
  int get total => 0;
  bool contains(Product p) => _items.contains(p);

  // TODO(2): add (ignore duplicates), remove and clear must change _items AND
  //          call notifyListeners(). Run flutter test to check your model.
  void add(Product p) => _items.add(p);
  void remove(Product p) => _items.remove(p);
  void clear() => _items.clear();
}

void main() {
  // TODO(3): wrap MaterialApp in ChangeNotifierProvider(create: (context) => CartModel(), ...).
  runApp(MaterialApp(
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange)),
    home: const CatalogPage(),
  ));
}

class CatalogPage extends StatelessWidget {
  const CatalogPage({super.key});

  @override
  Widget build(BuildContext context) {
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
    // TODO(4): read the count with context.select<CartModel, int>(...).
    const count = 0;
    return FloatingActionButton.extended(
      onPressed: () => Navigator.push(
          context, MaterialPageRoute<void>(builder: (context) => const CartPage())),
      icon: const Icon(Icons.shopping_cart),
      label: const Text('Cart ($count)'),
    );
  }
}

class ProductTile extends StatelessWidget {
  const ProductTile({super.key, required this.product});
  final Product product;

  @override
  Widget build(BuildContext context) {
    // TODO(4): const inCart = false -> context.select<CartModel, bool>(...).
    const inCart = false;
    return ListTile(
      leading: const Icon(Icons.shopping_bag),
      title: Text(product.name),
      subtitle: Text(product.priceLabel),
      trailing: inCart
          ? const Icon(Icons.check_circle)
          : FilledButton.tonal(
              // TODO(5): add the product with context.read<CartModel>().add(product).
              onPressed: () => debugPrint('Add ' + product.name),
              child: const Text('Add'),
            ),
    );
  }
}

class CartPage extends StatelessWidget {
  const CartPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your cart'),
        // TODO(7): add an IconButton (Icons.delete_sweep) that shows a
        //          "Clear cart?" dialog and calls clear() when the user taps Clear.
      ),
      body: const Column(children: [
        // TODO(6): replace this with Expanded(child: Consumer<CartModel>(...)) that
        //          lists cart.items with a remove button, or 'Your cart is empty'.
        Expanded(child: Center(child: Text('Your cart is empty'))),
        TotalBar(),
      ]),
    );
  }
}

class TotalBar extends StatelessWidget {
  const TotalBar({super.key});

  @override
  Widget build(BuildContext context) {
    // TODO(6): final total = context.watch<CartModel>().total;
    const total = 0;
    return Container(
      color: Theme.of(context).colorScheme.surfaceContainer,
      padding: const EdgeInsets.all(16),
      child: SafeArea(
        top: false,
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('Total: ₹$total', style: Theme.of(context).textTheme.titleMedium),
          FilledButton(
            // TODO(8): when total > 0, clear the cart and show the snack bar
            //          'Order placed: ₹$total'.
            onPressed: null,
            child: const Text('Checkout'),
          ),
        ]),
      ),
    );
  }
}
