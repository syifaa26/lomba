import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../models/rest_stop_model.dart';

/// Card presenting a rest stop with distance, amenities, and instant share action.
class RestStopCard extends StatelessWidget {
  final RestStopModel stop;
  final VoidCallback? onShareWithDriver;
  final VoidCallback? onViewOnMap;

  const RestStopCard({
    super.key,
    required this.stop,
    this.onShareWithDriver,
    this.onViewOnMap,
  });

  @override
  Widget build(BuildContext context) {
    final isRestArea = stop.isRestArea;
    final badgeColor = isRestArea ? AppTheme.accentCyan : AppTheme.statusNormal;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Colors.white12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    stop.name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: badgeColor.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: badgeColor, width: 1),
                  ),
                  child: Text(
                    isRestArea ? 'REST AREA' : 'SPBU',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: badgeColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.near_me, size: 14, color: AppTheme.accentCyan),
                const SizedBox(width: 4),
                Text(
                  '${stop.distanceKm} km dari posisi mobil saat ini',
                  style: const TextStyle(fontSize: 12, color: AppTheme.accentCyan, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: stop.facilities.map((fac) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundDark,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Text(
                    fac,
                    style: const TextStyle(fontSize: 10, color: Colors.white70),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: Semantics(
                    button: true,
                    label: 'Kirim rekomendasi istirahat ${stop.name} ke pengemudi',
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(minHeight: 48),
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.statusWarning,
                          foregroundColor: AppTheme.backgroundDark,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        icon: const Icon(Icons.send_rounded, size: 16),
                        label: const Text(
                          'Kirim ke Pengemudi',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                        onPressed: onShareWithDriver,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Semantics(
                  button: true,
                  label: 'Lihat titik lokasi ${stop.name} di peta',
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(minHeight: 48),
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.accentCyan,
                        side: const BorderSide(color: AppTheme.accentCyan),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      icon: const Icon(Icons.map_outlined, size: 16),
                      label: const Text('Peta', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      onPressed: onViewOnMap,
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
}
