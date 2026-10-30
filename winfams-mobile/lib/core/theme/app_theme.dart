import 'package:flutter/material.dart';

/// Design system tokens and ThemeData for WinFams Mobile.
class AppTheme {
  AppTheme._();

  // Safety Status Color Tokens
  static const Color statusNormal = Color(0xFF10B981); // Emerald Green
  static const Color statusWarning = Color(0xFFF59E0B); // Amber / Orange
  static const Color statusCritical = Color(0xFFEF4444); // Crimson Red
  static const Color statusOffline = Color(0xFF6B7280); // Gray

  // Brand Palette
  static const Color primaryBlue = Color(0xFF1E3A8A); // Deep Navy
  static const Color accentCyan = Color(0xFF06B6D4);
  static const Color backgroundDark = Color(0xFF0F172A); // Slate 900
  static const Color surfaceDark = Color(0xFF1E293B); // Slate 800
  static const Color cardDark = Color(0xFF334155); // Slate 700

  static Color getStatusColor(String state) {
    switch (state.toUpperCase()) {
      case 'CRITICAL_DROWSY':
        return statusCritical;
      case 'WARNING_FATIGUE':
        return statusWarning;
      case 'DRIVING':
      case 'NORMAL':
        return statusNormal;
      default:
        return statusOffline;
    }
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: backgroundDark,
      colorScheme: const ColorScheme.dark(
        primary: accentCyan,
        onPrimary: backgroundDark,
        secondary: statusNormal,
        surface: surfaceDark,
        error: statusCritical,
      ),
      cardTheme: CardThemeData(
        color: surfaceDark,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: backgroundDark,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentCyan,
          foregroundColor: backgroundDark,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

