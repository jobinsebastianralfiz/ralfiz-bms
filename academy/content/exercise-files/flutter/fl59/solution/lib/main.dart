// TaskFlow 11.2 SOLUTION: HTTPS-only client, deep link validation, biometric app lock.
// Run on a device or emulator with a screen lock (and ideally a fingerprint) set up.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';

/// Dart's own HttpClient ignores Android cleartext settings and iOS ATS,
/// so TaskFlow enforces HTTPS itself, for every request.
class HttpsOnlyInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.uri.scheme != 'https') {
      final url = options.uri.toString();
      handler.reject(DioException(requestOptions: options, message: 'Blocked insecure URL: $url'));
      return;
    }
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
  if (uri.scheme != 'https' || !_allowedHosts.contains(uri.host)) {
    return RejectedLink('Unknown link source');
  }
  final match = _taskPath.firstMatch(uri.path);
  if (match == null) return RejectedLink('Unknown page');
  return OpenTask(int.parse(match.group(1)!));
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
  late final AppLifecycleListener _lifecycle;
  bool _locked = true;
  String? _message;

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(onHide: () => setState(() => _locked = true));
  }

  @override
  void dispose() {
    _lifecycle.dispose();
    super.dispose();
  }

  Future<void> _unlock() async {
    String? message;
    var ok = false;
    try {
      if (!await _auth.isDeviceSupported()) {
        message = 'Set up a screen lock on this device first.';
      } else {
        ok = await _auth.authenticate(localizedReason: 'Unlock TaskFlow to see your tasks');
      }
    } on LocalAuthException catch (e) {
      message = switch (e.code) {
        LocalAuthExceptionCode.userCanceled || LocalAuthExceptionCode.systemCanceled => 'Unlock cancelled.',
        LocalAuthExceptionCode.temporaryLockout ||
        LocalAuthExceptionCode.biometricLockout =>
          'Too many attempts. Try again later.',
        LocalAuthExceptionCode.noCredentialsSet => 'Set up a screen lock on this device first.',
        _ => 'Could not unlock: ' + e.code.name,
      };
    }
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