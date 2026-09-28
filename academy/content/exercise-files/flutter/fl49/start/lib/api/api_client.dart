// TaskFlow - lesson 9.1 (STARTER)
// lib/api/api_client.dart: one configured Dio for the whole app.
// It compiles as it is. Complete TODO(1) to TODO(6).
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
  // TODO(4): return a switch expression on e.type:
  //   connectionTimeout, sendTimeout, receiveTimeout -> RequestTimeoutException
  //   connectionError -> NetworkException
  //   cancel -> CancelledException
  //   badResponse -> _fromResponse(e.response)
  //   anything else (_) -> UnknownException
  return const UnknownException();
}

AppException _fromResponse(Response<dynamic>? response) {
  final code = response?.statusCode;
  // TODO(5): read data['message'] when the body is a Map with a String message,
  // then switch on code: 401 -> UnauthorizedException, 404 -> ServerException
  // (404, 'Not found.'), 500 and above -> a "server had a problem" message,
  // otherwise ServerException(code, serverMessage ?? 'Request failed.').
  return ServerException(code, 'Request failed.');
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
    // TODO(2): set the Accept-Language header to language and the
    // X-Client header to 'TaskFlow-Flutter' before passing the request on.
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
    // TODO(3): in debug mode only (kDebugMode), add a LogInterceptor LAST,
    // with requestBody: true, responseBody: false and a logPrint that
    // calls debugPrint(line.toString()).
  }

  static final _defaultOptions = BaseOptions(
    baseUrl: 'https://dummyjson.com',
    // TODO(1): add connectTimeout (10 s), receiveTimeout (15 s) and an
    // Accept: application/json default header.
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
    // TODO(6): wrap this call in try / on DioException catch, like get(),
    // and throw mapDioException(e) so callers never see a DioException.
    final response = await dio.post<T>(
      path,
      data: data,
      cancelToken: cancelToken,
      options: options,
    );
    return response.data as T;
  }
}
