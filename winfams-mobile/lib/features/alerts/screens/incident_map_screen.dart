import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/models/fatigue_incident.dart';
import '../../../core/theme/app_theme.dart';

/// Screen displaying the exact geographic point where a fatigue incident was detected.
class IncidentMapScreen extends StatefulWidget {
  final FatigueIncident incident;

  const IncidentMapScreen({super.key, required this.incident});

  @override
  State<IncidentMapScreen> createState() => _IncidentMapScreenState();
}

class _IncidentMapScreenState extends State<IncidentMapScreen> {
  final MapController _mapController = MapController();

  @override
  Widget build(BuildContext context) {
    final loc = widget.incident.location;
    final lat = loc.lat ?? AppConstants.defaultLat;
    final lng = loc.lng ?? AppConstants.defaultLng;
    final isCritical = widget.incident.isCritical;
    final statusColor = isCritical ? AppTheme.statusCritical : AppTheme.statusWarning;

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: Text(isCritical ? 'Titik Insiden Microsleep' : 'Titik Peringatan Kelelahan'),
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(lat, lng),
              initialZoom: 16.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'id.winfams.mobile',
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: LatLng(lat, lng),
                    width: 84,
                    height: 84,
                    child: Semantics(
                      label: 'Lokasi kejadian ${widget.incident.type}',
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.backgroundDark,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: statusColor),
                            ),
                            child: Text(
                              '${loc.speedKmh.toInt()} km/h',
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: statusColor),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Icon(
                            Icons.location_on,
                            size: 40,
                            color: statusColor,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          Positioned(
            left: 16,
            right: 16,
            bottom: 24,
            child: Card(
              color: AppTheme.surfaceDark,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: statusColor, width: 1.5),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          isCritical ? 'Peringatan Bahaya Microsleep' : 'Peringatan Lelah Pengemudi',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: statusColor),
                        ),
                        Text(
                          '${(widget.incident.confidenceScore * 100).toInt()}% Akurat',
                          style: const TextStyle(fontSize: 12, color: Colors.white70),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Durasi Terpejam: ${widget.incident.durationSeconds.toStringAsFixed(1)} detik | Kecepatan: ${loc.speedKmh.toInt()} km/jam',
                      style: const TextStyle(fontSize: 13, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Koordinat GPS: ${lat.toStringAsFixed(5)}, ${lng.toStringAsFixed(5)}',
                      style: const TextStyle(fontSize: 11, color: Colors.white60),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            right: 16,
            bottom: 140,
            child: FloatingActionButton.small(
              heroTag: 'recenter_incident_fab',
              backgroundColor: AppTheme.surfaceDark,
              foregroundColor: AppTheme.accentCyan,
              tooltip: 'Pusatkan ke Titik Kejadian',
              onPressed: () {
                _mapController.move(LatLng(lat, lng), 16.0);
              },
              child: const Icon(Icons.my_location),
            ),
          ),
        ],
      ),
    );
  }
}
