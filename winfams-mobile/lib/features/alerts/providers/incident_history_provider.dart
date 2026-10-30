import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/models/fatigue_incident.dart';
import '../../../core/models/location_data.dart';
import '../../../core/network/api_client.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/incident_history_state.dart';

/// Provider for IncidentHistoryNotifier managing fatigue incident records.
class IncidentHistoryNotifier extends Notifier<IncidentHistoryState> {
  @override
  IncidentHistoryState build() {
    final authState = ref.watch(authProvider);
    final initialList = _getSampleTripIncidents();

    // Trigger async fetch if family is available
    final familyId = authState.currentFamily?.id;
    if (familyId != null) {
      Future.microtask(() => fetchIncidents(familyId));
    }

    return IncidentHistoryState(incidents: initialList);
  }

  ApiClient get _apiClient => ref.read(apiClientProvider);

  Future<void> fetchIncidents([int? familyId]) async {
    final fid = familyId ?? ref.read(authProvider).currentFamily?.id;
    if (fid == null) return;

    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final items = await _apiClient.getFamilyIncidents(fid);
      if (items.isNotEmpty) {
        state = state.copyWith(incidents: items, isLoading: false);
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (_) {
      // Keep existing sample incidents on network error
      state = state.copyWith(isLoading: false);
    }
  }

  void setFilter(String? filter) {
    state = state.copyWith(selectedFilter: filter, clearFilter: filter == null);
  }

  void selectIncident(FatigueIncident? incident) {
    state = state.copyWith(
      selectedIncident: incident,
      clearSelectedIncident: incident == null,
    );
  }

  void addIncident(FatigueIncident incident) {
    final updated = List<FatigueIncident>.from(state.incidents)..insert(0, incident);
    state = state.copyWith(incidents: updated);
  }

  List<FatigueIncident> _getSampleTripIncidents() {
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    return [
      FatigueIncident(
        incidentId: 'inc_001',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.94,
        durationSeconds: 2.2,
        location: const LocationData(
          lat: AppConstants.defaultLat - 0.0050,
          lng: AppConstants.defaultLng + 0.0035,
          speedKmh: 74.0,
        ),
        timestamp: now - 900, // 15 mins ago
        resolved: true,
      ),
      FatigueIncident(
        incidentId: 'inc_002',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'WARNING_FATIGUE',
        confidenceScore: 0.82,
        durationSeconds: 3.1,
        location: const LocationData(
          lat: AppConstants.defaultLat + 0.0040,
          lng: AppConstants.defaultLng - 0.0020,
          speedKmh: 58.0,
        ),
        timestamp: now - 3600, // 1 hr ago
        resolved: true,
      ),
      FatigueIncident(
        incidentId: 'inc_003',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.89,
        durationSeconds: 1.8,
        location: const LocationData(
          lat: AppConstants.defaultLat - 0.0120,
          lng: AppConstants.defaultLng + 0.0080,
          speedKmh: 81.0,
        ),
        timestamp: now - 86400, // Yesterday
        resolved: true,
      ),
    ];
  }
}

/// Global provider for IncidentHistoryNotifier.
final incidentHistoryProvider =
    NotifierProvider<IncidentHistoryNotifier, IncidentHistoryState>(
  IncidentHistoryNotifier.new,
);
