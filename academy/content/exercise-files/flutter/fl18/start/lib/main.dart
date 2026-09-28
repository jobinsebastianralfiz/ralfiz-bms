// Business Card - STARTER (lesson 2.2)
// This file runs as it is and shows temporary placeholder content.
// Fill in TODO(1) to TODO(7). Use your own name and details if you like.
import 'package:flutter/material.dart';

void main() => runApp(const BusinessCardApp());

class BusinessCardApp extends StatelessWidget {
  const BusinessCardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Business Card',
      // TODO(1): Hide the debug banner.
      // TODO(2): Add a theme: ThemeData(colorScheme: ColorScheme.fromSeed(
      //   seedColor: Colors.teal)).
      // TODO(7): Add a darkTheme from the same seed with
      //   brightness: Brightness.dark, and themeMode: ThemeMode.system.
      home: const CardPage(),
    );
  }
}

class CardPage extends StatelessWidget {
  const CardPage({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    return Scaffold(
      // TODO(3): Add an AppBar with the title 'My Card', centerTitle: true
      //   and a share IconButton in actions.
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // TODO(4): A CircleAvatar (radius 48, backgroundColor
              //   colors.primary) showing your initials in
              //   text.headlineMedium with colors.onPrimary.
              const SizedBox(height: 16),
              // TODO(5): Your name in text.headlineSmall (bold) and your job
              //   title in text.titleMedium with colors.primary.
              Text('Your name here', style: text.bodyMedium),
              const SizedBox(height: 24),
              // TODO(6): A Card with horizontal margin 24 holding a Column of
              //   ContactRow widgets (phone, email, location) separated by
              //   Divider(height: 1).
              ContactRow(icon: Icons.phone, text: colors.primary.toString()),
            ],
          ),
        ),
      ),
    );
  }
}

/// One line of contact details.
class ContactRow extends StatelessWidget {
  const ContactRow({super.key, required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(text),
    );
  }
}
