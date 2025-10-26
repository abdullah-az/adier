# CTO Flutter Application

A multi-platform Flutter application built with clean architecture, localization support, and modern state management.

## Features

- 🌍 **Multi-platform Support**: Android, iOS, Web, macOS, Windows, Linux
- 🏗️ **Clean Architecture**: Organized folder structure following clean architecture principles
- 🎨 **Material Design 3**: Modern UI with light and dark themes
- 🌐 **Internationalization**: English and Arabic localization support
- ⚡ **State Management**: Riverpod for predictable and testable state management
- 🧭 **Routing**: go_router for declarative navigation
- 🔌 **API Integration**: Dio HTTP client ready for REST API calls
- 🎬 **Media Support**: Video and audio playback capabilities
- 📱 **Responsive Design**: Adapts to different screen sizes

## Project Structure

```
lib/
├── main.dart                    # App entry point
├── l10n/                       # Localization ARB files
│   ├── app_en.arb             # English translations
│   └── app_ar.arb             # Arabic translations
└── src/
    ├── core/                   # Core app functionality
    │   ├── constants/         # App-wide constants
    │   ├── theme/            # Theme configuration and providers
    │   ├── router/           # Navigation configuration
    │   ├── localization/     # Locale management
    │   └── utils/            # Utility functions
    ├── features/              # Feature modules
    │   ├── home/             # Home page
    │   ├── auth/             # Authentication
    │   └── profile/          # User profile
    ├── data/                  # Data layer
    │   ├── models/           # Data models (Freezed)
    │   ├── repositories/     # Data repositories
    │   └── providers/        # Riverpod providers
    └── widgets/               # Shared widgets
```

## Prerequisites

### Required Software

- **Flutter SDK**: 3.35.7 or later
- **Dart SDK**: 3.9.2 or later (included with Flutter)
- **Git**: For version control

### Platform-Specific Requirements

#### Android
- Android Studio or Android SDK Command-line Tools
- Android SDK (API 21 or higher)
- Java Development Kit (JDK) 11 or later

#### iOS (macOS only)
- Xcode 15 or later
- CocoaPods

#### Web
- Chrome browser (for debugging)

#### Desktop (Linux, macOS, Windows)
- Platform-specific build tools (installed automatically by Flutter)

## Getting Started

### 1. Install Flutter

Follow the official Flutter installation guide for your platform:
https://docs.flutter.dev/get-started/install

### 2. Clone the Repository

```bash
git clone <repository-url>
cd frontend/cto
```

### 3. Install Dependencies

```bash
flutter pub get
```

### 4. Generate Code

Generate localization and Freezed files:

```bash
# Generate localizations
flutter gen-l10n

# Generate model code (Freezed, JSON serialization)
flutter pub run build_runner build --delete-conflicting-outputs
```

### 5. Run the Application

```bash
# List available devices
flutter devices

# Run on default device
flutter run

# Run on specific platform
flutter run -d chrome          # Web
flutter run -d linux           # Linux desktop
flutter run -d windows         # Windows desktop
flutter run -d macos           # macOS desktop
flutter run -d <device-id>     # Android/iOS device
```

## Development Commands

### Code Generation

```bash
# Watch mode - automatically regenerates on file changes
flutter pub run build_runner watch --delete-conflicting-outputs

# One-time generation
flutter pub run build_runner build --delete-conflicting-outputs

# Clean generated files
flutter pub run build_runner clean
```

### Localization

```bash
# Generate localization files from ARB files
flutter gen-l10n
```

To add new translations:
1. Edit `lib/l10n/app_en.arb` (English - template)
2. Edit `lib/l10n/app_ar.arb` (Arabic)
3. Run `flutter gen-l10n`

### Testing

```bash
# Run fast unit and widget tests (includes goldens)
flutter test

# Update golden references when layouts change
flutter test --update-goldens

# Execute integration test suite
flutter test integration_test
```

### Localization Validation

```bash
# Ensure ARB files stay in sync across locales
dart run tool/check_localizations.dart
```

### QA Checklist

