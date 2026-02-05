import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'screens/brain_screen.dart';
import 'screens/home_screen.dart';
import 'screens/queue_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/connect_accounts_screen.dart';
import 'services/backend_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  WidgetsBinding.instance.addObserver(_AppLifecycleObserver());
  runApp(const ProviderScope(child: OpenMetricApp()));
}

final _router = GoRouter(
  initialLocation: '/splash',
  routes: [
    GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/queue', builder: (context, state) => const QueueScreen()),
    GoRoute(path: '/brain', builder: (context, state) => const BrainScreen()),
    GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
    GoRoute(path: '/connect', builder: (context, state) => const ConnectAccountsScreen()),
  ],
);

class OpenMetricApp extends StatelessWidget {
  const OpenMetricApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Open Metric',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
      themeMode: ThemeMode.system,
      routerConfig: _router,
    );
  }
}

class _AppLifecycleObserver extends WidgetsBindingObserver {
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.detached) {
      BackendService.instance.kill();
    }
  }
}
