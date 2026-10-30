import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/core/models/device_status.dart';
import 'package:winfams_mobile/core/models/fatigue_incident.dart';
import 'package:winfams_mobile/core/models/location_data.dart';
import 'package:winfams_mobile/core/providers/device_provider.dart';
import 'package:winfams_mobile/main.dart';

void main() {
  group('MOB-01: Immutable Data Models Test', () {
    test('LocationData serializes and deserializes properly', () {
      const loc = LocationData(
        lat: -1.265386,
        lng: 116.831200,
        speedKmh: 64.5,
        heading: 180.0,
      );

      final map = loc.toMap();
      final parsed = LocationData.fromMap(map);

      expect(parsed, equals(loc));
      expect(parsed.hasCoordinates, isTrue);
      expect(parsed.speedKmh, 64.5);
    });

    test('LocationData handles null coordinates gracefully', () {
      const loc = LocationData();
      expect(loc.hasCoordinates, isFalse);
      expect(loc.lat, isNull);
      expect(loc.lng, isNull);
    });

    test('DeviceStatus strictly matches PRD JSON contract', () {
      const jsonString = '''
      {
        "device_id": "pi4_car_01",
        "driver_uid": "user_123",
        "is_online": true,
        "state": "CRITICAL_DROWSY",
        "drowsy_confidence": 0.88,
        "yawn_confidence": 0.05,
        "location": {
          "lat": -1.265386,
          "lng": 116.831200,
          "speed_kmh": 64.5,
          "heading": 180.0
        },
        "last_updated": 1730334600
      }
      ''';

      final status = DeviceStatus.fromJson(jsonString);

      expect(status.deviceId, 'pi4_car_01');
      expect(status.driverUid, 'user_123');
      expect(status.isOnline, isTrue);
      expect(status.isCritical, isTrue);
      expect(status.drowsyConfidence, 0.88);
      expect(status.location.lat, -1.265386);
      expect(status.location.lng, 116.831200);
      expect(status.lastUpdated, 1730334600);
    });

    test('FatigueIncident strictly matches PRD JSON contract', () {
      const jsonString = '''
      {
        "incident_id": "inc_987654",
        "device_id": "pi4_car_01",
        "driver_uid": "user_123",
        "family_group_id": "fam_001",
        "type": "CRITICAL_DROWSY",
        "confidence_score": 0.88,
        "duration_seconds": 2.1,
        "location": {
          "lat": -1.265386,
          "lng": 116.831200,
          "speed_kmh": 72.0,
          "heading": 180.0
        },
        "timestamp": 1730334605,
        "resolved": false
      }
      ''';

      final incident = FatigueIncident.fromJson(jsonString);

      expect(incident.incidentId, 'inc_987654');
      expect(incident.familyGroupId, 'fam_001');
      expect(incident.isCritical, isTrue);
      expect(incident.confidenceScore, 0.88);
      expect(incident.durationSeconds, 2.1);
      expect(incident.resolved, isFalse);
    });
  });

  group('MOB-01: Riverpod Provider & UI Tests', () {
    test('DeviceStatusNotifier updates state properly', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final initial = container.read(deviceStatusProvider);
      expect(initial.deviceId, 'pi4_car_01');
      expect(initial.state, 'NORMAL');

      container.read(deviceStatusProvider.notifier).updateState(
            'WARNING_FATIGUE',
            yawnScore: 0.75,
          );

      final updated = container.read(deviceStatusProvider);
      expect(updated.state, 'WARNING_FATIGUE');
      expect(updated.yawnConfidence, 0.75);
    });

    testWidgets('DashboardShellScreen renders with status and metrics',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: WinFamsApp(home: DashboardShellScreen()),
        ),
      );

      expect(find.text('WinFams'), findsOneWidget);
      expect(find.text('Status Pengemudi'), findsOneWidget);
      expect(find.text('Eye Closure'), findsOneWidget);
      expect(find.text('Yawn Score'), findsOneWidget);
      expect(find.text('ID Kendaraan: pi4_car_01'), findsOneWidget);
    });
  });
}

