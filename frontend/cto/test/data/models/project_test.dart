import 'package:cto/src/data/models/project.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Project Model', () {
    test('should deserialize from JSON correctly', () {
      final json = {
        'id': 'proj_123',
        'name': 'Test Project',
        'description': 'A test project',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'metadata': {'key': 'value'},
      };

      final project = Project.fromJson(json);

      expect(project.id, 'proj_123');
      expect(project.name, 'Test Project');
      expect(project.description, 'A test project');
      expect(project.metadata, {'key': 'value'});
      expect(project.createdAt, DateTime.parse('2024-01-01T00:00:00Z'));
    });

    test('should serialize to JSON correctly', () {
      final project = Project(
        id: 'proj_123',
        name: 'Test Project',
        description: 'A test project',
        createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
        updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        metadata: {'key': 'value'},
      );

      final json = project.toJson();

      expect(json['id'], 'proj_123');
      expect(json['name'], 'Test Project');
      expect(json['description'], 'A test project');
      expect(json['metadata'], {'key': 'value'});
    });

    test('should handle null description and metadata', () {
      final json = {
        'id': 'proj_123',
        'name': 'Test Project',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final project = Project.fromJson(json);

      expect(project.description, isNull);
      expect(project.metadata, isNull);
    });
  });
}
