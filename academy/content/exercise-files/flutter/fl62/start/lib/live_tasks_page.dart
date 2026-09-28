import 'package:flutter/material.dart';
// ignore: unused_import
import 'package:image_picker/image_picker.dart'; // used once TODO(4) is done
import 'package:supabase_flutter/supabase_flutter.dart';

import 'data/supabase_task_repository.dart';

class LiveTasksPage extends StatefulWidget {
  const LiveTasksPage({super.key, required this.repo});
  final TaskRepository repo;
  @override
  State<LiveTasksPage> createState() => _LiveTasksPageState();
}

class _LiveTasksPageState extends State<LiveTasksPage> {
  static const bucket = 'task-files';
  final _db = Supabase.instance.client;
  final _title = TextEditingController();
  final _pendingTitles = <String>[]; // titles this device is adding right now
  final _uploading = <String>{}; // task ids with an upload in progress
  final _signedUrls = <String, Future<String>>{}; // path -> signed URL
  Stream<List<Map<String, dynamic>>>? _tasks;
  RealtimeChannel? _channel;
  String? _projectId;
  bool _live = false;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    try {
      final projectId = await widget.repo.inboxProjectId();
      if (!mounted) return;
      setState(() {
        _projectId = projectId;
        // TODO(1): _tasks = _db.from('tasks').stream(primaryKey: ['id'])
        //   .eq('project_id', projectId).order('created_at', ascending: false);
      });
      // TODO(2): _channel = _db.channel('tasks-$projectId')
      //   .onPostgresChanges(event: insert, schema: 'public', table: 'tasks',
      //     filter: eq project_id, callback: _onInsert)
      //   .subscribe((status, error) { ...set _live when status is subscribed... });
    } on TaskFailure catch (e) {
      _show(e.message);
    }
  }

  void _onInsert(PostgresChangePayload payload) {
    final title = payload.newRecord['title'] as String? ?? '';
    if (_pendingTitles.remove(title)) return; // added on this device
    _show('Added on another device: ' + title);
  }

  Future<void> _add() async {
    final projectId = _projectId;
    final text = _title.text.trim();
    if (projectId == null || text.isEmpty) return;
    _pendingTitles.add(text);
    try {
      await widget.repo.add(projectId, text); // the stream redraws the list
      _title.clear();
    } on TaskFailure catch (e) {
      _pendingTitles.remove(text);
      _show(e.message);
    }
  }

  Future<void> _setDone(String id, bool done) async {
    try {
      await widget.repo.setDone(id, done);
    } on TaskFailure catch (e) {
      _show(e.message);
    }
  }

  Future<void> _attach(String taskId) async {
    // TODO(4): pick with ImagePicker().pickImage(source: ImageSource.gallery,
    //   maxWidth: 1600, imageQuality: 85); return if null.
    //   path = '$uid/$taskId/$stamp.jpg'; add taskId to _uploading;
    //   uploadBinary(path, bytes, fileOptions: FileOptions(contentType: ...));
    //   update tasks set attachment_path = path where id = taskId;
    //   catch StorageException; remove taskId from _uploading in finally.
    _show('TODO(4): upload a photo for ' + taskId + ' to ' + bucket);
  }

  // TODO(5): return _signedUrls.putIfAbsent(path, () => ...createSignedUrl(path, 3600));
  Future<String> _signedUrl(String path) => Future.error('TODO(5): sign ' + path);

  void _show(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  void dispose() {
    // TODO(3): remove the channel if it is not null.
    _title.dispose();
    super.dispose();
  }

  Widget _tile(Map<String, dynamic> row) {
    final id = row['id'] as String;
    final path = row['attachment_path'] as String?;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      ListTile(
        leading: Checkbox(value: row['done'] as bool, onChanged: (v) => _setDone(id, v ?? false)),
        title: Text(row['title'] as String),
        trailing: IconButton(icon: const Icon(Icons.attach_file),
            onPressed: _uploading.contains(id) ? null : () => _attach(id)),
      ),
      if (_uploading.contains(id)) const LinearProgressIndicator(),
      if (path != null)
        Padding(
          padding: const EdgeInsets.fromLTRB(72, 0, 16, 12),
          child: FutureBuilder<String>(
            future: _signedUrl(path),
            builder: (context, snap) {
              if (snap.hasError) return const Text('Could not load photo');
              if (!snap.hasData) return const SizedBox(height: 140, child: Center(child: CircularProgressIndicator()));
              return ClipRRect(borderRadius: BorderRadius.circular(12),
                  child: Image.network(snap.data!, height: 140, fit: BoxFit.cover));
            },
          ),
        ),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Inbox'), actions: [
        Icon(_live ? Icons.wifi : Icons.wifi_off),
        IconButton(icon: const Icon(Icons.logout), onPressed: () => _db.auth.signOut()),
      ]),
      body: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (!_live)
          Container(color: scheme.errorContainer, padding: const EdgeInsets.all(12),
              child: Text('Reconnecting… live updates paused',
                  style: TextStyle(color: scheme.onErrorContainer))),
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
          child: Row(spacing: 8, children: [
            Expanded(child: TextField(controller: _title,
                decoration: const InputDecoration(hintText: 'New task'))),
            IconButton.filled(icon: const Icon(Icons.add), onPressed: _add),
          ]),
        ),
        Expanded(
          child: StreamBuilder<List<Map<String, dynamic>>>(
            stream: _tasks,
            builder: (context, snap) {
              if (snap.hasError) return Center(child: Text('Error: ' + snap.error.toString()));
              if (!snap.hasData) return const Center(child: CircularProgressIndicator());
              final rows = snap.data!;
              if (rows.isEmpty) return const Center(child: Text('No tasks yet'));
              return ListView.separated(
                itemCount: rows.length,
                separatorBuilder: (context, i) => const Divider(height: 1),
                itemBuilder: (context, i) => _tile(rows[i]),
              );
            },
          ),
        ),
      ]),
    );
  }
}
