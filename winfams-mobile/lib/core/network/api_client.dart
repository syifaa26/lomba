import 'package:dio/dio.dart';
import '../constants/app_constants.dart';
import '../models/family_model.dart';
import '../models/fatigue_incident.dart';

/// Network client for communicating with the WinFams REST API.
class ApiClient {
  final Dio dio;
  String? _authToken;

  ApiClient({Dio? customDio, String baseUrl = AppConstants.defaultBaseUrl})
      : dio = customDio ??
            Dio(
              BaseOptions(
                baseUrl: baseUrl,
                connectTimeout: const Duration(seconds: 10),
                receiveTimeout: const Duration(seconds: 10),
                headers: {
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                },
              ),
            );

  void setAuthToken(String? token) {
    _authToken = token;
    if (token != null) {
      dio.options.headers['Authorization'] = 'Bearer $token';
    } else {
      dio.options.headers.remove('Authorization');
    }
  }

  String? get authToken => _authToken;

  Future<Map<String, Object?>> register({
    required String name,
    required String email,
    required String password,
    String phoneNumber = '',
  }) async {
    final response = await dio.post<Map<String, Object?>>(
      AppConstants.epRegister,
      data: {
        'name': name,
        'email': email,
        'password': password,
        'phone_number': phoneNumber,
      },
    );
    final data = response.data ?? <String, Object?>{};
    return data;
  }

  Future<Map<String, Object?>> login({
    required String email,
    required String password,
  }) async {
    final response = await dio.post<Map<String, Object?>>(
      AppConstants.epLogin,
      data: {
        'email': email,
        'password': password,
      },
    );
    final data = response.data ?? <String, Object?>{};
    return data;
  }

  Future<FamilyModel> createFamily({required String name}) async {
    final response = await dio.post<Map<String, Object?>>(
      AppConstants.epFamilies,
      data: {'name': name},
    );
    final data = response.data ?? <String, Object?>{};
    return FamilyModel.fromMap(data);
  }

  Future<FamilyModel> joinFamily({
    required String inviteCode,
    String role = 'MONITOR',
  }) async {
    final response = await dio.post<Map<String, Object?>>(
      AppConstants.epFamiliesJoin,
      data: {
        'invite_code': inviteCode,
        'role': role,
      },
    );
    final data = response.data ?? <String, Object?>{};
    return FamilyModel.fromMap(data);
  }

  Future<DeviceItemModel> registerDevice({
    required int familyId,
    required String deviceUid,
    required String vehicleName,
    String apiKey = '',
  }) async {
    final response = await dio.post<Map<String, Object?>>(
      '${AppConstants.epFamilies}/$familyId/devices',
      data: {
        'device_uid': deviceUid,
        'vehicle_name': vehicleName,
        'api_key': apiKey,
      },
    );
    final data = response.data ?? <String, Object?>{};
    return DeviceItemModel.fromMap(data);
  }

  Future<Map<String, Object?>> getFamilyOverview(int familyId) async {
    final response = await dio.get<Map<String, Object?>>(
      '${AppConstants.epFamilies}/$familyId/overview',
    );
    return response.data ?? <String, Object?>{};
  }

  Future<List<FatigueIncident>> getFamilyIncidents(
    int familyId, {
    String? incidentType,
  }) async {
    final queryParams = <String, Object?>{};
    if (incidentType != null) {
      queryParams['incident_type'] = incidentType;
    }
    final response = await dio.get<List<dynamic>>(
      '${AppConstants.epFamilies}/$familyId/incidents',
      queryParameters: queryParams,
    );
    final rawList = response.data ?? <dynamic>[];
    return rawList.map((item) {
      if (item is Map<String, Object?>) {
        return FatigueIncident.fromMap(item);
      } else if (item is Map) {
        return FatigueIncident.fromMap(
          item.map((k, v) => MapEntry(k.toString(), v as Object?)),
        );
      }
      return const FatigueIncident(
        incidentId: '',
        deviceId: '',
        driverUid: '',
        type: 'WARNING_FATIGUE',
      );
    }).toList();
  }

  Future<List<Map<String, Object?>>> getNearbyRestStops({
    required double lat,
    required double lng,
  }) async {
    final response = await dio.get<List<dynamic>>(
      '/api/v1/rest-stops/nearby',
      queryParameters: {'lat': lat, 'lng': lng},
    );
    final rawList = response.data ?? <dynamic>[];
    return rawList
        .whereType<Map>()
        .map((e) => e.map((k, v) => MapEntry(k.toString(), v as Object?)))
        .toList();
  }
}
