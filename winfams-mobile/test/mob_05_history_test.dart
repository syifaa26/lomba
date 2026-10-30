import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/core/models/fatigue_incident.dart';
import 'package:winfams_mobile/core/models/location_data.dart';
import 'package:winfams_mobile/features/alerts/models/incident_history_state.dart';
import 'package:winfams_mobile/features/alerts/providers/incident_history_provider.dart';
import 'package:winfams_mobile/features/alerts/screens/incident_history_screen.dart';
import 'package:winfams_mobile/features/alerts/screens/incident_map_screen.dart';
import 'package:winfams_mobile/features/alerts/widgets/incident_card.dart';

void main() {
  group('MOB-05: Incident History State & Provider Tests', () {
    test('IncidentHistoryState filters correctly by incident type', () {
      final inc1 = const FatigueIncident(
        incidentId: '1',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
      );
      final inc2 = const FatigueIncident(
        incidentId: '2',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'WARNING_FATIGUE',
      );

      final state = IncidentHistoryState(incidents: [inc1, inc2]);
      expect(state.filteredIncidents.length, 2);
      expect(state.criticalCount, 1);
      expect(state.warningCount, 1);

      final filteredCritical = state.copyWith(selectedFilter: 'CRITICAL_DROWSY');
      expect(filteredCritical.filteredIncidents.length, 1);
      expect(filteredCritical.filteredIncidents.first.incidentId, '1');

      final filteredWarning = state.copyWith(selectedFilter: 'WARNING_FATIGUE');
      expect(filteredWarning.filteredIncidents.length, 1);
      expect(filteredWarning.filteredIncidents.first.incidentId, '2');
    });

    test('IncidentHistoryNotifier updates filter and selection', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final initial = container.read(incidentHistoryProvider);
      expect(initial.incidents.isNotEmpty, isTrue);

      container.read(incidentHistoryProvider.notifier).setFilter('CRITICAL_DROWSY');
      expect(container.read(incidentHistoryProvider).selectedFilter, 'CRITICAL_DROWSY');

      final firstInc = initial.incidents.first;
      container.read(incidentHistoryProvider.notifier).selectIncident(firstInc);
      expect(container.read(incidentHistoryProvider).selectedIncident, equals(firstInc));
    });
  });

  group('MOB-05: UI Widgets & Screen Verification', () {
    testWidgets('IncidentCard renders details and responds to map button',
        (tester) async {
      bool mapTapped = false;
      final incident = const FatigueIncident(
        incidentId: 'inc_test',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.92,
        durationSeconds: 2.3,
        location: LocationData(lat: -1.2650, lng: 116.8320, speedKmh: 68.0),
        timestamp: 1730334600,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: IncidentCard(
              incident: incident,
              onTapMap: () {
                mapTapped = true;
              },
            ),
          ),
        ),
      );

      expect(find.text('MICROSLEEP'), findsOneWidget);
      expect(find.text('2.3s'), findsOneWidget);
      expect(find.text('92%'), findsOneWidget);
      expect(find.text('68 km/h'), findsOneWidget);
      expect(find.text('Peta Titik'), findsOneWidget);

      await tester.tap(find.text('Peta Titik'));
      await tester.pump();
      expect(mapTapped, isTrue);
    });

    testWidgets('IncidentMapScreen renders coordinates card and map elements',
        (tester) async {
      final incident = const FatigueIncident(
        incidentId: 'inc_map_test',
        deviceId: 'pi4_car_01',
        driverUid: 'user_1',
        type: 'CRITICAL_DROWSY',
        confidenceScore: 0.88,
        durationSeconds: 2.0,
        location: LocationData(lat: -1.2653, lng: 116.8312, speedKmh: 65.0),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: IncidentMapScreen(incident: incident),
        ),
      );

      expect(find.text('Titik Insiden Microsleep'), findsOneWidget);
      expect(find.text('Peringatan Bahaya Microsleep'), findsOneWidget);
      expect(find.text('88% Akurat'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);
    });

    testWidgets('IncidentHistoryScreen displays summary, filters, and list',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: IncidentHistoryScreen(),
          ),
        ),
      );

      expect(find.text('Riwayat Insiden & Perjalanan'), findsOneWidget);
      expect(find.text('Total Catatan'), findsOneWidget);
      expect(find.text('Semua'), findsOneWidget);
      expect(find.text('Microsleep'), findsAtLeastNWidgets(1));
      expect(find.text('Menguap'), findsOneWidget);
      expect(find.byType(IncidentCard), findsWidgets);

      // Tap Microsleep filter chip
      await tester.tap(find.widgetWithText(ChoiceChip, 'Microsleep'));
      await tester.pumpAndSettle();

      expect(find.byType(IncidentCard), findsWidgets);
    });
  });
}
