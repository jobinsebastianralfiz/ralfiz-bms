import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'notes_database.dart';

// SOLUTION - lesson 7.3: Notes app (sqflite for notes, shared_preferences
// for the theme). Run on an Android or iOS device or emulator.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final db = await NotesDatabase.open();
  final prefs = SharedPreferencesAsync();
  final dark = await prefs.getBool('darkMode') ?? false;
  runApp(NotesApp(db: db, prefs: prefs, initialDark: dark));
}

class NotesApp extends StatefulWidget {
  const NotesApp({super.key, required this.db, required this.prefs, required this.initialDark});
  final NotesDatabase db;
  final SharedPreferencesAsync prefs;
  final bool initialDark;

  @override
  State<NotesApp> createState() => _NotesAppState();
}

class _NotesAppState extends State<NotesApp> {
  late bool _dark = widget.initialDark;

  Future<void> _setDark(bool value) async {
    setState(() => _dark = value);
    await widget.prefs.setBool('darkMode', value);
  }

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

  Future<void> _openEditor([Note? note]) async {
    final result = await Navigator.push<Note>(
        context, MaterialPageRoute(builder: (_) => EditNotePage(note: note)));
    if (result == null) return;
    if (result.id == null) {
      await widget.db.insert(result);
    } else {
      await widget.db.update(result);
    }
    await _reload();
  }

  void _delete(Note note) {
    // Remove from the list NOW, so the dismissed tile leaves the tree.
    setState(() => _notes = [for (final n in _notes) if (n.id != note.id) n]);
    widget.db.delete(note.id!);
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Notes'), actions: [
        IconButton(
          icon: Icon(widget.dark ? Icons.light_mode : Icons.dark_mode),
          onPressed: () => widget.onDarkChanged(!widget.dark),
        ),
      ]),
      floatingActionButton: FloatingActionButton(
          onPressed: () => _openEditor(), child: const Icon(Icons.add)),
      body: _notes.isEmpty
          ? const Center(child: Text('No notes yet. Tap + to write one.'))
          : ListView(children: [
              for (final note in _notes)
                Dismissible(
                  key: ValueKey(note.id),
                  direction: DismissDirection.endToStart,
                  onDismissed: (_) => _delete(note),
                  background: Container(
                    color: colors.error,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 16),
                    child: Icon(Icons.delete, color: colors.onError),
                  ),
                  child: ListTile(
                    title: Text(note.title),
                    subtitle: Text(note.body, maxLines: 1, overflow: TextOverflow.ellipsis),
                    onTap: () => _openEditor(note),
                  ),
                ),
            ]),
    );
  }
}

class EditNotePage extends StatefulWidget {
  const EditNotePage({super.key, this.note});
  final Note? note;

  @override
  State<EditNotePage> createState() => _EditNotePageState();
}

class _EditNotePageState extends State<EditNotePage> {
  late final _title = TextEditingController(text: widget.note?.title);
  late final _body = TextEditingController(text: widget.note?.body);

  @override
  void dispose() {
    _title.dispose();
    _body.dispose();
    super.dispose();
  }

  void _save() {
    if (_title.text.trim().isEmpty) return;
    Navigator.pop(context, Note(id: widget.note?.id, title: _title.text.trim(),
        body: _body.text, updatedAt: DateTime.now()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.note == null ? 'New note' : 'Edit note'),
        actions: [IconButton(icon: const Icon(Icons.check), onPressed: _save)],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          TextField(controller: _title, decoration: const InputDecoration(labelText: 'Title')),
          const SizedBox(height: 12),
          Expanded(
            child: TextField(
              controller: _body,
              decoration: const InputDecoration(
                  labelText: 'Note', alignLabelWithHint: true, border: OutlineInputBorder()),
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
            ),
          ),
        ]),
      ),
    );
  }
}
