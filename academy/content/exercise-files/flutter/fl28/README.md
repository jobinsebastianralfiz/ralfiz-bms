# Lesson 4.2 lab: theming Travel Explorer

Move every design decision into AppTheme and add a working dark mode.

## Requirements
1. AppTheme.light() and AppTheme.dark() built from one seed (0xFF00796B).
2. MaterialApp uses theme, darkTheme and themeMode from a ValueNotifier<ThemeMode>.
3. An Appearance section with a SegmentedButton: System, Light, Dark.
4. Component themes: CardThemeData (radius 20, Clip.antiAlias),
   FilledButtonThemeData (minimum height 52), bold headlineSmall.
5. A TravelColors ThemeExtension with deal / onDeal colours for light and dark, used by DealTag.
6. No Colors.xxx constants inside screen widgets.

## Files
- start/lib/main.dart: light theme only, hard-coded colours. Complete TODO(1) to TODO(5).
- solution/lib/main.dart: the finished, fully themed app.

## Acceptance criteria
- Choosing Dark turns the whole app dark immediately; System follows the device.
- All destination names are readable in both modes.
- The "20% off" tag is pale yellow in light mode and dark amber in dark mode.
- Searching the screen widgets for "Colors." finds nothing.
