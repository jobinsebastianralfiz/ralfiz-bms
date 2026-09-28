import 'package:flutter/material.dart';

void main() => runApp(const RecipeBookApp());

class Recipe {
  const Recipe(this.name, this.minutes, this.level);
  final String name;
  final int minutes;
  final String level;

  String get info => '$minutes min · $level';
  bool get isQuick => minutes <= 30;
}

const recipes = <Recipe>[
  Recipe('Masala Dosa', 35, 'Easy'),
  Recipe('Lemon Rice', 20, 'Easy'),
  Recipe('Paneer Butter Masala', 45, 'Medium'),
  Recipe('Appam and Stew', 60, 'Medium'),
  Recipe('Egg Roast', 25, 'Easy'),
  Recipe('Kerala Fish Curry', 50, 'Hard'),
  Recipe('Banana Fritters', 15, 'Easy'),
  Recipe('Chicken Biryani', 90, 'Hard'),
];

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
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    // Used by TODO(2).
    final quick = recipes.where((r) => r.isQuick).toList();
    final count = quick.length;
    debugPrint('Quick recipes: $count');

    // TODO(1): Replace this Scaffold body with a CustomScrollView.
    //          Remove the appBar and add SliverAppBar.large(title: Text('Recipe Book'))
    //          as the first sliver.
    // TODO(2): Add SliverToBoxAdapter(child: SectionTitle('Quick (30 min or less)')),
    //          then a SliverToBoxAdapter holding SizedBox(height: 120) with a
    //          horizontal ListView.separated of QuickCard(recipe: quick[index]).
    // TODO(3): Add SectionTitle('All recipes') and a SliverPadding (horizontal 16)
    //          around SliverGrid.builder with SliverGridDelegateWithMaxCrossAxisExtent
    //          (maxCrossAxisExtent 220, spacing 12, childAspectRatio 3 / 4).
    return Scaffold(
      appBar: AppBar(title: const Text('Recipe Book')),
      body: ListView(
        children: [
          for (final recipe in recipes)
            ListTile(title: Text(recipe.name), subtitle: Text(recipe.info)),
        ],
      ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      child: Text(text, style: Theme.of(context).textTheme.titleMedium),
    );
  }
}

class QuickCard extends StatelessWidget {
  const QuickCard({super.key, required this.recipe});
  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SizedBox(
      width: 150,
      child: Card.filled(
        color: scheme.secondaryContainer,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(Icons.bolt, color: scheme.onSecondaryContainer),
              Text(recipe.name, maxLines: 2, overflow: TextOverflow.ellipsis),
              Text(recipe.info, style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}

class RecipeTile extends StatelessWidget {
  const RecipeTile({super.key, required this.recipe});
  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    // TODO(4): Return a Card(clipBehavior: Clip.antiAlias) with a Column
    //          (crossAxisAlignment: stretch): an Expanded ColoredBox using
    //          primaryContainer with a restaurant Icon, then a Padding(10) with
    //          the name (titleSmall, maxLines 1, ellipsis) and recipe.info (bodySmall).
    return Card(child: Center(child: Text(recipe.name)));
  }
}
