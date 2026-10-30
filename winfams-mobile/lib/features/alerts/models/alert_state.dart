import '../../../core/models/fatigue_incident.dart';

/// Immutable state managing active emergency alarms, critical incidents, and family response.
class AlertState {
  final FatigueIncident? activeIncident;
  final bool isAlarmActive;
  final bool isMuted;
  final String driverName;
  final String driverPhoneNumber;
  final String vehicleName;
  final List<FatigueIncident> alertHistory;

  const AlertState({
    this.activeIncident,
    this.isAlarmActive = false,
    this.isMuted = false,
    this.driverName = 'Budi Santoso',
    this.driverPhoneNumber = '081234567890',
    this.vehicleName = 'Avanza Hitam - B 1234 XYZ',
    this.alertHistory = const [],
  });

  bool get hasActiveAlert => activeIncident != null && isAlarmActive;

  AlertState copyWith({
    FatigueIncident? activeIncident,
    bool? isAlarmActive,
    bool? isMuted,
    String? driverName,
    String? driverPhoneNumber,
    String? vehicleName,
    List<FatigueIncident>? alertHistory,
    bool clearActiveIncident = false,
  }) {
    return AlertState(
      activeIncident: clearActiveIncident
          ? null
          : (activeIncident ?? this.activeIncident),
      isAlarmActive: isAlarmActive ?? this.isAlarmActive,
      isMuted: isMuted ?? this.isMuted,
      driverName: driverName ?? this.driverName,
      driverPhoneNumber: driverPhoneNumber ?? this.driverPhoneNumber,
      vehicleName: vehicleName ?? this.vehicleName,
      alertHistory: alertHistory ?? this.alertHistory,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is AlertState &&
        other.activeIncident == activeIncident &&
        other.isAlarmActive == isAlarmActive &&
        other.isMuted == isMuted &&
        other.driverName == driverName &&
        other.driverPhoneNumber == driverPhoneNumber &&
        other.vehicleName == vehicleName;
  }

  @override
  int get hashCode {
    return Object.hash(
      activeIncident,
      isAlarmActive,
      isMuted,
      driverName,
      driverPhoneNumber,
      vehicleName,
    );
  }
}
