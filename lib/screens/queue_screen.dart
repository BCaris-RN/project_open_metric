import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import '../api/api_client.dart';

class QueueScreen extends ConsumerWidget {
  const QueueScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueAsync = ref.watch(queueProvider);
    final techFont = GoogleFonts.jetBrainsMono();

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('MISSION QUEUE', style: techFont.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.blueAccent,
        child: const Icon(Icons.add, color: Colors.white),
        onPressed: () => _showAddPostDialog(context, ref),
      ),
      body: queueAsync.when(
        data: (queue) {
          if (queue.isEmpty) {
            return Center(child: Text('NO ACTIVE MISSIONS', style: techFont.copyWith(color: Colors.grey)));
          }
          return ListView.builder(
            itemCount: queue.length,
            padding: const EdgeInsets.all(8),
            itemBuilder: (ctx, i) {
              final item = queue[i];
              final map = item is Map ? item : null;
              final status = map?['status']?.toString() ?? 'pending';
              final text = map?['text']?.toString() ?? 'No text';
              final platforms = map?['platforms']?.toString() ?? 'unknown';
              return Card(
                color: const Color(0xFF1E1E1E),
                margin: const EdgeInsets.symmetric(vertical: 5),
                child: ListTile(
                  leading: Icon(
                    status == 'pending' ? Icons.hourglass_empty : Icons.check_circle,
                    color: status == 'pending' ? Colors.orange : Colors.green,
                  ),
                  title: Text(
                    text,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white),
                  ),
                  subtitle: Text(
                    'Platforms: $platforms',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, s) => Center(child: Text('Error: $e', style: const TextStyle(color: Colors.red))),
      ),
    );
  }

  void _showAddPostDialog(BuildContext context, WidgetRef ref) {
    final textController = TextEditingController();
    var isGenerating = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            backgroundColor: const Color(0xFF2C2C2C),
            title: Text('NEW MISSION', style: GoogleFonts.jetBrainsMono(color: Colors.white)),
            content: TextField(
              controller: textController,
              maxLines: 5,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: "Type a topic (e.g. 'AI Trends') and tap the sparkle.",
                hintStyle: const TextStyle(color: Colors.grey),
                border: const OutlineInputBorder(),
                filled: true,
                fillColor: const Color(0xFF1E1E1E),
                suffixIcon: isGenerating
                    ? const Padding(
                        padding: EdgeInsets.all(10),
                        child: SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : IconButton(
                        icon: const Icon(Icons.auto_awesome, color: Colors.purpleAccent),
                        tooltip: 'Generate with AI',
                        onPressed: () async {
                          final topic = textController.text.trim();
                          if (topic.isEmpty) {
                            return;
                          }
                          setState(() => isGenerating = true);
                          final generated = await generateAiContent(topic);
                          textController.text = generated;
                          setState(() => isGenerating = false);
                        },
                      ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('CANCEL', style: TextStyle(color: Colors.grey)),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent),
                onPressed: () async {
                  final text = textController.text.trim();
                  if (text.isEmpty) {
                    return;
                  }
                  final success = await addPost(text);
                  if (!context.mounted) {
                    return;
                  }
                  if (success) {
                    Navigator.pop(ctx);
                    ref.invalidate(queueProvider);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Mission added to queue.')),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Failed to add post. Check connection.')),
                    );
                  }
                },
                child: const Text('SCHEDULE', style: TextStyle(color: Colors.white)),
              ),
            ],
          );
        },
      ),
    );
  }
}
