// Recipe Book - lesson 3.2 (SOLUTION): the decorated recipe list.
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
      home: const RecipeListPage(),
    );
  }
}

class Recipe {
  const Recipe({
    required this.title,
    required this.category,
    required this.minutes,
    required this.color,
    required this.icon,
  });

  final String title;
  final String category;
  final int minutes;
  final Color color;
  final IconData icon;

  String get timeLabel => '$minutes min';
}

const recipes = [
  Recipe(
    title: 'Grandma’s slow-cooked Malabar chicken biryani',
    category: 'Main course',
    minutes: 90,
    color: Colors.deepOrange,
    icon: Icons.rice_bowl,
  ),
  Recipe(
    title: 'Kerala vegetable stew',
    category: 'Main course',
    minutes: 35,
    color: Colors.green,
    icon: Icons.soup_kitchen,
  ),
  Recipe(
    title: 'Appam',
    category: 'Breakfast',
    minutes: 25,
    color: Colors.amber,
    icon: Icons.egg_alt,
  ),
  Recipe(
    title: 'Payasam',
    category: 'Dessert',
    minutes: 40,
    color: Colors.purple,
    icon: Icons.icecream,
  ),
];

class RecipeListPage extends StatelessWidget {
  const RecipeListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recipe Book')),
      // Center + maxWidth: full width on phones, 600 max on tablets.
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: ListView(
            padding: const EdgeInsets.symmetric(vertical: 8),
            children: [for (final r in recipes) RecipeCard(recipe: r)],
          ),
        ),
      ),
    );
  }
}

class RecipeCard extends StatelessWidget {
  const RecipeCard({super.key, required this.recipe});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colors.outlineVariant),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        spacing: 12,
        children: [
          Thumbnail(color: recipe.color, icon: recipe.icon),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 2,
              children: [
                Text(recipe.title, style: text.titleMedium),
                Text(recipe.category, style: text.bodySmall),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: colors.primaryContainer,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              recipe.timeLabel,
              style: text.labelMedium?.copyWith(
                color: colors.onPrimaryContainer,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class Thumbnail extends StatelessWidget {
  const Thumbnail({super.key, required this.color, required this.icon});

  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 72,
      height: 72,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [color.withValues(alpha: 0.55), color],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(icon, color: Colors.white, size: 32),
    );
  }
}
