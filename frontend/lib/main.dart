import 'package:flutter/widgets.dart';

import 'src/core/bootstrap.dart';
import 'src/core/config/app_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  const flavorName = String.fromEnvironment('APP_FLAVOR', defaultValue: 'development');
  final flavor = AppFlavorX.fromName(flavorName);

  await bootstrap(flavor: flavor);
}
