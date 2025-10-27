import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/src/data/models/user_model.dart';
import 'package:cto/src/data/repositories/user_repository.dart';

class _MockDio extends Mock implements Dio {}

void main() {
  late Dio dio;
  late UserRepository repository;

  setUp(() {
    dio = _MockDio();
    repository = UserRepository(dio: dio);
  });

  group('UserRepository', () {
    test('getUsers returns parsed users', () async {
      when(() => dio.get<List<dynamic>>('/users')).thenAnswer(
        (_) async => Response<List<dynamic>>(
          data: [
            {
              'id': '1',
              'name': 'Alice',
              'email': 'alice@example.com',
            },
          ],
          requestOptions: RequestOptions(path: '/users'),
        ),
      );

      final users = await repository.getUsers();

      expect(users, hasLength(1));
      expect(users.first, isA<UserModel>());
      expect(users.first.name, 'Alice');
    });

    test('getUser returns parsed user', () async {
      when(() => dio.get<Map<String, dynamic>>('/users/1')).thenAnswer(
        (_) async => Response<Map<String, dynamic>>(
          data: {
            'id': '1',
            'name': 'Alice',
            'email': 'alice@example.com',
          },
          requestOptions: RequestOptions(path: '/users/1'),
        ),
      );

      final user = await repository.getUser('1');

      expect(user.id, '1');
      expect(user.name, 'Alice');
    });

    test('propagates Dio errors as exceptions', () async {
      when(() => dio.get<Map<String, dynamic>>('/users/1')).thenThrow(
        DioException(requestOptions: RequestOptions(path: '/users/1')),
      );

      expect(
        () => repository.getUser('1'),
        throwsA(isA<Exception>()),
      );
    });
  });
}
