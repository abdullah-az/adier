import 'dart:convert';
import 'dart:typed_data';

import 'package:cto/src/data/models/user_model.dart';
import 'package:cto/src/data/repositories/user_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class CountingAdapter implements HttpClientAdapter {
  CountingAdapter(this._handler);

  final ResponseBody Function(RequestOptions options) _handler;
  final List<RequestOptions> requests = [];

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    return _handler(options);
  }
}

ResponseBody jsonResponse(dynamic data) {
  return ResponseBody.fromString(
    jsonEncode(data),
    200,
    headers: {
      Headers.contentTypeHeader: ['application/json'],
    },
  );
}

void main() {
  group('UserRepository', () {
    test('getUser fetches and caches user data', () async {
      final adapter = CountingAdapter((options) {
        expect(options.path, '/users/1');
        return jsonResponse({
          'id': '1',
          'name': 'Jane',
          'email': 'jane@example.com',
        });
      });

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost'))
        ..httpClientAdapter = adapter;
      final repository = UserRepository(dio: dio);

      final user = await repository.getUser('1');
      expect(user, isA<UserModel>());
      expect(user.name, 'Jane');
      expect(adapter.requests.length, 1);

      final cachedUser = await repository.getUser('1');
      expect(cachedUser, same(user));
      expect(adapter.requests.length, 1, reason: 'should use cache on second call');
    });

    test('forceRefresh bypasses cache', () async {
      var counter = 0;
      final adapter = CountingAdapter((options) {
        counter += 1;
        return jsonResponse({
          'id': '2',
          'name': 'User $counter',
          'email': 'user$counter@example.com',
        });
      });

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost'))
        ..httpClientAdapter = adapter;
      final repository = UserRepository(dio: dio);

      final first = await repository.getUser('2', forceRefresh: true);
      final second = await repository.getUser('2', forceRefresh: true);

      expect(first.name, isNot(second.name));
      expect(adapter.requests.length, 2);
    });

    test('getUsers caches list and hydrates individual cache', () async {
      final adapter = CountingAdapter((options) {
        if (options.path == '/users') {
          return jsonResponse([
            {
              'id': '10',
              'name': 'Alpha',
              'email': 'alpha@example.com',
            },
            {
              'id': '11',
              'name': 'Beta',
              'email': 'beta@example.com',
            },
          ]);
        }
        return jsonResponse({
          'id': options.path.split('/').last,
          'name': 'Fetched',
          'email': 'fetched@example.com',
        });
      });

      final dio = Dio(BaseOptions(baseUrl: 'http://localhost'))
        ..httpClientAdapter = adapter;
      final repository = UserRepository(dio: dio);

      final users = await repository.getUsers();
      expect(users.map((u) => u.id), ['10', '11']);
      expect(adapter.requests.length, 1);

      // Should use hydrated cache instead of making another request.
      final user = await repository.getUser('10');
      expect(user.name, 'Alpha');
      expect(adapter.requests.length, 1);

      // Force refresh should trigger another network call.
      await repository.getUsers(forceRefresh: true);
      expect(adapter.requests.length, 2);
    });
  });
}
