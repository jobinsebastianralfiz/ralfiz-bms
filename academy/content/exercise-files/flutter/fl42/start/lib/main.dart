import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart'; // run flutterfire configure first (see brief.md)

// STARTER - lesson 7.4: Chat app, part 1. Compiles once firebase_options.dart
// exists. The form is ready; the Firebase parts are TODOs.
Future<void> main() async {
  // TODO(1): call WidgetsFlutterBinding.ensureInitialized() and
  // await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform).
  runApp(ChatApp(auth: AuthRepository(FirebaseAuth.instance)));
}

class AuthRepository {
  AuthRepository(this._auth);
  final FirebaseAuth _auth;

  // TODO(2): return _auth.authStateChanges() and implement signIn,
  // register and signOut with the FirebaseAuth methods.
  Stream<User?> authStateChanges() => const Stream.empty();
  Future<void> signIn(String email, String password) async {}
  Future<void> register(String email, String password) async {}
  Future<void> signOut() async {}

  // TODO(3): map e.code to friendly messages with a switch expression:
  // invalid-email, invalid-credential / wrong-password / user-not-found,
  // email-already-in-use, weak-password, too-many-requests,
  // network-request-failed, and a default.
  static String messageFor(FirebaseAuthException e) => e.code;
}

class ChatApp extends StatelessWidget {
  const ChatApp({super.key, required this.auth});
  final AuthRepository auth;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Chat',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue)),
      // TODO(4): make ChatApp stateful, create the auth stream once, and use
      // a StreamBuilder<User?>: spinner while waiting, SignInPage when the
      // user is null, HomePage(user) otherwise.
      home: SignInPage(auth: auth),
    );
  }
}

class SignInPage extends StatefulWidget {
  const SignInPage({super.key, required this.auth});
  final AuthRepository auth;

  @override
  State<SignInPage> createState() => _SignInPageState();
}

class _SignInPageState extends State<SignInPage> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // TODO(5): set _busy, call register or signIn, catch
    // FirebaseAuthException and show AuthRepository.messageFor(e) in _error,
    // and clear _busy in finally (check mounted before setState).
  }

  @override
  Widget build(BuildContext context) {
    final action = _register ? 'Create account' : 'Sign in';
    return Scaffold(
      appBar: AppBar(title: Text(action)),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Icon(Icons.forum, size: 64),
          const SizedBox(height: 24),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(
                labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _password,
            obscureText: true,
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline),
              errorText: _error,
            ),
          ),
          const SizedBox(height: 24),
          FilledButton(onPressed: _busy ? null : _submit, child: Text(action)),
          TextButton(
            onPressed: () => setState(() => _register = !_register),
            child: Text(_register ? 'I already have an account' : 'Create an account'),
          ),
        ],
      ),
    );
  }
}

// TODO(6): add HomePage(auth, user): AppBar 'Chat' with a logout IconButton
// that calls auth.signOut, and a centred avatar with 'Signed in as <email>'.
