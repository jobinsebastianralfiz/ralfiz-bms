// TaskFlow 11.1 STARTER. Compiles as is; finish TODO(1) to TODO(6).
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Build-time settings from --dart-define or --dart-define-from-file.
/// They are NOT secret: anyone can read them from the compiled app.
class AppConfig {
  // TODO(1): read API_BASE_URL and ENV with String.fromEnvironment,
  // keeping these values as the defaultValue.
  static const apiBaseUrl = 'https://dummyjson.com';
  static const environment = 'dev';
}

/// Session tokens live in the iOS Keychain or Keystore-backed storage on Android.
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage])
      : _storage = storage ?? FlutterSecureStorage(iOptions: _iosOptions);
  static const _iosOptions = IOSOptions(accessibility: KeychainAccessibility.first_unlock_this_device);

  final FlutterSecureStorage _storage;
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  // TODO(2): write both tokens with _storage.write under _accessKey and _refreshKey.
  Future<void> saveTokens({required String access, required String refresh}) async {}

  // TODO(3): read the values back with _storage.read.
  Future<String?> readAccessToken() async => null;
  Future<String?> readRefreshToken() async => null;

  // TODO(4): delete both keys (sign out must leave nothing behind).
  Future<void> clear() async {}
}

/// Shows only the start of a token, never the whole value.
String mask(String? token) {
  if (token == null || token.isEmpty) return 'none';
  if (token.length <= 8) return '****';
  final size = token.length;
  return token.substring(0, 6) + '... ($size chars)';
}

/// Debug-only network log that hides credentials.
class RedactingLogInterceptor extends Interceptor {
  static const _hidden = {'authorization', 'password', 'accesstoken', 'refreshtoken'};

  // TODO(5): return a copy where every key in _hidden (ignoring case) has
  // the value '***'. Right now passwords and tokens leak into the log.
  Map<String, dynamic> _redact(Map<String, dynamic> map) => map;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final data = options.data;
    final body = data is Map<String, dynamic> ? _redact(data) : data;
    final headers = _redact(options.headers);
    debugPrint('--> ' + options.method + ' ' + options.uri.toString());
    debugPrint('    headers: $headers');
    debugPrint('    body: $body');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    final data = response.data;
    final body = data is Map<String, dynamic> ? _redact(data) : '(not a map)';
    final code = response.statusCode;
    debugPrint('<-- $code ' + response.requestOptions.uri.path);
    debugPrint('    body: $body');
    handler.next(response);
  }
}

class ApiClient {
  ApiClient(this._tokens)
      : dio = Dio(BaseOptions(
          baseUrl: AppConfig.apiBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        )) {
    // TODO(6): add an InterceptorsWrapper whose onRequest reads the access
    // token from _tokens and sets the Authorization: Bearer header, and only
    // add the log interceptor when kDebugMode is true.
    dio.interceptors.add(RedactingLogInterceptor());
  }

  final TokenStorage _tokens;
  final Dio dio;
}

class AuthRepository {
  AuthRepository(this._api, this._tokens);
  final ApiClient _api;
  final TokenStorage _tokens;

  Future<void> login(String username, String password) async {
    final res = await _api.dio.post<Map<String, dynamic>>('/auth/login',
        data: {'username': username, 'password': password, 'expiresInMins': 30});
    final body = res.data!;
    await _tokens.saveTokens(
        access: body['accessToken'] as String, refresh: body['refreshToken'] as String);
  }

  Future<String> me() async {
    final res = await _api.dio.get<Map<String, dynamic>>('/auth/me');
    final data = res.data!;
    return (data['firstName'] as String) + ' ' + (data['lastName'] as String);
  }

  Future<void> logout() => _tokens.clear();
}

void main() {
  final tokens = TokenStorage();
  final auth = AuthRepository(ApiClient(tokens), tokens);
  runApp(MaterialApp(
    title: 'TaskFlow',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3949AB))),
    home: SessionPage(auth: auth, tokens: tokens),
  ));
}

class SessionPage extends StatefulWidget {
  const SessionPage({super.key, required this.auth, required this.tokens});
  final AuthRepository auth;
  final TokenStorage tokens;

  @override
  State<SessionPage> createState() => _SessionPageState();
}

class _SessionPageState extends State<SessionPage> {
  String _access = 'none';
  String _user = '-';
  String? _error;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadSavedToken(); // a token saved in an earlier run survives restarts
  }

  Future<void> _loadSavedToken() async {
    final token = await widget.tokens.readAccessToken();
    if (mounted) setState(() => _access = mask(token));
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() => _busy = true);
    String? error;
    try {
      await action();
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      error = code == null ? 'Network error: ' + e.type.name : 'Server said $code';
    }
    final token = await widget.tokens.readAccessToken();
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = error;
      _access = mask(token);
    });
  }

  Future<void> _signOut() => widget.auth.logout().then((_) => _user = '-');

  @override
  Widget build(BuildContext context) {
    final env = AppConfig.environment + ' | ' + AppConfig.apiBaseUrl;
    return Scaffold(
      appBar: AppBar(title: const Text('TaskFlow session')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        ListTile(leading: const Icon(Icons.key), title: const Text('Access token'), subtitle: Text(_access)),
        ListTile(leading: const Icon(Icons.person), title: const Text('Signed-in user'), subtitle: Text(_user)),
        ListTile(leading: const Icon(Icons.dns), title: const Text('Environment'), subtitle: Text(env)),
        if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _busy ? null : () => _run(() => widget.auth.login('emilys', 'emilyspass')),
          icon: const Icon(Icons.login),
          label: const Text('Sign in as emilys'),
        ),
        OutlinedButton(
          onPressed: _busy ? null : () => _run(() async => _user = await widget.auth.me()),
          child: const Text('Who am I?'),
        ),
        TextButton(onPressed: _busy ? null : () => _run(_signOut), child: const Text('Sign out')),
      ]),
    );
  }
}