import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'location_data.dart';

/// Immutable real-time edge device status model mapped from Firebase RTDB.
@immutable
class DeviceStatus {
  final String deviceId;
  final String driverUid;
  final bool isOnline;
  final String state;
  final double drowsyConfidence;
  final double yawnConfidence;
  final LocationData location;
  final int lastUpdated;

  const DeviceStatus({
    required this.deviceId,
    required this.driverUid,
    this.isOnline = false,
    this.state = 'NORMAL',
    this.drowsyConfidence = 0.0,
    this.yawnConfidence = 0.0,
    this.location = const LocationData(),
    this.lastUpdated = 0,
  });

  bool get isCritical => state == 'CRITICAL_DROWSY';
  bool get isWarning => state == 'WARNING_FATIGUE';
  bool get isDriving => state == 'DRIVING';

  DeviceStatus copyWith({
    String? deviceId,
    String? driverUid,
    bool? isOnline,
    String? state,
    double? drowsyConfidence,
    double? yawnConfidence,
    LocationData? location,
    int? lastUpdated,
  }) {
    return DeviceStatus(
      deviceId: deviceId ?? this.deviceId,
      driverUid: driverUid ?? this.driverUid,
      isOnline: isOnline ?? this.isOnline,
      state: state ?? this.state,
      drowsyConfidence: drowsyConfidence ?? this.drowsyConfidence,
      yawnConfidence: yawnConfidence ?? this.yawnConfidence,
      location: location ?? this.location,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'device_id': deviceId,
      'driver_uid': driverUid,
      'is_online': isOnline,
      'state': state,
      'drowsy_confidence': drowsyConfidence,
      'yawn_confidence': yawnConfidence,
      'location': location.toMap(),
      'last_updated': lastUpdated,
    };
  }

  String toJson() => json.encode(toMap());

  factory DeviceStatus.fromMap(Map<String, Object?> map) {
    final Object? rawLocation = map['location'];
    final LocationData parsedLocation;
    if (rawLocation is Map<String, Object?>) {
      parsedLocation = LocationData.fromMap(rawLocation);
    } else if (rawLocation is Map) {
      parsedLocation = LocationData.fromMap(
        rawLocation.map((k, v) => MapEntry(k.toString(), v as Object?)),
      );
    } else {
      parsedLocation = const LocationData();
    }

    return DeviceStatus(
      deviceId: (map['device_id'] ?? map['device_uid']) as String? ?? '',
      driverUid: map['driver_uid'] as String? ?? '',
      isOnline: map['is_online'] as bool? ?? false,
      state: (map['state'] ?? map['current_state']) as String? ?? 'NORMAL',
      drowsyConfidence: (map['drowsy_confidence'] as num?)?.toDouble() ?? 0.0,
      yawnConfidence: (map['yawn_confidence'] as num?)?.toDouble() ?? 0.0,
      location: parsedLocation,
      lastUpdated: (map['last_updated'] ?? map['timestamp'] ?? map['recorded_at']) as int? ??
          ((map['last_updated'] ?? map['timestamp'] ?? map['recorded_at']) as num?)?.toInt() ??
          0,
    );
  }

  factory DeviceStatus.fromJson(String source) =>
      DeviceStatus.fromMap(json.decode(source) as Map<String, Object?>);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is DeviceStatus &&
        other.deviceId == deviceId &&
        other.driverUid == driverUid &&
        other.isOnline == isOnline &&
        other.state == state &&
        other.drowsyConfidence == drowsyConfidence &&
        other.yawnConfidence == yawnConfidence &&
        other.location == location &&
        other.lastUpdated == lastUpdated;
  }

  @override
  int get hashCode => Object.hash(
        deviceId,
        driverUid,
        isOnline,
        state,
        drowsyConfidence,
        yawnConfidence,
        location,
        lastUpdated,
      );

  @override
  String toString() {
    return 'DeviceStatus(id: $deviceId, state: $state, online: $isOnline, loc: $location)';
  }
}

