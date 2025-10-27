import 'package:cto/src/data/api/api_client.dart';
import 'package:cto/src/data/errors/api_failure.dart';
import 'package:cto/src/data/repositories/project_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';

void main() {
  late Dio dio;
  late DioAdapter dioAdapter;
  late ProjectRepository repository;

  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000/api'));
    dioAdapter = DioAdapter(dio: dio);
    final apiClient = ApiClient(dio);
    repository = ProjectRepository(apiClient);
  });

  group('ProjectRepository', () {
    group('getProjects', () {
      test('returns list of projects on success', () async {
        final mockData = [
          {
            'id': 'proj_1',
            'name': 'Project 1',
            'description': 'First project',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
          },
          {
            'id': 'proj_2',
            'name': 'Project 2',
            'created_at': '2024-01-02T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
          },
        ];

        dioAdapter.onGet(
          '/projects',
          (server) => server.reply(200, mockData),
        );

        final projects = await repository.getProjects();

        expect(projects.length, 2);
        expect(projects[0].id, 'proj_1');
        expect(projects[0].name, 'Project 1');
        expect(projects[1].id, 'proj_2');
      });

      test('throws error on failure', () async {
        dioAdapter.onGet(
          '/projects',
          (server) => server.reply(500, {'message': 'Server error'}),
        );

        expect(
          () => repository.getProjects(),
          throwsA(isA<ServerFailure>()),
        );
      });
    });

    group('getProject', () {
      test('returns project on success', () async {
        final mockData = {
          'id': 'proj_1',
          'name': 'Project 1',
          'description': 'First project',
          'created_at': '2024-01-01T00:00:00Z',
          'updated_at': '2024-01-01T00:00:00Z',
        };

        dioAdapter.onGet(
          '/projects/proj_1',
          (server) => server.reply(200, mockData),
        );

        final project = await repository.getProject('proj_1');

        expect(project.id, 'proj_1');
        expect(project.name, 'Project 1');
        expect(project.description, 'First project');
      });

      test('throws NotFoundFailure on 404', () async {
        dioAdapter.onGet(
          '/projects/invalid_id',
          (server) => server.reply(404, {'message': 'Project not found'}),
        );

        expect(
          () => repository.getProject('invalid_id'),
          throwsA(isA<NotFoundFailure>()),
        );
      });
    });

    group('createProject', () {
      test('creates project successfully', () async {
        final requestData = {
          'name': 'New Project',
          'description': 'A new project',
        };

        final responseData = {
          'id': 'proj_new',
          'name': 'New Project',
          'description': 'A new project',
          'created_at': '2024-01-01T00:00:00Z',
          'updated_at': '2024-01-01T00:00:00Z',
        };

        dioAdapter.onPost(
          '/projects',
          (server) => server.reply(200, responseData),
          data: requestData,
        );

        final project = await repository.createProject(
          name: 'New Project',
          description: 'A new project',
        );

        expect(project.id, 'proj_new');
        expect(project.name, 'New Project');
      });
    });

    group('deleteProject', () {
      test('deletes project successfully', () async {
        dioAdapter.onDelete(
          '/projects/proj_1',
          (server) => server.reply(204, null),
        );

        expect(
          () => repository.deleteProject('proj_1'),
          completes,
        );
      });
    });

    group('getProjectVideos', () {
      test('returns list of video assets', () async {
        final mockData = [
          {
            'id': 'asset_1',
            'project_id': 'proj_1',
            'filename': 'video1.mp4',
            'original_filename': 'video1.mp4',
            'relative_path': 'uploads/proj_1/video1.mp4',
            'checksum': 'abc123',
            'size_bytes': 1048576,
            'mime_type': 'video/mp4',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
          },
        ];

        dioAdapter.onGet(
          '/projects/proj_1/videos',
          (server) => server.reply(200, mockData),
        );

        final videos = await repository.getProjectVideos('proj_1');

        expect(videos.length, 1);
        expect(videos[0].id, 'asset_1');
        expect(videos[0].filename, 'video1.mp4');
      });
    });
  });
}
