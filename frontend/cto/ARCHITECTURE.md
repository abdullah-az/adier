# Architecture Overview

## Clean Architecture Principles

This Flutter application follows **Clean Architecture** principles to ensure maintainability, testability, and separation of concerns.

### Layer Structure

```
┌─────────────────────────────────────┐
│     Presentation Layer (UI)        │
│  - Pages, Widgets, State           │
│  - Riverpod Providers & Notifiers  │
└─────────────────┬───────────────────┘
                  │
                  ↓
┌─────────────────────────────────────┐
│      Domain Layer (Business)        │
│  - Models (Freezed)                 │
│  - Business Logic                   │
└─────────────────┬───────────────────┘
                  │
                  ↓
┌─────────────────────────────────────┐
│      Data Layer (Sources)           │
│  - Repositories                     │
│  - API Clients (Dio)                │
│  - Data Sources                     │
└─────────────────────────────────────┘
```

## Directory Structure

### `/lib/src/core/`
Core application infrastructure that's shared across features:

- **`constants/`** - Application-wide constants (API URLs, keys, routes)
- **`theme/`** - Theme configuration and theme providers
- **`router/`** - Navigation configuration using go_router
- **`localization/`** - Locale management and language switching
- **`utils/`** - Helper functions and utilities

### `/lib/src/features/`
Feature-based modules organized by domain:

Each feature contains:
- `{feature}_page.dart` - Main UI page
- `{feature}_provider.dart` - State management
- `widgets/` - Feature-specific widgets
- `models/` - Feature-specific models (if any)

Current features:
- **`home/`** - Landing page with theme/language toggles
- **`auth/`** - Authentication (placeholder)
- **`profile/`** - User profile (placeholder)

### `/lib/src/data/`
Data layer handling external data sources:

- **`models/`** - Data transfer objects with Freezed
  - Immutable data classes
  - JSON serialization
  - Copy-with functionality
  
- **`repositories/`** - Data access abstraction
  - API communication
  - Local storage
  - Data transformation
  
- **`providers/`** - Riverpod data providers
  - Repository providers
  - Data fetching providers
  - Caching strategies

### `/lib/src/widgets/`
Reusable UI components shared across features:

- `loading_widget.dart` - Loading indicators
- `error_widget.dart` - Error display with retry
- (Add more as needed)

### `/lib/l10n/`
Localization files:

- `app_en.arb` - English translations (template)
- `app_ar.arb` - Arabic translations
- Auto-generated `.dart` files for type-safe translations

## State Management

### Riverpod Architecture

The app uses **flutter_riverpod** for state management with these provider types:

#### 1. **Provider** - Immutable Dependencies
```dart
final userRepositoryProvider = Provider<UserRepository>((ref) {
  return UserRepository();
});
```
Used for services, repositories, and read-only data.

#### 2. **StateNotifierProvider** - Mutable State
```dart
final themeModeProvider = StateNotifierProvider<ThemeModeNotifier, ThemeMode>((ref) {
  return ThemeModeNotifier();
});
```
Used for app-wide state like theme, locale, authentication status.

#### 3. **FutureProvider** - Async Data
```dart
final userListProvider = FutureProvider<List<UserModel>>((ref) async {
  final repository = ref.read(userRepositoryProvider);
  return repository.getUsers();
});
```
Used for one-time async operations.

#### 4. **StreamProvider** - Real-time Data
Used for WebSocket connections, real-time updates, etc.

### Provider Scope

The entire app is wrapped in `ProviderScope` in `main.dart`, enabling dependency injection throughout the widget tree.

## Navigation

### go_router Configuration

Routes are centrally defined in `/lib/src/core/router/app_router.dart`:

```dart
final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => HomePage()),
    GoRoute(path: '/auth', builder: (context, state) => AuthPage()),
    GoRoute(path: '/profile', builder: (context, state) => ProfilePage()),
  ],
);
```

#### Navigation Methods

**Push** - Add new route to stack:
```dart
context.push('/profile');
```