- [ ] All unit, widget (including golden), and integration tests pass (`flutter test` / `flutter test integration_test`).
- [ ] Localization script reports no missing keys (`dart run tool/check_localizations.dart`).
- [ ] Upload workflow renders via `ListView.builder` and allows progressing uploads.
- [ ] Timeline editor supports drag-and-drop reordering and export confirmation.
- [ ] Subtitle editor accepts valid time ranges and blocks invalid submissions.
- [ ] Export dialog presents format, resolution, and subtitle options.

### Performance Notes

- Heavy lists (home quick actions, uploads, timeline, subtitles, export checklist) use `ListView.builder`/`ListView.separated` to avoid unnecessary widget churn.
- `UserRepository` now caches list and detail requests to reduce duplicate `Dio` calls; pass `forceRefresh: true` to bust the cache when needed.
- Timeline math utilities centralize duration calculations to prevent recomputing offsets during drag operations.
- Profiled the editor flow with Flutter DevTools (simulated 60 fps timeline; no jank observed under sample data).

### Linting and Formatting

```bash
# Analyze code for issues
flutter analyze

# Format code
dart format lib/ test/

# Fix auto-fixable lint issues
dart fix --apply
```

### Build Commands

```bash
# Android APK (debug)
flutter build apk

# Android App Bundle (release)
flutter build appbundle

# iOS (requires macOS)
flutter build ios

# Web
flutter build web

# Linux
flutter build linux

# Windows (requires Windows)
flutter build windows

# macOS (requires macOS)
flutter build macos
```

## Architecture Overview

### Clean Architecture Layers

1. **Presentation Layer** (`lib/src/features/`)
   - UI components (pages, widgets)
   - State management with Riverpod
   - User interaction handling

2. **Domain Layer** (`lib/src/data/models/`)
   - Business logic
   - Data models (using Freezed for immutability)
   - Entity definitions

3. **Data Layer** (`lib/src/data/repositories/`)
   - Repository implementations
   - API communication (Dio)
   - Data source abstractions

### State Management

The app uses **Riverpod** for state management:

- `Provider`: For immutable dependencies (repositories, services)
- `StateNotifierProvider`: For mutable state (theme, locale)
- `FutureProvider`: For async data fetching
- `StreamProvider`: For real-time data streams

### Routing

Navigation is handled by **go_router**:

- Declarative routing configuration
- Deep linking support
- Type-safe navigation
- Route guards for authentication

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `flutter_riverpod` | State management |
| `hooks_riverpod` | Riverpod with Flutter Hooks |
| `go_router` | Declarative routing |
| `dio` | HTTP client |
| `freezed` | Code generation for immutable classes |
| `json_serializable` | JSON serialization |
| `intl` | Internationalization |
| `video_player` | Video playback |
| `just_audio` | Audio playback |
| `file_picker` | File selection |
| `responsive_framework` | Responsive design utilities |

## Configuration

### API Base URL

Update the API endpoint in `lib/src/core/constants/app_constants.dart`:

```dart
static const String apiBaseUrl = 'https://your-api.com/api';
```

### App Name and Version

Edit `pubspec.yaml`:

```yaml
name: cto
description: "Your app description"
version: 1.0.0+1
```

### Theme Customization

Modify theme colors in `lib/src/core/theme/app_theme.dart`:

```dart
colorScheme: ColorScheme.fromSeed(
  seedColor: Colors.blue,  // Change to your brand color
  brightness: Brightness.light,
),
```

## Troubleshooting

### Common Issues

#### "Waiting for another flutter command to release the startup lock"
```bash
rm -rf ~/.flutter-devtools/.flutter-devtools.lock
```

#### Build Runner Issues
```bash
flutter pub run build_runner clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

#### Localization Not Working
```bash
flutter clean
flutter gen-l10n
flutter pub get
```

#### Platform-Specific Build Errors

**Android:**
- Update `android/app/build.gradle` minSdkVersion to 21
- Ensure Android SDK is properly installed

**iOS:**
- Run `pod install` in `ios/` directory
- Clean build folder in Xcode

**Web:**
- Check CORS configuration on your API server

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Riverpod Documentation](https://riverpod.dev/)
- [Go Router Documentation](https://pub.dev/packages/go_router)
- [Material Design 3](https://m3.material.io/)
- [Freezed Package](https://pub.dev/packages/freezed)

## License

[Add your license information here]
