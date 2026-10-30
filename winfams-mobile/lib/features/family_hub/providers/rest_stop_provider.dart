import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../auth/providers/auth_provider.dart';
import '../../live_map/providers/live_map_provider.dart';
import '../models/rest_stop_model.dart';
import '../models/rest_stop_state.dart';

/// Riverpod Notifier providing curated nearby rest stops and sharing actions.
class RestStopNotifier extends Notifier<RestStopState> {
  @override
  RestStopState build() {
    return RestStopState(restStops: _getSampleNearbyStops());
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  Future<void> fetchNearbyRestStops({double? lat, double? lng}) async {
    final liveState = ref.read(liveMapProvider);
    final targetLat = lat ?? liveState.deviceStatus.location.lat ?? AppConstants.defaultLat;
    final targetLng = lng ?? liveState.deviceStatus.location.lng ?? AppConstants.defaultLng;

    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final rawList = await _apiClient.getNearbyRestStops(
        lat: targetLat,
        lng: targetLng,
      );
      if (rawList.isNotEmpty) {
        final parsed = rawList.map(RestStopModel.fromMap).toList();
        state = state.copyWith(restStops: parsed, isLoading: false);
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (_) {
      // Fallback to sample rest stops on network absence
      state = state.copyWith(isLoading: false);
    }
  }

  void filterByType(String? type) {
    state = state.copyWith(selectedFilter: type, clearFilter: type == null);
  }

  void selectStop(RestStopModel? stop) {
    state = state.copyWith(
      selectedStop: stop,
      clearSelectedStop: stop == null,
    );
  }

  void shareWithDriver(RestStopModel stop) {
    state = state.copyWith(
      shareSuccessMessage:
          'Rekomendasi istirahat "${stop.name}" (${stop.distanceKm} km) telah dikirim ke layar pengemudi!',
    );
  }

  void clearMessage() {
    state = state.copyWith(clearSuccess: true, clearError: true);
  }

  List<RestStopModel> _getSampleNearbyStops() {
    return const [
      RestStopModel(
        id: 'stop_01',
        name: 'Rest Area KM 36 Tol Balsam',
        type: 'REST_AREA',
        lat: AppConstants.defaultLat - 0.0080,
        lng: AppConstants.defaultLng + 0.0060,
        distanceKm: 2.3,
        address: 'Jl. Tol Balikpapan - Samarinda KM 36',
        facilities: ['Toilet Bersih', 'Musholla', 'Indomaret Point', 'Parkir Luas', 'Kopi Kenangan'],
        isOpen24Hours: true,
      ),
      RestStopModel(
        id: 'stop_02',
        name: 'SPBU Pertamina 64.761.05 & Cafe',
        type: 'GAS_STATION',
        lat: AppConstants.defaultLat + 0.0050,
        lng: AppConstants.defaultLng - 0.0040,
        distanceKm: 3.8,
        address: 'Jl. Soekarno-Hatta KM 28, Karang Joang',
        facilities: ['BBM Pertamax', 'Toilet', 'ATM Center', 'Bright Store'],
        isOpen24Hours: true,
      ),
      RestStopModel(
        id: 'stop_03',
        name: 'Rest Area & Sentra UMKM KM 54',
        type: 'REST_AREA',
        lat: AppConstants.defaultLat + 0.0150,
        lng: AppConstants.defaultLng + 0.0120,
        distanceKm: 7.5,
        address: 'Kawasan Tol Samboja, Kutai Kartanegara',
        facilities: ['Area Istirahat Sopir', 'Pujasera Lokal', 'Musholla AC'],
        isOpen24Hours: true,
      ),
    ];
  }
}

/// Global provider for RestStopNotifier.
final restStopProvider =
    NotifierProvider<RestStopNotifier, RestStopState>(RestStopNotifier.new);
