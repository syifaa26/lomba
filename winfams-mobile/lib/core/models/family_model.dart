import 'dart:convert';

/// Immutable model representing a family safety group.
class FamilyModel {
  final int id;
  final String name;
  final String inviteCode;
  final int createdBy;
  final DateTime createdAt;

  const FamilyModel({
    required this.id,
    required this.name,
    required this.inviteCode,
    required this.createdBy,
    required this.createdAt,
  });

  FamilyModel copyWith({
    int? id,
    String? name,
    String? inviteCode,
    int? createdBy,
    DateTime? createdAt,
  }) {
    return FamilyModel(
      id: id ?? this.id,
      name: name ?? this.name,
      inviteCode: inviteCode ?? this.inviteCode,
      createdBy: createdBy ?? this.createdBy,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'invite_code': inviteCode,
      'created_by': createdBy,
      'created_at': createdAt.toIso8601String(),
    };
  }

  factory FamilyModel.fromMap(Map<String, Object?> map) {
    return FamilyModel(
      id: (map['id'] as num?)?.toInt() ?? 0,
      name: (map['name'] as String?) ?? '',
      inviteCode: (map['invite_code'] as String?) ?? '',
      createdBy: (map['created_by'] as num?)?.toInt() ?? 0,
      createdAt: map['created_at'] != null
          ? DateTime.tryParse(map['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  String toJson() => json.encode(toMap());

  factory FamilyModel.fromJson(String source) =>
      FamilyModel.fromMap(json.decode(source) as Map<String, Object?>);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is FamilyModel &&
        other.id == id &&
        other.name == name &&
        other.inviteCode == inviteCode &&
        other.createdBy == createdBy;
  }

  @override
  int get hashCode => Object.hash(id, name, inviteCode, createdBy);
}

/// Immutable model representing a member inside a family.
class FamilyMemberModel {
  final int id;
  final int userId;
  final String name;
  final String email;
  final String role;
  final DateTime joinedAt;

  const FamilyMemberModel({
    required this.id,
    required this.userId,
    required this.name,
    required this.email,
    required this.role,
    required this.joinedAt,
  });

  factory FamilyMemberModel.fromMap(Map<String, Object?> map) {
    return FamilyMemberModel(
      id: (map['id'] as num?)?.toInt() ?? 0,
      userId: (map['user_id'] as num?)?.toInt() ?? 0,
      name: (map['name'] as String?) ?? '',
      email: (map['email'] as String?) ?? '',
      role: (map['role'] as String?) ?? 'MONITOR',
      joinedAt: map['joined_at'] != null
          ? DateTime.tryParse(map['joined_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'email': email,
      'role': role,
      'joined_at': joinedAt.toIso8601String(),
    };
  }
}

/// Immutable model representing an IoT edge device in the family fleet.
class DeviceItemModel {
  final int id;
  final String deviceUid;
  final String vehicleName;
  final bool isOnline;
  final String currentState;
  final double? lastLat;
  final double? lastLng;
  final double lastSpeedKmh;
  final DateTime? lastSeenAt;
  final int? activeDriverId;

  const DeviceItemModel({
    required this.id,
    required this.deviceUid,
    required this.vehicleName,
    this.isOnline = false,
    this.currentState = 'IDLE',
    this.lastLat,
    this.lastLng,
    this.lastSpeedKmh = 0.0,
    this.lastSeenAt,
    this.activeDriverId,
  });

  factory DeviceItemModel.fromMap(Map<String, Object?> map) {
    return DeviceItemModel(
      id: (map['id'] as num?)?.toInt() ?? 0,
      deviceUid: (map['device_uid'] as String?) ?? '',
      vehicleName: (map['vehicle_name'] as String?) ?? '',
      isOnline: (map['is_online'] as bool?) ?? false,
      currentState: (map['current_state'] as String?) ?? 'IDLE',
      lastLat: (map['last_lat'] as num?)?.toDouble(),
      lastLng: (map['last_lng'] as num?)?.toDouble(),
      lastSpeedKmh: (map['last_speed_kmh'] as num?)?.toDouble() ?? 0.0,
      lastSeenAt: map['last_seen_at'] != null
          ? DateTime.tryParse(map['last_seen_at'] as String)
          : null,
      activeDriverId: (map['active_driver_id'] as num?)?.toInt(),
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'device_uid': deviceUid,
      'vehicle_name': vehicleName,
      'is_online': isOnline,
      'current_state': currentState,
      'last_lat': lastLat,
      'last_lng': lastLng,
      'last_speed_kmh': lastSpeedKmh,
      'last_seen_at': lastSeenAt?.toIso8601String(),
      'active_driver_id': activeDriverId,
    };
  }
}
