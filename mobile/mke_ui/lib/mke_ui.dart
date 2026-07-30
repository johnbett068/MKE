import 'package:flutter/material.dart';

abstract final class MkeColors {
  static const orange = Color(0xFFFF8C00);
  static const orangeDark = Color(0xFFE67E00);
  static const orangeSoft = Color(0xFFFFF7ED);
  static const blue = Color(0xFF155EEF);
  static const navy = Color(0xFF0B1F3A);
  static const canvas = Color(0xFFF7F9FC);
  static const text = Color(0xFF101828);
  static const muted = Color(0xFF667085);
  static const border = Color(0xFFE4E7EC);
  static const success = Color(0xFF12B76A);
  static const danger = Color(0xFFD92D20);
}

ThemeData mkeTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: MkeColors.orange,
    primary: MkeColors.orange,
    secondary: MkeColors.blue,
    surface: Colors.white,
    error: MkeColors.danger,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: MkeColors.canvas,
    fontFamily: 'Inter',
    textTheme: const TextTheme(
      headlineMedium: TextStyle(
        color: MkeColors.text,
        fontSize: 28,
        fontWeight: FontWeight.w700,
      ),
      titleLarge: TextStyle(
        color: MkeColors.text,
        fontSize: 20,
        fontWeight: FontWeight.w700,
      ),
      bodyLarge: TextStyle(color: MkeColors.text, height: 1.5),
      bodyMedium: TextStyle(color: MkeColors.muted, height: 1.45),
    ),
    cardTheme: const CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(20)),
        side: BorderSide(color: MkeColors.border),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: MkeColors.orange,
        foregroundColor: Colors.white,
        minimumSize: const Size.fromHeight(54),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: MkeColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: MkeColors.border),
      ),
    ),
  );
}

class MkeBrandMark extends StatelessWidget {
  const MkeBrandMark({super.key, this.size = 44});
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(size * .3),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [MkeColors.orange, Color(0xFFFF6B35), MkeColors.blue],
        ),
      ),
      alignment: Alignment.center,
      child: Text(
        'M',
        style: TextStyle(
          color: Colors.white,
          fontSize: size * .46,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}
