import '../../../core/constants/app_constants.dart';
import '../../../core/models/device_status.dart';
import '../../../core/models/family_model.dart';
import '../../../core/models/location_data.dart';

/// Immutable state holding real-time vehicle telemetry and map dashboard configurations.
class LiveMapState {
  final bool isConnected;
  final bool isConnecting;
  final DeviceStatus deviceStatus;
  final String vehicleName;
  final String driverName;
  final List<FamilyMemberModel> familyMembers;
  final int? selectedMemberId;
  final double centerLat;
  final double centerLng;
  final double zoom;
  final String? errorMessage;
  final String lastAlertMessage;

  const LiveMapState({
    this.isConnected = false,
    this.isConnecting = false,
    this.deviceStatus = const DeviceStatus(
      deviceId: 'pi4_car_01',
      driverUid: 'user_1',
      state: 'DRIVING',
      isOnline: true,
      location: LocationData(
        lat: AppConstants.defaultLat,
        lng: AppConstants.defaultLng,
        speedKmh: 45.0,
      ),
    ),
    this.vehicleName = 'Avanza Hitam - B 1234 XYZ',
    this.driverName = 'Budi Santoso',
    this.familyMembers = const [],
    this.selectedMemberId,
    this.centerLat = AppConstants.defaultLat,
    this.centerLng = AppConstants.defaultLng,
    this.zoom = 15.0,
    this.errorMessage,
    this.lastAlertMessage = '',
  });

  bool get isCritical => deviceStatus.isCritical;
  bool get isWarning => deviceStatus.isWarning;

  LiveMapState copyWith({
    bool? isConnected,
    bool? isConnecting,
    DeviceStatus? deviceStatus,
    String? vehicleName,
    String? driverName,
    List<FamilyMemberModel>? familyMembers,
    int? selectedMemberId,
    double? centerLat,
    double? centerLng,
    double? zoom,
    String? errorMessage,
    String? lastAlertMessage,
    bool clearError = false,
  }) {
    return LiveMapState(
      isConnected: isConnected ?? this.isConnected,
      isConnecting: isConnecting ?? this.isConnecting,
      deviceStatus: deviceStatus ?? this.deviceStatus,
      vehicleName: vehicleName ?? this.vehicleName,
      driverName: driverName ?? this.driverName,
      familyMembers: familyMembers ?? this.familyMembers,
      selectedMemberId: selectedMemberId ?? this.selectedMemberId,
      centerLat: centerLat ?? this.centerLat,
      centerLng: centerLng ?? this.centerLng,
      zoom: zoom ?? this.zoom,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      lastAlertMessage: lastAlertMessage ?? this.lastAlertMessage,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is LiveMapState &&
        other.isConnected == isConnected &&
        other.isConnecting == isConnecting &&
        other.deviceStatus == deviceStatus &&
        other.vehicleName == vehicleName &&
        other.driverName == driverName &&
        other.centerLat == centerLat &&
        other.centerLng == centerLng &&
        other.zoom == zoom;
  }

  @override
  int get hashCode {
    return Object.hash(
      isConnected,
      isConnecting,
      deviceStatus,
      vehicleName,
      driverName,
      centerLat,
      centerLng,
      zoom,
    );
  }
}
