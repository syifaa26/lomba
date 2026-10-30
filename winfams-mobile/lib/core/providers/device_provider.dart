import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/device_status.dart';
import '../models/location_data.dart';

/// Notifier managing active device identifier currently monitored.
class ActiveDeviceIdNotifier extends Notifier<String> {
  @override
  String build() => 'pi4_car_01';

  void setDeviceId(String id) {
    state = id;
  }
}

/// Global provider for active device ID.
final activeDeviceIdProvider =
    NotifierProvider<ActiveDeviceIdNotifier, String>(
  ActiveDeviceIdNotifier.new,
);

/// Notifier managing real-time device telemetry status.
class DeviceStatusNotifier extends Notifier<DeviceStatus> {
  @override
  DeviceStatus build() {
    final String deviceId = ref.watch(activeDeviceIdProvider);
    return DeviceStatus(
      deviceId: deviceId,
      driverUid: 'user_123',
      isOnline: true,
      state: 'NORMAL',
      drowsyConfidence: 0.0,
      yawnConfidence: 0.0,
      location: const LocationData(
        lat: -1.265386,
        lng: 116.831200,
        speedKmh: 0.0,
        heading: 0.0,
      ),
      lastUpdated: DateTime.now().millisecondsSinceEpoch ~/ 1000,
    );
  }

  void updateStatus(DeviceStatus newStatus) {
    state = newStatus;
  }

  void updateState(String newState, {double? drowsyScore, double? yawnScore}) {
    state = state.copyWith(
      state: newState,
      drowsyConfidence: drowsyScore ?? state.drowsyConfidence,
      yawnConfidence: yawnScore ?? state.yawnConfidence,
      lastUpdated: DateTime.now().millisecondsSinceEpoch ~/ 1000,
    );
  }

  void updateLocation(LocationData newLocation) {
    state = state.copyWith(
      location: newLocation,
      lastUpdated: DateTime.now().millisecondsSinceEpoch ~/ 1000,
    );
  }
}

/// Global provider for real-time device status.
final deviceStatusProvider =
    NotifierProvider<DeviceStatusNotifier, DeviceStatus>(
  DeviceStatusNotifier.new,
);
