import 'package:flutter/material.dart';

// STARTER - lesson 7.3: Notes app. It runs, but everything is kept in
// memory: restart the app and your notes and theme choice are gone.
// Add packages first: flutter pub add sqflite path shared_preferences

class Note {
  const Note({this.id, required this.title, required this.body, required this.updatedAt});
  final int? id;
  final String title;
  final String body;
  final DateTime updatedAt;

  // TODO(1): add Map<String, Object?> toMap() (columns id, title, body,
  // updated_at as millisecondsSinceEpoch; leave id out when it is null)
  // and factory Note.fromMap using a switch with a map pattern.
}

class NotesDatabase {
  // In-memory stand-in with the same methods the real one will have.
  final List<Note> _rows = [];
  int _nextId = 1;

  // TODO(2): make this open a real database: p.join(await getDatabasesPath(),
  // 'notes.db'), openDatabase with version 1 and an onCreate that runs
  // CREATE TABLE notes(...). Use a private constructor that takes the Database.
  static Future<NotesDatabase> open() async => NotesDatabase();

  // TODO(3): replace each body with _db.query / insert / update / delete.
  Future<List<Note>> all() async =>
      [..._rows]..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));

  Future<int> insert(Note note) async {
    final id = _nextId++;
    _rows.add(Note(id: id, title: note.title, body: note.body, updatedAt: note.updatedAt));
    return id;
  }

  Future<int> update(Note note) async {
    final i = _rows.indexWhere((n) => n.id == note.id);
    if (i == -1) return 0;
    _rows[i] = note;
    return 1;
  }

  Future<int> delete(int id) async {
    final before = _rows.length;
    _rows.removeWhere((n) => n.id == id);
    return before - _rows.length;
  }
}

// TODO(4): make main async, call WidgetsFlutterBinding.ensureInitialized(),
// open the database and read the darkMode bool with SharedPreferencesAsync.
Future<void> main() async {
  final db = await NotesDatabase.open();
  runApp(NotesApp(db: db));
}

class NotesApp extends StatefulWidget {
  const NotesApp({super.key, required this.db});
  final NotesDatabase db;

  @override
  State<NotesApp> createState() => _NotesAppState();
}

class _NotesAppState extends State<NotesApp> {
  bool _dark = false;

  // TODO(5): also save the value with prefs.setBool('darkMode', value).
  void _setDark(bool value) => setState(() => _dark = value);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Notes',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.amber)),
      darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.amber, brightness: Brightness.dark)),
      themeMode: _dark ? ThemeMode.dark : ThemeMode.light,
      home: NotesPage(db: widget.db, dark: _dark, onDarkChanged: _setDark),
    );
  }
}

class NotesPage extends StatefulWidget {
  const NotesPage({super.key, required this.db, required this.dark, required this.onDarkChanged});
  final NotesDatabase db;
  final bool dark;
  final ValueChanged<bool> onDarkChanged;

  @override
  State<NotesPage> createState() => _NotesPageState();
}

class _NotesPageState extends State<NotesPage> {
  List<Note> _notes = [];

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final notes = await widget.db.all();
    if (mounted) setState(() => _notes = notes);
  }

  Future<void> _add() async {
    // TODO(6): open an editor page (New note / Edit note) instead of this
    // fixed note, and let tapping a tile edit it with db.update.
    await widget.db.insert(Note(title: 'Note ' + (_notes.length + 1).toString(),
        body: 'Written at ' + DateTime.now().toString(), updatedAt: DateTime.now()));
    await _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notes'), actions: [
        IconButton(
          icon: Icon(widget.dark ? Icons.light_mode : Icons.dark_mode),
          onPressed: () => widget.onDarkChanged(!widget.dark),
        ),
      ]),
      floatingActionButton:
          FloatingActionButton(onPressed: _add, child: const Icon(Icons.add)),
      // TODO(7): wrap each tile in a Dismissible that deletes the note.
      // Remove it from _notes with setState immediately, then call db.delete.
      body: _notes.isEmpty
          ? const Center(child: Text('No notes yet. Tap + to write one.'))
          : ListView(children: [
              for (final note in _notes)
                ListTile(
                  title: Text(note.title),
                  subtitle: Text(note.body, maxLines: 1, overflow: TextOverflow.ellipsis),
                ),
            ]),
    );
  }
}
