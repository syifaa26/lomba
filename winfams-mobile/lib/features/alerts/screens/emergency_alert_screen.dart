import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/models/fatigue_incident.dart';
import '../../../core/theme/app_theme.dart';
import '../models/alert_state.dart';
import '../providers/alert_provider.dart';
import '../widgets/pulsing_alert_beacon.dart';

/// Fullscreen high-priority emergency alert screen triggered on CRITICAL_DROWSY detection.
class EmergencyAlertScreen extends ConsumerWidget {
  final VoidCallback? onNavigateToMap;

  const EmergencyAlertScreen({super.key, this.onNavigateToMap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alertState = ref.watch(alertProvider);
    final incident = alertState.activeIncident;

    final durationText = incident != null && incident.durationSeconds > 0
        ? '${incident.durationSeconds.toStringAsFixed(1)} Detik'
        : '2.4 Detik';
    final confidenceText = incident != null && incident.confidenceScore > 0
        ? '${(incident.confidenceScore * 100).toInt()}%'
        : '92%';
    final speedText = incident != null && incident.location.speedKmh > 0
        ? '${incident.location.speedKmh.toInt()} km/h'
        : '72 km/h';

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 12),
              PulsingAlertBeacon(isMuted: alertState.isMuted),
              const SizedBox(height: 20),
              Semantics(
                header: true,
                child: Column(
                  children: const [
                    Text(
                      'BAHAYA: MICROSLEEP!',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.statusCritical,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Pengemudi terpejam saat kendaraan sedang melaju kencang.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 13, color: Colors.white70),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              _buildStatsCard(alertState, durationText, confidenceText, speedText),
              const SizedBox(height: 20),
              _buildCallButton(context, alertState),
              const SizedBox(height: 12),
              _buildMapButton(context),
              const SizedBox(height: 12),
              _buildActionRow(context, ref, alertState),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatsCard(AlertState state, String dur, String conf, String spd) {
    return Card(
      color: AppTheme.surfaceDark,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppTheme.statusCritical, width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                const CircleAvatar(
                  radius: 20,
                  backgroundColor: AppTheme.cardDark,
                  child: Icon(Icons.person, color: Colors.white),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        state.driverName,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      Text(
                        'Kendaraan: ${state.vehicleName}',
                        style: const TextStyle(fontSize: 12, color: Colors.white70),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 20, color: Colors.white12),
            Row(
              children: [
                _buildCell('Durasi Mata', dur, AppTheme.statusCritical),
                _buildCell('Skor Yakin AI', conf, AppTheme.statusWarning),
                _buildCell('Kecepatan', spd, AppTheme.accentCyan),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCell(String label, String value, Color color) {
    return Expanded(
      child: Column(
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Colors.white60)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Widget _buildCallButton(BuildContext context, AlertState state) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 52),
      child: ElevatedButton.icon(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.statusCritical,
          foregroundColor: Colors.white,
          elevation: 4,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        icon: const Icon(Icons.phone_in_talk, size: 24),
        label: Text(
          'HUBUNGI PENGEMUDI (${state.driverPhoneNumber})',
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
        ),
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: AppTheme.surfaceDark,
              content: Text('Menghubungi telepon ${state.driverPhoneNumber}...'),
            ),
          );
        },
      ),
    );
  }

  Widget _buildMapButton(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 48),
      child: ElevatedButton.icon(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.surfaceDark,
          foregroundColor: AppTheme.accentCyan,
          side: const BorderSide(color: AppTheme.accentCyan, width: 1.5),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        icon: const Icon(Icons.map_outlined, size: 22),
        label: const Text('Pantau Lokasi Langsung di Peta', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
        onPressed: () {
          if (onNavigateToMap != null) {
            onNavigateToMap!();
          } else {
            Navigator.of(context).maybePop();
          }
        },
      ),
    );
  }

  Widget _buildActionRow(BuildContext context, WidgetRef ref, AlertState alertState) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white70,
              side: const BorderSide(color: Colors.white24),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            icon: Icon(alertState.isMuted ? Icons.volume_up_outlined : Icons.volume_off_outlined, size: 18),
            label: Text(alertState.isMuted ? 'Bunyikan Alarm' : 'Matikan Suara', style: const TextStyle(fontSize: 12)),
            onPressed: () {
              if (alertState.isMuted) {
                ref.read(alertProvider.notifier).triggerEmergencyAlert(
                      alertState.activeIncident ??
                          const FatigueIncident(
                            incidentId: 'manual',
                            deviceId: 'pi4_car_01',
                            driverUid: 'user_1',
                            type: 'CRITICAL_DROWSY',
                          ),
                    );
              } else {
                ref.read(alertProvider.notifier).silenceAlarm();
              }
            },
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: AppTheme.statusNormal,
              side: const BorderSide(color: AppTheme.statusNormal),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            icon: const Icon(Icons.check_circle_outline, size: 18),
            label: const Text('Tandai Aman', style: TextStyle(fontSize: 12)),
            onPressed: () {
              ref.read(alertProvider.notifier).resolveActiveIncident();
              Navigator.of(context).maybePop();
            },
          ),
        ),
      ],
    );
  }
}
