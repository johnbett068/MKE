import 'dart:async';

import 'package:dio/dio.dart';

import 'auth_session.dart';

class ApiFailure implements Exception {
  const ApiFailure(this.message, {this.statusCode, this.fields});
  final String message;
  final int? statusCode;
  final Map<String, dynamic>? fields;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({required String baseUrl, TokenStore? tokenStore, Dio? dio})
      : tokens = tokenStore ?? TokenStore(),
        http = dio ??
            Dio(
              BaseOptions(
                baseUrl: baseUrl,
                connectTimeout: const Duration(seconds: 12),
                receiveTimeout: const Duration(seconds: 20),
                headers: {'Accept': 'application/json'},
              ),
            ) {
    http.interceptors.add(
      InterceptorsWrapper(onRequest: _authorize, onError: _handleUnauthorized),
    );
  }

  final Dio http;
  final TokenStore tokens;
  Completer<AuthTokens?>? _refreshing;

  Future<void> _authorize(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final session = await tokens.read();
    if (session != null) {
      options.headers['Authorization'] = 'Bearer ${session.access}';
    }
    handler.next(options);
  }

  Future<void> _handleUnauthorized(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final request = error.requestOptions;
    final alreadyRetried = request.extra['mle_retried'] == true;
    if (error.response?.statusCode != 401 || alreadyRetried) {
      handler.reject(_normalize(error));
      return;
    }
    final refreshed = await _refresh();
    if (refreshed == null) {
      handler.reject(_normalize(error));
      return;
    }
    request.extra['mle_retried'] = true;
    request.headers['Authorization'] = 'Bearer ${refreshed.access}';
    try {
      handler.resolve(await http.fetch<dynamic>(request));
    } on DioException catch (retryError) {
      handler.reject(_normalize(retryError));
    }
  }

  Future<AuthTokens?> _refresh() async {
    if (_refreshing != null) return _refreshing!.future;
    final completer = Completer<AuthTokens?>();
    _refreshing = completer;
    try {
      final current = await tokens.read();
      if (current == null) {
        completer.complete(null);
        return null;
      }
      final refreshDio = Dio(BaseOptions(baseUrl: http.options.baseUrl));
      final response = await refreshDio.post<Map<String, dynamic>>(
        '/api/v1/auth/token/refresh/',
        data: {'refresh': current.refresh},
      );
      final body = response.data!;
      final updated = AuthTokens(
        access: body['access'] as String,
        refresh: (body['refresh'] as String?) ?? current.refresh,
      );
      await tokens.write(updated);
      completer.complete(updated);
      return updated;
    } catch (_) {
      await tokens.clear();
      completer.complete(null);
      return null;
    } finally {
      _refreshing = null;
    }
  }

  Future<AuthTokens?> refreshTokens() => _refresh();

  Future<AuthTokens> login(String email, String password) async {
    try {
      final response = await http.post<Map<String, dynamic>>(
        '/api/v1/auth/token/',
        data: {'email': email, 'password': password},
      );
      final session = AuthTokens(
        access: response.data!['access'] as String,
        refresh: response.data!['refresh'] as String,
      );
      await tokens.write(session);
      return session;
    } on DioException catch (error) {
      throw _normalize(error);
    }
  }

  DioException _normalize(DioException error) {
    final data = error.response?.data;
    final fields = data is Map ? Map<String, dynamic>.from(data) : null;
    final detail = fields?['detail'];
    return error.copyWith(
      error: ApiFailure(
        detail is String ? detail : 'Unable to complete the request.',
        statusCode: error.response?.statusCode,
        fields: fields,
      ),
    );
  }
}
