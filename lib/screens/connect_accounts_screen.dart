import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import '../api/api_client.dart';

class ConnectAccountsScreen extends ConsumerStatefulWidget {
  const ConnectAccountsScreen({super.key});

  @override
  ConsumerState<ConnectAccountsScreen> createState() => _ConnectAccountsScreenState();
}

class _ConnectAccountsScreenState extends ConsumerState<ConnectAccountsScreen> {
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final techFont = GoogleFonts.jetBrainsMono();

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('CONNECT ACCOUNTS', style: techFont.copyWith(color: Colors.white)),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.link,
              size: 72,
              color: _isLoading ? Colors.orangeAccent : Colors.blueAccent,
            ),
            const SizedBox(height: 16),
            Text(
              _isLoading ? 'Please log in via the browser window...' : 'Metricool Connection',
              style: techFont.copyWith(color: Colors.white70, fontSize: 14),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _isLoading
                  ? null
                  : () async {
                      setState(() => _isLoading = true);
                      final success = await authMetricool();
                      if (!mounted) return;
                      setState(() => _isLoading = false);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(success ? 'Metricool connected.' : 'Connection failed.'),
                        ),
                      );
                      ref.invalidate(configProvider);
                    },
              icon: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.login),
              label: Text(_isLoading ? 'CONNECTING...' : 'LOG IN TO METRICOOL'),
            ),
          ],
        ),
      ),
    );
  }
}
