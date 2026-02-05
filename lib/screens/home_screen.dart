import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';

import '../api/api_client.dart';
import '../services/backend_service.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(statsProvider);
    final logsAsync = ref.watch(logsProvider);
    final techFont = GoogleFonts.jetBrainsMono();

    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          'OPEN-METRIC // COMMAND',
          style: techFont.copyWith(fontWeight: FontWeight.bold, color: Colors.white),
        ),
        actions: [
          _BackendStatusChip(techFont: techFont),
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white70),
            tooltip: 'Settings',
            onPressed: () => context.push('/settings'),
          ),
          IconButton(
            icon: const Icon(Icons.psychology, color: Colors.purpleAccent),
            tooltip: 'Access Brain',
            onPressed: () => context.push('/brain'),
          ),
          IconButton(
            icon: const Icon(Icons.list_alt, color: Colors.greenAccent),
            tooltip: 'Mission Queue',
            onPressed: () => context.push('/queue'),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: Colors.greenAccent,
        backgroundColor: const Color(0xFF1E1E1E),
        onRefresh: () async {
          await Future.wait([
            ref.refresh(statsProvider.future),
            ref.refresh(logsProvider.future),
          ]);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('ENGAGEMENT VELOCITY', style: techFont.copyWith(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 10),
              Container(
                height: 200,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF161616),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF333333)),
                ),
                child: _buildEngagementChart(),
              ),
              const SizedBox(height: 24),
              statsAsync.when(
                data: (data) {
                  final reachText = (data['reach'] ?? data['Reach'] ?? '0').toString();
                  final engageText = (data['engagement_score'] ?? data['Engagement'] ?? '0').toString();
                  final likesText = (data['likes'] ?? data['Likes'] ?? '0').toString();
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildGauge('REACH', 0.75, Colors.blueAccent, reachText),
                      _buildGauge('ENGAGE', 0.4, Colors.orangeAccent, engageText),
                      _buildGauge('LIKES', 0.98, Colors.greenAccent, likesText),
                    ],
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (e, s) => Text('Offline', style: techFont.copyWith(color: Colors.redAccent)),
              ),
              const SizedBox(height: 24),
              Text('OPERATIONS', style: techFont.copyWith(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 10),
              Row(
                children: [
                  _NeonButton(
                    label: 'HARVEST',
                    icon: Icons.download,
                    color: Colors.blue,
                    onTap: () {
                      triggerHarvest();
                    },
                  ),
                  const SizedBox(width: 10),
                  _NeonButton(
                    label: 'FILL QUEUE',
                    icon: Icons.upload,
                    color: Colors.orange,
                    onTap: () => triggerAction('fill_queue'),
                  ),
                  const SizedBox(width: 10),
                  _NeonButton(
                    label: 'SYNC BRAIN',
                    icon: Icons.sync,
                    color: Colors.purple,
                    onTap: () {
                      syncBrain();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Text('SYSTEM LOGS', style: techFont.copyWith(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 10),
              Container(
                height: 180,
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF080808),
                  border: Border.all(color: const Color(0xFF222222)),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: logsAsync.when(
                  data: (logs) => ListView.builder(
                    reverse: true,
                    itemCount: logs.length,
                    itemBuilder: (ctx, i) => Text(
                      '> ${logs[logs.length - 1 - i]}',
                      style: GoogleFonts.firaCode(color: Colors.greenAccent.withValues(alpha: 0.8), fontSize: 11),
                    ),
                  ),
                  loading: () => const Center(child: CircularProgressIndicator(color: Colors.green)),
                  error: (e, s) => Text('Connection Lost.', style: TextStyle(color: Colors.red.shade400)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEngagementChart() {
    return LineChart(
      LineChartData(
        gridData: FlGridData(show: false),
        titlesData: FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        minX: 0,
        maxX: 6,
        minY: 0,
        maxY: 6,
        lineBarsData: [
          LineChartBarData(
            spots: const [
              FlSpot(0, 3),
              FlSpot(1, 1),
              FlSpot(2, 4),
              FlSpot(3, 2),
              FlSpot(4, 5),
              FlSpot(5, 3),
              FlSpot(6, 4),
            ],
            isCurved: true,
            color: Colors.cyanAccent,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(show: false),
            belowBarData: BarAreaData(show: true, color: Colors.cyanAccent.withValues(alpha: 0.1)),
          ),
        ],
      ),
    );
  }

  Widget _buildGauge(String label, double percent, Color color, String valueText) {
    return CircularPercentIndicator(
      radius: 45.0,
      lineWidth: 5.0,
      percent: percent,
      center: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            valueText,
            style: GoogleFonts.jetBrainsMono(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 12),
          ),
          Text(label, style: GoogleFonts.jetBrainsMono(fontSize: 8, color: Colors.grey)),
        ],
      ),
      progressColor: color,
      backgroundColor: const Color(0xFF222222),
      circularStrokeCap: CircularStrokeCap.round,
      animation: true,
    );
  }
}

class _BackendStatusChip extends StatelessWidget {
  const _BackendStatusChip({required this.techFont});

  final TextStyle techFont;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<bool>(
      stream: Stream.periodic(const Duration(seconds: 1))
          .asyncMap((_) => BackendService.instance.isReady()),
      initialData: false,
      builder: (context, snapshot) {
        final isOnline = snapshot.data ?? false;
        final color = isOnline ? Colors.greenAccent : Colors.redAccent;
        final label = isOnline ? 'CORE ONLINE' : 'CORE OFFLINE';
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: color.withValues(alpha: 0.8)),
            ),
            child: Text(
              label,
              style: techFont.copyWith(fontSize: 10, color: color),
            ),
          ),
        );
      },
    );
  }
}

class _NeonButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _NeonButton({required this.label, required this.icon, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              border: Border.all(color: color.withValues(alpha: 0.5)),
              borderRadius: BorderRadius.circular(8),
              color: color.withValues(alpha: 0.05),
            ),
            child: Column(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(height: 6),
                Text(
                  label,
                  style: GoogleFonts.jetBrainsMono(color: color, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
