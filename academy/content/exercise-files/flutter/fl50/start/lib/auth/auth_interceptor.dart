// TaskFlow - lesson 9.2 (STARTER)
// It compiles as it is. Complete TODO(1) to TODO(5).
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
    // TODO(1): unless options.extra[skipAuth] == true, read the access token
    // and, when it is not null, set the Authorization header to
    // 'Bearer <token>' (use $access interpolation).
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final request = err.requestOptions;
    // TODO(2): if the status code is not 401, or the request has skipAuth,
    // call handler.next(err) and return.

    final path = request.path;

    // TODO(3): read the current access token. If it is not null and differs
    // from the token this request was sent with (request.headers
    // ['Authorization']), another request already refreshed it:
    // debugPrint('auth: 401 on $path, token already refreshed'), then
    // await _retry(request, current, handler) and return.

    // TODO(4): debugPrint('auth: 401 on $path, refreshing') and call
    // _refresh(). When it returns null: debugPrint('auth: refresh failed,
    // signing out'), clear the tokens, call onSessionExpired(), call
    // handler.next(err) and return. Otherwise await _retry(request, fresh,
    // handler).
    handler.next(err);
  }

  /// Returns the new access token, or null when the refresh failed.
  Future<String?> _refresh() async {
    // TODO(5): read the refresh token (return null if missing). POST
    // /auth/refresh with _plainDio and the body
    // {'refreshToken': refreshToken, 'expiresInMins': 30}. Save both new
    // tokens and return accessToken. Return null on DioException.
    return null;
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
