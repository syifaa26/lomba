import 'dart:async';
import '../../../core/models/fatigue_incident.dart';
import '../../../core/network/api_client.dart';

/// Service handling high-priority push notifications and alert telemetry.
class NotificationService {
  final ApiClient _apiClient;
  final _incidentStreamController = StreamController<FatigueIncident>.broadcast();
  String? _fcmToken;

  NotificationService({required ApiClient apiClient}) : _apiClient = apiClient;

  Stream<FatigueIncident> get emergencyIncidentStream =>
      _incidentStreamController.stream;

  String? get fcmToken => _fcmToken;

  Future<bool> updateFcmToken(String token) async {
    _fcmToken = token;
    try {
      await _apiClient.dio.put<Map<String, Object?>>(
        '/api/v1/auth/fcm-token',
        data: {'fcm_token': token},
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  void handleIncomingPushPayload(Map<String, Object?> data) {
    try {
      final incident = FatigueIncident.fromMap(data);
      if (incident.isCritical || incident.isWarning) {
        _incidentStreamController.add(incident);
      }
    } catch (_) {}
  }

  void simulateEmergencyIncident({
    String incidentId = 'inc_demo_01',
    String deviceId = 'pi4_car_01',
    String type = 'CRITICAL_DROWSY',
    double confidence = 0.92,
    double duration = 2.4,
    double lat = -1.265386,
    double lng = 116.831200,
    double speedKmh = 72.0,
  }) {
    handleIncomingPushPayload({
      'incident_id': incidentId,
      'device_id': deviceId,
      'type': type,
      'confidence_score': confidence,
      'duration_seconds': duration,
      'location': {
        'lat': lat,
        'lng': lng,
        'speed_kmh': speedKmh,
      },
      'timestamp': DateTime.now().millisecondsSinceEpoch ~/ 1000,
      'resolved': false,
    });
  }

  void dispose() {
    _incidentStreamController.close();
  }
}
