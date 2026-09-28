// Recipe Book - lesson 3.1 (SOLUTION): the recipe detail screen.
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
              // Title row: Expanded lets a long title wrap.
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.restaurant),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(recipe.title, style: text.headlineSmall),
                  ),
                ],
              ),
              // Stats row: three equal thirds.
              Row(
                children: [
                  Expanded(
                    child: InfoTile(Icons.schedule, recipe.timeLabel, 'Time'),
                  ),
                  Expanded(
                    child: InfoTile(Icons.people, recipe.servesLabel, 'Serves'),
                  ),
                  Expanded(
                    child: InfoTile(
                        Icons.local_fire_department, recipe.kcalLabel, 'kcal'),
                  ),
                ],
              ),
              const Divider(),
              Text('Ingredients', style: text.titleMedium),
              // The list takes the remaining height and scrolls.
              Expanded(
                child: ListView(
                  children: [
                    for (final (name, qty) in recipe.ingredients)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: [
                            const Icon(Icons.check, size: 18),
                            const SizedBox(width: 8),
                            Expanded(child: Text(name)),
                            Text(qty, style: text.labelLarge),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
              Row(
                spacing: 12,
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.share),
                      label: const Text('Share'),
                    ),
                  ),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.play_arrow),
                      label: const Text('Start cooking'),
                    ),
                  ),
                ],
              ),
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
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
      ],
    );
  }
}
