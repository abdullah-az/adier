import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/dio_provider.dart';
import '../repositories/project_repository.dart';

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ProjectRepository(dio: dio);
});
