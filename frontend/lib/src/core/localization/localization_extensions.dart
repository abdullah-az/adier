import 'package:flutter_gen/gen_l10n/app_localizations.dart';

import '../config/app_config.dart';

extension AppFlavorLocalization on AppFlavor {
  String localizedLabel(AppLocalizations l10n) => switch (this) {
        AppFlavor.development => l10n.flavorDevelopment,
        AppFlavor.staging => l10n.flavorStaging,
        AppFlavor.production => l10n.flavorProduction,
      };
}
