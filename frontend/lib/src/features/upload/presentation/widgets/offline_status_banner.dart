import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class OfflineStatusBanner extends StatelessWidget {
  const OfflineStatusBanner({
    super.key,
    required this.visible,
    required this.l10n,
  });

  final bool visible;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    if (!visible) {
      return const SizedBox.shrink();
    }

    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Card(
        color: theme.colorScheme.errorContainer.withOpacity(0.75),
        elevation: 0,
        child: ListTile(
          leading: Icon(Icons.wifi_off_rounded, color: theme.colorScheme.onErrorContainer),
          title: Text(
            l10n.uploadOfflineBannerMessage,
            style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onErrorContainer),
          ),
        ),
      ),
    );
  }
}
