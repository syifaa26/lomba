import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/family_model.dart';
import '../../../core/models/user_model.dart';
import '../../../core/network/api_client.dart';
import '../models/auth_state.dart';

/// Riverpod provider for the global API client instance.
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

/// Riverpod Notifier managing authentication, family groups, and device pairing.
class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    return const AuthState(status: AuthStatus.unauthenticated);
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  void clearError() {
    state = state.copyWith(clearError: true);
  }

  Future<bool> login({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final res = await _apiClient.login(email: email, password: password);
      final token = res['access_token'] as String?;
      final userMap = res['user'] as Map<String, Object?>?;

      if (token == null || userMap == null) {
        state = state.copyWith(
          status: AuthStatus.error,
          errorMessage: 'Respon server tidak valid.',
        );
        return false;
      }

      _apiClient.setAuthToken(token);
      final user = UserModel.fromMap(userMap);

      state = state.copyWith(
        status: AuthStatus.authenticated,
        token: token,
        user: user,
      );
      return true;
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']?.toString()
          : e.message;
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: detail ?? 'Gagal masuk. Periksa kembali email dan kata sandi.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Terjadi kesalahan sistem: $e',
      );
      return false;
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
    String phoneNumber = '',
  }) async {
    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final res = await _apiClient.register(
        name: name,
        email: email,
        password: password,
        phoneNumber: phoneNumber,
      );
      final token = res['access_token'] as String?;
      final userMap = res['user'] as Map<String, Object?>?;

      if (token != null && userMap != null) {
        _apiClient.setAuthToken(token);
        state = state.copyWith(
          status: AuthStatus.authenticated,
          token: token,
          user: UserModel.fromMap(userMap),
        );
      } else {
        state = state.copyWith(status: AuthStatus.unauthenticated);
      }
      return true;
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']?.toString()
          : e.message;
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: detail ?? 'Registrasi gagal. Email mungkin sudah terdaftar.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Terjadi kesalahan sistem: $e',
      );
      return false;
    }
  }

  Future<bool> createFamily(String familyName) async {
    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final family = await _apiClient.createFamily(name: familyName);
      state = state.copyWith(
        status: AuthStatus.authenticated,
        currentFamily: family,
      );
      return true;
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']?.toString()
          : e.message;
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: detail ?? 'Gagal membuat grup keluarga.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Terjadi kesalahan: $e',
      );
      return false;
    }
  }

  Future<bool> joinFamily(String inviteCode) async {
    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final family = await _apiClient.joinFamily(inviteCode: inviteCode);
      state = state.copyWith(
        status: AuthStatus.authenticated,
        currentFamily: family,
      );
      return true;
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']?.toString()
          : e.message;
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: detail ?? 'Kode undangan tidak valid.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Terjadi kesalahan: $e',
      );
      return false;
    }
  }

  Future<bool> pairDevice({
    required String deviceUid,
    required String vehicleName,
    String apiKey = '',
  }) async {
    final familyId = state.currentFamily?.id;
    if (familyId == null) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Pilih atau buat grup keluarga terlebih dahulu.',
      );
      return false;
    }

    state = state.copyWith(status: AuthStatus.loading, clearError: true);
    try {
      final device = await _apiClient.registerDevice(
        familyId: familyId,
        deviceUid: deviceUid,
        vehicleName: vehicleName,
        apiKey: apiKey,
      );
      final updatedDevices = List<DeviceItemModel>.from(state.devices)..add(device);
      state = state.copyWith(
        status: AuthStatus.authenticated,
        devices: updatedDevices,
      );
      return true;
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response?.data as Map)['detail']?.toString()
          : e.message;
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: detail ?? 'Gagal mendaftarkan alat Pi 4.',
      );
      return false;
    } catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: 'Terjadi kesalahan: $e',
      );
      return false;
    }
  }

  void logout() {
    _apiClient.setAuthToken(null);
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

/// Global provider for AuthNotifier.
final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);
