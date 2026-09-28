import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class Product {
  const Product(this.id, this.name, this.price);
  final int id;
  final String name;
  final int price;
  String get priceLabel => '₹$price';
}

const products = [
  Product(1, 'Canvas Tote', 499), Product(2, 'Steel Bottle', 799),
  Product(3, 'Desk Lamp', 1299), Product(4, 'Wireless Mouse', 999),
];

class AuthState extends ChangeNotifier {
  bool _signedIn = false;
  bool get signedIn => _signedIn;
  void signIn() => _set(true);
  void signOut() => _set(false);
  void _set(bool value) {
    _signedIn = value;
    notifyListeners();
  }
}

final auth = AuthState();

final router = GoRouter(
  refreshListenable: auth,
  redirect: (context, state) {
    final loc = state.matchedLocation;
    if (!auth.signedIn && loc.startsWith('/account')) {
      final from = Uri.encodeComponent(loc);
      return '/login?from=$from';
    }
    if (auth.signedIn && loc == '/login') return state.uri.queryParameters['from'] ?? '/';
    return null;
  },
  errorBuilder: (context, state) =>
      NotFoundScreen(message: 'No page at ' + state.uri.path),
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, shell) => HomeShell(shell: shell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const CatalogScreen(),
            routes: [
              GoRoute(path: 'product/:id', name: 'product', builder: (context, state) {
                return ProductScreen(id: int.tryParse(state.pathParameters['id'] ?? ''));
              }),
            ],
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
              path: '/cart',
              builder: (context, state) =>
                  const MessagePage(title: 'Cart', children: [Text('Your cart is empty')])),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(
              path: '/account',
              builder: (context, state) => MessagePage(title: 'Account', children: [
                    const Text('Signed in as Asha'),
                    OutlinedButton(onPressed: auth.signOut, child: const Text('Sign out')),
                  ])),
        ]),
      ],
    ),
  ],
);

void main() => runApp(MaterialApp.router(
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      routerConfig: router,
    ));

class HomeShell extends StatelessWidget {
  const HomeShell({super.key, required this.shell});
  final StatefulNavigationShell shell;
  @override
  Widget build(BuildContext context) => Scaffold(
        body: shell,
        bottomNavigationBar: NavigationBar(
          selectedIndex: shell.currentIndex,
          onDestinationSelected: (i) =>
              shell.goBranch(i, initialLocation: i == shell.currentIndex),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.storefront), label: 'Shop'),
            NavigationDestination(icon: Icon(Icons.shopping_cart), label: 'Cart'),
            NavigationDestination(icon: Icon(Icons.person), label: 'Account'),
          ],
        ),
      );
}

class CatalogScreen extends StatelessWidget {
  const CatalogScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Shop Catalog')),
        body: ListView.builder(
          itemCount: products.length,
          itemBuilder: (context, i) {
            final p = products[i];
            final id = p.id;
            return ListTile(
              leading: const Icon(Icons.shopping_bag),
              title: Text(p.name),
              subtitle: Text(p.priceLabel),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.goNamed('product', pathParameters: {'id': '$id'}),
            );
          },
        ),
      );
}

class ProductScreen extends StatelessWidget {
  const ProductScreen({super.key, required this.id});
  final int? id;
  @override
  Widget build(BuildContext context) {
    final matches = products.where((p) => p.id == id).toList();
    if (matches.isEmpty) return const NotFoundScreen(message: 'Product not found');
    final p = matches.first;
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(p.name)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, spacing: 12, children: [
          Text(p.name, style: text.headlineSmall),
          Text(p.priceLabel, style: text.titleLarge),
          FilledButton.icon(
              onPressed: () => context.go('/cart'),
              icon: const Icon(Icons.add_shopping_cart),
              label: const Text('Add to cart')),
        ]),
      ),
    );
  }
}

class MessagePage extends StatelessWidget {
  const MessagePage({super.key, required this.title, required this.children});
  final String title;
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(title)),
        body: Center(
            child: Column(mainAxisSize: MainAxisSize.min, spacing: 12, children: children)),
      );
}

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});
  @override
  Widget build(BuildContext context) => MessagePage(title: 'Sign in', children: [
        const Text('Sign in to see your account'),
        FilledButton(onPressed: auth.signIn, child: const Text('Sign in')),
        TextButton(onPressed: () => context.go('/'), child: const Text('Keep browsing')),
      ]);
}

class NotFoundScreen extends StatelessWidget {
  const NotFoundScreen({super.key, required this.message});
  final String message;
  @override
  Widget build(BuildContext context) => MessagePage(title: 'Not found', children: [
        Text(message),
        FilledButton(onPressed: () => context.go('/'), child: const Text('Back to shop')),
      ]);
}
