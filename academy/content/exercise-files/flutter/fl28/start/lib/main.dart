import 'package:flutter/material.dart';

void main() => runApp(const TravelApp());

final themeMode = ValueNotifier(ThemeMode.system);

@immutable
class TravelColors extends ThemeExtension<TravelColors> {
  const TravelColors({required this.deal, required this.onDeal});
  final Color deal;
  final Color onDeal;

  static const light =
      TravelColors(deal: Color(0xFFFFE08A), onDeal: Color(0xFF3D2E00));
  static const dark =
      TravelColors(deal: Color(0xFF5B4300), onDeal: Color(0xFFFFE08A));

  // TODO(4): return a copy with the given colours replaced.
  @override
  TravelColors copyWith({Color? deal, Color? onDeal}) => this;

  // TODO(4): blend with Color.lerp(a, b, t)! for both colours.
  @override
  TravelColors lerp(TravelColors? other, double t) => this;
}

abstract final class AppTheme {
  static const seed = Color(0xFF00796B);

  static ThemeData light() => _build(Brightness.light, TravelColors.light);
  // TODO(1): add dark() that uses Brightness.dark and TravelColors.dark.

  static ThemeData _build(Brightness brightness, TravelColors travel) {
    final scheme = ColorScheme.fromSeed(seedColor: seed, brightness: brightness);
    // TODO(3): add textTheme (bold headlineSmall), cardTheme: CardThemeData
    //          (Clip.antiAlias, radius 20) and filledButtonTheme (minimumSize 64 x 52).
    // TODO(4): add extensions: [travel].
    return ThemeData(colorScheme: scheme);
  }
}

class TravelApp extends StatelessWidget {
  const TravelApp({super.key});

  @override
  Widget build(BuildContext context) {
    // TODO(1): wrap MaterialApp in ValueListenableBuilder(valueListenable: themeMode)
    //          and pass darkTheme: AppTheme.dark() and themeMode: mode.
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Explorer')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Appearance', style: text.titleMedium),
          const SizedBox(height: 8),
          // TODO(2): SegmentedButton<ThemeMode> (System, Light, Dark) that reads
          //          themeMode.value and sets themeMode.value = set.first.
          //          Tip: wrap it in a ValueListenableBuilder so it redraws.
          const SizedBox(height: 16),
          Text('Top deals', style: text.headlineSmall),
          const DestinationTile(name: 'Goa', place: 'India · Beach', deal: '20% off'),
          const DestinationTile(name: 'Jaipur', place: 'India · Heritage', deal: 'Free tour'),
          const DestinationTile(name: 'Dubai', place: 'UAE · City'),
          const SizedBox(height: 16),
          FilledButton(onPressed: () {}, child: const Text('See all deals')),
        ],
      ),
    );
  }
}

class DestinationTile extends StatelessWidget {
  const DestinationTile({super.key, required this.name, required this.place, this.deal});
  final String name;
  final String place;
  final String? deal;

  @override
  Widget build(BuildContext context) {
    // TODO(5): replace Colors.white and Colors.black with colour roles
    //          (surfaceContainerHigh for the card, onSurface / onSurfaceVariant for text).
    return Card(
      color: Colors.white,
      child: ListTile(
        title: Text(name, style: const TextStyle(color: Colors.black)),
        subtitle: Text(place, style: const TextStyle(color: Colors.black54)),
        trailing: switch (deal) {
          null => null,
          final String label => DealTag(label),
        },
      ),
    );
  }
}

class DealTag extends StatelessWidget {
  const DealTag(this.label, {super.key});
  final String label;

  @override
  Widget build(BuildContext context) {
    // TODO(4): read Theme.of(context).extension<TravelColors>()! and use
    //          travel.deal for the background and travel.onDeal for the text.
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.amber,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(label),
    );
  }
}
