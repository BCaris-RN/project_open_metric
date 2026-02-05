import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../api/api_client.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _metricoolEmail = TextEditingController();
  final _metricoolPassword = TextEditingController();
  final _driveId = TextEditingController();

  @override
  void dispose() {
    _metricoolEmail.dispose();
    _metricoolPassword.dispose();
    _driveId.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final configAsync = ref.watch(configProvider);
    final techFont = GoogleFonts.jetBrainsMono();

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('SETTINGS', style: techFont.copyWith(color: Colors.white)),
      ),
      body: configAsync.when(
        data: (config) {
          final metricoolConnected = (config['metricool_connected'] ?? false) as bool;
          final driveConnected = (config['drive_connected'] ?? false) as bool;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _StatusRow(
                label: 'Metricool',
                isConnected: metricoolConnected,
              ),
              const SizedBox(height: 8),
              _StatusRow(
                label: 'Google Drive',
                isConnected: driveConnected,
              ),
              const SizedBox(height: 24),
              Text('METRICOOL CREDENTIALS', style: techFont.copyWith(color: Colors.grey)),
              const SizedBox(height: 8),
              _TextField(
                controller: _metricoolEmail,
                hint: 'Email',
                icon: Icons.email,
              ),
              const SizedBox(height: 8),
              _TextField(
                controller: _metricoolPassword,
                hint: 'Password',
                icon: Icons.lock,
                obscure: true,
              ),
              const SizedBox(height: 24),
              Text('GOOGLE DRIVE', style: techFont.copyWith(color: Colors.grey)),
              const SizedBox(height: 8),
              _TextField(
                controller: _driveId,
                hint: 'Drive Folder ID',
                icon: Icons.folder,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () async {
                  final success = await saveConfig(
                    metricoolEmail: _metricoolEmail.text.trim().isEmpty
                        ? null
                        : _metricoolEmail.text.trim(),
                    metricoolPassword: _metricoolPassword.text.trim().isEmpty
                        ? null
                        : _metricoolPassword.text.trim(),
                    driveId: _driveId.text.trim().isEmpty ? null : _driveId.text.trim(),
                  );
                  if (!mounted) return;
                  if (success) {
                    ref.invalidate(configProvider);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Settings saved.')),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Failed to save settings.')),
                    );
                  }
                },
                icon: const Icon(Icons.save),
                label: const Text('SAVE'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => context.push('/connect'),
                icon: const Icon(Icons.link),
                label: const Text('CONNECT ACCOUNTS'),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => Center(child: Text('Error: $e', style: const TextStyle(color: Colors.red))),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.label, required this.isConnected});

  final String label;
  final bool isConnected;

  @override
  Widget build(BuildContext context) {
    final color = isConnected ? Colors.greenAccent : Colors.redAccent;
    final text = isConnected ? 'CONNECTED' : 'DISCONNECTED';
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: GoogleFonts.jetBrainsMono(color: Colors.white)),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.2),
            border: Border.all(color: color),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            text,
            style: GoogleFonts.jetBrainsMono(color: color, fontSize: 12),
          ),
        ),
      ],
    );
  }
}

class _TextField extends StatelessWidget {
  const _TextField({
    required this.controller,
    required this.hint,
    required this.icon,
    this.obscure = false,
  });

  final TextEditingController controller;
  final String hint;
  final IconData icon;
  final bool obscure;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Colors.grey),
        prefixIcon: Icon(icon, color: Colors.grey),
        filled: true,
        fillColor: const Color(0xFF1E1E1E),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
