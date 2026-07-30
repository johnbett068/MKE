import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:web_socket_channel/io.dart';

import 'auth_session.dart';
import 'dtos.dart';

class RealtimeClient {
  RealtimeClient({
    required this.websocketBaseUrl,
    required this.tokens,
    this.refreshTokens,
  });

  final String websocketBaseUrl;
  final TokenStore tokens;
  final Future<AuthTokens?> Function()? refreshTokens;
  final _events = StreamController<RealtimeEnvelope>.broadcast();
  IOWebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _reconnectTimer;
  String? _path;
  bool _closed = false;
  int _attempt = 0;

  Stream<RealtimeEnvelope> get events => _events.stream;

  Future<void> connect(String path) async {
    _path = path;
    _closed = false;
    await _open();
  }

  Future<void> _open() async {
    var session = await tokens.read();
    if (session?.accessExpiresSoon == true && refreshTokens != null) {
      session = await refreshTokens!();
    }
    if (session == null || _path == null || _closed) return;
    try {
      _channel = IOWebSocketChannel.connect(
        Uri.parse('$websocketBaseUrl$_path'),
        headers: {HttpHeaders.authorizationHeader: 'Bearer ${session.access}'},
        pingInterval: const Duration(seconds: 20),
        connectTimeout: const Duration(seconds: 12),
      );
      await _channel!.ready;
      _attempt = 0;
      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
        cancelOnError: true,
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final json = jsonDecode(raw as String) as Map<String, dynamic>;
      final envelope = RealtimeEnvelope.fromJson(json);
      if (envelope.schemaVersion == '1.0') _events.add(envelope);
    } catch (error, stack) {
      _events.addError(error, stack);
    }
  }

  void send(String type, Map<String, dynamic> data, {String? requestId}) {
    _channel?.sink.add(
      jsonEncode({
        'schema_version': '1.0',
        'type': type,
        if (requestId != null) 'request_id': requestId,
        'data': data,
      }),
    );
  }

  void _scheduleReconnect() {
    if (_closed || _reconnectTimer?.isActive == true) return;
    _subscription?.cancel();
    final seconds = min(30, pow(2, _attempt).toInt());
    _attempt++;
    _reconnectTimer = Timer(Duration(seconds: seconds), _open);
  }

  Future<void> close() async {
    _closed = true;
    _reconnectTimer?.cancel();
    await _subscription?.cancel();
    await _channel?.sink.close();
    await _events.close();
  }
}
