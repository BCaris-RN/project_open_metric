import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;

class BackendService {
  BackendService._();

  static final BackendService instance = BackendService._();

  Process? _process;
  bool _starting = false;

  Future<void> start() async {
    if (_process != null || _starting) {
      return;
    }
    _starting = true;

    _process = await Process.start(
      'python',
      ['backend/server.py'],
      runInShell: true,
    );

    _process?.stdout.listen((data) {
      stdout.write(String.fromCharCodes(data));
    });

    _process?.stderr.listen((data) {
      stderr.write(String.fromCharCodes(data));
    });

    _starting = false;

    if (!Platform.isWindows) {
      ProcessSignal.sigint.watch().listen((_) => kill());
      ProcessSignal.sigterm.watch().listen((_) => kill());
    }
  }

  Future<bool> isReady() async {
    try {
      final response = await http.get(Uri.parse('http://127.0.0.1:8000/'));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  void kill() {
    _process?.kill();
    _process = null;
  }
}
