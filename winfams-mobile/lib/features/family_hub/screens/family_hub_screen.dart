import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../live_map/providers/live_map_provider.dart';
import '../providers/rest_stop_provider.dart';
import '../widgets/rest_stop_card.dart';
import 'rest_stop_map_screen.dart';

/// Screen providing Smart Rest-Stop recommendations when driver fatigue is detected.
class FamilyHubScreen extends ConsumerWidget {
  const FamilyHubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final restState = ref.watch(restStopProvider);
    final liveState = ref.watch(liveMapProvider);
    final notifier = ref.read(restStopProvider.notifier);
    final stops = restState.filteredStops;

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Smart Rest-Stop Finder'),
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (liveState.deviceStatus.isWarning || liveState.deviceStatus.isCritical)
              _buildFatigueRecommendationBanner(liveState.deviceStatus.state),
            _buildFilterRow(restState.selectedFilter, notifier),
            if (restState.shareSuccessMessage != null)
              _buildFeedbackBanner(context, ref, restState.shareSuccessMessage!),
            Expanded(
              child: RefreshIndicator(
                color: AppTheme.accentCyan,
                backgroundColor: AppTheme.surfaceDark,
                onRefresh: () => notifier.fetchNearbyRestStops(),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  itemCount: stops.length,
                  itemBuilder: (context, index) {
                    final item = stops[index];
                    return RestStopCard(
                      stop: item,
                      onShareWithDriver: () {
                        notifier.shareWithDriver(item);
                      },
                      onViewOnMap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => RestStopMapScreen(
                              stop: item,
                              vehicleLat: liveState.centerLat,
                              vehicleLng: liveState.centerLng,
                              onShareRecommendation: () => notifier.shareWithDriver(item),
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFatigueRecommendationBanner(String driverState) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 6),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.statusWarning.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.statusWarning, width: 1.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: AppTheme.statusWarning, size: 24),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'STATUS PENGEMUDI: $driverState',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.statusWarning,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Pengemudi terdeteksi mengantuk / menguap berulang. Bagikan rekomendasi tempat istirahat terdekat di bawah ini.',
                  style: TextStyle(fontSize: 12, color: Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackBanner(BuildContext context, WidgetRef ref, String msg) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 6, 16, 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppTheme.statusNormal.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.statusNormal),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle, color: AppTheme.statusNormal, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              msg,
              style: const TextStyle(fontSize: 12, color: Colors.white, fontWeight: FontWeight.w600),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 16, color: Colors.white70),
            onPressed: () => ref.read(restStopProvider.notifier).clearMessage(),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterRow(String? currentFilter, RestStopNotifier notifier) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Row(
        children: [
          _buildFilterChip('Semua Lokasi', currentFilter == null, () => notifier.filterByType(null)),
          const SizedBox(width: 8),
          _buildFilterChip(
            'Rest Area',
            currentFilter == 'REST_AREA',
            () => notifier.filterByType('REST_AREA'),
          ),
          const SizedBox(width: 8),
          _buildFilterChip(
            'SPBU',
            currentFilter == 'GAS_STATION',
            () => notifier.filterByType('GAS_STATION'),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, VoidCallback onTap) {
    return Semantics(
      button: true,
      label: 'Filter kategori $label',
      child: ChoiceChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => onTap(),
        selectedColor: AppTheme.accentCyan.withValues(alpha: 0.25),
        backgroundColor: AppTheme.surfaceDark,
        side: BorderSide(color: isSelected ? AppTheme.accentCyan : Colors.white24),
        labelStyle: TextStyle(
          color: isSelected ? AppTheme.accentCyan : Colors.white70,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
      ),
    );
  }
}
