import '../../../core/models/family_model.dart';
import '../../../core/models/user_model.dart';

/// Authentication state lifecycle phases.
enum AuthStatus {
  initial,
  loading,
  authenticated,
  unauthenticated,
  error,
}

/// Immutable state holding authentication, family, and paired devices information.
class AuthState {
  final AuthStatus status;
  final String? token;
  final UserModel? user;
  final FamilyModel? currentFamily;
  final List<DeviceItemModel> devices;
  final String? errorMessage;

  const AuthState({
    this.status = AuthStatus.initial,
    this.token,
    this.user,
    this.currentFamily,
    this.devices = const [],
    this.errorMessage,
  });

  bool get isLoading => status == AuthStatus.loading;
  bool get isAuthenticated =>
      status == AuthStatus.authenticated && token != null && user != null;
  bool get hasFamily => currentFamily != null;
  bool get hasDevice => devices.isNotEmpty;

  AuthState copyWith({
    AuthStatus? status,
    String? token,
    UserModel? user,
    FamilyModel? currentFamily,
    List<DeviceItemModel>? devices,
    String? errorMessage,
    bool clearError = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      token: token ?? this.token,
      user: user ?? this.user,
      currentFamily: currentFamily ?? this.currentFamily,
      devices: devices ?? this.devices,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is AuthState &&
        other.status == status &&
        other.token == token &&
        other.user == user &&
        other.currentFamily == currentFamily &&
        other.errorMessage == errorMessage;
  }

  @override
  int get hashCode {
    return Object.hash(status, token, user, currentFamily, errorMessage);
  }
}
