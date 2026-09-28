// Recipe Book - lesson 3.3 (STARTER): hero banner and badge.
// Compiles and runs as it is. Complete TODO(1) to TODO(5).
import 'package:flutter/material.dart';

void main() => runApp(const RecipeBookApp());

class RecipeBookApp extends StatelessWidget {
  const RecipeBookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Recipe Book',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange),
      ),
      home: const RecipeDetailPage(recipe: biryani),
    );
  }
}

class Recipe {
  const Recipe({
    required this.title,
    required this.minutes,
    required this.color,
    required this.imageUrl,
    required this.ingredients,
    this.isNew = false,
  });

  final String title;
  final int minutes;
  final Color color;
  final String imageUrl;
  final List<String> ingredients;
  final bool isNew;

  String get timeLabel => '$minutes min';
}

const biryani = Recipe(
  title: 'Chicken biryani',
  minutes: 90,
  color: Colors.deepOrange,
  imageUrl: 'https://picsum.photos/seed/biryani/800/500',
  isNew: true,
  ingredients: ['Basmati rice', 'Chicken', 'Onions', 'Ghee', 'Garam masala'],
);

class RecipeDetailPage extends StatefulWidget {
  const RecipeDetailPage({super.key, required this.recipe});

  final Recipe recipe;

  @override
  State<RecipeDetailPage> createState() => _RecipeDetailPageState();
}

class _RecipeDetailPageState extends State<RecipeDetailPage> {
  bool _saved = false;
  int _listCount = 0;

  @override
  Widget build(BuildContext context) {
    final recipe = widget.recipe;
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Recipe Book'),
        actions: [
          IconButton(
            onPressed: () {},
            tooltip: 'Shopping list',
            // TODO(5): wrap this Icon in a Badge whose label is
            // Text('$_listCount') and which is hidden when _listCount is 0.
            icon: const Icon(Icons.shopping_basket_outlined),
          ),
        ],
      ),
      body: ListView(
        children: [
          SizedBox(
            height: 240,
            // TODO(1): replace this ColoredBox with a Stack
            // (fit: StackFit.expand) whose first child is
            // Image.network(recipe.imageUrl, fit: BoxFit.cover) with an
            // errorBuilder that returns ColoredBox(color: recipe.color).
            // TODO(2): add a DecoratedBox with a LinearGradient from
            // Colors.transparent (top) to Colors.black87 (bottom).
            // TODO(3): add Positioned(left: 16, right: 16, bottom: 16) with a
            // Column (mainAxisSize.min, start aligned): the title in white
            // headlineSmall and the time in white70 bodyMedium.
            // TODO(4): if recipe.isNew, add a Positioned amber "NEW" pill at
            // top 12, left 12. Add a Positioned IconButton.filledTonal at
            // top 8, right 8 that toggles _saved with setState and shows
            // Icons.favorite or Icons.favorite_border.
            child: ColoredBox(
              color: recipe.color,
              child: Center(
                child: Text(
                  recipe.title,
                  style: text.headlineSmall?.copyWith(color: Colors.white),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text('Ingredients', style: text.titleMedium),
          ),
          for (final item in recipe.ingredients)
            ListTile(leading: const Icon(Icons.check), title: Text(item)),
          Padding(
            padding: const EdgeInsets.all(16),
            child: FilledButton.icon(
              onPressed: () => setState(() => _listCount++),
              icon: const Icon(Icons.add_shopping_cart),
              label: const Text('Add to shopping list'),
            ),
          ),
          // Remove this line once TODO(4) uses _saved.
          Text('Saved: $_saved', textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
