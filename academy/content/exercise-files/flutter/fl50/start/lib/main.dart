// TaskFlow - lesson 9.2: wiring, go_router redirect and the two pages.
// lib/main.dart. This file is complete and is the same in the solution.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import 'api/api_client.dart';
import 'auth/auth_cubit.dart';
import 'auth/auth_interceptor.dart';

/// A record is enough here; lesson 9.3 gives Task a proper class.
typedef Task = ({int id, String title, bool completed});

class TaskRepository {
  TaskRepository(this._api);
  final ApiClient _api;

  /// /auth/todos only answers when a valid Bearer token is attached.
  Future<List<Task>> fetchTasks({int skip = 0, int limit = 5}) async {
    final json = await _api.get<Map<String, dynamic>>('/auth/todos',
        query: {'skip': skip, 'limit': limit});
    return [
      for (final t in json['todos'] as List<dynamic>)
        (id: t['id'] as int, title: t['todo'] as String, completed: t['completed'] as bool),
    ];
  }
}

// ----------------------------- routing -----------------------------
GoRouter buildRouter(AuthCubit auth) => GoRouter(
      initialLocation: '/splash',
      refreshListenable: StreamListenable(auth.stream),
      redirect: (context, state) {
        final loc = state.matchedLocation;
        return switch (auth.state) {
          AuthUnknown() => loc == '/splash' ? null : '/splash',
          Unauthenticated() => loc == '/login' ? null : '/login',
          Authenticated() => loc == '/login' || loc == '/splash' ? '/tasks' : null,
        };
      },
      routes: [
        GoRoute(path: '/splash', builder: (_, __) => const Scaffold(
            body: Center(child: CircularProgressIndicator()))),
        GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
        GoRoute(path: '/tasks', builder: (_, __) => const TasksPage()),
      ],
    );

void main() {
  final tokens = InMemoryTokenStorage();
  final expired = StreamController<void>.broadcast();
  final api = ApiClient(interceptors: [
    AuthInterceptor(tokens: tokens, onSessionExpired: () => expired.add(null)),
  ]);
  final authCubit = AuthCubit(AuthRepository(api, tokens, expired.stream))
    ..restore();
  runApp(MultiRepositoryProvider(
    providers: [
      RepositoryProvider<TokenStorage>.value(value: tokens),
      RepositoryProvider.value(value: TaskRepository(api)),
    ],
    child: BlocProvider.value(
      value: authCubit,
      child: MaterialApp.router(
        title: 'TaskFlow',
        theme: ThemeData(colorSchemeSeed: const Color(0xFF00796B)),
        routerConfig: buildRouter(authCubit),
      ),
    ),
  ));
}

// ----------------------------- pages -----------------------------
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _user = TextEditingController(text: 'emilys');
  final _pass = TextEditingController(text: 'emilyspass');

  @override
  void dispose() {
    _user.dispose();
    _pass.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AuthCubit>().state;
    final submitting = state is Unauthenticated && state.submitting;
    final message = state is Unauthenticated ? state.message : null;
    return Scaffold(
      appBar: AppBar(title: const Text('Sign in to TaskFlow')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          TextField(
              controller: _user,
              decoration: const InputDecoration(
                  labelText: 'Username', prefixIcon: Icon(Icons.person))),
          const SizedBox(height: 12),
          TextField(
              controller: _pass,
              obscureText: true,
              decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock),
                  errorText: message)),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: submitting
                ? null
                : () => context.read<AuthCubit>().login(_user.text.trim(), _pass.text),
            child: Text(submitting ? 'Signing in…' : 'Sign in'),
          ),
        ],
      ),
    );
  }
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key});
  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  late Future<List<Task>> _future;
  @override
  void initState() {
    super.initState();
    _future = _loadThreeAtOnce();
  }

  /// Three parallel requests: after a 401 they all wait for ONE refresh.
  Future<List<Task>> _loadThreeAtOnce() async {
    final repo = context.read<TaskRepository>();
    final pages = await Future.wait(
        [for (final skip in [0, 5, 10]) repo.fetchTasks(skip: skip)]);
    return [for (final page in pages) ...page];
  }

  void _reload() => setState(() => _future = _loadThreeAtOnce());

  /// Debug helper: break the access token, and the refresh token too if asked.
  Future<void> _breakTokens({required bool keepRefresh}) async {
    final tokens = context.read<TokenStorage>();
    final refresh = await tokens.readRefreshToken();
    await tokens.save(
        access: 'expired', refresh: keepRefresh ? refresh ?? '' : 'invalid');
    if (mounted) _reload(); // context/state checks after an await
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthCubit>().state;
    final name = auth is Authenticated ? auth.user.firstName : '';
    return Scaffold(
      appBar: AppBar(
        title: Text('Hi, $name'),
        actions: [
          IconButton(
              tooltip: 'Expire access token',
              icon: const Icon(Icons.timer_off),
              onPressed: () => _breakTokens(keepRefresh: true)),
          IconButton(
              tooltip: 'Break both tokens',
              icon: const Icon(Icons.key_off),
              onPressed: () => _breakTokens(keepRefresh: false)),
          IconButton(
              tooltip: 'Sign out',
              icon: const Icon(Icons.logout),
              onPressed: () => context.read<AuthCubit>().logout()),
        ],
      ),
      body: FutureBuilder<List<Task>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) return Center(child: Text(snap.error.toString()));
          return ListView(children: [
            for (final t in snap.data!)
              ListTile(
                  leading: Icon(t.completed ? Icons.check_circle : Icons.radio_button_unchecked),
                  title: Text(t.title)),
          ]);
        },
      ),
    );
  }
}