**Go** - Replace current route:
```dart
context.go('/home');
```

**Pop** - Go back:
```dart
context.pop();
```

## Internationalization (i18n)

### ARB File Structure

Translations are defined in Application Resource Bundle (ARB) format:

```json
{
  "@@locale": "en",
  "welcome": "Welcome",
  "@welcome": {
    "description": "Welcome message"
  }
}
```

### Usage in Code

```dart
final l10n = AppLocalizations.of(context)!;
Text(l10n.welcome);
```

### Language Switching

Managed by `LocaleNotifier` in `/lib/src/core/localization/locale_provider.dart`:

```dart
// Toggle between English and Arabic
ref.read(localeProvider.notifier).toggleLocale();

// Set specific locale
ref.read(localeProvider.notifier).setLocale(Locale('ar'));
```

## Theme Management

### Light and Dark Themes

Defined in `/lib/src/core/theme/app_theme.dart` using Material Design 3:

- Automatic color scheme generation from seed color
- Consistent styling across components
- CardThemeData, InputDecorationTheme, etc.

### Theme Switching

```dart
// Toggle theme
ref.read(themeModeProvider.notifier).toggleThemeMode();

// Set specific theme
ref.read(themeModeProvider.notifier).setThemeMode(ThemeMode.dark);
```

## Data Models

### Freezed + JSON Serializable

Data models use `freezed` for immutability and `json_serializable` for JSON conversion:

```dart
@freezed
class UserModel with _$UserModel {
  const factory UserModel({
    required String id,
    required String name,
    required String email,
  }) = _UserModel;

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);
}
```

### Code Generation

Run after creating/modifying models:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

## HTTP Communication

### Dio Client

Configured in `/lib/src/data/repositories/`:

```dart
final dio = Dio(BaseOptions(
  baseUrl: AppConstants.apiBaseUrl,
  connectTimeout: Duration(milliseconds: 30000),
));
```

### Repository Pattern

Repositories abstract data sources:

```dart
class UserRepository {
  final Dio _dio;
  
  Future<UserModel> getUser(String id) async {
    final response = await _dio.get('/users/$id');
    return UserModel.fromJson(response.data);
  }
}
```

## Best Practices

### 1. Separation of Concerns
- UI logic stays in widgets
- Business logic lives in providers/notifiers
- Data fetching handled by repositories

### 2. Immutability
- Use `const` constructors wherever possible
- Use Freezed for data models
- Use immutable state in Riverpod providers

### 3. Type Safety
- Strong typing throughout
- Generated localization classes
- Freezed models with type checking

### 4. Testability
- Providers can be easily overridden in tests
- Repository pattern enables mocking
- Pure functions in utilities

### 5. Error Handling
- Try-catch in repositories
- Error states in providers
- User-friendly error widgets

## Testing Strategy

### Unit Tests
Test business logic and data transformations:
- Model serialization
- Provider logic
- Utility functions

### Widget Tests
Test UI components in isolation:
- Individual widgets
- Feature pages
- Navigation flows

### Integration Tests
Test full user flows:
- End-to-end scenarios
- API integration
- State persistence

## Future Enhancements

### Planned Features
1. **Authentication** - JWT token management, secure storage
2. **Offline Support** - Local database (Hive/Drift), sync strategies
3. **Push Notifications** - Firebase Cloud Messaging
4. **Analytics** - User behavior tracking
5. **Crash Reporting** - Error monitoring
6. **CI/CD** - Automated testing and deployment

### Architectural Improvements
1. **Use Cases Layer** - Extract business logic from providers
2. **Dependency Injection** - More sophisticated DI container
3. **Feature Flags** - Remote configuration
4. **Modular Architecture** - Flutter packages per feature

## References

- [Flutter Clean Architecture](https://resocoder.com/flutter-clean-architecture-tdd/)
- [Riverpod Documentation](https://riverpod.dev/)
- [Go Router Guide](https://pub.dev/packages/go_router)
- [Freezed Package](https://pub.dev/packages/freezed)
- [Flutter Internationalization](https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization)
