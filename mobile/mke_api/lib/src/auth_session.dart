import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';

class AuthTokens {
  const AuthTokens({required this.access, required this.refresh});
  final String access;
  final String refresh;

  bool get accessExpiresSoon {
    try {
      final parts = access.split('.');
      final payload = jsonDecode(
        utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))),
      ) as Map<String, dynamic>;
      final expiry = DateTime.fromMillisecondsSinceEpoch(
        (payload['exp'] as int) * 1000,
        isUtc: true,
      );
      return expiry.isBefore(
        DateTime.now().toUtc().add(const Duration(seconds: 30)),
      );
    } catch (_) {
      return true;
    }
  }
}

class TokenStore {
  TokenStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessKey = 'mke_access_token';
  static const _refreshKey = 'mke_refresh_token';
  final FlutterSecureStorage _storage;

  Future<AuthTokens?> read() async {
    final access = await _storage.read(key: _accessKey);
    final refresh = await _storage.read(key: _refreshKey);
    if (access == null || refresh == null) return null;
    return AuthTokens(access: access, refresh: refresh);
  }

  Future<void> write(AuthTokens tokens) async {
    await _storage.write(key: _accessKey, value: tokens.access);
    await _storage.write(key: _refreshKey, value: tokens.refresh);
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}
