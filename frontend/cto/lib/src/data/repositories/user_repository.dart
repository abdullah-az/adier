import 'package:dio/dio.dart';
import '../models/user_model.dart';
import '../../core/constants/app_constants.dart';

class UserRepository {
  final Dio _dio;

  UserRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  Future<UserModel> getUser(String id) async {
    try {
      final response = await _dio.get('/users/$id');
      return UserModel.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load user: $e');
    }
  }

  Future<List<UserModel>> getUsers() async {
    try {
      final response = await _dio.get('/users');
      final List<dynamic> data = response.data;
      return data.map((json) => UserModel.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load users: $e');
    }
  }
}
