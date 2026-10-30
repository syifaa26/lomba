import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/core/models/device_status.dart';
import 'package:winfams_mobile/core/models/location_data.dart';
import 'package:winfams_mobile/features/live_map/models/live_map_state.dart';
import 'package:winfams_mobile/features/live_map/providers/live_map_provider.dart';
import 'package:winfams_mobile/features/live_map/screens/live_map_screen.dart';
import 'package:winfams_mobile/features/live_map/services/live_map_websocket_service.dart';
import 'package:winfams_mobile/features/live_map/widgets/driver_status_bottom_sheet.dart';
import 'package:winfams_mobile/features/live_map/widgets/vehicle_marker_layer.dart';

void main() {
  group('MOB-03: LiveMap State & WebSocket Service', () {
    test('LiveMapState default values and copyWith', () {
      const state = LiveMapState(
        vehicleName: 'Mobil Keluarga',
        driverName: 'Ayah',
      );

      expect(state.vehicleName, 'Mobil Keluarga');
      expect(state.driverName, 'Ayah');
      expect(state.isConnected, isFalse);

      final updated = state.copyWith(
        isConnected: true,
        centerLat: -1.2500,
        centerLng: 116.8500,
      );

      expect(updated.isConnected, isTrue);
      expect(updated.centerLat, -1.2500);
      expect(updated.centerLng, 116.8500);
    });

    test('LiveMapWebSocketService stream emits incoming data', () async {
      final wsService = LiveMapWebSocketService();
      addTearDown(wsService.dispose);

      final emittedFuture = wsService.stream.first;

      wsService.pushSimulatedTelemetry(
        deviceUid: 'pi4_car_01',
        state: 'DRIVING',
        lat: -1.2650,
        lng: 116.8300,
        speedKmh: 62.0,
      );

      final emitted = await emittedFuture;
      expect(emitted['device_uid'], 'pi4_car_01');
      expect(emitted['state'], 'DRIVING');

      final loc = emitted['location'] as Map<String, Object?>;
      expect(loc['speed_kmh'], 62.0);
    });

    test('LiveMapNotifier updates state on telemetry broadcast', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final wsService = container.read(liveMapWebSocketServiceProvider);
      // Wait for notifier build
      final initial = container.read(liveMapProvider);
      expect(initial.deviceStatus.deviceId, 'pi4_car_01');

      // Push simulated critical telemetry
      wsService.pushSimulatedTelemetry(
        deviceUid: 'pi4_car_01',
        state: 'CRITICAL_DROWSY',
        lat: -1.2700,
        lng: 116.8400,
        speedKmh: 75.0,
        drowsyScore: 0.92,
      );

      // Allow stream to pump through microtasks
      await Future<void>.delayed(const Duration(milliseconds: 20));

      final updated = container.read(liveMapProvider);
      expect(updated.deviceStatus.state, 'CRITICAL_DROWSY');
      expect(updated.isCritical, isTrue);
      expect(updated.centerLat, -1.2700);
      expect(updated.centerLng, 116.8400);
      expect(updated.deviceStatus.location.speedKmh, 75.0);
      expect(updated.lastAlertMessage, contains('PERINGATAN DARURAT'));
    });
  });

  group('MOB-03: UI Components Verification', () {
    testWidgets('DriverStatusBottomSheet displays telemetry and metrics',
        (tester) async {
      const state = LiveMapState(
        vehicleName: 'Innova Hitam - B 1234 XYZ',
        driverName: 'Budi Santoso',
        deviceStatus: DeviceStatus(
          deviceId: 'pi4_car_01',
          driverUid: 'user_1',
          state: 'DRIVING',
          isOnline: true,
          drowsyConfidence: 0.15,
          yawnConfidence: 0.10,
          location: LocationData(
            lat: -1.2653,
            lng: 116.8312,
            speedKmh: 64.0,
          ),
        ),
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: DriverStatusBottomSheet(state: state),
          ),
        ),
      );

      expect(find.text('Innova Hitam - B 1234 XYZ'), findsOneWidget);
      expect(find.text('Pengemudi: Budi Santoso'), findsOneWidget);
      expect(find.text('DRIVING'), findsOneWidget);
      expect(find.text('64 km/h'), findsOneWidget);
      expect(find.text('15%'), findsOneWidget); // Eye closure
      expect(find.text('10%'), findsOneWidget); // Yawn score
    });

    testWidgets('DriverStatusBottomSheet displays emergency button on critical',
        (tester) async {
      bool callTapped = false;
      const criticalState = LiveMapState(
        deviceStatus: DeviceStatus(
          deviceId: 'pi4_car_01',
          driverUid: 'user_1',
          state: 'CRITICAL_DROWSY',
          isOnline: true,
          drowsyConfidence: 0.90,
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DriverStatusBottomSheet(
              state: criticalState,
              onCallDriver: () {
                callTapped = true;
              },
            ),
          ),
        ),
      );

      expect(find.text('CRITICAL_DROWSY'), findsOneWidget);
      expect(find.text('HUBUNGI PENGEMUDI (DARURAT)'), findsOneWidget);

      await tester.tap(find.text('HUBUNGI PENGEMUDI (DARURAT)'));
      await tester.pump();
      expect(callTapped, isTrue);
    });

    testWidgets('LiveMapScreen renders app bar, connection status, and bottom sheet',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LiveMapScreen(),
          ),
        ),
      );

      expect(find.byType(LiveMapScreen), findsOneWidget);
      expect(find.byType(DriverStatusBottomSheet), findsOneWidget);
      expect(find.byType(VehicleMarkerLayer), findsOneWidget);
    });
  });
}
