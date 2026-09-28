// TaskFlow - lesson 9.1 (SOLUTION)
// lib/api/api_client.dart: one configured Dio for the whole app.
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

// ---------------------------------------------------------------------------
// App exceptions: the only errors the rest of the app needs to understand.
// ---------------------------------------------------------------------------
sealed class AppException implements Exception {
  const AppException(this.message);
  final String message;

  @override
  String toString() => message;
}

final class NetworkException extends AppException {
  const NetworkException() : super('No internet connection. Check your network.');
}

final class RequestTimeoutException extends AppException {
  const RequestTimeoutException() : super('The server took too long to answer.');
}

final class UnauthorizedException extends AppException {
  const UnauthorizedException()
      : super('Your session has expired. Please sign in again.');
}

final class ServerException extends AppException {
  const ServerException(this.statusCode, super.message);
  final int? statusCode;
}

final class CancelledException extends AppException {
  const CancelledException() : super('Request cancelled.');
}

final class UnknownException extends AppException {
  const UnknownException([super.message = 'Something went wrong. Please try again.']);
}

/// Turns any DioException into one of our AppExceptions.
AppException mapDioException(DioException e) {
  return switch (e.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout =>
      const RequestTimeoutException(),
    DioExceptionType.connectionError => const NetworkException(),
    DioExceptionType.cancel => const CancelledException(),
    DioExceptionType.badResponse => _fromResponse(e.response),
    _ => const UnknownException(), // badCertificate, unknown, and future types
  };
}

AppException _fromResponse(Response<dynamic>? response) {
  final code = response?.statusCode;
  final data = response?.data;
  // DummyJSON (and many APIs) send {"message": "..."} with 4xx errors.
  final serverMessage =
      data is Map && data['message'] is String ? data['message'] as String : null;
  return switch (code) {
    401 => const UnauthorizedException(),
    404 => const ServerException(404, 'Not found.'),
    final c? when c >= 500 =>
      ServerException(c, 'The server had a problem. Try again later.'),
    _ => ServerException(code, serverMessage ?? 'Request failed.'),
  };
}

// ---------------------------------------------------------------------------
// Interceptors
// ---------------------------------------------------------------------------

/// Adds headers that every TaskFlow request needs.
class HeadersInterceptor extends Interceptor {
  HeadersInterceptor({this.language = 'en'});
  final String language;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Accept-Language'] = language;
    options.headers['X-Client'] = 'TaskFlow-Flutter';
    handler.next(options);
  }
}

// ---------------------------------------------------------------------------
// ApiClient
// ---------------------------------------------------------------------------
class ApiClient {
  ApiClient({
    Dio? httpClient,
    List<Interceptor> interceptors = const [],
  }) : dio = httpClient ?? Dio(_defaultOptions) {
    dio.interceptors.add(HeadersInterceptor());
    dio.interceptors.addAll(interceptors);
    // LogInterceptor goes last so it logs the final request.
    if (kDebugMode) {
      dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: false,
        logPrint: (line) => debugPrint(line.toString()),
      ));
    }
  }

  static final _defaultOptions = BaseOptions(
    baseUrl: 'https://dummyjson.com',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    headers: {'Accept': 'application/json'},
  );

  final Dio dio;

  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? query,
    CancelToken? cancelToken,
    Options? options,
  }) async {
    try {
      final response = await dio.get<T>(
        path,
        queryParameters: query,
        cancelToken: cancelToken,
        options: options,
      );
      return response.data as T;
    } on DioException catch (e) {
      throw mapDioException(e);
    }
  }

  Future<T> post<T>(
    String path, {
    Object? data,
    CancelToken? cancelToken,
    Options? options,
  }) async {
    try {
      final response = await dio.post<T>(
        path,
        data: data,
        cancelToken: cancelToken,
        options: options,
      );
      return response.data as T;
    } on DioException catch (e) {
      throw mapDioException(e);
    }
  }
}
