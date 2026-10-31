/// Global application constants and schema keys for WinFams Mobile.
class AppConstants {
  AppConstants._();

  // App Identity
  static const String appName = 'WinFams';
  static const String appTagline = 'Window to Family Safety';

  // Driver States
  static const String stateNormal = 'NORMAL';
  static const String stateDriving = 'DRIVING';
  static const String stateWarningFatigue = 'WARNING_FATIGUE';
  static const String stateCriticalDrowsy = 'CRITICAL_DROWSY';

  // Incident Types
  static const String incidentCritical = 'CRITICAL_DROWSY';
  static const String incidentWarning = 'WARNING_FATIGUE';

  // Firebase Realtime Database Paths
  static const String rtdbDevicesPath = 'devices';
  static const String rtdbStatusChild = 'status';

  // Firestore Collections
  static const String firestoreIncidentsCollection = 'incidents';
  static const String firestoreUsersCollection = 'users';
  static const String firestoreFamilyGroupsCollection = 'family_groups';

  // FCM Topics
  static const String fcmFamilyTopicPrefix = 'family_';

  // Fallback Coordinates (Balikpapan / IKN area as per PRD spec)
  static const double defaultLat = -1.265386;
  static const double defaultLng = 116.831200;

  // REST API Endpoints
  static const String defaultBaseUrl = 'https://api.pemasukan.me';
  static const String epRegister = '/api/v1/auth/register';
  static const String epLogin = '/api/v1/auth/login';
  static const String epFcmToken = '/api/v1/auth/fcm-token';
  static const String epFamilies = '/api/v1/families';
  static const String epFamiliesJoin = '/api/v1/families/join';

  // WebSocket Endpoints
  static const String defaultWsBaseUrl = 'wss://api.pemasukan.me';
  static const String wsFamilyPrefix = '/ws/families';
}
