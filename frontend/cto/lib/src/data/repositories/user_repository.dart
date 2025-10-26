import 'package:dio/dio.dart';
import '../models/user_model.dart';
import '../../core/constants/app_constants.dart';

class UserRepository {
  final Dio _dio;
  final Map<String, UserModel> _userCache = {};
  List<UserModel>? _usersCache;

  UserRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  Future<UserModel> getUser(String id, {bool forceRefresh = false}) async {
    if (!forceRefresh && _userCache.containsKey(id)) {
      return _userCache[id]!;
    }

    try {
      final response = await _dio.get('/users/$id');
      final user = UserModel.fromJson(response.data);
      _userCache[id] = user;
      return user;
    } catch (e) {
      throw Exception('Failed to load user: $e');
    }
  }

  Future<List<UserModel>> getUsers({bool forceRefresh = false}) async {
    if (!forceRefresh && _usersCache != null) {
      return _usersCache!;
    }

    try {
      final response = await _dio.get('/users');
      final List<dynamic> data = response.data;
      final users = data.map((json) => UserModel.fromJson(json)).toList();
      _usersCache = users;
      for (final user in users) {
        _userCache[user.id] = user;
      }
      return users;
    } catch (e) {
      throw Exception('Failed to load users: $e');
    }
  }
}
