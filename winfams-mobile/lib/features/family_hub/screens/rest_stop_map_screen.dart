import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../models/rest_stop_model.dart';

/// Screen displaying the route connection between family vehicle and selected rest stop.
class RestStopMapScreen extends StatefulWidget {
  final RestStopModel stop;
  final double vehicleLat;
  final double vehicleLng;
  final VoidCallback? onShareRecommendation;

  const RestStopMapScreen({
    super.key,
    required this.stop,
    this.vehicleLat = AppConstants.defaultLat,
    this.vehicleLng = AppConstants.defaultLng,
    this.onShareRecommendation,
  });

  @override
  State<RestStopMapScreen> createState() => _RestStopMapScreenState();
}

class _RestStopMapScreenState extends State<RestStopMapScreen> {
  final MapController _mapController = MapController();

  @override
  Widget build(BuildContext context) {
    final stop = widget.stop;

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: Text(stop.name),
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(stop.lat, stop.lng),
              initialZoom: 14.5,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'id.winfams.mobile',
              ),
              MarkerLayer(
                markers: [
                  // Vehicle Marker
                  Marker(
                    point: LatLng(widget.vehicleLat, widget.vehicleLng),
                    width: 70,
                    height: 70,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Icon(Icons.directions_car, color: AppTheme.accentCyan, size: 30),
                        Text('Mobil', style: TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  // Rest Stop Marker
                  Marker(
                    point: LatLng(stop.lat, stop.lng),
                    width: 80,
                    height: 80,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          stop.isRestArea ? Icons.local_cafe : Icons.local_gas_station,
                          color: AppTheme.statusWarning,
                          size: 32,
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.backgroundDark,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            '${stop.distanceKm} km',
                            style: const TextStyle(fontSize: 10, color: AppTheme.statusWarning, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
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
                side: const BorderSide(color: AppTheme.statusWarning, width: 1.5),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      stop.name,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Jarak: ${stop.distanceKm} km | Alamat: ${stop.address}',
                      style: const TextStyle(fontSize: 12, color: Colors.white70),
                    ),
                    const SizedBox(height: 14),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.statusWarning,
                        foregroundColor: AppTheme.backgroundDark,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      icon: const Icon(Icons.send_rounded, size: 18),
                      label: const Text('Kirim Rekomendasi ke Mobil', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () {
                        widget.onShareRecommendation?.call();
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            backgroundColor: AppTheme.surfaceDark,
                            content: Text('Rute ke "${stop.name}" dikirim ke dashboard mobil!'),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
