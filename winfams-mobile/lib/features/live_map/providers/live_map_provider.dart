import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/device_status.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/live_map_state.dart';
import '../services/live_map_websocket_service.dart';

/// Provider for the LiveMap WebSocket service singleton.
final liveMapWebSocketServiceProvider = Provider<LiveMapWebSocketService>((ref) {
  final service = LiveMapWebSocketService();
  ref.onDispose(service.dispose);
  return service;
});

/// Riverpod Notifier managing real-time map state, vehicle position, and driver alerts.
class LiveMapNotifier extends Notifier<LiveMapState> {
  StreamSubscription? _telemetrySub;

  @override
  LiveMapState build() {
    final authState = ref.watch(authProvider);
    final vehicleName = authState.devices.isNotEmpty
        ? authState.devices.first.vehicleName
        : 'Kendaraan Keluarga';
    final driverName = authState.user?.name ?? 'Pengemudi Utama';

    ref.onDispose(() {
      _telemetrySub?.cancel();
    });

    // Defer side-effects until after build() returns the initial state.
    // Writing to `state` inside build() before returning causes
    // "Tried to read the state of an uninitialized provider".
    Future.microtask(() {
      _listenToWebSocketStream();
      final familyId = authState.currentFamily?.id;
      if (familyId != null) {
        connectToFamily(familyId, token: authState.token);
      }
    });

    return LiveMapState(
      vehicleName: vehicleName,
      driverName: driverName,
    );
  }

  LiveMapWebSocketService get _wsService =>
      ref.read(liveMapWebSocketServiceProvider);

  void _listenToWebSocketStream() {
    _telemetrySub?.cancel();
    _telemetrySub = _wsService.stream.listen(
      (data) {
        _handleIncomingTelemetry(data);
      },
      onError: (Object error) {
        state = state.copyWith(
          isConnected: false,
          errorMessage: 'Sambungan terputus: $error',
        );
      },
    );
  }

  void connectToFamily(int familyId, {String? token}) {
    state = state.copyWith(isConnecting: true, clearError: true);
    _wsService.connect(familyId: familyId, token: token);
    state = state.copyWith(
      isConnected: true,
      isConnecting: false,
    );
  }

  void _handleIncomingTelemetry(Map<String, Object?> data) {
    final newStatus = DeviceStatus.fromMap(data);
    String alertMsg = '';

    if (newStatus.isCritical) {
      alertMsg = 'PERINGATAN DARURAT: Pengemudi mengalami kantuk berat!';
    } else if (newStatus.isWarning) {
      alertMsg = 'PERINGATAN: Pengemudi terdeteksi mengantuk / menguap berulang!';
    }

    final double newLat = newStatus.location.lat ?? state.centerLat;
    final double newLng = newStatus.location.lng ?? state.centerLng;

    state = state.copyWith(
      isConnected: true,
      deviceStatus: newStatus,
      centerLat: newLat,
      centerLng: newLng,
      lastAlertMessage: alertMsg,
    );
  }

  void centerOnVehicle() {
    final lat = state.deviceStatus.location.lat;
    final lng = state.deviceStatus.location.lng;
    if (lat != null && lng != null) {
      state = state.copyWith(centerLat: lat, centerLng: lng, zoom: 16.0);
    }
  }

  void setZoom(double newZoom) {
    state = state.copyWith(zoom: newZoom);
  }

  void simulateDrivingStep({
    required double deltaLat,
    required double deltaLng,
    required double speedKmh,
    String stateName = 'DRIVING',
    double drowsy = 0.1,
    double yawn = 0.05,
  }) {
    final currentLat = state.deviceStatus.location.lat ?? state.centerLat;
    final currentLng = state.deviceStatus.location.lng ?? state.centerLng;

    _wsService.pushSimulatedTelemetry(
      deviceUid: state.deviceStatus.deviceId,
      state: stateName,
      lat: currentLat + deltaLat,
      lng: currentLng + deltaLng,
      speedKmh: speedKmh,
      drowsyScore: drowsy,
      yawnScore: yawn,
    );
  }
}

/// Global provider for LiveMapNotifier.
final liveMapProvider =
    NotifierProvider<LiveMapNotifier, LiveMapState>(LiveMapNotifier.new);
