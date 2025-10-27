sealed class ApiFailure {
  const ApiFailure(this.message);

  final String message;

  R when<R>({
    required R Function(NetworkFailure value) network,
    required R Function(ServerFailure value) server,
    required R Function(TimeoutFailure value) timeout,
    required R Function(UnauthorizedFailure value) unauthorized,
    required R Function(ForbiddenFailure value) forbidden,
    required R Function(NotFoundFailure value) notFound,
    required R Function(ValidationFailure value) validation,
    required R Function(ParsingFailure value) parsing,
    required R Function(UploadFailure value) upload,
    required R Function(UnknownFailure value) unknown,
  }) {
    final self = this;
    if (self is NetworkFailure) return network(self);
    if (self is ServerFailure) return server(self);
    if (self is TimeoutFailure) return timeout(self);
    if (self is UnauthorizedFailure) return unauthorized(self);
    if (self is ForbiddenFailure) return forbidden(self);
    if (self is NotFoundFailure) return notFound(self);
    if (self is ValidationFailure) return validation(self);
    if (self is ParsingFailure) return parsing(self);
    if (self is UploadFailure) return upload(self);
    return unknown(self as UnknownFailure);
  }
}

class NetworkFailure extends ApiFailure {
  const NetworkFailure({required super.message, this.exception});

  final Exception? exception;
}

class ServerFailure extends ApiFailure {
  const ServerFailure({
    required this.statusCode,
    required super.message,
    this.data,
  });

  final int statusCode;
  final Map<String, dynamic>? data;
}

class TimeoutFailure extends ApiFailure {
  const TimeoutFailure({required super.message});
}

class UnauthorizedFailure extends ApiFailure {
  const UnauthorizedFailure({required super.message});
}

class ForbiddenFailure extends ApiFailure {
  const ForbiddenFailure({required super.message});
}

class NotFoundFailure extends ApiFailure {
  const NotFoundFailure({required super.message});
}

class ValidationFailure extends ApiFailure {
  const ValidationFailure({
    required super.message,
    this.errors,
  });

  final Map<String, List<String>>? errors;
}

class ParsingFailure extends ApiFailure {
  const ParsingFailure({
    required super.message,
    this.exception,
  });

  final Exception? exception;
}

class UploadFailure extends ApiFailure {
  const UploadFailure({
    required super.message,
    this.progress,
  });

  final double? progress;
}

class UnknownFailure extends ApiFailure {
  const UnknownFailure({
    required super.message,
    this.error,
  });

  final Object? error;
}
