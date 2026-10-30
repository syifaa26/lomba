import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/fatigue_incident.dart';
import '../../auth/providers/auth_provider.dart';
import '../../live_map/providers/live_map_provider.dart';
import '../models/alert_state.dart';
import '../services/notification_service.dart';

/// Provider for NotificationService.
final notificationServiceProvider = Provider<NotificationService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final service = NotificationService(apiClient: apiClient);
  ref.onDispose(service.dispose);
  return service;
});

/// Riverpod Notifier managing emergency alarm state and immediate family notification response.
class AlertNotifier extends Notifier<AlertState> {
  StreamSubscription? _pushSub;
  StreamSubscription? _wsSub;

  @override
  AlertState build() {
    final authState = ref.watch(authProvider);
    final notificationService = ref.watch(notificationServiceProvider);
    final wsService = ref.watch(liveMapWebSocketServiceProvider);

    final driverName = authState.user?.name ?? 'Budi Santoso';
    final driverPhone = authState.user?.phoneNumber.isNotEmpty == true
        ? authState.user!.phoneNumber
        : '081234567890';
    final vehicleName = authState.devices.isNotEmpty
        ? authState.devices.first.vehicleName
        : 'Avanza Hitam - B 1234 XYZ';

    ref.onDispose(() {
      _pushSub?.cancel();
      _wsSub?.cancel();
    });

    _pushSub = notificationService.emergencyIncidentStream.listen((incident) {
      triggerEmergencyAlert(incident);
    });

    _wsSub = wsService.stream.listen((data) {
      final stateStr = data['state']?.toString() ?? '';
      if (stateStr == 'CRITICAL_DROWSY') {
        final incident = FatigueIncident.fromMap(data);
        triggerEmergencyAlert(incident);
      }
    });

    return AlertState(
      driverName: driverName,
      driverPhoneNumber: driverPhone,
      vehicleName: vehicleName,
    );
  }

  void triggerEmergencyAlert(FatigueIncident incident) {
    final history = List<FatigueIncident>.from(state.alertHistory)..insert(0, incident);
    state = state.copyWith(
      activeIncident: incident,
      isAlarmActive: true,
      isMuted: false,
      alertHistory: history,
    );
  }

  void silenceAlarm() {
    state = state.copyWith(isMuted: true);
  }

  void resolveActiveIncident() {
    final active = state.activeIncident;
    if (active != null) {
      final updatedActive = active.copyWith(resolved: true);
      final updatedHistory = state.alertHistory.map((item) {
        return item.incidentId == active.incidentId ? updatedActive : item;
      }).toList();

      state = state.copyWith(
        activeIncident: updatedActive,
        isAlarmActive: false,
        alertHistory: updatedHistory,
      );
    } else {
      state = state.copyWith(isAlarmActive: false);
    }
  }

  void dismissAlert() {
    state = state.copyWith(
      clearActiveIncident: true,
      isAlarmActive: false,
      isMuted: false,
    );
  }
}

/// Global provider for AlertNotifier.
final alertProvider = NotifierProvider<AlertNotifier, AlertState>(AlertNotifier.new);
