import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/api_client.dart';

class BrainScreen extends StatefulWidget {
  const BrainScreen({super.key});

  @override
  State<BrainScreen> createState() => _BrainScreenState();
}

class _BrainScreenState extends State<BrainScreen> {
  String _status = 'READY';
  bool _isLoading = false;

  // Replace this with your actual Google Sheet URL.
  final String _sheetUrl = 'https://docs.google.com/spreadsheets';

  Future<void> _triggerSync() async {
    setState(() {
      _isLoading = true;
      _status = 'SYNCING WITH HIVE MIND...';
    });

    final bool result = await syncBrain();

    if (mounted) {
      setState(() {
        _isLoading = false;
        _status = result ? 'SYNC COMPLETE' : 'SYNC FAILED (Check Terminal)';
      });
    }
  }

  Future<void> _openSheet() async {
    final Uri url = Uri.parse(_sheetUrl);
    if (!await launchUrl(url)) {
      throw Exception('Could not launch $_sheetUrl');
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool isComplete = _status.contains('COMPLETE');
    final bool isFailed = _status.contains('FAILED');

    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        title: Text(
          'BRAIN // DATA LAKE',
          style: GoogleFonts.jetBrainsMono(fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF2C2C2C),
        elevation: 0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isComplete ? Icons.check_circle : Icons.storage,
              size: 80,
              color: isFailed ? Colors.redAccent : Colors.purpleAccent,
            ),
            const SizedBox(height: 30),
            Text(
              _status,
              style: GoogleFonts.firaCode(fontSize: 18, color: Colors.white70),
            ),
            const SizedBox(height: 50),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _triggerSync,
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.sync),
              label: Text(_isLoading ? 'UPLOADING...' : 'SYNC TO GOOGLE DRIVE'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
              ),
            ),
            const SizedBox(height: 20),
            OutlinedButton.icon(
              onPressed: _openSheet,
              icon: const Icon(Icons.open_in_browser),
              label: const Text('OPEN GOOGLE SHEET'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.purpleAccent,
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
