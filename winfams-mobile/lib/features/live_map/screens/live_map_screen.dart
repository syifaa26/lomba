import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../../../core/theme/app_theme.dart';
import '../../alerts/screens/emergency_alert_screen.dart';
import '../../alerts/screens/incident_history_screen.dart';
import '../../auth/providers/auth_provider.dart';
import '../../family_hub/screens/family_hub_screen.dart';
import '../providers/live_map_provider.dart';
import '../widgets/driver_status_bottom_sheet.dart';
import '../widgets/family_members_horizontal_bar.dart';
import '../widgets/vehicle_marker_layer.dart';

/// Screen providing real-time map visualization of moving family vehicles via WebSocket.
class LiveMapScreen extends ConsumerStatefulWidget {
  const LiveMapScreen({super.key});

  @override
  ConsumerState<LiveMapScreen> createState() => _LiveMapScreenState();
}

class _LiveMapScreenState extends ConsumerState<LiveMapScreen> {
  final MapController _mapController = MapController();

  @override
  Widget build(BuildContext context) {
    final liveState = ref.watch(liveMapProvider);
    final authState = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.shield_outlined, color: AppTheme.accentCyan),
            const SizedBox(width: 8),
            Text(
              authState.currentFamily?.name ?? 'Live Family Map',
              style: const TextStyle(fontSize: 18),
            ),
          ],
        ),
        actions: [
          _buildConnectionBadge(liveState.isConnected),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.white),
            onSelected: (val) {
              if (val == 'simulate') {
                ref.read(liveMapProvider.notifier).simulateDrivingStep(
                      deltaLat: 0.0015,
                      deltaLng: 0.0010,
                      speedKmh: 68.0,
                      stateName: 'DRIVING',
                    );
                _mapController.move(
                  LatLng(liveState.centerLat + 0.0015, liveState.centerLng + 0.0010),
                  liveState.zoom,
                );
              } else if (val == 'simulate_warning') {
                ref.read(liveMapProvider.notifier).simulateDrivingStep(
                      deltaLat: 0.0005,
                      deltaLng: 0.0005,
                      speedKmh: 55.0,
                      stateName: 'WARNING_FATIGUE',
                      yawn: 0.85,
                    );
              } else if (val == 'history') {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const IncidentHistoryScreen()),
                );
              } else if (val == 'rest_stops') {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const FamilyHubScreen()),
                );
              } else if (val == 'logout') {
                ref.read(authProvider.notifier).logout();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'rest_stops',
                child: Text('Smart Rest-Stop Finder'),
              ),
              const PopupMenuItem(
                value: 'history',
                child: Text('Riwayat Insiden & Titik Peta'),
              ),
              const PopupMenuItem(
                value: 'simulate',
                child: Text('Simulasi Gerak Mobil'),
              ),
              const PopupMenuItem(
                value: 'simulate_warning',
                child: Text('Simulasi Alert Kantuk'),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'logout',
                child: Text('Keluar Akun'),
              ),
            ],
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(liveState.centerLat, liveState.centerLng),
              initialZoom: liveState.zoom,
              interactionOptions: const InteractionOptions(
                flags: InteractiveFlag.all,
              ),
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'id.winfams.mobile',
              ),
              VehicleMarkerLayer(state: liveState),
            ],
          ),
          Positioned(
            top: 12,
            left: 0,
            right: 0,
            child: FamilyMembersHorizontalBar(
              members: liveState.familyMembers,
              selectedMemberId: liveState.selectedMemberId,
            ),
          ),
          if (liveState.lastAlertMessage.isNotEmpty)
            Positioned(
              top: 70,
              left: 16,
              right: 16,
              child: Semantics(
                liveRegion: true,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppTheme.statusCritical.withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: const [
                      BoxShadow(color: Colors.black45, blurRadius: 8),
                    ],
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.white),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          liveState.lastAlertMessage,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          Positioned(
            right: 16,
            bottom: 220,
            child: FloatingActionButton.small(
              heroTag: 'center_vehicle_fab',
              backgroundColor: AppTheme.surfaceDark,
              foregroundColor: AppTheme.accentCyan,
              tooltip: 'Pusatkan ke Mobil',
              onPressed: () {
                ref.read(liveMapProvider.notifier).centerOnVehicle();
                _mapController.move(
                  LatLng(liveState.centerLat, liveState.centerLng),
                  16.0,
                );
              },
              child: const Icon(Icons.my_location),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: DriverStatusBottomSheet(
              state: liveState,
              onCallDriver: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const EmergencyAlertScreen()),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectionBadge(bool isConnected) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isConnected
            ? AppTheme.statusNormal.withValues(alpha: 0.2)
            : Colors.grey.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isConnected ? AppTheme.statusNormal : Colors.grey,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircleAvatar(
            radius: 3.5,
            backgroundColor: isConnected ? AppTheme.statusNormal : Colors.grey,
          ),
          const SizedBox(width: 5),
          Text(
            isConnected ? 'LIVE WS' : 'OFFLINE',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: isConnected ? AppTheme.statusNormal : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}
