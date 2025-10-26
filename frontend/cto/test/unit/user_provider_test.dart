import 'package:cto/src/data/models/user_model.dart';
import 'package:cto/src/data/providers/user_provider.dart';
import 'package:cto/src/data/repositories/user_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeUserRepository extends UserRepository {
  FakeUserRepository(this._users) : super(dio: Dio());

  final Map<String, UserModel> _users;

  @override
  Future<UserModel> getUser(String id, {bool forceRefresh = false}) async {
    final user = _users[id];
    if (user == null) {
      throw Exception('User not found');
    }
    return user;
  }

  @override
  Future<List<UserModel>> getUsers({bool forceRefresh = false}) async {
    return _users.values.toList(growable: false);
  }
}

void main() {
  group('User providers', () {
    late ProviderContainer container;

    setUp(() {
      final fakeRepository = FakeUserRepository({
        '1': const UserModel(id: '1', name: 'Alice', email: 'alice@example.com'),
        '2': const UserModel(id: '2', name: 'Bob', email: 'bob@example.com'),
      });

      container = ProviderContainer(
        overrides: [
          userRepositoryProvider.overrideWithValue(fakeRepository),
        ],
      );
    });

    tearDown(() {
      container.dispose();
    });

    test('userListProvider returns all users', () async {
      final users = await container.read(userListProvider.future);
      expect(users, hasLength(2));
      expect(users.first.name, 'Alice');
    });

    test('userProvider retrieves user by id', () async {
      final user = await container.read(userProvider('2').future);
      expect(user.email, 'bob@example.com');
    });
  });
}
