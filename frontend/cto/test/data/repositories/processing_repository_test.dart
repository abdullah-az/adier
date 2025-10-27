import 'package:cto/src/data/api/api_client.dart';
import 'package:cto/src/data/models/export_job.dart';
import 'package:cto/src/data/models/timeline_clip.dart';
import 'package:cto/src/data/repositories/processing_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';

void main() {
  late Dio dio;
  late DioAdapter dioAdapter;
  late ProcessingRepository repository;

  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000/api'));
    dioAdapter = DioAdapter(dio: dio);
    repository = ProcessingRepository(ApiClient(dio));
  });

  group('ProcessingRepository', () {
    group('createJob', () {
      test('creates job successfully', () async {
        final requestData = {
          'job_type': 'export',
          'payload': {'clips': []},
        };

        final responseData = {
          'id': 'job_1',
          'project_id': 'proj_1',
          'job_type': 'export',
          'status': 'queued',
          'progress': 0.0,
          'attempts': 0,
          'max_attempts': 3,
          'retry_delay_seconds': 5.0,
          'payload': {'clips': []},
          'result': {},
          'logs': [],
          'created_at': '2024-01-01T00:00:00Z',
          'updated_at': '2024-01-01T00:00:00Z',
        };

        dioAdapter.onPost(
          '/projects/proj_1/jobs',
          (server) => server.reply(200, responseData),
          data: requestData,
        );

        final job = await repository.createJob(
          projectId: 'proj_1',
          jobType: 'export',
          payload: {'clips': []},
        );

        expect(job.id, 'job_1');
        expect(job.projectId, 'proj_1');
        expect(job.status, ExportJobStatus.queued);
      });
    });

    group('listJobs', () {
      test('returns list of jobs', () async {
        final responseData = [
          {
            'id': 'job_1',
            'project_id': 'proj_1',
            'job_type': 'export',
            'status': 'completed',
            'progress': 100.0,
            'attempts': 1,
            'max_attempts': 3,
            'retry_delay_seconds': 5.0,
            'payload': {'clips': []},
            'result': {},
            'logs': [],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
          },
        ];

        dioAdapter.onGet(
          '/projects/proj_1/jobs',
          (server) => server.reply(200, responseData),
        );

        final jobs = await repository.listJobs('proj_1');

        expect(jobs.length, 1);
        expect(jobs[0].id, 'job_1');
        expect(jobs[0].status, ExportJobStatus.completed);
      });
    });

    group('submitExportJob', () {
      test('submits export job successfully', () async {
        final payload = {
          'clips': [
            {
              'asset_id': 'asset_1',
              'in_point': 0.0,
              'out_point': 5.0,
              'include_audio': true,
            }
          ]
        };

        final responseData = {
          'id': 'job_2',
          'project_id': 'proj_1',
          'job_type': 'export',
          'status': 'queued',
          'progress': 0.0,
          'attempts': 0,
          'max_attempts': 3,
          'retry_delay_seconds': 5.0,
          'payload': payload,
          'result': {},
          'logs': [],
          'created_at': '2024-01-01T00:00:00Z',
          'updated_at': '2024-01-01T00:00:00Z',
        };

        dioAdapter.onPost(
          '/projects/proj_1/jobs',
          (server) => server.reply(200, responseData),
          data: {
            'job_type': 'export',
            'payload': payload,
          },
        );

        final clip = TimelineClip(
          assetId: 'asset_1',
          inPoint: 0.0,
          outPoint: 5.0,
          includeAudio: true,
          transition: null,
          subtitles: null,
          watermark: null,
        );

        final job = await repository.submitExportJob(
          projectId: 'proj_1',
          request: TimelineCompositionRequest(
            clips: [clip],
          ),
        );

        expect(job.id, 'job_2');
        expect(job.status, ExportJobStatus.queued);
      });
    });
  });
}
