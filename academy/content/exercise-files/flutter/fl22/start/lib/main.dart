// Recipe Book - lesson 3.1 (STARTER): the recipe detail screen.
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
      home: const RecipeDetailPage(recipe: sampleRecipe),
    );
  }
}

class Recipe {
  const Recipe({
    required this.title,
    required this.minutes,
    required this.serves,
    required this.kcal,
    required this.ingredients,
  });

  final String title;
  final int minutes;
  final int serves;
  final int kcal;
  final List<(String, String)> ingredients; // (name, quantity)

  String get timeLabel => '$minutes min';
  String get servesLabel => '$serves';
  String get kcalLabel => '$kcal';
}

const sampleRecipe = Recipe(
  title: 'Grandma’s slow-cooked Malabar chicken biryani',
  minutes: 90,
  serves: 6,
  kcal: 520,
  ingredients: [
    ('Basmati rice', '500 g'),
    ('Chicken, bone-in pieces', '1 kg'),
    ('Onions, thinly sliced', '4'),
    ('Ghee', '3 tbsp'),
    ('Garam masala', '2 tsp'),
    ('Mint and coriander leaves', '1 cup'),
    ('Cashews and raisins', 'a handful'),
  ],
);

class RecipeDetailPage extends StatelessWidget {
  const RecipeDetailPage({super.key, required this.recipe});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Recipe Book')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 12,
            children: [
              // TODO(1): replace this Text with a Row: Icons.restaurant,
              // a SizedBox(width: 8) and the title in Expanded, so the long
              // title wraps instead of overflowing. Use text.headlineSmall.
              Text(recipe.title, style: text.headlineSmall),

              // TODO(2): add a Row with three Expanded InfoTile widgets:
              // (Icons.schedule, recipe.timeLabel, 'Time'),
              // (Icons.people, recipe.servesLabel, 'Serves'),
              // (Icons.local_fire_department, recipe.kcalLabel, 'kcal').

              const Divider(),
              Text('Ingredients', style: text.titleMedium),

              // TODO(4): wrap this ListView in Expanded (it needs a bounded
              // height inside a Column), then build one Row per ingredient:
              // check icon (size 18), gap, Expanded(Text(name)), Text(qty).
              SizedBox(
                height: 200,
                child: ListView(
                  children: [
                    for (final (name, qty) in recipe.ingredients)
                      Text('$name - $qty'),
                  ],
                ),
              ),

              // TODO(5): add a Row (spacing: 12) with an OutlinedButton.icon
              // "Share" and a FilledButton.icon "Start cooking", each wrapped
              // in Expanded so they share the width equally.
            ],
          ),
        ),
      ),
    );
  }
}

class InfoTile extends StatelessWidget {
  const InfoTile(this.icon, this.value, this.label, {super.key});

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    // TODO(3): return a Column (mainAxisSize: MainAxisSize.min) with
    // Icon(icon) in the primary colour, the value in bold and the label
    // in labelSmall.
    return Text(value);
  }
}
