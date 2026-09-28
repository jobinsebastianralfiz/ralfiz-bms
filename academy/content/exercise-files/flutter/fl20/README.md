# Lab 2.4: Brew Lab menu

Build the menu screen of a small cafe app using theme text styles, Text.rich,
a custom font, bundled photos, a network banner and icons.

## Files
- pubspec.yaml: declares assets/images/ and the Pacifico font.
- start/lib/main.dart: compiles, with TODO(1) to TODO(3).
- solution/lib/main.dart: the finished screen.

## Setup
1. Run: flutter create brew_lab
2. Inside brew_lab create two folders: assets/images and assets/fonts.
3. Put four photos (any JPG files) in assets/images named exactly:
   latte.jpg, cold_brew.jpg, chai.jpg, cake.jpg
4. Download the Pacifico family from fonts.google.com and copy
   Pacifico-Regular.ttf into assets/fonts.
5. Replace pubspec.yaml with the one from this lab. If your project has a
   different name, change the name: line back to it.
6. Run: flutter pub get
7. Replace lib/main.dart with start/lib/main.dart and run the app.

Note: DartPad cannot load your local assets, so run this lab on an
emulator, a device, Chrome or desktop.

## Tasks
1. TODO(1): Pacifico title and the Text.rich opening-hours line.
2. TODO(2): Image.network banner with loadingBuilder and errorBuilder.
3. TODO(3): Image.asset thumbnails in ClipRRect and a star rating Row.

## Acceptance criteria
- The AppBar title "Brew Lab" is drawn in the Pacifico script font.
- The line reads "Open today until 9 pm" and only "until 9 pm" is bold and in
  the primary colour.
- While the banner loads a spinner shows; with no network a broken_image icon
  shows instead of a red error box.
- Each of the four menu rows shows its own photo with rounded corners, the
  price with the rupee sign and an amber star with the rating.
- Renaming one photo file makes that row show the fallback image icon, and
  restoring the name fixes it after a full restart (not hot reload).
