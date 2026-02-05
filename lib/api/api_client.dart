import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

// For Windows desktop, use the local loopback address.
final String baseUrl = 'http://127.0.0.1:8000';
const String apiKey = String.fromEnvironment('OPEN_METRIC_API_KEY', defaultValue: '');

Map<String, String> _headers({bool json = false}) {
  final headers = <String, String>{};
  if (apiKey.isNotEmpty) {
    headers['X-API-Key'] = apiKey;
  }
  if (json) {
    headers['Content-Type'] = 'application/json';
  }
  return headers;
}

final statsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  try {
    final response = await http.get(Uri.parse('$baseUrl/stats'), headers: _headers());
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
  } catch (e) {
    // ignore: avoid_print
    print('Error fetching stats: $e');
  }
  return {};
});

final queueProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  try {
    final response = await http.get(Uri.parse('$baseUrl/queue'), headers: _headers());
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data is List) {
        return data;
      }
    }
  } catch (e) {
    // ignore: avoid_print
    print('Error fetching queue: $e');
  }
  return [];
});

final logsProvider = FutureProvider.autoDispose<List<String>>((ref) async {
  try {
    final response = await http.get(Uri.parse('$baseUrl/logs'), headers: _headers());
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data is Map) {
        final lines = data['lines'] ?? data['logs'];
        if (lines is List) {
          return lines.map((item) => item.toString()).toList();
        }
      }
    }
  } catch (e) {
    // ignore: avoid_print
    print('Error fetching logs: $e');
  }
  return ['System Offline... Check Connection.'];
});

final configProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return fetchConfigStatus();
});

Future<void> triggerAction(String endpoint) async {
  try {
    await http.post(Uri.parse('$baseUrl/action/$endpoint'), headers: _headers());
  } catch (e) {
    // ignore: avoid_print
    print('Action failed: $e');
  }
}

Future<bool> triggerHarvest() async {
  try {
    final response = await http.post(Uri.parse('$baseUrl/harvest'), headers: _headers());
    return response.statusCode == 200;
  } catch (e) {
    // ignore: avoid_print
    print('Harvest failed: $e');
    return false;
  }
}

Future<bool> addPost(String text) async {
  try {
    final response = await http.post(
      Uri.parse('$baseUrl/queue/add'),
      headers: _headers(json: true),
      body: json.encode({
        'text': text,
        'platforms': ['linkedin'],
        'status': 'pending',
      }),
    );
    return response.statusCode == 200;
  } catch (e) {
    // ignore: avoid_print
    print('Error adding post: $e');
    return false;
  }
}

Future<String> generateAiContent(String topic, {String tone = 'engaging'}) async {
  try {
    final response = await http.post(
      Uri.parse('$baseUrl/generate'),
      headers: _headers(json: true),
      body: json.encode({
        'topic': topic,
        'tone': tone,
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['content']?.toString() ?? 'Error: No content generated.';
    }
  } catch (e) {
    // ignore: avoid_print
    print('AI Generation Error: $e');
  }
  return 'Error: Could not reach AI brain.';
}

Future<bool> syncBrain() async {
  try {
    final response = await http.post(Uri.parse('$baseUrl/sync-drive'), headers: _headers());
    return response.statusCode == 200;
  } catch (e) {
    // ignore: avoid_print
    print('Brain sync failed: $e');
    return false;
  }
}

Future<Map<String, dynamic>> fetchConfigStatus() async {
  try {
    final response = await http.get(Uri.parse('$baseUrl/config'), headers: _headers());
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data is Map) {
        return data.map((key, value) => MapEntry(key.toString(), value));
      }
    }
  } catch (e) {
    // ignore: avoid_print
    print('Config fetch failed: $e');
  }
  return {};
}

Future<bool> saveConfig({
  String? metricoolEmail,
  String? metricoolPassword,
  String? driveId,
}) async {
  try {
    final response = await http.post(
      Uri.parse('$baseUrl/config'),
      headers: _headers(json: true),
      body: json.encode({
        'metricool_email': metricoolEmail,
        'metricool_password': metricoolPassword,
        'drive_id': driveId,
      }),
    );
    return response.statusCode == 200;
  } catch (e) {
    // ignore: avoid_print
    print('Config save failed: $e');
    return false;
  }
}

Future<bool> authMetricool() async {
  try {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/metricool'),
      headers: _headers(json: true),
    );
    return response.statusCode == 200;
  } catch (e) {
    // ignore: avoid_print
    print('Metricool auth failed: $e');
    return false;
  }
}
