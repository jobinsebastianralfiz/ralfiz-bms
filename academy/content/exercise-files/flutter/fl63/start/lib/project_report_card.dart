import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

typedef ProjectReport = ({int total, int done, int open, bool posted, bool slackConfigured});

class ProjectReportCard extends StatefulWidget {
  const ProjectReportCard({super.key, required this.projectId});
  final String projectId;
  @override
  State<ProjectReportCard> createState() => _ProjectReportCardState();
}

class _ProjectReportCardState extends State<ProjectReportCard> {
  ProjectReport? _report;
  String? _error;
  bool _loading = false;

  Future<void> _send() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // TODO(1): final res = await Supabase.instance.client.functions
      //   .invoke('project-report', body: {'projectId': widget.projectId});
      final Object? data = null;

      // TODO(2): replace this check with a map pattern on res.data:
      // if (res.data case {'total': int total, 'done': int done, 'open': int open,
      //     'posted': bool posted, 'slackConfigured': bool slackConfigured}) { ... }
      if (data == null) {
        setState(() => _error = 'TODO(1) and TODO(2)');
      }
      // TODO(3): add "on FunctionException catch (e)" here (use a local
      // status variable): 401 -> 'Please sign in again.',
      // otherwise 'Report failed (' + status.toString() + ').'
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _stat(String value, String label, {Color? color}) => Column(children: [
        Text(value, style: Theme.of(context).textTheme.headlineMedium
            ?.copyWith(fontWeight: FontWeight.bold, color: color)),
        Text(label, style: Theme.of(context).textTheme.labelMedium),
      ]);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final report = _report;
    final error = _error;
    return SafeArea(
      child: Card(
        margin: const EdgeInsets.all(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12,
            children: [
              Text('Weekly report', style: theme.textTheme.titleLarge),
              if (_loading) const LinearProgressIndicator(),
              if (report != null) ...[
                Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
                  _stat(report.total.toString(), 'Total'),
                  _stat(report.done.toString(), 'Done', color: theme.colorScheme.primary),
                  _stat(report.open.toString(), 'Open'),
                ]),
                Text(report.posted
                    ? 'Posted to Slack'
                    : report.slackConfigured ? 'Slack did not accept the post' : 'Slack not configured'),
              ],
              if (error != null) Text(error, style: TextStyle(color: theme.colorScheme.error)),
              FilledButton.icon(
                onPressed: _loading ? null : _send,
                icon: const Icon(Icons.send),
                label: const Text('Send report'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Keeps the supabase_flutter import used until you finish TODO(1).
// ignore: unused_element
SupabaseClient _client() => Supabase.instance.client;
