# Flutter Frontend Scaffold

This directory contains the Flutter application for the AI Video Editor platform. The project is structured for scalability with clear separations of concerns and tooling aligned to the wider product.

## Project Highlights

- **Architecture**: Source code is organised under `lib/src` with dedicated folders for `core`, `features`, `data`, and cross-cutting `widgets`.
- **Routing**: [`go_router`](https://pub.dev/packages/go_router) powers navigation with a shell layout and placeholder destinations for Dashboard, Workspace, and Settings flows.
- **State Management**: [`flutter_riverpod`](https://pub.dev/packages/flutter_riverpod) is configured globally with a lightweight service registry for dependency injection.
- **Theming**: Custom `AppTheme` provides Material 3 light/dark variants, typography via Google Fonts, and navigation styling.
- **Responsive**: Utility classes define desktop/tablet/mobile breakpoints with adaptive scaffolding for navigation rail/bottom bar experiences.
- **Flavors**: Dedicated entry points in `lib/main_<flavor>.dart` delegate to a common bootstrap with environment-specific configuration derived from assets under `assets/config/`.

## Getting Started

Install Flutter (3.22 or newer recommended) and run the following commands from the project root:

```bash
cd frontend
flutter pub get
flutter run --target lib/main_development.dart --dart-define APP_FLAVOR=development
```

For staging or production builds, swap the target file and `APP_FLAVOR` value (`staging`, `production`).

Static analysis can be executed with:

```bash
flutter analyze
```

Widget tests live under `test/` and can be run via `flutter test`.
