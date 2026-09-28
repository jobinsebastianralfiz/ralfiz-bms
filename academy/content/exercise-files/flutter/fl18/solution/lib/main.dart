// Business Card - SOLUTION (lesson 2.2)
// Paste into DartPad or a new Flutter project and run.
import 'package:flutter/material.dart';

void main() => runApp(const BusinessCardApp());

class BusinessCardApp extends StatelessWidget {
  const BusinessCardApp({super.key});

  static const _seed = Colors.teal;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Business Card',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: _seed),
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: _seed,
          brightness: Brightness.dark,
        ),
      ),
      themeMode: ThemeMode.system,
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
      appBar: AppBar(
        title: const Text('My Card'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Share',
            onPressed: () {},
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircleAvatar(
                radius: 48,
                backgroundColor: colors.primary,
                child: Text(
                  'AK',
                  style: text.headlineMedium?.copyWith(color: colors.onPrimary),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Asha Kumar',
                style: text.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              Text(
                'Flutter Developer',
                style: text.titleMedium?.copyWith(color: colors.primary),
              ),
              const SizedBox(height: 24),
              const Card(
                margin: EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  children: [
                    ContactRow(icon: Icons.phone, text: '+91 98765 43210'),
                    Divider(height: 1),
                    ContactRow(icon: Icons.email, text: 'asha@example.com'),
                    Divider(height: 1),
                    ContactRow(icon: Icons.location_on, text: 'Kochi, India'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// One line of contact details. Extracted so the card stays readable.
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
