import 'dart:convert';

/// Immutable model representing a nearby rest area, gas station, or safety haven.
class RestStopModel {
  final String id;
  final String name;
  final String type;
  final double lat;
  final double lng;
  final double distanceKm;
  final String address;
  final List<String> facilities;
  final bool isOpen24Hours;
  final String? phoneNumber;

  const RestStopModel({
    required this.id,
    required this.name,
    this.type = 'REST_AREA',
    required this.lat,
    required this.lng,
    this.distanceKm = 0.0,
    this.address = '',
    this.facilities = const [],
    this.isOpen24Hours = true,
    this.phoneNumber,
  });

  bool get isRestArea => type == 'REST_AREA';
  bool get isGasStation => type == 'GAS_STATION';

  RestStopModel copyWith({
    String? id,
    String? name,
    String? type,
    double? lat,
    double? lng,
    double? distanceKm,
    String? address,
    List<String>? facilities,
    bool? isOpen24Hours,
    String? phoneNumber,
  }) {
    return RestStopModel(
      id: id ?? this.id,
      name: name ?? this.name,
      type: type ?? this.type,
      lat: lat ?? this.lat,
      lng: lng ?? this.lng,
      distanceKm: distanceKm ?? this.distanceKm,
      address: address ?? this.address,
      facilities: facilities ?? this.facilities,
      isOpen24Hours: isOpen24Hours ?? this.isOpen24Hours,
      phoneNumber: phoneNumber ?? this.phoneNumber,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'lat': lat,
      'lng': lng,
      'distance_km': distanceKm,
      'address': address,
      'facilities': facilities,
      'is_open_24h': isOpen24Hours,
      'phone_number': phoneNumber,
    };
  }

  factory RestStopModel.fromMap(Map<String, Object?> map) {
    return RestStopModel(
      id: map['id']?.toString() ?? '',
      name: (map['name'] as String?) ?? 'Rest Area Terdekat',
      type: (map['type'] as String?) ?? 'REST_AREA',
      lat: (map['lat'] as num?)?.toDouble() ?? 0.0,
      lng: (map['lng'] as num?)?.toDouble() ?? 0.0,
      distanceKm: (map['distance_km'] as num?)?.toDouble() ?? 0.0,
      address: (map['address'] as String?) ?? '',
      facilities: (map['facilities'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const ['Toilet', 'Musholla', 'Parkir'],
      isOpen24Hours: (map['is_open_24h'] as bool?) ?? true,
      phoneNumber: map['phone_number'] as String?,
    );
  }

  String toJson() => json.encode(toMap());

  factory RestStopModel.fromJson(String source) =>
      RestStopModel.fromMap(json.decode(source) as Map<String, Object?>);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is RestStopModel &&
        other.id == id &&
        other.name == name &&
        other.type == type &&
        other.lat == lat &&
        other.lng == lng;
  }

  @override
  int get hashCode => Object.hash(id, name, type, lat, lng);
}
