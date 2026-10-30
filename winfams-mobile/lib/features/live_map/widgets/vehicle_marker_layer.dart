import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../core/theme/app_theme.dart';
import '../models/live_map_state.dart';

/// Renders a real-time vehicle pin on the OpenStreetMap with status aura.
class VehicleMarkerLayer extends StatelessWidget {
  final LiveMapState state;

  const VehicleMarkerLayer({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final status = state.deviceStatus;
    final lat = status.location.lat ?? state.centerLat;
    final lng = status.location.lng ?? state.centerLng;
    final statusColor = AppTheme.getStatusColor(status.state);

    return MarkerLayer(
      markers: [
        Marker(
          point: LatLng(lat, lng),
          width: 90,
          height: 90,
          child: Semantics(
            label: 'Kendaraan ${state.vehicleName}, Status ${status.state}, Kecepatan ${status.location.speedKmh.toInt()} km per jam',
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundDark.withValues(alpha: 0.85),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor, width: 1),
                  ),
                  child: Text(
                    '${status.location.speedKmh.toInt()} km/h',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
                const SizedBox(height: 2),
                Stack(
                  alignment: Alignment.center,
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: statusColor.withValues(alpha: 0.25),
                        boxShadow: [
                          BoxShadow(
                            color: statusColor.withValues(alpha: 0.5),
                            blurRadius: 10,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                    ),
                    Container(
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppTheme.backgroundDark,
                        border: Border.all(color: statusColor, width: 2),
                      ),
                      child: const Icon(
                        Icons.directions_car,
                        size: 20,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
