import '../../../core/models/fatigue_incident.dart';

/// Immutable state holding historical fatigue incidents and active filters.
class IncidentHistoryState {
  final List<FatigueIncident> incidents;
  final bool isLoading;
  final String? selectedFilter;
  final FatigueIncident? selectedIncident;
  final String? errorMessage;

  const IncidentHistoryState({
    this.incidents = const [],
    this.isLoading = false,
    this.selectedFilter,
    this.selectedIncident,
    this.errorMessage,
  });

  List<FatigueIncident> get filteredIncidents {
    if (selectedFilter == null || selectedFilter!.isEmpty) {
      return incidents;
    }
    return incidents.where((inc) => inc.type == selectedFilter).toList();
  }

  int get criticalCount =>
      incidents.where((inc) => inc.type == 'CRITICAL_DROWSY').length;

  int get warningCount =>
      incidents.where((inc) => inc.type == 'WARNING_FATIGUE').length;

  IncidentHistoryState copyWith({
    List<FatigueIncident>? incidents,
    bool? isLoading,
    String? selectedFilter,
    FatigueIncident? selectedIncident,
    String? errorMessage,
    bool clearFilter = false,
    bool clearSelectedIncident = false,
    bool clearError = false,
  }) {
    return IncidentHistoryState(
      incidents: incidents ?? this.incidents,
      isLoading: isLoading ?? this.isLoading,
      selectedFilter: clearFilter ? null : (selectedFilter ?? this.selectedFilter),
      selectedIncident: clearSelectedIncident
          ? null
          : (selectedIncident ?? this.selectedIncident),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is IncidentHistoryState &&
        other.isLoading == isLoading &&
        other.selectedFilter == selectedFilter &&
        other.selectedIncident == selectedIncident &&
        other.errorMessage == errorMessage;
  }

  @override
  int get hashCode {
    return Object.hash(isLoading, selectedFilter, selectedIncident, errorMessage);
  }
}
