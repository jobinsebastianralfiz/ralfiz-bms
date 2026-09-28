import 'package:flutter/material.dart';

import 'main.dart';

class MessageBubble extends StatelessWidget {
  const MessageBubble({super.key, required this.message, required this.mine, required this.pending});
  final Message message;
  final bool mine;
  final bool pending;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final small = Theme.of(context).textTheme.labelSmall;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Column(crossAxisAlignment: mine ? CrossAxisAlignment.end : CrossAxisAlignment.start, children: [
          Container(
            constraints: const BoxConstraints(maxWidth: 280),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: mine ? scheme.primaryContainer : scheme.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              if (!mine) Text(message.senderName, style: small?.copyWith(color: scheme.primary)),
              Text(message.text),
            ]),
          ),
          if (pending) Text('Sending…', style: small),
        ]),
      ),
    );
  }
}
