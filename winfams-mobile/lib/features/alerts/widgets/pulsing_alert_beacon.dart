import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

/// Animated pulsing beacon indicating critical microsleep emergency.
class PulsingAlertBeacon extends StatefulWidget {
  final bool isMuted;

  const PulsingAlertBeacon({super.key, this.isMuted = false});

  @override
  State<PulsingAlertBeacon> createState() => _PulsingAlertBeaconState();
}

class _PulsingAlertBeaconState extends State<PulsingAlertBeacon>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _animation = Tween<double>(begin: 0.85, end: 1.15).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      liveRegion: true,
      label: 'Peringatan Bahaya: Microsleep terdeteksi pada pengemudi!',
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          return Transform.scale(
            scale: _animation.value,
            child: Container(
              width: 140,
              height: 140,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.statusCritical.withValues(alpha: 0.15),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.statusCritical.withValues(alpha: 0.5),
                    blurRadius: 28 * _animation.value,
                    spreadRadius: 8 * _animation.value,
                  ),
                ],
              ),
              child: Center(
                child: Container(
                  width: 90,
                  height: 90,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.statusCritical,
                  ),
                  child: Icon(
                    widget.isMuted
                        ? Icons.volume_off_rounded
                        : Icons.warning_rounded,
                    size: 48,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
