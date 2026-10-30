import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/features/family_hub/models/rest_stop_model.dart';
import 'package:winfams_mobile/features/family_hub/models/rest_stop_state.dart';
import 'package:winfams_mobile/features/family_hub/providers/rest_stop_provider.dart';
import 'package:winfams_mobile/features/family_hub/screens/family_hub_screen.dart';
import 'package:winfams_mobile/features/family_hub/screens/rest_stop_map_screen.dart';
import 'package:winfams_mobile/features/family_hub/widgets/rest_stop_card.dart';

void main() {
  group('MOB-06: Rest Stop Data Models & Provider Tests', () {
    test('RestStopModel parses from map and serializes accurately', () {
      final map = {
        'id': 'stop_100',
        'name': 'Rest Area KM 36',
        'type': 'REST_AREA',
        'lat': -1.2500,
        'lng': 116.8500,
        'distance_km': 2.5,
        'address': 'Tol Balikpapan KM 36',
        'facilities': ['Toilet', 'Musholla', 'Kafe'],
        'is_open_24h': true,
      };

      final stop = RestStopModel.fromMap(map);
      expect(stop.id, 'stop_100');
      expect(stop.name, 'Rest Area KM 36');
      expect(stop.isRestArea, isTrue);
      expect(stop.distanceKm, 2.5);
      expect(stop.facilities.length, 3);

      final outMap = stop.toMap();
      expect(outMap['name'], 'Rest Area KM 36');
    });

    test('RestStopState correctly filters by type', () {
      const stop1 = RestStopModel(
        id: '1',
        name: 'Rest Area KM 36',
        type: 'REST_AREA',
        lat: -1.25,
        lng: 116.85,
      );
      const stop2 = RestStopModel(
        id: '2',
        name: 'SPBU Pertamina KM 28',
        type: 'GAS_STATION',
        lat: -1.24,
        lng: 116.84,
      );

      final state = const RestStopState(restStops: [stop1, stop2]);
      expect(state.filteredStops.length, 2);

      final restAreaFilter = state.copyWith(selectedFilter: 'REST_AREA');
      expect(restAreaFilter.filteredStops.length, 1);
      expect(restAreaFilter.filteredStops.first.id, '1');

      final spbuFilter = state.copyWith(selectedFilter: 'GAS_STATION');
      expect(spbuFilter.filteredStops.length, 1);
      expect(spbuFilter.filteredStops.first.id, '2');
    });

    test('RestStopNotifier handles shareWithDriver and clearMessage', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final initial = container.read(restStopProvider);
      expect(initial.restStops.isNotEmpty, isTrue);

      final firstStop = initial.restStops.first;
      container.read(restStopProvider.notifier).shareWithDriver(firstStop);

      final sharedState = container.read(restStopProvider);
      expect(sharedState.shareSuccessMessage, contains(firstStop.name));

      container.read(restStopProvider.notifier).clearMessage();
      expect(container.read(restStopProvider).shareSuccessMessage, isNull);
    });
  });

  group('MOB-06: UI Widgets & Screen Verification', () {
    testWidgets('RestStopCard displays amenities and triggers actions',
        (tester) async {
      bool shareTapped = false;
      bool mapTapped = false;

      const stop = RestStopModel(
        id: 'stop_card_test',
        name: 'Rest Area KM 36 Tol Balsam',
        type: 'REST_AREA',
        lat: -1.2650,
        lng: 116.8350,
        distanceKm: 2.3,
        address: 'Tol Balikpapan KM 36',
        facilities: ['Toilet Bersih', 'Musholla', 'Parkir Luas'],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RestStopCard(
              stop: stop,
              onShareWithDriver: () {
                shareTapped = true;
              },
              onViewOnMap: () {
                mapTapped = true;
              },
            ),
          ),
        ),
      );

      expect(find.text('Rest Area KM 36 Tol Balsam'), findsOneWidget);
      expect(find.text('REST AREA'), findsOneWidget);
      expect(find.textContaining('2.3 km'), findsOneWidget);
      expect(find.text('Toilet Bersih'), findsOneWidget);
      expect(find.text('Musholla'), findsOneWidget);

      await tester.tap(find.text('Kirim ke Pengemudi'));
      await tester.pump();
      expect(shareTapped, isTrue);

      await tester.tap(find.text('Peta'));
      await tester.pump();
      expect(mapTapped, isTrue);
    });

    testWidgets('RestStopMapScreen renders vehicle, rest stop markers, and share button',
        (tester) async {
      const stop = RestStopModel(
        id: 'map_test_stop',
        name: 'SPBU Pertamina KM 28',
        type: 'GAS_STATION',
        lat: -1.2600,
        lng: 116.8300,
        distanceKm: 3.5,
        address: 'Jl. Soekarno Hatta KM 28',
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: RestStopMapScreen(stop: stop),
        ),
      );

      expect(find.text('SPBU Pertamina KM 28'), findsWidgets);
      expect(find.text('Mobil'), findsOneWidget);
      expect(find.textContaining('3.5 km'), findsWidgets);
      expect(find.text('Kirim Rekomendasi ke Mobil'), findsOneWidget);
    });

    testWidgets('FamilyHubScreen renders filter chips and rest stop cards',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: FamilyHubScreen(),
          ),
        ),
      );

      expect(find.text('Smart Rest-Stop Finder'), findsOneWidget);
      expect(find.text('Semua Lokasi'), findsOneWidget);
      expect(find.text('Rest Area'), findsWidgets);
      expect(find.text('SPBU'), findsWidgets);
      expect(find.byType(RestStopCard), findsWidgets);

      // Tap filter chip SPBU
      await tester.tap(find.widgetWithText(ChoiceChip, 'SPBU'));
      await tester.pumpAndSettle();

      expect(find.byType(RestStopCard), findsWidgets);
    });
  });
}
