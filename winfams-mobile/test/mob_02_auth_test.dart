import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:winfams_mobile/core/models/family_model.dart';
import 'package:winfams_mobile/core/models/user_model.dart';
import 'package:winfams_mobile/features/auth/models/auth_state.dart';
import 'package:winfams_mobile/features/auth/providers/auth_provider.dart';
import 'package:winfams_mobile/features/auth/screens/auth_gate.dart';
import 'package:winfams_mobile/features/auth/screens/device_pairing_screen.dart';
import 'package:winfams_mobile/features/auth/screens/family_setup_screen.dart';
import 'package:winfams_mobile/features/auth/screens/login_screen.dart';
import 'package:winfams_mobile/features/auth/screens/register_screen.dart';

void main() {
  group('MOB-02: Data Models Verification', () {
    test('UserModel serializes and deserializes properly', () {
      final now = DateTime.now();
      final user = UserModel(
        id: 1,
        name: 'Budi Santoso',
        email: 'budi@winfams.id',
        phoneNumber: '08123456789',
        fcmToken: 'mock_fcm_token_123',
        createdAt: now,
      );

      final map = user.toMap();
      final parsed = UserModel.fromMap(map);

      expect(parsed.id, 1);
      expect(parsed.name, 'Budi Santoso');
      expect(parsed.email, 'budi@winfams.id');
      expect(parsed.phoneNumber, '08123456789');
      expect(parsed.fcmToken, 'mock_fcm_token_123');
    });

    test('FamilyModel and DeviceItemModel parse correctly', () {
      final familyMap = {
        'id': 10,
        'name': 'Keluarga Budi',
        'invite_code': 'FAM-9988',
        'created_by': 1,
        'created_at': DateTime.now().toIso8601String(),
      };
      final family = FamilyModel.fromMap(familyMap);
      expect(family.id, 10);
      expect(family.name, 'Keluarga Budi');
      expect(family.inviteCode, 'FAM-9988');

      final deviceMap = {
        'id': 101,
        'device_uid': 'pi4_car_01',
        'vehicle_name': 'Innova Hitam - B 1234 XYZ',
        'is_online': true,
        'current_state': 'DRIVING',
        'last_lat': -1.2653,
        'last_lng': 116.8312,
        'last_speed_kmh': 60.0,
      };
      final device = DeviceItemModel.fromMap(deviceMap);
      expect(device.id, 101);
      expect(device.deviceUid, 'pi4_car_01');
      expect(device.vehicleName, 'Innova Hitam - B 1234 XYZ');
      expect(device.isOnline, isTrue);
      expect(device.currentState, 'DRIVING');
    });
  });

  group('MOB-02: Auth State & Notifier Logic', () {
    test('AuthNotifier initial state is unauthenticated', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final state = container.read(authProvider);
      expect(state.status, AuthStatus.unauthenticated);
      expect(state.isAuthenticated, isFalse);
      expect(state.hasFamily, isFalse);
      expect(state.hasDevice, isFalse);
    });

    test('AuthNotifier logout resets state', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      container.read(authProvider.notifier).logout();
      final state = container.read(authProvider);
      expect(state.status, AuthStatus.unauthenticated);
      expect(state.token, isNull);
    });
  });

  group('MOB-02: UI & Accessibility Screen Verification', () {
    testWidgets('LoginScreen renders email, password fields and validates',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(home: LoginScreen()),
        ),
      );

      expect(find.text('WinFams'), findsOneWidget);
      expect(find.text('Alamat Email'), findsOneWidget);
      expect(find.text('Kata Sandi'), findsOneWidget);
      expect(find.text('Masuk Sekarang'), findsOneWidget);

      // Tap submit with empty fields to trigger validation
      await tester.tap(find.text('Masuk Sekarang'));
      await tester.pumpAndSettle();

      expect(find.text('Email wajib diisi'), findsOneWidget);
      expect(find.text('Kata sandi wajib diisi'), findsOneWidget);
    });

    testWidgets('RegisterScreen renders inputs and validates', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(home: RegisterScreen()),
        ),
      );

      expect(find.text('Buat Akun Baru'), findsOneWidget);
      expect(find.text('Nama Lengkap'), findsOneWidget);
      expect(find.text('Nomor Telepon Darurat'), findsOneWidget);
      expect(find.text('Daftar Sekarang'), findsOneWidget);

      await tester.ensureVisible(find.text('Daftar Sekarang'));
      await tester.tap(find.text('Daftar Sekarang'));
      await tester.pumpAndSettle();

      expect(find.text('Nama lengkap wajib diisi'), findsOneWidget);
    });

    testWidgets('FamilySetupScreen displays toggle and input fields',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(home: FamilySetupScreen()),
        ),
      );

      expect(find.text('Grup Keluarga'), findsOneWidget);
      expect(find.text('Buat Keluarga'), findsOneWidget);
      expect(find.text('Gabung Kode'), findsOneWidget);
      expect(find.text('Nama Keluarga'), findsOneWidget);

      // Switch to Join Kode tab
      await tester.tap(find.text('Gabung Kode'));
      await tester.pumpAndSettle();

      expect(find.text('Kode Undangan'), findsOneWidget);
      expect(find.text('Gabung ke Keluarga'), findsOneWidget);
    });

    testWidgets('DevicePairingScreen displays device inputs and submit button',
        (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(home: DevicePairingScreen()),
        ),
      );

      expect(find.text('Pairing Alat Pi 4'), findsOneWidget);
      expect(find.text('Device UID Raspberry Pi 4'), findsOneWidget);
      expect(find.text('Nama Kendaraan & Pelat'), findsOneWidget);
      expect(find.text('Hubungkan Alat ke Keluarga'), findsOneWidget);
    });

    testWidgets('AuthGate routes to LoginScreen initially', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(home: AuthGate()),
        ),
      );

      expect(find.byType(LoginScreen), findsOneWidget);
    });
  });
}
