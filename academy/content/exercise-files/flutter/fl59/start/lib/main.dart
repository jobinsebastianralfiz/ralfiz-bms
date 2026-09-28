// TaskFlow 11.2 STARTER: compiles and runs, but nothing is enforced yet. TODO(1) to TODO(5).
// Run on a device or emulator with a screen lock (and ideally a fingerprint) set up.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';

/// Dart's own HttpClient ignores Android cleartext settings and iOS ATS,
/// so TaskFlow enforces HTTPS itself, for every request.
class HttpsOnlyInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // TODO(1): if options.uri.scheme is not 'https', reject the request with
    // handler.reject(DioException(requestOptions: options, message: 'Blocked insecure URL: ...'))
    // and return. Otherwise continue with handler.next(options).
    handler.next(options);
  }
}

/// Where an incoming link is allowed to take the user.
sealed class LinkTarget {}

class OpenTask extends LinkTarget {
  OpenTask(this.id);
  final int id;
}

class RejectedLink extends LinkTarget {
  RejectedLink(this.reason);
  final String reason;
}

const _allowedHosts = {'taskflow.example.com'};
final _taskPath = RegExp(r'^/tasks/(\d{1,9})$');

/// Treat every link as untrusted input: check scheme, host and path shape.
LinkTarget parseTaskLink(Uri uri) {
  // TODO(2): return RejectedLink('Unknown link source') unless the scheme is https
  // and the host is in _allowedHosts. Then match uri.path against _taskPath:
  // no match gives RejectedLink('Unknown page'), a match gives OpenTask(id).
  final digits = uri.pathSegments.isEmpty ? '' : uri.pathSegments.last;
  return OpenTask(int.tryParse(digits) ?? 0);
}

String describe(LinkTarget target) => switch (target) {
      OpenTask(:final id) => 'Open task $id',
      RejectedLink(:final reason) => 'Rejected: $reason',
    };

void main() {
  final dio = Dio(BaseOptions(connectTimeout: const Duration(seconds: 10)))
    ..interceptors.add(HttpsOnlyInterceptor());
  runApp(MaterialApp(
    title: 'TaskFlow',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF00897B))),
    home: AppLockGate(child: HomePage(dio: dio)),
  ));
}

/// Shows a lock screen until local_auth succeeds, and locks again
/// whenever the app is hidden (sent to the background).
class AppLockGate extends StatefulWidget {
  const AppLockGate({super.key, required this.child});
  final Widget child;

  @override
  State<AppLockGate> createState() => _AppLockGateState();
}

class _AppLockGateState extends State<AppLockGate> {
  final _auth = LocalAuthentication();
  bool _locked = true;
  String? _message;

  @override
  void initState() {
    super.initState();
    // TODO(5): create an AppLifecycleListener whose onHide sets _locked = true,
    // keep it in a late final field and dispose it in dispose().
  }

  Future<void> _unlock() async {
    String? message;
    var ok = false;
    // TODO(3): check _auth.isDeviceSupported(). If false, set message to
    // 'Set up a screen lock on this device first.'. Otherwise set ok to the result
    // of _auth.authenticate(localizedReason: 'Unlock TaskFlow to see your tasks').
    // TODO(4): wrap it in try / on LocalAuthException and map e.code to a message
    // (cancelled, too many attempts, no screen lock, or 'Could not unlock: ' + e.code.name).
    ok = true; // INSECURE placeholder: unlocks without asking anyone.
    if (!mounted) return;
    setState(() {
      _locked = !ok;
      _message = message;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_locked) return widget.child;
    return Scaffold(
      body: Center(
        child: Column(mainAxisSize: MainAxisSize.min, spacing: 16, children: [
          const Icon(Icons.lock, size: 64),
          Text('TaskFlow is locked', style: Theme.of(context).textTheme.titleLarge),
          if (_message != null) Text(_message!),
          FilledButton.icon(onPressed: _unlock, icon: const Icon(Icons.fingerprint), label: const Text('Unlock')),
        ]),
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.dio});
  final Dio dio;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _result = 'Tap a button to test the client.';
  static final _links = [
    Uri.parse('https://taskflow.example.com/tasks/42'),
    Uri.parse('https://taskflow.example.com/admin/delete-all'),
    Uri.parse('https://evil.example.net/tasks/42'),
  ];

  Future<void> _fetch(String url) async {
    String result;
    try {
      final res = await widget.dio.get<Map<String, dynamic>>(url);
      final todos = res.data!['todos'] as List<dynamic>;
      final count = todos.length;
      result = 'Loaded $count todos over HTTPS';
    } on DioException catch (e) {
      result = e.message ?? 'Request failed: ' + e.type.name;
    }
    if (!mounted) return;
    setState(() => _result = result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Security checks')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text(_result, style: Theme.of(context).textTheme.bodyLarge),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: () => _fetch('https://dummyjson.com/todos?limit=3'),
          child: const Text('Fetch over HTTPS'),
        ),
        OutlinedButton(
          onPressed: () => _fetch('http://dummyjson.com/todos?limit=3'),
          child: const Text('Try plain HTTP'),
        ),
        const Divider(height: 32),
        Text('Incoming links', style: Theme.of(context).textTheme.titleMedium),
        for (final link in _links)
          ListTile(
            leading: const Icon(Icons.link),
            title: Text(link.host + link.path),
            subtitle: Text(describe(parseTaskLink(link))),
          ),
      ]),
    );
  }
}