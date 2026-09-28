import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'data/supabase_task_repository.dart';

// flutter run --dart-define-from-file=env/dev.json
const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const supabaseKey = String.fromEnvironment('SUPABASE_PUBLISHABLE_KEY');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(url: supabaseUrl, publishableKey: supabaseKey);
  final client = Supabase.instance.client; // get_it would own this (lesson 9.5)
  runApp(TaskFlowApp(repo: SupabaseTaskRepository(client), auth: client.auth));
}

void showMessage(BuildContext context, String text) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));

class TaskFlowApp extends StatelessWidget {
  const TaskFlowApp({super.key, required this.repo, required this.auth});
  final TaskRepository repo;
  final GoTrueClient auth;

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'TaskFlow',
        theme: ThemeData(colorSchemeSeed: const Color(0xFF3ECF8E)),
        home: StreamBuilder<AuthState>(
          stream: auth.onAuthStateChange,
          builder: (context, snapshot) => auth.currentSession == null
              ? const SignInPage()
              : TasksPage(key: ValueKey(auth.currentUser?.id), repo: repo),
        ),
      );
}

class SignInPage extends StatefulWidget {
  const SignInPage({super.key});
  @override
  State<SignInPage> createState() => _SignInPageState();
}

class _SignInPageState extends State<SignInPage> {
  final _email = TextEditingController();
  final _password = TextEditingController();

  Future<void> _run({required bool signUp}) async {
    final auth = Supabase.instance.client.auth;
    final email = _email.text.trim();
    try {
      if (signUp) {
        final res = await auth.signUp(email: email, password: _password.text);
        if (res.session == null && mounted) showMessage(context, 'Check your email to confirm.');
      } else {
        await auth.signInWithPassword(email: email, password: _password.text);
      }
    } on AuthException catch (e) {
      if (mounted) showMessage(context, e.message);
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('TaskFlow')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          TextField(controller: _email, decoration: const InputDecoration(labelText: 'Email')),
          TextField(controller: _password, obscureText: true,
              decoration: const InputDecoration(labelText: 'Password')),
          const SizedBox(height: 16),
          FilledButton(onPressed: () => _run(signUp: false), child: const Text('Sign in')),
          TextButton(onPressed: () => _run(signUp: true), child: const Text('Create account')),
        ]),
      );
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key, required this.repo});
  final TaskRepository repo;
  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  static const _pageSize = 20;
  final _title = TextEditingController();
  final _tasks = <Task>[];
  String? _projectId;
  int _page = 0;
  bool _loading = true;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _run(() async {
      _projectId = await widget.repo.inboxProjectId();
      await _loadMore();
    });
  }

  Future<void> _run(Future<void> Function() action) async {
    try {
      await action();
    } on TaskFailure catch (e) {
      if (mounted) showMessage(context, e.message);
    }
  }

  Future<void> _loadMore() async {
    final projectId = _projectId;
    if (projectId == null) return;
    setState(() => _loading = true);
    try {
      final page = await widget.repo.fetchPage(projectId, page: _page, pageSize: _pageSize);
      _tasks.addAll(page);
      _page++;
      _hasMore = page.length == _pageSize;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _add() => _run(() async {
        final projectId = _projectId;
        final text = _title.text.trim();
        if (projectId == null || text.isEmpty) return;
        final task = await widget.repo.add(projectId, text);
        if (!mounted) return;
        setState(() => _tasks.insert(0, task));
        _title.clear();
      });

  Future<void> _toggle(Task task, bool done) => _run(() async {
        await widget.repo.setDone(task.id, done); // throws NotAllowed if RLS hid it
        final i = _tasks.indexWhere((x) => x.id == task.id);
        if (mounted && i >= 0) setState(() => _tasks[i] = task.copyWith(done: done));
      });

  Future<void> _delete(Task task) => _run(() async {
        setState(() => _tasks.remove(task));
        await widget.repo.delete(task.id);
      });

  @override
  void dispose() {
    _title.dispose();
    super.dispose();
  }

  Widget _row(int i) {
    if (i == _tasks.length) {
      return !_hasMore ? const SizedBox.shrink() : Center(child: TextButton(
          onPressed: _loading ? null : () => _run(_loadMore), child: const Text('Load more')));
    }
    final task = _tasks[i];
    return Dismissible(
      key: ValueKey(task.id),
      onDismissed: (_) => _delete(task),
      child: ListTile(
        leading: Checkbox(value: task.done, onChanged: (v) => _toggle(task, v ?? false)),
        title: Text(task.title),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Inbox'), actions: [
          IconButton(icon: const Icon(Icons.logout),
              onPressed: () => Supabase.instance.client.auth.signOut()),
        ]),
        body: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
            child: Row(spacing: 8, children: [
              Expanded(child: TextField(controller: _title,
                  decoration: const InputDecoration(hintText: 'New task'))),
              IconButton.filled(icon: const Icon(Icons.add), onPressed: _add),
            ]),
          ),
          Expanded(
            child: _tasks.isEmpty
                ? Center(child: _loading ? const CircularProgressIndicator() : const Text('No tasks yet'))
                : ListView.separated(
                    itemCount: _tasks.length + 1,
                    separatorBuilder: (context, i) => const Divider(height: 1),
                    itemBuilder: (context, i) => _row(i),
                  ),
          ),
        ]),
      );
}
