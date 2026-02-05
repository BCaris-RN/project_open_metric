import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late final AnimationController _fadeController;
  late final AnimationController _bootController;
  late final AnimationController _flickerController;
  late final Animation<double> _opacity;
  late final Animation<double> _scale;

  Timer? _bootTimer;
  int _visibleLines = 0;

  final List<String> _bootLines = const [
    'Boot core: OK',
    'Loading telemetry channels',
    'Warming model cache',
    'Syncing queue state',
    'Linking analyst nodes',
    'Handshake with orchestrator',
  ];

  @override
  void initState() {
    super.initState();

    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    _bootController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    );
    _flickerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);

    _opacity = CurvedAnimation(parent: _fadeController, curve: Curves.easeOut);
    _scale = Tween<double>(begin: 0.96, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeOutCubic),
    );

    _fadeController.forward();
    _bootController.forward();

    _bootController.addStatusListener((status) {
      if (status == AnimationStatus.completed && mounted) {
        context.go('/');
      }
    });

    _bootTimer = Timer.periodic(const Duration(milliseconds: 420), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() {
        _visibleLines = min(_visibleLines + 1, _bootLines.length);
        if (_visibleLines >= _bootLines.length) {
          timer.cancel();
        }
      });
    });
  }

  @override
  void dispose() {
    _bootTimer?.cancel();
    _fadeController.dispose();
    _bootController.dispose();
    _flickerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      body: Stack(
        children: [
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: const Alignment(0.0, -0.4),
                  radius: 1.2,
                  colors: [
                    const Color(0xFF1A1F2B),
                    const Color(0xFF0B0C10),
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(
            child: CustomPaint(
              painter: _GridPainter(),
            ),
          ),
          Center(
            child: FadeTransition(
              opacity: _opacity,
              child: ScaleTransition(
                scale: _scale,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.hub,
                      size: 84,
                      color: Colors.blueAccent,
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'OPEN-METRIC',
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 2.0,
                      ),
                    ),
                    const SizedBox(height: 10),
                    AnimatedBuilder(
                      animation: _flickerController,
                      builder: (context, child) {
                        final glow = 0.6 + (_flickerController.value * 0.4);
                        return Opacity(opacity: glow, child: child);
                      },
                      child: Text(
                        'INITIALIZING AGENTS...',
                        style: GoogleFonts.firaCode(
                          fontSize: 14,
                          color: Colors.greenAccent,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    _BootLog(lines: _bootLines.take(_visibleLines).toList()),
                    const SizedBox(height: 24),
                    AnimatedBuilder(
                      animation: _bootController,
                      builder: (context, child) {
                        return ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: LinearProgressIndicator(
                            value: _bootController.value,
                            minHeight: 6,
                            backgroundColor: const Color(0xFF121417),
                            color: Colors.blueAccent,
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(
            child: IgnorePointer(
              child: AnimatedBuilder(
                animation: _flickerController,
                builder: (context, child) {
                  return CustomPaint(
                    painter: _ScanlinePainter(_flickerController.value),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BootLog extends StatelessWidget {
  const _BootLog({required this.lines});

  final List<String> lines;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 280,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0C0E12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF1F2630)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final line in lines)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(
                '> $line',
                style: GoogleFonts.firaCode(
                  fontSize: 11,
                  color: Colors.greenAccent.withValues(alpha: 0.8),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF1A2030).withValues(alpha: 0.25)
      ..strokeWidth = 1;

    const step = 32.0;
    for (double x = 0; x <= size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y <= size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ScanlinePainter extends CustomPainter {
  _ScanlinePainter(this.progress);

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final linePaint = Paint()..color = Colors.white.withValues(alpha: 0.03);
    const gap = 6.0;
    for (double y = 0; y < size.height; y += gap) {
      canvas.drawRect(Rect.fromLTWH(0, y, size.width, 1), linePaint);
    }

    final glowPaint = Paint()..color = Colors.blueAccent.withValues(alpha: 0.08);
    final yPos = size.height * progress;
    canvas.drawRect(Rect.fromLTWH(0, yPos, size.width, 2), glowPaint);
  }

  @override
  bool shouldRepaint(covariant _ScanlinePainter oldDelegate) => oldDelegate.progress != progress;
}
