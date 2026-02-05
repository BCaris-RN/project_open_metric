import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'screens/brain_screen.dart';
import 'screens/home_screen.dart';
import 'screens/queue_screen.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const ProviderScope(child: OpenMetricApp()));
}

final _router = GoRouter(
  initialLocation: '/splash',
  routes: [
    GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/queue', builder: (context, state) => const QueueScreen()),
    GoRoute(path: '/brain', builder: (context, state) => const BrainScreen()),
  ],
);

class OpenMetricApp extends StatelessWidget {
  const OpenMetricApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Open Metric',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      routerConfig: _router,
    );
  }
}
