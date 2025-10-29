import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

import '../../../core/config/app_config.dart';
import '../../../core/localization/localization_extensions.dart';
import '../../../core/responsive/responsive_layout.dart';
import '../../../widgets/app_logo.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(appConfigProvider);

    return ResponsiveLayout(
      mobile: (context) => _DashboardView(config: config),
      tablet: (context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: _DashboardView(config: config),
        ),
      ),
      desktop: (context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 960),
          child: _DashboardView(config: config),
        ),
      ),
    );
  }
}

class _DashboardView extends StatelessWidget {
  const _DashboardView({required this.config});

  final AppConfig config;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context)!;
    final flavorLabel = config.flavor.localizedLabel(l10n);

    return ListView(
      padding: const EdgeInsets.all(24),
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const AppLogo(),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(l10n.appTitle, style: theme.textTheme.headlineMedium),
                  const SizedBox(height: 4),
                  Text(
                    l10n.dashboardEnvironment(flavorLabel),
                    style: theme.textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Text(
          l10n.dashboardWelcome,
          style: theme.textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        Text(
          l10n.dashboardDescription,
          style: theme.textTheme.bodyLarge,
        ),
        const SizedBox(height: 24),
        Wrap(
          spacing: 16,
          runSpacing: 16,
          children: <Widget>[
            _InfoCard(
              title: l10n.dashboardCardGenerationTitle,
              message: l10n.dashboardCardGenerationMessage,
            ),
            _InfoCard(
              title: l10n.dashboardCardSchedulingTitle,
              message: l10n.dashboardCardSchedulingMessage,
            ),
            _InfoCard(
              title: l10n.dashboardCardInsightsTitle,
              message: l10n.dashboardCardInsightsMessage,
            ),
          ],
        ),
      ],
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SizedBox(
      width: 280,
      child: Card(
        elevation: 0,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(message, style: theme.textTheme.bodyMedium),
            ],
          ),
        ),
      ),
    );
  }
}
