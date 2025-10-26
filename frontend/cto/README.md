# CTO Flutter Application

A multi-platform Flutter app bootstrap that demonstrates Riverpod-driven state management, declarative navigation with go_router, and built-in localization for English and Arabic. The project is organised following clean architecture conventions and is ready for Android, iOS, web, and desktop targets.

## Prerequisites

- Flutter SDK 3.9.0 or newer (3.13+/3.16+ recommended)
- Dart SDK 3.9.0 or newer (bundled with Flutter)
- Platform-specific tooling (Android Studio/SDK, Xcode, Chrome, etc.) for the devices you intend to target

Verify your Flutter installation:

```bash
flutter --version
flutter doctor
```

## Getting Started

```bash
cd frontend/cto
flutter pub get
```

### Optional: Code Generation

Freezed/JSON serialisation hooks are already configured. When you add models that rely on generated code, run:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### Run the App

```bash
# List all available devices
flutter devices

# Run on the best available device
flutter run

# Run on a specific platform
flutter run -d chrome      # Web
flutter run -d linux       # Linux desktop
flutter run -d windows     # Windows desktop
flutter run -d macos       # macOS desktop
flutter run -d <device-id> # Android/iOS device or emulator
```

## Project Structure

```
lib/
├── main.dart                 # App entry point with ProviderScope and routing
├── l10n/                     # ARB localization resources + generated delegates
└── src/
    ├── core/                 # Cross-cutting concerns
    │   ├── constants/        # App-wide constants
    │   ├── localization/     # Locale state and helpers
    │   ├── router/           # go_router configuration and shell layout
    │   └── theme/            # Theme definitions and providers
    ├── data/                 # Data layer (models, repositories, providers)
    ├── features/             # Feature-first UI modules
    └── widgets/              # Reusable presentation widgets
```

## Key Capabilities

- **Riverpod** (`flutter_riverpod`, `hooks_riverpod`) for state management
- **go_router** shell routing with a global app bar and deep-link friendly navigation
- **Theming** with Material 3 light/dark palettes controllable at runtime
- **Localization** powered by `flutter_localizations` + ARB files for English/Arabic with RTL support
- **Networking** scaffolded via `dio` and repository/provider layers
- **Media & Files**: `video_player`, `just_audio`, and `file_picker` are pre-configured for future use
- **Responsive UI** with `responsive_framework`

## Localization Workflow

1. Update or add strings in `lib/l10n/app_en.arb` (source of truth) and mirror them in `lib/l10n/app_ar.arb`.
2. Regenerate localizations:
   ```bash
   flutter gen-l10n
   ```
3. Hot-reload/hot-restart to see the changes.

## Common Commands

```bash
flutter analyze            # Static analysis
flutter test               # Run test suite
flutter pub run build_runner build --delete-conflicting-outputs
flutter clean && flutter pub get
```

## Useful Links

- [Flutter documentation](https://docs.flutter.dev/)
- [Riverpod documentation](https://riverpod.dev/)
- [go_router package](https://pub.dev/packages/go_router)
- [Internationalization guide](https://docs.flutter.dev/development/accessibility-and-localization/internationalization)

This project is ready to be extended with new features, screens, and integrations while keeping a clean separation of concerns.
