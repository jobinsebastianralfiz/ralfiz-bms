import 'package:flutter/material.dart';

void main() => runApp(MaterialApp(
      title: 'Shop Catalog',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple)),
      home: const CatalogPage(),
    ));

class Product {
  const Product(this.name, this.price, this.icon);
  final String name;
  final int price;
  final IconData icon;
  String get priceLabel => '₹$price';
  String lineLabel(int qty) => '$qty × $priceLabel';
}

const products = [
  Product('Headphones', 1999, Icons.headphones),
  Product('Smart watch', 4499, Icons.watch),
  Product('Backpack', 1299, Icons.backpack),
  Product('Water bottle', 499, Icons.local_drink),
];

class CatalogPage extends StatefulWidget {
  const CatalogPage({super.key});
  @override
  State<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends State<CatalogPage> {
  final _cart = <Product, int>{};
  int get _count => _cart.values.fold(0, (sum, q) => sum + q);
  void _snack(String text) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  Future<void> _openProduct(Product product) async {
    final qty = await Navigator.of(context).push<int>(
      MaterialPageRoute(builder: (context) => ProductPage(product: product)),
    );
    if (!mounted || qty == null) return;
    setState(() => _cart.update(product, (old) => old + qty, ifAbsent: () => qty));
    final name = product.name;
    _snack('Added $qty × $name');
  }
  Future<void> _openCart() async {
    final ordered = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (context) => CartPage(cart: Map.of(_cart))),
    );
    if (!mounted || ordered != true) return;
    setState(_cart.clear);
    _snack('Order placed');
  }
  @override
  Widget build(BuildContext context) {
    final count = _count;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Shop'),
        actions: [
          IconButton(
            tooltip: 'Cart',
            onPressed: _cart.isEmpty ? null : _openCart,
            icon: Badge.count(count: count, isLabelVisible: count > 0,
                child: const Icon(Icons.shopping_cart_outlined)),
          ),
        ],
      ),
      body: ListView(children: [
        for (final p in products)
          ListTile(
            leading: Icon(p.icon),
            title: Text(p.name),
            subtitle: Text(p.priceLabel),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _openProduct(p),
          ),
      ]),
    );
  }
}

class ProductPage extends StatefulWidget {
  const ProductPage({super.key, required this.product});
  final Product product;
  @override
  State<ProductPage> createState() => _ProductPageState();
}

class _ProductPageState extends State<ProductPage> {
  int _qty = 1;
  @override
  Widget build(BuildContext context) {
    final p = widget.product;
    return Scaffold(
      appBar: AppBar(title: Text(p.name)),
      body: Center(
        child: Column(mainAxisSize: MainAxisSize.min, spacing: 12, children: [
          Icon(p.icon, size: 96),
          Text(p.priceLabel, style: Theme.of(context).textTheme.headlineMedium),
          Row(mainAxisSize: MainAxisSize.min, children: [
            IconButton.outlined(
                onPressed: _qty > 1 ? () => setState(() => _qty--) : null,
                icon: const Icon(Icons.remove)),
            Text('  $_qty  ', style: Theme.of(context).textTheme.titleLarge),
            IconButton.outlined(
                onPressed: () => setState(() => _qty++), icon: const Icon(Icons.add)),
          ]),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).pop(_qty),
            icon: const Icon(Icons.add_shopping_cart),
            label: const Text('Add to cart'),
          ),
        ]),
      ),
    );
  }
}

class CartPage extends StatefulWidget {
  const CartPage({super.key, required this.cart});
  final Map<Product, int> cart;
  @override
  State<CartPage> createState() => _CartPageState();
}

class _CartPageState extends State<CartPage> {
  final _note = TextEditingController();
  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }
  Future<bool> _confirmDiscard() async {
    final leave = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Discard your note?'),
        content: const Text('Your delivery note will be lost.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Stay')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Discard')),
        ],
      ),
    );
    return leave ?? false;
  }
  @override
  Widget build(BuildContext context) {
    final total = widget.cart.entries.fold(0, (sum, e) => sum + e.key.price * e.value);
    return PopScope<bool>(
      canPop: _note.text.isEmpty,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final leave = await _confirmDiscard();
        if (!leave || !mounted) return;
        Navigator.of(context).pop();
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('Cart')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          for (final MapEntry(key: p, value: qty) in widget.cart.entries)
            ListTile(leading: Icon(p.icon), title: Text(p.name), trailing: Text(p.lineLabel(qty))),
          ListTile(title: const Text('Total'), trailing: Text('₹$total')),
          TextField(
            controller: _note,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'Delivery note'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Place order'),
          ),
        ]),
      ),
    );
  }
}
