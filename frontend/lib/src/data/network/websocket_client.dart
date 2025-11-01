import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketClient {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  final String _wsUrl;
  final Duration _reconnectDelay;
  final int _maxReconnectAttempts;
  int _reconnectAttempts = 0;
  bool _isConnecting = false;
  bool _shouldReconnect = true;

  String get wsUrl => _wsUrl;
  Duration get reconnectDelay => _reconnectDelay;
  int get maxReconnectAttempts => _maxReconnectAttempts;

  final StreamController<WebSocketMessage> _messageController = 
      StreamController<WebSocketMessage>.broadcast();
  final StreamController<WebSocketState> _stateController = 
      StreamController<WebSocketState>.broadcast();

  Stream<WebSocketMessage> get messages => _messageController.stream;
  Stream<WebSocketState> get states => _stateController.stream;

  WebSocketClient({
    required String wsUrl,
    Duration reconnectDelay = const Duration(seconds: 3),
    int maxReconnectAttempts = 5,
  }) : _wsUrl = wsUrl,
       _reconnectDelay = reconnectDelay,
       _maxReconnectAttempts = maxReconnectAttempts;

  Future<void> connect() async {
    if (_isConnecting || (_channel != null && _isConnected())) {
      return;
    }

    _isConnecting = true;
    _stateController.add(WebSocketState.connecting);

    try {
      developer.log('Connecting to WebSocket: $_wsUrl', name: 'WebSocketClient');
      
      _channel = WebSocketChannel.connect(Uri.parse(_wsUrl));
      _reconnectAttempts = 0;
      _isConnecting = false;

      _stateController.add(WebSocketState.connected);
      developer.log('WebSocket connected', name: 'WebSocketClient');

      _subscription = _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDone,
        cancelOnError: false,
      );
    } catch (e) {
      _isConnecting = false;
      _stateController.add(WebSocketState.error);
      developer.log('WebSocket connection failed: $e', name: 'WebSocketClient');
      
      if (_shouldReconnect) {
        _scheduleReconnect();
      }
    }
  }

  void _handleMessage(dynamic message) {
    try {
      final jsonString = message is String ? message : utf8.decode(message);
      developer.log('WebSocket message received: $jsonString', name: 'WebSocketClient');
      
      final data = jsonDecode(jsonString) as Map<String, dynamic>;
      final webSocketMessage = WebSocketMessage.fromJson(data);
      _messageController.add(webSocketMessage);
    } catch (e) {
      developer.log('Failed to parse WebSocket message: $e', name: 'WebSocketClient');
      _messageController.add(WebSocketMessage.error('Failed to parse message: $e'));
    }
  }

  void _handleError(dynamic error) {
    developer.log('WebSocket error: $error', name: 'WebSocketClient');
    _stateController.add(WebSocketState.error);
    
    if (_shouldReconnect) {
      _scheduleReconnect();
    }
  }

  void _handleDone() {
    developer.log('WebSocket connection closed', name: 'WebSocketClient');
    _stateController.add(WebSocketState.disconnected);
    
    if (_shouldReconnect) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      developer.log('Max reconnect attempts reached', name: 'WebSocketClient');
      _shouldReconnect = false;
      return;
    }

    _reconnectAttempts++;
    developer.log('Scheduling reconnect attempt $_reconnectAttempts', name: 'WebSocketClient');
    
    Future.delayed(_reconnectDelay, () {
      if (_shouldReconnect) {
        connect();
      }
    });
  }

  void sendMessage(Map<String, dynamic> data) {
    if (_isConnected()) {
      try {
        final jsonString = jsonEncode(data);
        developer.log('Sending WebSocket message: $jsonString', name: 'WebSocketClient');
        _channel!.sink.add(jsonString);
      } catch (e) {
        developer.log('Failed to send WebSocket message: $e', name: 'WebSocketClient');
      }
    } else {
      developer.log('Cannot send message - WebSocket not connected', name: 'WebSocketClient');
    }
  }

  bool _isConnected() {
    return _channel != null && _channel!.sink != null && !_isConnecting;
  }

  void disconnect() {
    _shouldReconnect = false;
    _subscription?.cancel();
    _subscription = null;
    
    _channel?.sink.close();
    _channel = null;
    
    _stateController.add(WebSocketState.disconnected);
    developer.log('WebSocket disconnected', name: 'WebSocketClient');
  }

  void dispose() {
    disconnect();
    _messageController.close();
    _stateController.close();
  }
}

enum WebSocketState {
  connecting,
  connected,
  disconnected,
  error,
}

class WebSocketMessage {
  final String type;
  final Map<String, dynamic>? data;
  final String? error;

  WebSocketMessage({
    required this.type,
    this.data,
    this.error,
  });

  factory WebSocketMessage.fromJson(Map<String, dynamic> json) {
    return WebSocketMessage(
      type: json['type'] as String,
      data: json['data'] as Map<String, dynamic>?,
      error: json['error'] as String?,
    );
  }

  factory WebSocketMessage.error(String error) {
    return WebSocketMessage(
      type: 'error',
      error: error,
    );
  }

  factory WebSocketMessage.progress({
    required String jobId,
    required int progress,
    required String status,
    Map<String, dynamic>? metadata,
  }) {
    return WebSocketMessage(
      type: 'job_progress',
      data: {
        'job_id': jobId,
        'progress': progress,
        'status': status,
        'metadata': metadata ?? {},
      },
    );
  }

  factory WebSocketMessage.notification({
    required String title,
    required String message,
    String? level,
  }) {
    return WebSocketMessage(
      type: 'notification',
      data: {
        'title': title,
        'message': message,
        'level': level ?? 'info',
      },
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'data': data,
      'error': error,
    };
  }

  @override
  String toString() {
    return 'WebSocketMessage(type: $type, data: $data, error: $error)';
  }
}