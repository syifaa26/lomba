import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../live_map/screens/live_map_screen.dart';
import '../providers/auth_provider.dart';
import 'device_pairing_screen.dart';
import 'family_setup_screen.dart';
import 'login_screen.dart';

/// Decides which root screen to present based on the user's authentication and onboarding status.
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    if (!authState.isAuthenticated) {
      return const LoginScreen();
    }

    if (!authState.hasFamily) {
      return const FamilySetupScreen();
    }

    if (!authState.hasDevice) {
      return const DevicePairingScreen();
    }

    return const LiveMapScreen();
  }
}
