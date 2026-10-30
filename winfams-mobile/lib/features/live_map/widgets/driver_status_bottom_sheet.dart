import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/live_map_state.dart';

/// Bottom persistent card displaying live driver metrics, status badge, and emergency actions.
class DriverStatusBottomSheet extends StatelessWidget {
  final LiveMapState state;
  final VoidCallback? onCallDriver;

  const DriverStatusBottomSheet({
    super.key,
    required this.state,
    this.onCallDriver,
  });

  @override
  Widget build(BuildContext context) {
    final status = state.deviceStatus;
    final statusColor = AppTheme.getStatusColor(status.state);

    return Card(
      margin: EdgeInsets.zero,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        state.vehicleName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Pengemudi: ${state.driverName}',
                        style: const TextStyle(fontSize: 13, color: Colors.white70),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: statusColor, width: 1.5),
                  ),
                  child: Text(
                    status.state,
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                _buildMetric(
                  label: 'Kecepatan',
                  value: '${status.location.speedKmh.toStringAsFixed(0)} km/h',
                  icon: Icons.speed,
                  color: AppTheme.accentCyan,
                ),
                const SizedBox(width: 8),
                _buildMetric(
                  label: 'Eye Closure',
                  value: '${(status.drowsyConfidence * 100).toInt()}%',
                  icon: Icons.remove_red_eye_outlined,
                  color: status.drowsyConfidence > 0.55
                      ? AppTheme.statusCritical
                      : AppTheme.accentCyan,
                ),
                const SizedBox(width: 8),
                _buildMetric(
                  label: 'Yawn Score',
                  value: '${(status.yawnConfidence * 100).toInt()}%',
                  icon: Icons.face_outlined,
                  color: status.yawnConfidence > 0.60
                      ? AppTheme.statusWarning
                      : AppTheme.statusNormal,
                ),
              ],
            ),
            if (status.isCritical || status.isWarning) ...[
              const SizedBox(height: 14),
              Semantics(
                button: true,
                label: 'Hubungi pengemudi sekarang',
                child: ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 48),
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: status.isCritical
                          ? AppTheme.statusCritical
                          : AppTheme.statusWarning,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    icon: const Icon(Icons.phone_in_talk, size: 20),
                    label: Text(
                      status.isCritical
                          ? 'HUBUNGI PENGEMUDI (DARURAT)'
                          : 'Peringatkan Pengemudi Istirahat',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    onPressed: onCallDriver ?? () {},
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMetric({
    required String label,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: AppTheme.backgroundDark,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white12),
        ),
        child: Column(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(fontSize: 10, color: Colors.white60),
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
