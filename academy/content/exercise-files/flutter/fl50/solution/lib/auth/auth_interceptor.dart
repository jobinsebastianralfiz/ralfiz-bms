// TaskFlow - lesson 9.2 (SOLUTION)
// lib/auth/auth_interceptor.dart: token storage and the auth interceptor.
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Where the tokens live. Lesson 11.1 replaces the in-memory version with
/// flutter_secure_storage. Never put tokens in shared_preferences.
abstract interface class TokenStorage {
  Future<String?> readAccessToken();
  Future<String?> readRefreshToken();
  Future<void> save({required String access, required String refresh});
  Future<void> clear();
}

class InMemoryTokenStorage implements TokenStorage {
  String? _access;
  String? _refresh;

  @override
  Future<String?> readAccessToken() async => _access;

  @override
  Future<String?> readRefreshToken() async => _refresh;

  @override
  Future<void> save({required String access, required String refresh}) async {
    _access = access;
    _refresh = refresh;
  }

  @override
  Future<void> clear() async {
    _access = null;
    _refresh = null;
  }
}

/// Key for Options(extra: {skipAuth: true}): use it on requests that must
/// not carry a token (login) or must not trigger a refresh.
const skipAuth = 'skipAuth';

/// Attaches the Bearer token and refreshes it once on a 401.
///
/// QueuedInterceptor handles one error at a time, so when five requests fail
/// together only the first one refreshes; the others wait, see the new token
/// and simply retry.
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required this.tokens,
    required this.onSessionExpired,
    Dio? plainDio,
  }) : _plainDio = plainDio ??
            Dio(BaseOptions(
              baseUrl: 'https://dummyjson.com',
              // Timeouts matter here: while the refresh runs, every other
              // 401 waits in the queue behind it.
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 15),
            ));

  final TokenStorage tokens;

  /// Called when the refresh token is rejected: the user must sign in again.
  final void Function() onSessionExpired;

  /// A Dio WITHOUT this interceptor, for the refresh call and the retries.
  /// Using the main Dio here would queue behind ourselves and deadlock.
  final Dio _plainDio;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (options.extra[skipAuth] != true) {
      final access = await tokens.readAccessToken();
      if (access != null) {
        options.headers['Authorization'] = 'Bearer $access';
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final request = err.requestOptions;
    if (err.response?.statusCode != 401 || request.extra[skipAuth] == true) {
      handler.next(err);
      return;
    }

    final path = request.path;

    // Did another request refresh the token while this one waited?
    final current = await tokens.readAccessToken();
    final sentWith = request.headers['Authorization'];
    if (current != null && sentWith != 'Bearer $current') {
      debugPrint('auth: 401 on $path, token already refreshed');
      await _retry(request, current, handler);
      return;
    }

    debugPrint('auth: 401 on $path, refreshing');
    final fresh = await _refresh();
    if (fresh == null) {
      debugPrint('auth: refresh failed, signing out');
      await tokens.clear();
      onSessionExpired();
      handler.next(err); // the caller receives UnauthorizedException
      return;
    }
    await _retry(request, fresh, handler);
  }

  /// Returns the new access token, or null when the refresh failed.
  Future<String?> _refresh() async {
    final refreshToken = await tokens.readRefreshToken();
    if (refreshToken == null) return null;
    try {
      final response = await _plainDio.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refreshToken': refreshToken, 'expiresInMins': 30},
      );
      final data = response.data!;
      final access = data['accessToken'] as String;
      await tokens.save(
        access: access,
        refresh: data['refreshToken'] as String,
      );
      return access;
    } on DioException {
      return null;
    }
  }

  Future<void> _retry(
    RequestOptions request,
    String accessToken,
    ErrorInterceptorHandler handler,
  ) async {
    request.headers['Authorization'] = 'Bearer $accessToken';
    try {
      final response = await _plainDio.fetch<dynamic>(request);
      handler.resolve(response);
    } on DioException catch (e) {
      handler.next(e);
    }
  }
}
