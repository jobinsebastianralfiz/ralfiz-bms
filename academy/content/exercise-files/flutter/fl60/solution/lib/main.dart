// TaskFlow 12.1 SOLUTION. Run: flutter run --dart-define-from-file=config/supabase.json
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const supabaseKey = String.fromEnvironment('SUPABASE_PUBLISHABLE_KEY');
const redirectUrl = 'io.supabase.taskflow://login-callback/';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(url: supabaseUrl, publishableKey: supabaseKey);
  final cubit = AuthCubit(AuthRepository(Supabase.instance.client.auth));
  final router = buildRouter(cubit);
  runApp(BlocProvider.value(value: cubit, child: MaterialApp.router(
    title: 'TaskFlow',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3ECF8E))),
    routerConfig: router,
  )));
}

/// The only class that talks to Supabase Auth.
class AuthRepository {
  AuthRepository(this._auth);
  final GoTrueClient _auth;
  Stream<AuthState> get changes => _auth.onAuthStateChange;

  Future<void> signIn(String email, String password) =>
      _auth.signInWithPassword(email: email, password: password);

  /// Returns false when Supabase sent a confirmation email instead of a session.
  Future<bool> signUp(String email, String password) async {
    final res = await _auth.signUp(email: email, password: password, emailRedirectTo: redirectUrl);
    return res.session != null;
  }
  Future<void> sendMagicLink(String email) =>
      _auth.signInWithOtp(email: email, emailRedirectTo: redirectUrl);
  Future<void> signOut() => _auth.signOut();
}

/// Named SessionState because supabase_flutter already exports AuthState.
sealed class SessionState {
  const SessionState();
}

class SessionUnknown extends SessionState { const SessionUnknown(); }
class SignedOut extends SessionState { const SignedOut(); }
class SignedIn extends SessionState {
  const SignedIn(this.user);
  final User user;
}

class AuthCubit extends Cubit<SessionState> {
  AuthCubit(this.repo) : super(const SessionUnknown()) {
    // The first event is initialSession: the saved session, or null.
    _sub = repo.changes.listen(
      (data) {
        final session = data.session;
        emit(session == null ? const SignedOut() : SignedIn(session.user));
      },
      onError: (Object error) {}, // e.g. offline during a token refresh
    );
  }

  final AuthRepository repo;
  late final StreamSubscription<AuthState> _sub;
  Future<void> signOut() => repo.signOut();

  @override
  Future<void> close() async {
    await _sub.cancel();
    return super.close();
  }
}

/// Lets go_router re-run its redirect whenever the cubit emits.
class StreamListenable extends ChangeNotifier {
  StreamListenable(Stream<dynamic> stream) : _sub = stream.listen(null) {
    _sub.onData((_) => notifyListeners());
  }
  final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}

GoRouter buildRouter(AuthCubit cubit) => GoRouter(
      initialLocation: '/tasks',
      refreshListenable: StreamListenable(cubit.stream),
      redirect: (context, state) {
        final at = state.matchedLocation;
        return switch (cubit.state) {
          SessionUnknown() => at == '/splash' ? null : '/splash',
          SignedOut() => at == '/sign-in' ? null : '/sign-in',
          SignedIn() => (at == '/sign-in' || at == '/splash') ? '/tasks' : null,
        };
      },
      routes: [
        // The auth callback link opens the app at '/', so send it somewhere real.
        GoRoute(path: '/', redirect: (_, __) => '/tasks'),
        GoRoute(path: '/splash', builder: (_, __) => const Scaffold(body: Center(child: CircularProgressIndicator()))),
        GoRoute(path: '/sign-in', builder: (_, __) => const SignInPage()),
        GoRoute(path: '/tasks', builder: (_, __) => const TasksPage()),
      ],
    );

class SignInPage extends StatefulWidget {
  const SignInPage({super.key});
  @override
  State<SignInPage> createState() => _SignInPageState();
}

class _SignInPageState extends State<SignInPage> {
  final _email = TextEditingController(), _password = TextEditingController();
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _run(Future<String?> Function(AuthRepository repo) action) async {
    setState(() => _busy = true);
    final repo = context.read<AuthCubit>().repo;
    String? error, info;
    try {
      info = await action(repo);
    } on AuthException catch (e) {
      error = e.message;
    }
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = error;
    });
    if (info != null) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(info)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sign in to TaskFlow')),
      body: ListView(padding: const EdgeInsets.all(24), children: [
        TextField(controller: _email, keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.mail))),
        const SizedBox(height: 12),
        TextField(controller: _password, obscureText: true,
            decoration: InputDecoration(labelText: 'Password', prefixIcon: const Icon(Icons.lock), errorText: _error)),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: _busy ? null : () => _run((r) => r.signIn(_email.text.trim(), _password.text).then((_) => null)),
          child: const Text('Sign in'),
        ),
        OutlinedButton(
          onPressed: _busy
              ? null
              : () => _run((r) async => await r.signUp(_email.text.trim(), _password.text)
                  ? null
                  : 'Check your email to confirm your account.'),
          child: const Text('Create account'),
        ),
        TextButton(
          onPressed: _busy ? null : () => _run((r) async {
            final email = _email.text.trim();
            await r.sendMagicLink(email);
            return 'Magic link sent to $email';
          }),
          child: const Text('Email me a magic link'),
        ),
      ]),
    );
  }
}

class TasksPage extends StatelessWidget {
  const TasksPage({super.key});
  @override
  Widget build(BuildContext context) {
    final state = context.watch<AuthCubit>().state;
    final email = state is SignedIn ? (state.user.email ?? 'unknown') : '';
    return Scaffold(
      appBar: AppBar(title: const Text('TaskFlow'), actions: [
        IconButton(onPressed: () => context.read<AuthCubit>().signOut(), icon: const Icon(Icons.logout)),
      ]),
      body: Center(child: Text('Signed in as $email\nYour tasks arrive in lesson 12.2.', textAlign: TextAlign.center)),
    );
  }
}