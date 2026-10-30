import 'rest_stop_model.dart';

/// Immutable state holding nearby rest stops, active filter, and sharing feedback.
class RestStopState {
  final List<RestStopModel> restStops;
  final bool isLoading;
  final String? selectedFilter;
  final RestStopModel? selectedStop;
  final String? shareSuccessMessage;
  final String? errorMessage;

  const RestStopState({
    this.restStops = const [],
    this.isLoading = false,
    this.selectedFilter,
    this.selectedStop,
    this.shareSuccessMessage,
    this.errorMessage,
  });

  List<RestStopModel> get filteredStops {
    if (selectedFilter == null || selectedFilter!.isEmpty) {
      return restStops;
    }
    return restStops.where((stop) => stop.type == selectedFilter).toList();
  }

  RestStopState copyWith({
    List<RestStopModel>? restStops,
    bool? isLoading,
    String? selectedFilter,
    RestStopModel? selectedStop,
    String? shareSuccessMessage,
    String? errorMessage,
    bool clearFilter = false,
    bool clearSelectedStop = false,
    bool clearSuccess = false,
    bool clearError = false,
  }) {
    return RestStopState(
      restStops: restStops ?? this.restStops,
      isLoading: isLoading ?? this.isLoading,
      selectedFilter: clearFilter ? null : (selectedFilter ?? this.selectedFilter),
      selectedStop: clearSelectedStop ? null : (selectedStop ?? this.selectedStop),
      shareSuccessMessage:
          clearSuccess ? null : (shareSuccessMessage ?? this.shareSuccessMessage),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is RestStopState &&
        other.isLoading == isLoading &&
        other.selectedFilter == selectedFilter &&
        other.selectedStop == selectedStop &&
        other.shareSuccessMessage == shareSuccessMessage &&
        other.errorMessage == errorMessage;
  }

  @override
  int get hashCode {
    return Object.hash(
      isLoading,
      selectedFilter,
      selectedStop,
      shareSuccessMessage,
      errorMessage,
    );
  }
}
