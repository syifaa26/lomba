import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../models/auth_state.dart';
import '../providers/auth_provider.dart';
import '../widgets/auth_button.dart';
import '../widgets/auth_text_field.dart';
import 'device_pairing_screen.dart';

/// Screen for creating a new family group or joining one with an invite code.
class FamilySetupScreen extends ConsumerStatefulWidget {
  const FamilySetupScreen({super.key});

  @override
  ConsumerState<FamilySetupScreen> createState() => _FamilySetupScreenState();
}

class _FamilySetupScreenState extends ConsumerState<FamilySetupScreen> {
  int _selectedTab = 0; // 0 = Buat Baru, 1 = Gabung
  final _createFormKey = GlobalKey<FormState>();
  final _joinFormKey = GlobalKey<FormState>();

  final _familyNameController = TextEditingController();
  final _inviteCodeController = TextEditingController();

  @override
  void dispose() {
    _familyNameController.dispose();
    _inviteCodeController.dispose();
    super.dispose();
  }

  void _submitCreate() {
    if (_createFormKey.currentState?.validate() ?? false) {
      ref.read(authProvider.notifier).createFamily(_familyNameController.text.trim());
    }
  }

  void _submitJoin() {
    if (_joinFormKey.currentState?.validate() ?? false) {
      ref.read(authProvider.notifier).joinFamily(_inviteCodeController.text.trim());
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: AppTheme.backgroundDark,
      appBar: AppBar(
        title: const Text('Grup Keluarga'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Keluar',
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (authState.hasFamily) ...[
                _buildActiveFamilyCard(authState),
              ] else ...[
                _buildHeader(),
                const SizedBox(height: 20),
                if (authState.errorMessage != null) _buildErrorMessage(authState.errorMessage!),
                _buildTabSelector(),
                const SizedBox(height: 24),
                if (_selectedTab == 0) _buildCreateForm(authState.isLoading) else _buildJoinForm(authState.isLoading),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Semantics(
      header: true,
      child: Column(
        children: const [
          Icon(Icons.family_restroom, size: 56, color: AppTheme.accentCyan),
          SizedBox(height: 12),
          Text(
            'Siapkan Lingkar Keluarga',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          SizedBox(height: 6),
          Text(
            'Pantau seluruh anggota keluarga Anda dalam satu dasbor terpadu.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: Colors.white70),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorMessage(String msg) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.statusCritical.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.statusCritical),
      ),
      child: Text(msg, style: const TextStyle(color: Colors.white, fontSize: 13)),
    );
  }

  Widget _buildTabSelector() {
    return SegmentedButton<int>(
      segments: const [
        ButtonSegment(value: 0, label: Text('Buat Keluarga')),
        ButtonSegment(value: 1, label: Text('Gabung Kode')),
      ],
      selected: {_selectedTab},
      onSelectionChanged: (set) => setState(() => _selectedTab = set.first),
    );
  }

  Widget _buildCreateForm(bool isLoading) {
    return Form(
      key: _createFormKey,
      child: Column(
        children: [
          AuthTextField(
            controller: _familyNameController,
            label: 'Nama Keluarga',
            hint: 'Contoh: Keluarga Budi',
            prefixIcon: Icons.group_outlined,
            validator: (val) => (val == null || val.trim().isEmpty) ? 'Nama keluarga wajib diisi' : null,
          ),
          const SizedBox(height: 24),
          AuthButton(
            label: 'Buat Grup Sekarang',
            isLoading: isLoading,
            onPressed: _submitCreate,
          ),
        ],
      ),
    );
  }

  Widget _buildJoinForm(bool isLoading) {
    return Form(
      key: _joinFormKey,
      child: Column(
        children: [
          AuthTextField(
            controller: _inviteCodeController,
            label: 'Kode Undangan',
            hint: 'Contoh: FAM-9821',
            prefixIcon: Icons.vpn_key_outlined,
            validator: (val) => (val == null || val.trim().isEmpty) ? 'Kode undangan wajib diisi' : null,
          ),
          const SizedBox(height: 24),
          AuthButton(
            label: 'Gabung ke Keluarga',
            isLoading: isLoading,
            onPressed: _submitJoin,
          ),
        ],
      ),
    );
  }

  Widget _buildActiveFamilyCard(AuthState authState) {
    final family = authState.currentFamily!;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            const Icon(Icons.check_circle_outline, color: AppTheme.statusNormal, size: 54),
            const SizedBox(height: 12),
            Text(
              family.name,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.backgroundDark,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppTheme.accentCyan.withValues(alpha: 0.4)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('KODE UNDANGAN', style: TextStyle(fontSize: 10, color: Colors.white60)),
                      SelectableText(
                        family.inviteCode,
                        style: const TextStyle(fontSize: 20, color: AppTheme.accentCyan, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  IconButton(
                    icon: const Icon(Icons.copy, color: AppTheme.accentCyan),
                    tooltip: 'Salin Kode',
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: family.inviteCode));
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Kode undangan ${family.inviteCode} disalin!'),
                          backgroundColor: AppTheme.statusNormal,
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            AuthButton(
              label: 'Lanjut ke Pairing Alat Pi 4',
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const DevicePairingScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
