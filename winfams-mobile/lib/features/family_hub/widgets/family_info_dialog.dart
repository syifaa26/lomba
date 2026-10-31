import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/models/family_model.dart';
import '../../../core/theme/app_theme.dart';

/// Modal dialog displaying family group information, connected devices, and invite code sharing.
class FamilyInfoDialog extends StatelessWidget {
  final FamilyModel? family;
  final List<DeviceItemModel> devices;

  const FamilyInfoDialog({
    super.key,
    required this.family,
    this.devices = const [],
  });

  void _copyToClipboard(BuildContext context, String code) {
    Clipboard.setData(ClipboardData(text: code));
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle, color: Colors.white),
            const SizedBox(width: 8),
            Text('Kode undangan $code berhasil disalin!'),
          ],
        ),
        backgroundColor: AppTheme.statusNormal,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final code = family?.inviteCode.isNotEmpty == true
        ? family!.inviteCode
        : 'TIDAK TERSEDIA';

    return Dialog(
      backgroundColor: AppTheme.surfaceDark,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.accentCyan.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.family_restroom, color: AppTheme.accentCyan, size: 36),
            ),
            const SizedBox(height: 12),
            Text(
              family?.name ?? 'Keluarga WinFams',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            const Text(
              'Grup Pemantauan Keselamatan',
              style: TextStyle(fontSize: 12, color: Colors.white60),
            ),
            const SizedBox(height: 20),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.backgroundDark,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.accentCyan.withValues(alpha: 0.4)),
              ),
              child: Column(
                children: [
                  const Text(
                    'KODE UNDANGAN KELUARGA',
                    style: TextStyle(
                      fontSize: 11,
                      letterSpacing: 1.2,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.accentCyan,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SelectableText(
                    code,
                    style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 4,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.copy, size: 18),
                      label: const Text('Salin Kode Undangan'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.accentCyan,
                        foregroundColor: AppTheme.backgroundDark,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      onPressed: () => _copyToClipboard(context, code),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'Bagikan kode ini kepada anggota keluarga agar dapat memantau status mobil di aplikasi mereka.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.white70),
            ),
            if (devices.isNotEmpty) ...[
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.directions_car, size: 16, color: AppTheme.statusNormal),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text(
                      '${devices.first.vehicleName} (${devices.first.deviceUid})',
                      style: const TextStyle(fontSize: 12, color: AppTheme.statusNormal),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 18),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Tutup', style: TextStyle(color: Colors.white60)),
            ),
          ],
        ),
      ),
    );
  }
}

