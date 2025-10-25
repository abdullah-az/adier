import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/user_repository.dart';
import '../models/user_model.dart';

final userRepositoryProvider = Provider<UserRepository>((ref) {
  return UserRepository();
});

final userListProvider = FutureProvider<List<UserModel>>((ref) async {
  final repository = ref.read(userRepositoryProvider);
  return repository.getUsers();
});

final userProvider = FutureProvider.family<UserModel, String>((ref, id) async {
  final repository = ref.read(userRepositoryProvider);
  return repository.getUser(id);
});
