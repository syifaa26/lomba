import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/core/models/fatigue_incident.dart';
import 'package:winfams_mobile/core/models/location_data.dart';
import 'package:winfams_mobile/core/network/api_client.dart';
import 'package:winfams_mobile/features/alerts/models/alert_state.dart';
import 'package:winfams_mobile/features/alerts/providers/alert_provider.dart';
import 'package:winfams_mobile/features/alerts/screens/emergency_alert_screen.dart';
import 'package:winfams_mobile/features/alerts/services/notification_service.dart';
import 'package:winfams_mobile/features/alerts/widgets/pulsing_alert_beacon.dart';

void main() {
  group('MOB-04: Alert State & Notification Service', () {
    test('AlertState default values and copyWith behavior', () {
      const state = AlertState(
        driverName: 'Budi Santoso',
        driverPhoneNumber: '081234567890',
        vehicleName: 'Innova B 1234 XYZ',
      );

      expect(state.driverName, 'Budi Santoso');
      expect(state.driverPhoneNumber, '081234567890');
      expect(state.isAlarmActive, isFalse);
      expect(state.hasActiveAlert, isFalse);

      final incident = FatigueIncident(
        incidentId: 'inc_test_1',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.94,
        durationSeconds: 2.5,
      );

      final updated = state.copyWith(
        activeIncident: incident,
        isAlarmActive: true,
      );

      expect(updated.hasActiveAlert, isTrue);
      expect(updated.activeIncident?.confidenceScore, 0.94);
    });

    test('NotificationService delivers parsed incident through stream', () async {
      final notifService = NotificationService(apiClient: ApiClient());
      addTearDown(notifService.dispose);

      final incidentFuture = notifService.emergencyIncidentStream.first;

      notifService.simulateEmergencyIncident(
        incidentId: 'inc_999',
        type: 'CRITICAL_DROWSY',
        confidence: 0.95,
        duration: 2.2,
      );

      final received = await incidentFuture;
      expect(received.incidentId, 'inc_999');
      expect(received.isCritical, isTrue);
      expect(received.confidenceScore, 0.95);
      expect(received.durationSeconds, 2.2);
    });

    test('AlertNotifier coordinates emergency alert lifecycle', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final initial = container.read(alertProvider);
      expect(initial.isAlarmActive, isFalse);
      expect(initial.activeIncident, isNull);

      final incident = const FatigueIncident(
        incidentId: 'inc_123',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.91,
      );

      // 1. Trigger
      container.read(alertProvider.notifier).triggerEmergencyAlert(incident);
      final activeState = container.read(alertProvider);
      expect(activeState.isAlarmActive, isTrue);
      expect(activeState.activeIncident?.incidentId, 'inc_123');
      expect(activeState.isMuted, isFalse);

      // 2. Silence
      container.read(alertProvider.notifier).silenceAlarm();
      expect(container.read(alertProvider).isMuted, isTrue);

      // 3. Resolve
      container.read(alertProvider.notifier).resolveActiveIncident();
      expect(container.read(alertProvider).isAlarmActive, isFalse);
      expect(container.read(alertProvider).activeIncident?.resolved, isTrue);

      // 4. Dismiss
      container.read(alertProvider.notifier).dismissAlert();
      expect(container.read(alertProvider).activeIncident, isNull);
    });
  });

  group('MOB-04: UI Widgets & EmergencyAlertScreen Verification', () {
    testWidgets('PulsingAlertBeacon renders with warning icon and semantics',
        (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: PulsingAlertBeacon(),
          ),
        ),
      );

      expect(find.byType(PulsingAlertBeacon), findsOneWidget);
      expect(find.byIcon(Icons.warning_rounded), findsOneWidget);

      await tester.pump(const Duration(milliseconds: 600));
      expect(find.byType(PulsingAlertBeacon), findsOneWidget);
    });

    testWidgets('EmergencyAlertScreen renders critical alerts and actions',
        (tester) async {
      final incident = const FatigueIncident(
        incidentId: 'inc_test_01',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.88,
        durationSeconds: 2.1,
        location: LocationData(lat: -1.2653, lng: 116.8312, speedKmh: 75.0),
      );

      final container = ProviderContainer();
      addTearDown(container.dispose);
      container.read(alertProvider.notifier).triggerEmergencyAlert(incident);

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const MaterialApp(
            home: EmergencyAlertScreen(),
          ),
        ),
      );

      expect(find.text('BAHAYA: MICROSLEEP!'), findsOneWidget);
      expect(find.text('2.1 Detik'), findsOneWidget);
      expect(find.text('88%'), findsOneWidget);
      expect(find.text('75 km/h'), findsOneWidget);
      expect(find.textContaining('HUBUNGI PENGEMUDI'), findsOneWidget);
      expect(find.text('Pantau Lokasi Langsung di Peta'), findsOneWidget);
      expect(find.text('Matikan Suara'), findsOneWidget);
      expect(find.text('Tandai Aman'), findsOneWidget);

      // Test tapping Call button
      await tester.tap(find.textContaining('HUBUNGI PENGEMUDI'));
      await tester.pump();
      expect(find.textContaining('Menghubungi telepon'), findsOneWidget);

      // Test silencing alarm
      await tester.tap(find.text('Matikan Suara'));
      await tester.pump();
      expect(find.text('Bunyikan Alarm'), findsOneWidget);
    });
  });
}
