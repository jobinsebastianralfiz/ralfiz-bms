import 'package:flutter/material.dart';

// TODO(1): read these with String.fromEnvironment('FLAVOR' / 'API_URL' / 'APP_VERSION')
// and sensible defaults: 'dev', 'https://jsonplaceholder.typicode.com', 'dev build'.
const flavor = 'dev';
const apiUrl = 'https://jsonplaceholder.typicode.com';
const appVersion = 'dev build';
const isProd = flavor == 'prod';

void main() => runApp(const NotesApp());

class NotesApp extends StatelessWidget {
  const NotesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      // TODO(2): 'Notes' in prod, 'Notes DEV' otherwise.
      title: 'Notes',
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
            // TODO(4): showAboutDialog with applicationName 'Notes',
            // applicationVersion: appVersion and an applicationIcon.
            onPressed: () {},
          ),
        ],
      ),
      body: const Column(
        children: [
          // TODO(2): orange 'DEV BUILD' strip when !isProd.
          // TODO(3): ListTiles for Flavor (flavor) and API (apiUrl).
          Expanded(child: Center(child: Text('Your notes appear here'))),
        ],
      ),
    );
  }
}
