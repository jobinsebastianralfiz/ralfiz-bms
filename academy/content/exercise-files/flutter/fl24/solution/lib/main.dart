// Recipe Book - lesson 3.3 (SOLUTION): hero banner and badge.
// Paste into lib/main.dart of a new project, or into DartPad.
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
            icon: Badge(
              label: Text('$_listCount'),
              isLabelVisible: _listCount > 0,
              child: const Icon(Icons.shopping_basket_outlined),
            ),
          ),
        ],
      ),
      body: ListView(
        children: [
          SizedBox(
            height: 240,
            child: Stack(
              fit: StackFit.expand,
              children: [
                // 1. Photo (back layer)
                Image.network(
                  recipe.imageUrl,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stack) =>
                      ColoredBox(color: recipe.color),
                ),
                // 2. Scrim so white text is readable on any photo
                const DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, Colors.black87],
                    ),
                  ),
                ),
                // 3. Title and time, stretched between left and right
                Positioned(
                  left: 16,
                  right: 16,
                  bottom: 16,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(recipe.title,
                          style: text.headlineSmall
                              ?.copyWith(color: Colors.white)),
                      Text(recipe.timeLabel,
                          style: text.bodyMedium
                              ?.copyWith(color: Colors.white70)),
                    ],
                  ),
                ),
                // 4. NEW pill (top left), only for new recipes
                if (recipe.isNew)
                  Positioned(
                    top: 12,
                    left: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.amber,
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text('NEW', style: text.labelMedium),
                    ),
                  ),
                // 5. Favourite button (top right, front layer)
                Positioned(
                  top: 8,
                  right: 8,
                  child: IconButton.filledTonal(
                    onPressed: () => setState(() => _saved = !_saved),
                    tooltip: _saved ? 'Remove from saved' : 'Save',
                    icon: Icon(_saved ? Icons.favorite : Icons.favorite_border),
                  ),
                ),
              ],
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
        ],
      ),
    );
  }
}
