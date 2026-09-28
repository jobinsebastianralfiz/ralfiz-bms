import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

// SOLUTION - lesson 7.3: the Note model and all SQLite code for the Notes app.

class Note {
  const Note({this.id, required this.title, required this.body, required this.updatedAt});
  final int? id;
  final String title;
  final String body;
  final DateTime updatedAt;

  Map<String, Object?> toMap() => {
        if (id != null) 'id': id,
        'title': title,
        'body': body,
        'updated_at': updatedAt.millisecondsSinceEpoch,
      };

  factory Note.fromMap(Map<String, Object?> map) => switch (map) {
        {'id': int id, 'title': String title, 'body': String body, 'updated_at': int ms} =>
          Note(id: id, title: title, body: body, updatedAt: DateTime.fromMillisecondsSinceEpoch(ms)),
        _ => throw FormatException('Bad note row: $map'),
      };
}

class NotesDatabase {
  NotesDatabase._(this._db);
  final Database _db;

  static Future<NotesDatabase> open() async {
    final path = p.join(await getDatabasesPath(), 'notes.db');
    final db = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) => db.execute(
        'CREATE TABLE notes(id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'title TEXT NOT NULL, body TEXT NOT NULL, updated_at INTEGER NOT NULL)',
      ),
    );
    return NotesDatabase._(db);
  }

  Future<List<Note>> all() async {
    final rows = await _db.query('notes', orderBy: 'updated_at DESC');
    return rows.map(Note.fromMap).toList();
  }

  Future<int> insert(Note note) => _db.insert('notes', note.toMap());

  Future<int> update(Note note) =>
      _db.update('notes', note.toMap(), where: 'id = ?', whereArgs: [note.id]);

  Future<int> delete(int id) =>
      _db.delete('notes', where: 'id = ?', whereArgs: [id]);
}
