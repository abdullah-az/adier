import 'package:flutter/foundation.dart';

/// A tiny, synchronous service locator to register runtime dependencies.
class ServiceRegistry {
  ServiceRegistry();

  final Map<Type, Object> _instances = <Type, Object>{};

  /// Registers a singleton [instance] that can later be retrieved with [get].
  ///
  /// If an instance of type [T] already exists, it will only be overwritten when
  /// [overrideExisting] is set to true.
  void registerSingleton<T extends Object>(
    T instance, {
    bool overrideExisting = false,
  }) {
    if (!_instances.containsKey(T) || overrideExisting) {
      _instances[T] = instance;
    }
  }

  /// Returns the registered singleton of type [T].
  T get<T extends Object>() {
    final instance = _instances[T];
    if (instance == null) {
      throw StateError('Service of type $T has not been registered.');
    }
    return instance as T;
  }

  /// Disposes known disposable instances and clears the registry.
  void dispose() {
    for (final instance in _instances.values) {
      if (instance case ChangeNotifier notifier) {
        notifier.dispose();
      }
    }
    _instances.clear();
  }
}
