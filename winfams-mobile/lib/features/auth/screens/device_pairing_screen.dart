import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../live_map/screens/live_map_screen.dart';
import '../providers/auth_provider.dart';
import '../widgets/auth_button.dart';
import '../widgets/auth_text_field.dart';

/// Screen allowing users to pair a Raspberry Pi 4 IoT device to their family group.
class DevicePairingScreen extends ConsumerStatefulWidget {
  const DevicePairingScreen({super.key});

  @override
  ConsumerState<DevicePairingScreen> createState() => _DevicePairingScreenState();
}

class _DevicePairingScreenState extends ConsumerState<DevicePairingScreen> {
  final _formKey = GlobalKey<FormState>();
  final _deviceUidController = TextEditingController(text: 'pi4_car_01');
  final _vehicleNameController = TextEditingController(text: 'Avanza Hitam - B 1234 XYZ');

  @override
  void dispose() {
    _deviceUidController.dispose();
    _vehicleNameController.dispose();
    super.dispose();
  }

  void _submitPairing() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(authProvider.notifier).pairDevice(
            deviceUid: _deviceUidController.text.trim(),
            vehicleName: _vehicleNameController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Pairing Alat Pi 4'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Semantics(
                header: true,
                child: Column(
                  children: const [
                    Icon(Icons.directions_car_filled_outlined,
                        size: 56, color: AppTheme.accentCyan),
                    SizedBox(height: 12),
                    Text(
                      'Hubungkan Perangkat Mobil',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Daftarkan alat Edge AI Raspberry Pi 4 yang terpasang di mobil keluarga.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: Colors.white70),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              if (authState.errorMessage != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.statusCritical.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.statusCritical),
                  ),
                  child: Text(
                    authState.errorMessage!,
                    style: const TextStyle(color: Colors.white, fontSize: 13),
                  ),
                ),
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    AuthTextField(
                      controller: _deviceUidController,
                      label: 'Device UID Raspberry Pi 4',
                      hint: 'Contoh: pi4_car_01',
                      prefixIcon: Icons.memory,
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Device UID wajib diisi';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    AuthTextField(
                      controller: _vehicleNameController,
                      label: 'Nama Kendaraan & Pelat',
                      hint: 'Contoh: Innova Hitam - B 1234 XYZ',
                      prefixIcon: Icons.drive_eta_outlined,
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Nama kendaraan wajib diisi';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    AuthButton(
                      label: 'Hubungkan Alat ke Keluarga',
                      isLoading: authState.isLoading,
                      onPressed: _submitPairing,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              if (authState.devices.isNotEmpty) ...[
                const Text(
                  'Perangkat Terdaftar:',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 12),
                ...authState.devices.map(
                  (device) => Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: const Icon(Icons.car_rental, color: AppTheme.accentCyan),
                      title: Text(device.vehicleName, style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('UID: ${device.deviceUid}'),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.statusNormal.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppTheme.statusNormal),
                        ),
                        child: const Text(
                          'TERHUBUNG',
                          style: TextStyle(color: AppTheme.statusNormal, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                AuthButton(
                  label: 'Buka Dasbor Monitoring',
                  backgroundColor: AppTheme.statusNormal,
                  foregroundColor: Colors.white,
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (_) => const LiveMapScreen()),
                    );
                  },
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
