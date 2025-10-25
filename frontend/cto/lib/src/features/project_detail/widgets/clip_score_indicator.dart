import 'package:flutter/material.dart';

class ClipScoreIndicator extends StatelessWidget {
  const ClipScoreIndicator({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.tooltip,
  });

  final String label;
  final double value;
  final IconData? icon;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final normalized = value.clamp(0, 1);
    final color = _resolveColor(normalized, theme);
    final background = color.withOpacity(0.12);
    final text = theme.textTheme.bodyMedium?.copyWith(color: color);

    final chip = Chip(
      avatar: CircleAvatar(
        radius: 6,
        backgroundColor: color,
        child: icon == null
            ? null
            : Icon(
                icon,
                size: 12,
                color: theme.colorScheme.onPrimary,
              ),
      ),
      label: Text(
        '$label ${(normalized * 100).round()}%',
        style: text,
      ),
      backgroundColor: background,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
    );

    if (tooltip != null && tooltip!.isNotEmpty) {
      return Tooltip(
        message: tooltip!,
        child: chip,
      );
    }
    return chip;
  }

  Color _resolveColor(double value, ThemeData theme) {
    if (value >= 0.8) {
      return theme.colorScheme.primary;
    }
    if (value >= 0.6) {
      return theme.colorScheme.tertiary;
    }
    return theme.colorScheme.error;
  }
}
