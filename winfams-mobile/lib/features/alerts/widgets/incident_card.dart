import 'package:flutter/material.dart';
import '../../../core/models/fatigue_incident.dart';
import '../../../core/theme/app_theme.dart';

/// Card item presenting a historical fatigue incident with metrics and map navigation.
class IncidentCard extends StatelessWidget {
  final FatigueIncident incident;
  final VoidCallback? onTapMap;

  const IncidentCard({
    super.key,
    required this.incident,
    this.onTapMap,
  });

  @override
  Widget build(BuildContext context) {
    final isCritical = incident.isCritical;
    final statusColor = isCritical ? AppTheme.statusCritical : AppTheme.statusWarning;
    final badgeLabel = isCritical ? 'MICROSLEEP' : 'MENGUAP / LELAH';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: isCritical
              ? AppTheme.statusCritical.withValues(alpha: 0.6)
              : Colors.white12,
          width: isCritical ? 1.5 : 1.0,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: statusColor, width: 1.2),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        isCritical ? Icons.warning_rounded : Icons.face,
                        size: 14,
                        color: statusColor,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        badgeLabel,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: statusColor,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  _formatTimestamp(incident.timestamp),
                  style: const TextStyle(fontSize: 12, color: Colors.white60),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildMetricCol('Durasi', '${incident.durationSeconds.toStringAsFixed(1)}s'),
                _buildMetricCol('AI Yakin', '${(incident.confidenceScore * 100).toInt()}%'),
                _buildMetricCol('Kecepatan', '${incident.location.speedKmh.toInt()} km/h'),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Koordinat: ${incident.location.lat?.toStringAsFixed(4) ?? "-"}, ${incident.location.lng?.toStringAsFixed(4) ?? "-"}',
                  style: const TextStyle(fontSize: 11, color: Colors.white38),
                ),
                Semantics(
                  button: true,
                  label: 'Lihat titik lokasi insiden di peta',
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(minHeight: 48, minWidth: 48),
                    child: TextButton.icon(
                      style: TextButton.styleFrom(
                        foregroundColor: AppTheme.accentCyan,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      ),
                      icon: const Icon(Icons.place_outlined, size: 18),
                      label: const Text('Peta Titik', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                      onPressed: onTapMap,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCol(String title, String val) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 11, color: Colors.white60)),
          const SizedBox(height: 2),
          Text(val, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white)),
        ],
      ),
    );
  }

  String _formatTimestamp(int timestamp) {
    if (timestamp <= 0) return 'Baru saja';
    final dt = DateTime.fromMillisecondsSinceEpoch(timestamp * 1000);
    final hours = dt.hour.toString().padLeft(2, '0');
    final mins = dt.minute.toString().padLeft(2, '0');
    return '$hours:$mins WIB';
  }
}
