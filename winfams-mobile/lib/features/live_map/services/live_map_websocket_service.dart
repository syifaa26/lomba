import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../core/constants/app_constants.dart';

/// Service managing real-time WebSocket connection to the WinFams backend.
class LiveMapWebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  final _controller = StreamController<Map<String, Object?>>.broadcast();

  Stream<Map<String, Object?>> get stream => _controller.stream;
  bool get isConnected => _channel != null;

  void connect({
    required int familyId,
    String? token,
    String wsBaseUrl = AppConstants.defaultWsBaseUrl,
  }) {
    disconnect();

    final tokenParam = token != null ? '?token=$token' : '';
    final uri = Uri.parse('$wsBaseUrl${AppConstants.wsFamilyPrefix}/$familyId$tokenParam');

    try {
      _channel = WebSocketChannel.connect(uri);
      _subscription = _channel?.stream.listen(
        (dynamic message) {
          try {
            if (message is String) {
              final decoded = json.decode(message);
              if (decoded is Map<String, Object?>) {
                _controller.add(decoded);
              } else if (decoded is Map) {
                _controller.add(
                  decoded.map((k, v) => MapEntry(k.toString(), v as Object?)),
                );
              }
            }
          } catch (_) {}
        },
        onError: (Object error) {
          _controller.addError('WebSocket connection error: $error');
          disconnect();
        },
        onDone: () {
          disconnect();
        },
      );
    } catch (e) {
      _controller.addError('Failed to establish WebSocket: $e');
    }
  }

  void pushSimulatedTelemetry({
    required String deviceUid,
    required String state,
    required double lat,
    required double lng,
    required double speedKmh,
    double drowsyScore = 0.0,
    double yawnScore = 0.0,
  }) {
    _controller.add({
      'device_uid': deviceUid,
      'state': state,
      'drowsy_confidence': drowsyScore,
      'yawn_confidence': yawnScore,
      'location': {
        'lat': lat,
        'lng': lng,
        'speed_kmh': speedKmh,
      },
      'timestamp': DateTime.now().millisecondsSinceEpoch ~/ 1000,
    });
  }

  void disconnect() {
    _subscription?.cancel();
    _subscription = null;
    _channel?.sink.close();
    _channel = null;
  }

  void dispose() {
    disconnect();
    _controller.close();
  }
}
