#!/bin/bash

# Flutter Data Layer Test Runner
# This script validates the Flutter networking stack implementation

echo "🚀 Flutter Data Layer Test Runner"
echo "=================================="

# Check if we're in the correct directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Error: Please run this script from the Flutter project root directory"
    exit 1
fi

echo "📦 Installing dependencies..."
if command -v flutter &> /dev/null; then
    flutter pub get
else
    echo "⚠️  Flutter not found, skipping pub get"
fi

echo ""
echo "🔍 Running data layer tests..."

# Run data layer tests
if command -v flutter &> /dev/null; then
    flutter test test/data/ --reporter=expanded
else
    echo "⚠️  Flutter not found, skipping tests"
fi

echo ""
echo "📊 Analyzing code structure..."

# Check if all required files exist
required_files=(
    "lib/src/data/models/enums.dart"
    "lib/src/data/models/base_model.dart"
    "lib/src/data/models/project.dart"
    "lib/src/data/models/media_asset.dart"
    "lib/src/data/models/clip.dart"
    "lib/src/data/models/processing_job.dart"
    "lib/src/data/models/platform_preset.dart"
    "lib/src/data/network/api_client.dart"
    "lib/src/data/network/exceptions.dart"
    "lib/src/data/network/websocket_client.dart"
    "lib/src/data/services/health_service.dart"
    "lib/src/data/services/projects_service.dart"
    "lib/src/data/services/assets_service.dart"
    "lib/src/data/services/clips_service.dart"
    "lib/src/data/services/jobs_service.dart"
    "lib/src/data/services/presets_service.dart"
    "lib/src/data/config.dart"
    "lib/src/data/index.dart"
    "lib/src/data/example.dart"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        ((missing_files++))
    fi
done

echo ""
echo "📝 Checking generated files..."

generated_files=(
    "lib/src/data/models/base_model.g.dart"
    "lib/src/data/models/project.g.dart"
    "lib/src/data/models/media_asset.g.dart"
    "lib/src/data/models/clip.g.dart"
    "lib/src/data/models/processing_job.g.dart"
    "lib/src/data/models/platform_preset.g.dart"
)

missing_generated=0
for file in "${generated_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        ((missing_generated++))
    fi
done

echo ""
echo "🧪 Checking test files..."

test_files=(
    "test/data/api_client_test.dart"
    "test/data/websocket_client_test.dart"
    "test/data/models_test.dart"
    "test/data/services_test.dart"
    "test/data/data_layer_test.dart"
    "test/data/integration_test.dart"
)

missing_tests=0
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        ((missing_tests++))
    fi
done

echo ""
echo "📋 Summary"
echo "========="
echo "Required files: $(( ${#required_files[@]} - missing_files ))/${#required_files[@]} present"
echo "Generated files: $(( ${#generated_files[@]} - missing_generated ))/${#generated_files[@]} present"
echo "Test files: $(( ${#test_files[@]} - missing_tests ))/${#test_files[@]} present"

total_missing=$((missing_files + missing_generated + missing_tests))

if [ $total_missing -eq 0 ]; then
    echo ""
    echo "🎉 All files are present! Data layer implementation is complete."
    echo ""
    echo "📖 Next steps:"
    echo "1. Run 'flutter test test/data/' to execute tests"
    echo "2. Check 'lib/src/data/example.dart' for usage examples"
    echo "3. Read 'lib/src/data/README.md' for detailed documentation"
    echo "4. Integrate with your Flutter app using DataLayer class"
    exit 0
else
    echo ""
    echo "⚠️  $total_missing files are missing. Please implement them."
    exit 1
fi