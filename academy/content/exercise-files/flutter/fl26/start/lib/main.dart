import 'package:flutter/material.dart';

void main() => runApp(const RecipeBookApp());

enum WindowSize { compact, medium, expanded }

// TODO(1): Return compact under 600, medium under 840, otherwise expanded.
//          Use a switch expression with relational patterns (< 600 => ...).
WindowSize windowSizeOf(double width) => WindowSize.compact;

class Recipe {
  const Recipe(this.name, this.minutes, this.level, this.steps);
  final String name;
  final int minutes;
  final String level;
  final List<String> steps;
  String get info => '$minutes min · $level';
}

const recipes = <Recipe>[
  Recipe('Masala Dosa', 35, 'Easy',
      ['Soak rice and dal', 'Grind and ferment', 'Cook potato masala', 'Spread, fill and fold']),
  Recipe('Lemon Rice', 20, 'Easy',
      ['Cook rice', 'Temper mustard and curry leaves', 'Add lemon juice and mix']),
  Recipe('Egg Roast', 25, 'Easy',
      ['Boil eggs', 'Fry onions until brown', 'Add spices and eggs']),
  Recipe('Kerala Fish Curry', 50, 'Hard',
      ['Soak kudampuli', 'Make the masala', 'Simmer fish in the gravy']),
];

class RecipeBookApp extends StatelessWidget {
  const RecipeBookApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange)),
      home: const AdaptiveHome(),
    );
  }
}

class AdaptiveHome extends StatefulWidget {
  const AdaptiveHome({super.key});
  @override
  State<AdaptiveHome> createState() => _AdaptiveHomeState();
}

class _AdaptiveHomeState extends State<AdaptiveHome> {
  int _tab = 0;
  Recipe? _selected;
  static const _destinations = [
    (icon: Icons.home_outlined, selected: Icons.home, label: 'Recipes'),
    (icon: Icons.favorite_outline, selected: Icons.favorite, label: 'Saved'),
    (icon: Icons.person_outline, selected: Icons.person, label: 'Profile'),
  ];
  void _selectTab(int index) => setState(() => _tab = index);
  void _openRecipe(Recipe recipe, bool twoPane) {
    if (twoPane) {
      setState(() => _selected = recipe);
      return;
    }
    Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (context) =>
          Scaffold(appBar: AppBar(title: Text(recipe.name)), body: RecipeDetail(recipe: recipe)),
    ));
  }
  @override
  Widget build(BuildContext context) {
    // TODO(2): Compute the window size from MediaQuery.sizeOf(context).width.
    const size = WindowSize.compact;
    final twoPane = size == WindowSize.expanded;
    final page = _tab == 0
        ? RecipesPane(
            twoPane: twoPane,
            selected: _selected,
            onSelect: (r) => _openRecipe(r, twoPane),
          )
        : Center(child: Text(_destinations[_tab].label));
    // TODO(3): If size is not compact, return a Scaffold whose body is a Row:
    //          NavigationRail (extended on expanded, labelType all on medium),
    //          VerticalDivider(width: 1), Expanded(child: page).
    // TODO(5): Wrap that Row in SafeArea.
    return Scaffold(
      appBar: AppBar(title: const Text('Recipe Book')),
      body: page,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: _selectTab,
        destinations: [
          for (final d in _destinations)
            NavigationDestination(
                icon: Icon(d.icon), selectedIcon: Icon(d.selected), label: d.label),
        ],
      ),
    );
  }
}

class RecipesPane extends StatelessWidget {
  const RecipesPane(
      {super.key, required this.twoPane, required this.selected, required this.onSelect});
  final bool twoPane;
  final Recipe? selected;
  final ValueChanged<Recipe> onSelect;
  @override
  Widget build(BuildContext context) {
    final list = ListView.builder(
      itemCount: recipes.length,
      itemBuilder: (context, index) {
        final recipe = recipes[index];
        return ListTile(
          title: Text(recipe.name),
          subtitle: Text(recipe.info),
          selected: twoPane && recipe == selected,
          onTap: () => onSelect(recipe),
        );
      },
    );
    // TODO(4): When twoPane is true, return a Row with SizedBox(width: 320, child: list),
    //          a VerticalDivider and an Expanded detail: "Pick a recipe" when selected
    //          is null, otherwise RecipeDetail. Use a switch expression on selected.
    return list;
  }
}

class RecipeDetail extends StatelessWidget {
  const RecipeDetail({super.key, required this.recipe});
  final Recipe recipe;
  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(recipe.name, style: text.headlineSmall),
        Text(recipe.info, style: text.bodyMedium),
        const SizedBox(height: 12),
        for (final (i, step) in recipe.steps.indexed)
          ListTile(
            leading: CircleAvatar(child: Text((i + 1).toString())),
            title: Text(step),
          ),
      ],
    );
  }
}
