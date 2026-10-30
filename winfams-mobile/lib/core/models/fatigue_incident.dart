import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'location_data.dart';

/// Immutable fatigue incident record mapped from Firestore and offline queue.
@immutable
class FatigueIncident {
  final String incidentId;
  final String deviceId;
  final String driverUid;
  final String familyGroupId;
  final String type;
  final double confidenceScore;
  final double durationSeconds;
  final LocationData location;
  final int timestamp;
  final bool resolved;

  const FatigueIncident({
    required this.incidentId,
    required this.deviceId,
    required this.driverUid,
    this.familyGroupId = '',
    required this.type,
    this.confidenceScore = 0.0,
    this.durationSeconds = 0.0,
    this.location = const LocationData(),
    this.timestamp = 0,
    this.resolved = false,
  });

  bool get isCritical => type == 'CRITICAL_DROWSY';
  bool get isWarning => type == 'WARNING_FATIGUE';

  FatigueIncident copyWith({
    String? incidentId,
    String? deviceId,
    String? driverUid,
    String? familyGroupId,
    String? type,
    double? confidenceScore,
    double? durationSeconds,
    LocationData? location,
    int? timestamp,
    bool? resolved,
  }) {
    return FatigueIncident(
      incidentId: incidentId ?? this.incidentId,
      deviceId: deviceId ?? this.deviceId,
      driverUid: driverUid ?? this.driverUid,
      familyGroupId: familyGroupId ?? this.familyGroupId,
      type: type ?? this.type,
      confidenceScore: confidenceScore ?? this.confidenceScore,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      location: location ?? this.location,
      timestamp: timestamp ?? this.timestamp,
      resolved: resolved ?? this.resolved,
    );
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'incident_id': incidentId,
      'device_id': deviceId,
      'driver_uid': driverUid,
      'family_group_id': familyGroupId,
      'type': type,
      'confidence_score': confidenceScore,
      'duration_seconds': durationSeconds,
      'location': location.toMap(),
      'timestamp': timestamp,
      'resolved': resolved,
    };
  }

  String toJson() => json.encode(toMap());

  factory FatigueIncident.fromMap(Map<String, Object?> map) {
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

    return FatigueIncident(
      incidentId: (map['incident_id'] ?? map['id'])?.toString() ?? '',
      deviceId: (map['device_id'] ?? map['device_uid']) as String? ?? '',
      driverUid: map['driver_uid'] as String? ?? '',
      familyGroupId: (map['family_group_id'] ?? map['family_id'])?.toString() ?? '',
      type: (map['type'] ?? map['incident_type']) as String? ?? 'CRITICAL_DROWSY',
      confidenceScore: (map['confidence_score'] as num?)?.toDouble() ?? 0.0,
      durationSeconds: (map['duration_seconds'] as num?)?.toDouble() ?? 0.0,
      location: parsedLocation,
      timestamp: (map['timestamp'] ?? map['recorded_at']) as int? ??
          ((map['timestamp'] ?? map['recorded_at']) as num?)?.toInt() ??
          0,
      resolved: map['resolved'] as bool? ?? false,
    );
  }

  factory FatigueIncident.fromJson(String source) =>
      FatigueIncident.fromMap(json.decode(source) as Map<String, Object?>);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is FatigueIncident &&
        other.incidentId == incidentId &&
        other.deviceId == deviceId &&
        other.driverUid == driverUid &&
        other.familyGroupId == familyGroupId &&
        other.type == type &&
        other.confidenceScore == confidenceScore &&
        other.durationSeconds == durationSeconds &&
        other.location == location &&
        other.timestamp == timestamp &&
        other.resolved == resolved;
  }

  @override
  int get hashCode => Object.hash(
        incidentId,
        deviceId,
        driverUid,
        familyGroupId,
        type,
        confidenceScore,
        durationSeconds,
        location,
        timestamp,
        resolved,
      );

  @override
  String toString() {
    return 'FatigueIncident(id: $incidentId, type: $type, score: $confidenceScore, time: $timestamp)';
  }
}

