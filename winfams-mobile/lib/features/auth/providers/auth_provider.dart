import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/family_model.dart';
import '../../../core/models/user_model.dart';
import '../../../core/network/api_client.dart';
import '../models/auth_state.dart';

/// Riverpod provider for the global API client instance.
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

/// Riverpod Notifier managing authentication, family groups, and device pairing.
class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState(status: AuthStatus.unauthenticated);

  ApiClient get _apiClient => ref.read(apiClientProvider);

  void clearError() => state = state.copyWith(clearError: true);

  String _dioError(DioException e, String fallback) {
    if (e.response?.data is Map) {
      return (e.response?.data as Map)['detail']?.toString() ?? fallback;
    }
    return e.message ?? fallback;
  }

  Future<void> _fetchUserFamilyAndDevices() async {
    try {
      final families = await _apiClient.getMyFamilies();
      if (families.isEmpty) return;
      final family = families.first;
      List<DeviceItemModel> devices = [];
      try {
        final overview = await _apiClient.getFamilyOverview(family.id);
        final rawDevices = (overview['devices'] as List<dynamic>?) ?? [];
        devices = rawDevices
            .whereType<Map>()
            .map((d) => DeviceItemModel.fromMap(
                  d.map((k, v) => MapEntry(k.toString(), v as Object?)),
                ))
            .toList();
      } catch (_) {}
      state = state.copyWith(currentFamily: family, devices: devices);
    } catch (_) {}
  }

  Future<void> refreshFamily() async {
    await _fetchUserFamilyAndDevices();
  }

  Future<bool> login({required String email, required String password}) async {
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
      state = state.copyWith(
        status: AuthStatus.authenticated,
        token: token,
        user: UserModel.fromMap(userMap),
      );
      await _fetchUserFamilyAndDevices();
      return true;
    } on DioException catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: _dioError(e, 'Gagal masuk. Periksa email & kata sandi.'),
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
        await _fetchUserFamilyAndDevices();
      } else {
        state = state.copyWith(status: AuthStatus.unauthenticated);
      }
      return true;
    } on DioException catch (e) {
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: _dioError(e, 'Registrasi gagal. Email mungkin sudah terdaftar.'),
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
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: _dioError(e, 'Gagal membuat grup keluarga.'),
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
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: _dioError(e, 'Kode undangan tidak valid.'),
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
      state = state.copyWith(
        status: AuthStatus.error,
        errorMessage: _dioError(e, 'Gagal mendaftarkan alat Pi 4.'),
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
