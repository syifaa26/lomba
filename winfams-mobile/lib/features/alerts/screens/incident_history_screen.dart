import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../models/incident_history_state.dart';
import '../providers/incident_history_provider.dart';
import '../widgets/incident_card.dart';
import 'incident_map_screen.dart';

/// Screen listing historical driver fatigue incidents with filter tabs and map navigation.
class IncidentHistoryScreen extends ConsumerWidget {
  const IncidentHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(incidentHistoryProvider);
    final notifier = ref.read(incidentHistoryProvider.notifier);
    final incidents = state.filteredIncidents;

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Riwayat Insiden & Perjalanan'),
      ),
      body: SafeArea(
        child: Column(
          children: [
            _buildSummaryBar(state),
            _buildFilterRow(state.selectedFilter, notifier),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () => notifier.fetchIncidents(),
                color: AppTheme.accentCyan,
                backgroundColor: AppTheme.surfaceDark,
                child: incidents.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        itemCount: incidents.length,
                        itemBuilder: (context, index) {
                          final item = incidents[index];
                          return IncidentCard(
                            incident: item,
                            onTapMap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => IncidentMapScreen(incident: item),
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

  Widget _buildSummaryBar(IncidentHistoryState state) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryItem('Total Catatan', '${state.incidents.length}', Colors.white),
          Container(width: 1, height: 28, color: Colors.white12),
          _buildSummaryItem('Microsleep', '${state.criticalCount}', AppTheme.statusCritical),
          Container(width: 1, height: 28, color: Colors.white12),
          _buildSummaryItem('Lelah/Menguap', '${state.warningCount}', AppTheme.statusWarning),
        ],
      ),
    );
  }

  Widget _buildSummaryItem(String label, String count, Color color) {
    return Column(
      children: [
        Text(count, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.white60)),
      ],
    );
  }

  Widget _buildFilterRow(String? currentFilter, IncidentHistoryNotifier notifier) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 6.0),
      child: Row(
        children: [
          _buildFilterChip('Semua', currentFilter == null, () => notifier.setFilter(null)),
          const SizedBox(width: 8),
          _buildFilterChip(
            'Microsleep',
            currentFilter == 'CRITICAL_DROWSY',
            () => notifier.setFilter('CRITICAL_DROWSY'),
            color: AppTheme.statusCritical,
          ),
          const SizedBox(width: 8),
          _buildFilterChip(
            'Menguap',
            currentFilter == 'WARNING_FATIGUE',
            () => notifier.setFilter('WARNING_FATIGUE'),
            color: AppTheme.statusWarning,
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, VoidCallback onTap, {Color? color}) {
    final chipColor = color ?? AppTheme.accentCyan;
    return Semantics(
      button: true,
      label: 'Filter kategori $label',
      child: ChoiceChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (_) => onTap(),
        selectedColor: chipColor.withValues(alpha: 0.25),
        backgroundColor: AppTheme.surfaceDark,
        side: BorderSide(color: isSelected ? chipColor : Colors.white24),
        labelStyle: TextStyle(
          color: isSelected ? chipColor : Colors.white70,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return ListView(
      children: const [
        SizedBox(height: 80),
        Icon(Icons.shield_outlined, size: 64, color: AppTheme.statusNormal),
        SizedBox(height: 16),
        Center(
          child: Text(
            'Tidak Ada Insiden Kantuk',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          ),
        ),
        SizedBox(height: 6),
        Center(
          child: Text(
            'Seluruh perjalanan pengemudi tercatat aman tanpa kendala.',
            style: TextStyle(fontSize: 13, color: Colors.white60),
          ),
        ),
      ],
    );
  }
}
