import 'dart:convert';

/// Immutable model representing an authenticated user profile.
class UserModel {
  final int id;
  final String name;
  final String email;
  final String phoneNumber;
  final String? fcmToken;
  final DateTime createdAt;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    required this.phoneNumber,
    this.fcmToken,
    required this.createdAt,
  });

  UserModel copyWith({
    int? id,
    String? name,
    String? email,
    String? phoneNumber,
    String? fcmToken,
    DateTime? createdAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      fcmToken: fcmToken ?? this.fcmToken,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'phone_number': phoneNumber,
      'fcm_token': fcmToken,
      'created_at': createdAt.toIso8601String(),
    };
  }

  factory UserModel.fromMap(Map<String, Object?> map) {
    return UserModel(
      id: (map['id'] as num?)?.toInt() ?? 0,
      name: (map['name'] as String?) ?? '',
      email: (map['email'] as String?) ?? '',
      phoneNumber: (map['phone_number'] as String?) ?? '',
      fcmToken: map['fcm_token'] as String?,
      createdAt: map['created_at'] != null
          ? DateTime.tryParse(map['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  String toJson() => json.encode(toMap());

  factory UserModel.fromJson(String source) =>
      UserModel.fromMap(json.decode(source) as Map<String, Object?>);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is UserModel &&
        other.id == id &&
        other.name == name &&
        other.email == email &&
        other.phoneNumber == phoneNumber &&
        other.fcmToken == fcmToken;
  }

  @override
  int get hashCode {
    return Object.hash(id, name, email, phoneNumber, fcmToken);
  }

  @override
  String toString() {
    return 'UserModel(id: $id, name: $name, email: $email, phone: $phoneNumber)';
  }
}
