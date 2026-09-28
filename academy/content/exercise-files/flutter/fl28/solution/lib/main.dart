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

  @override
  TravelColors copyWith({Color? deal, Color? onDeal}) =>
      TravelColors(deal: deal ?? this.deal, onDeal: onDeal ?? this.onDeal);

  @override
  TravelColors lerp(TravelColors? other, double t) {
    if (other is! TravelColors) return this;
    return TravelColors(
      deal: Color.lerp(deal, other.deal, t)!,
      onDeal: Color.lerp(onDeal, other.onDeal, t)!,
    );
  }
}

abstract final class AppTheme {
  static const seed = Color(0xFF00796B);

  static ThemeData light() => _build(Brightness.light, TravelColors.light);
  static ThemeData dark() => _build(Brightness.dark, TravelColors.dark);

  static ThemeData _build(Brightness brightness, TravelColors travel) {
    final scheme = ColorScheme.fromSeed(seedColor: seed, brightness: brightness);
    return ThemeData(
      colorScheme: scheme,
      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontWeight: FontWeight.w700),
      ),
      cardTheme: CardThemeData(
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(minimumSize: const Size(64, 52)),
      ),
      extensions: [travel],
    );
  }
}

class TravelApp extends StatelessWidget {
  const TravelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: themeMode,
      builder: (context, mode, _) => MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: mode,
        home: const HomePage(),
      ),
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
          ValueListenableBuilder(
            valueListenable: themeMode,
            builder: (context, mode, _) => SegmentedButton<ThemeMode>(
              segments: const [
                ButtonSegment(value: ThemeMode.system, label: Text('System')),
                ButtonSegment(value: ThemeMode.light, label: Text('Light')),
                ButtonSegment(value: ThemeMode.dark, label: Text('Dark')),
              ],
              selected: {mode},
              onSelectionChanged: (set) => themeMode.value = set.first,
            ),
          ),
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
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.surfaceContainerHigh,
      child: ListTile(
        title: Text(name, style: TextStyle(color: scheme.onSurface)),
        subtitle: Text(place, style: TextStyle(color: scheme.onSurfaceVariant)),
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
    final travel = Theme.of(context).extension<TravelColors>()!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: travel.deal,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(label, style: TextStyle(color: travel.onDeal)),
    );
  }
}
