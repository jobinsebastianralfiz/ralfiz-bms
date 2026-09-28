// Recipe Book - lesson 3.2 (STARTER): the decorated recipe list.
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
      // TODO(5): wrap this ListView in Center and
      // ConstrainedBox(constraints: const BoxConstraints(maxWidth: 600)).
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [for (final r in recipes) RecipeCard(recipe: r)],
      ),
    );
  }
}

class RecipeCard extends StatelessWidget {
  const RecipeCard({super.key, required this.recipe});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    // TODO(1): return a Container with
    //   margin: horizontal 16, vertical 6
    //   padding: all 12
    //   decoration: BoxDecoration with colorScheme.surface, a radius of 16,
    //   Border.all(color: colorScheme.outlineVariant) and one BoxShadow
    //   (Colors.black.withValues(alpha: 0.06), blurRadius 10, offset (0, 3)).
    // Its child is a Row (spacing: 12) with:
    //   Thumbnail(color: recipe.color, icon: recipe.icon)
    //   TODO(3): an Expanded Column (crossAxisAlignment start) with the
    //            title in titleMedium and the category in bodySmall
    //   TODO(4): a pill Container showing recipe.timeLabel (horizontal
    //            padding 10, vertical 4, primaryContainer colour,
    //            BorderRadius.circular(999))
    return ListTile(
      title: Text(recipe.title),
      subtitle: Text(recipe.category),
      trailing: Text(recipe.timeLabel),
    );
  }
}

class Thumbnail extends StatelessWidget {
  const Thumbnail({super.key, required this.color, required this.icon});

  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    // TODO(2): return a 72 x 72 Container whose BoxDecoration has a
    // LinearGradient from color.withValues(alpha: 0.55) to color
    // (topLeft to bottomRight) and a radius of 12. Its child is a white
    // Icon(icon, size: 32). No alignment is needed: the Container passes
    // tight 72 x 72 constraints to the Icon, and Icon centres its glyph.
    return Icon(icon, color: color);
  }
}
