import 'package:flutter/foundation.dart';

/// Immutable location and movement telemetry model.
@immutable
class LocationData {
  final double? lat;
  final double? lng;
  final double speedKmh;
  final double heading;

  const LocationData({
    this.lat,
    this.lng,
    this.speedKmh = 0.0,
    this.heading = 0.0,
  });

  bool get hasCoordinates => lat != null && lng != null;

  LocationData copyWith({
    double? lat,
    double? lng,
    double? speedKmh,
    double? heading,
  }) {
    return LocationData(
      lat: lat ?? this.lat,
      lng: lng ?? this.lng,
      speedKmh: speedKmh ?? this.speedKmh,
      heading: heading ?? this.heading,
    );
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'lat': lat,
      'lng': lng,
      'speed_kmh': speedKmh,
      'heading': heading,
    };
  }

  factory LocationData.fromMap(Map<String, Object?> map) {
    return LocationData(
      lat: (map['lat'] as num?)?.toDouble(),
      lng: (map['lng'] as num?)?.toDouble(),
      speedKmh: (map['speed_kmh'] as num?)?.toDouble() ?? 0.0,
      heading: (map['heading'] as num?)?.toDouble() ?? 0.0,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is LocationData &&
        other.lat == lat &&
        other.lng == lng &&
        other.speedKmh == speedKmh &&
        other.heading == heading;
  }

  @override
  int get hashCode => Object.hash(lat, lng, speedKmh, heading);

  @override
  String toString() {
    return 'LocationData(lat: $lat, lng: $lng, speed: ${speedKmh}km/h, heading: $heading°)';
  }
}

