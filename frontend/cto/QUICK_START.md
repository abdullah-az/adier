# Quick Start Guide

Get the CTO Flutter app running in 5 minutes!

## Prerequisites

- **Flutter SDK 3.35.7+** - [Install Flutter](https://docs.flutter.dev/get-started/install)
- **Git** - For cloning the repository
- Platform-specific tools (see below)

## Platform Setup

### Android Development
```bash
# Install Android Studio or Android SDK Command-line Tools
# Configure Android SDK in Flutter
flutter config --android-sdk /path/to/android/sdk
```

### iOS Development (macOS only)
```bash
# Install Xcode from App Store
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
```

### Linux Desktop
```bash
sudo apt-get install clang cmake ninja-build pkg-config libgtk-3-dev
```

### Windows Desktop
```powershell
# No additional setup needed
# Visual Studio 2019 or later recommended
```

### Web
```bash
# Chrome browser required for debugging
flutter config --enable-web
```

## Installation

### 1. Clone & Navigate
```bash
cd frontend/cto
```

### 2. Install Dependencies
```bash
flutter pub get
```

### 3. Generate Code
```bash
# Generate localization files
flutter gen-l10n

# Generate model code (Freezed, JSON serialization)
flutter pub run build_runner build --delete-conflicting-outputs
```

## Running the App

### Check Available Devices
```bash
flutter devices
```

### Run on Default Device
```bash
flutter run
```

### Run on Specific Platform
```bash
# Android emulator or device
flutter run -d android

# iOS simulator or device (macOS only)
flutter run -d ios

# Chrome (web)
flutter run -d chrome

# Linux desktop
flutter run -d linux

# Windows desktop (Windows only)
flutter run -d windows

# macOS desktop (macOS only)
flutter run -d macos
```

## Hot Reload

While the app is running:
- Press `r` - Hot reload (preserves state)
- Press `R` - Hot restart (resets state)
- Press `q` - Quit

## Key Features to Try

### 1. Theme Toggle
Click the theme icon in the top-right to switch between light and dark mode.

### 2. Language Toggle
Click the language icon to switch between English and Arabic.

### 3. Navigation
- Click "Auth" button to navigate to authentication page
- Click "Profile" button to navigate to profile page
- Use back button or browser back to return

## Development Workflow

### Watching for Changes (Auto Code Generation)
```bash
flutter pub run build_runner watch --delete-conflicting-outputs
```
Keep this running in a separate terminal while developing.

### Running Tests
```bash
flutter test
```

### Code Analysis
```bash
flutter analyze
```

### Format Code
```bash
dart format lib/ test/
```

## Troubleshooting

### "No devices found"
```bash
# For Android
flutter emulators  # List available emulators
flutter emulators --launch <emulator-id>

# For iOS
open -a Simulator

# For Web
# Just run: flutter run -d chrome
```

### "Build failed" on Android
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

### "Pod install failed" on iOS
```bash
cd ios
pod deintegrate
pod install
cd ..
```

### Localization not working
```bash
flutter clean
flutter pub get
flutter gen-l10n
```

## Project Structure Overview

```
lib/
├── main.dart              # App entry point
├── l10n/                  # Localization (English & Arabic)
└── src/
    ├── core/             # App infrastructure
    │   ├── constants/    # App constants
    │   ├── theme/        # Themes & providers
    │   ├── router/       # Navigation config
    │   └── localization/ # Locale management
    ├── features/         # Feature modules
    │   ├── home/         # Home page
    │   ├── auth/         # Authentication
    │   └── profile/      # User profile
    ├── data/            # Data layer
    │   ├── models/      # Data models
    │   ├── repositories/# Data access
    │   └── providers/   # Riverpod providers
    └── widgets/         # Shared widgets
```

## Next Steps

1. **Read ARCHITECTURE.md** - Understand the app structure
2. **Read README.md** - Full documentation
3. **Explore the code** - Start with `lib/main.dart`
4. **Add your features** - Follow the existing patterns

## Useful Commands Cheat Sheet

```bash
# Dependencies
flutter pub get                    # Install dependencies
flutter pub upgrade               # Upgrade dependencies
flutter pub outdated             # Check for updates

# Code Generation
flutter gen-l10n                 # Generate localizations
flutter pub run build_runner build --delete-conflicting-outputs

# Running
flutter run                      # Run on default device
flutter run -d <device-id>      # Run on specific device
flutter run --release           # Run in release mode

# Testing
flutter test                    # Run all tests
flutter test <file>            # Run specific test file
flutter test --coverage       # Generate coverage report

# Code Quality
flutter analyze                # Static analysis
dart format .                 # Format all files
dart fix --apply             # Auto-fix issues

# Building
flutter build apk            # Android APK
flutter build appbundle      # Android App Bundle
flutter build ios            # iOS
flutter build web            # Web
flutter build linux          # Linux
flutter build windows        # Windows
flutter build macos          # macOS

# Maintenance
flutter clean               # Clean build artifacts
flutter doctor              # Check Flutter installation
flutter upgrade             # Upgrade Flutter SDK
```

## Getting Help

- **Flutter Docs**: https://docs.flutter.dev/
- **Riverpod Docs**: https://riverpod.dev/
- **Go Router**: https://pub.dev/packages/go_router
- **Community**: https://flutter.dev/community

Happy coding! 🚀
