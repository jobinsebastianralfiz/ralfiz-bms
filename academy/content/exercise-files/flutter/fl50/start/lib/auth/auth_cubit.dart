// TaskFlow - lesson 9.2: User, AuthRepository, AuthCubit and StreamListenable.
// lib/auth/auth_cubit.dart. This file is complete and is the same in the solution.
import 'dart:async';

import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../api/api_client.dart';
import 'auth_interceptor.dart';

class User extends Equatable {
  const User({required this.id, required this.username, required this.firstName});
  factory User.fromJson(Map<String, dynamic> json) => User(
      id: json['id'] as int,
      username: json['username'] as String,
      firstName: json['firstName'] as String);
  final int id;
  final String username;
  final String firstName;
  @override
  List<Object?> get props => [id, username, firstName];
}

class AuthRepository {
  AuthRepository(this._api, this._tokens, this.sessionExpired);
  final ApiClient _api;
  final TokenStorage _tokens;
  final Stream<void> sessionExpired;

  Future<User> login(String username, String password) async {
    try {
      final json = await _api.post<Map<String, dynamic>>(
        '/auth/login',
        // expiresInMins: 1 makes the access token expire quickly for testing.
        data: {'username': username, 'password': password, 'expiresInMins': 1},
        options: Options(extra: {skipAuth: true}),
      );
      await _tokens.save(
          access: json['accessToken'] as String,
          refresh: json['refreshToken'] as String);
      return User.fromJson(json);
    } on AppException catch (e) {
      final badCredentials = e is UnauthorizedException ||
          (e is ServerException && e.statusCode == 400);
      if (badCredentials) {
        throw const ServerException(400, 'Invalid username or password.');
      }
      rethrow;
    }
  }

  Future<User?> restoreSession() async {
    if (await _tokens.readAccessToken() == null) return null;
    try {
      return User.fromJson(await _api.get<Map<String, dynamic>>('/auth/me'));
    } on AppException {
      return null;
    }
  }

  Future<void> logout() => _tokens.clear();
}

// ----------------------------- state -----------------------------
sealed class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => [];
}

final class AuthUnknown extends AuthState {
  const AuthUnknown();
}

final class Authenticated extends AuthState {
  const Authenticated(this.user);
  final User user;
  @override
  List<Object?> get props => [user];
}

final class Unauthenticated extends AuthState {
  const Unauthenticated({this.message, this.submitting = false});
  final String? message;
  final bool submitting;
  @override
  List<Object?> get props => [message, submitting];
}

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthUnknown()) {
    _expiredSub = _repository.sessionExpired.listen((_) => emit(
        const Unauthenticated(
            message: 'Your session has expired. Please sign in again.')));
  }

  final AuthRepository _repository;
  late final StreamSubscription<void> _expiredSub;

  Future<void> restore() async {
    final user = await _repository.restoreSession();
    emit(user == null ? const Unauthenticated() : Authenticated(user));
  }

  Future<void> login(String username, String password) async {
    emit(const Unauthenticated(submitting: true));
    try {
      emit(Authenticated(await _repository.login(username, password)));
    } on AppException catch (e) {
      emit(Unauthenticated(message: e.message));
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    emit(const Unauthenticated());
  }

  @override
  Future<void> close() {
    _expiredSub.cancel();
    return super.close();
  }
}

// ----------------------------- routing helper -----------------------------
/// Turns the cubit's stream into a Listenable that go_router can watch.
class StreamListenable extends ChangeNotifier {
  StreamListenable(Stream<dynamic> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
