import 'package:flutter/material.dart';

// flutter run --dart-define=FLAVOR=dev
// flutter build appbundle --dart-define=FLAVOR=prod --dart-define=APP_VERSION=1.0.0+1
const flavor = String.fromEnvironment('FLAVOR', defaultValue: 'dev');
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'https://jsonplaceholder.typicode.com');
const appVersion = String.fromEnvironment('APP_VERSION', defaultValue: 'dev build');
const isProd = flavor == 'prod';

void main() => runApp(const NotesApp());

class NotesApp extends StatelessWidget {
  const NotesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: isProd ? 'Notes' : 'Notes DEV',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0))),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: 'About',
            onPressed: () => showAboutDialog(
              context: context,
              applicationName: 'Notes',
              applicationVersion: appVersion,
              applicationIcon: const Icon(Icons.sticky_note_2, size: 40),
              children: const [Text('Made with Flutter by Ralfiz Academy.')],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          if (!isProd)
            Container(
              width: double.infinity,
              color: Colors.orange,
              padding: const EdgeInsets.all(6),
              child: const Text(
                'DEV BUILD',
                textAlign: TextAlign.center,
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black),
              ),
            ),
          const ListTile(leading: Icon(Icons.flag), title: Text('Flavor'), subtitle: Text(flavor)),
          const ListTile(leading: Icon(Icons.cloud), title: Text('API'), subtitle: Text(apiUrl)),
          const Expanded(child: Center(child: Text('Your notes appear here'))),
        ],
      ),
    );
  }
}
