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
    final quick = recipes.where((r) => r.isQuick).toList();
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          const SliverAppBar.large(title: Text('Recipe Book')),
          const SliverToBoxAdapter(
            child: SectionTitle('Quick (30 min or less)'),
          ),
          SliverToBoxAdapter(
            child: SizedBox(
              height: 120,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: quick.length,
                separatorBuilder: (context, index) => const SizedBox(width: 12),
                itemBuilder: (context, index) => QuickCard(recipe: quick[index]),
              ),
            ),
          ),
          const SliverToBoxAdapter(child: SectionTitle('All recipes')),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            sliver: SliverGrid.builder(
              gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                maxCrossAxisExtent: 220,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 3 / 4,
              ),
              itemCount: recipes.length,
              itemBuilder: (context, index) => RecipeTile(recipe: recipes[index]),
            ),
          ),
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
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: ColoredBox(
              color: scheme.primaryContainer,
              child: Icon(Icons.restaurant,
                  size: 40, color: scheme.onPrimaryContainer),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(recipe.name,
                    style: text.titleSmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                Text(recipe.info, style: text.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
