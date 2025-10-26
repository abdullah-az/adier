import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

typedef WebSocketMessageHandler = void Function(Map<String, dynamic> message);
typedef WebSocketErrorHandler = void Function(Object error, StackTrace? stackTrace);
typedef WebSocketStateHandler = void Function();

class WebSocketService {
  WebSocketService({required this.endpoint});

  final Uri endpoint;
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;

  bool get isConnected => _channel != null;

  void connect({
    WebSocketMessageHandler? onMessage,
    WebSocketErrorHandler? onError,
    WebSocketStateHandler? onDone,
  }) {
    disconnect();

    final channel = WebSocketChannel.connect(endpoint);
    _channel = channel;

    _subscription = channel.stream.listen(
      (event) {
        if (event is String) {
          try {
            final decoded = json.decode(event) as Map<String, dynamic>;
            onMessage?.call(decoded);
          } catch (e, stackTrace) {
            onError?.call(e, stackTrace);
          }
        }
      },
      onError: (error, stackTrace) {
        onError?.call(error, stackTrace);
      },
      onDone: () {
        onDone?.call();
      },
      cancelOnError: true,
    );
  }

  void send(Map<String, dynamic> message) {
    final channel = _channel;
    if (channel == null) {
      throw StateError('WebSocket is not connected');
    }

    channel.sink.add(json.encode(message));
  }

  void disconnect() {
    _subscription?.cancel();
    _channel?.sink.close();
    _subscription = null;
    _channel = null;
  }
}
