# WebSocket Progress Channel

This document describes the WebSocket-based progress channel implementation for real-time job progress updates.

## Overview

The progress channel provides real-time updates for processing jobs through WebSocket connections. Clients can subscribe to specific jobs and receive status transitions, progress percentages, and stage messages as the jobs are processed.

## Features

- **Real-time Updates**: Instant notification of job status changes and progress
- **Job Subscription**: Subscribe to specific jobs by ID
- **Multi-client Support**: Multiple clients can subscribe to the same job
- **Heartbeat Mechanism**: Automatic ping/pong to maintain connection health
- **Graceful Disconnection**: Clean handling of client disconnects
- **Error Handling**: Robust error handling and recovery

## API Endpoints

### WebSocket Endpoint

```
ws://localhost:8000/progress/ws/{job_id}
```

#### Connection

Connect to the WebSocket endpoint with a specific job ID:

```javascript
const ws = new WebSocket(`ws://localhost:8000/progress/ws/${jobId}`);
```

#### Messages

##### Client Messages

- **Ping Request**:
  ```json
  {
    "type": "ping"
  }
  ```

- **Subscribe to Additional Job**:
  ```json
  {
    "type": "subscribe",
    "job_id": "additional-job-id"
  }
  ```

##### Server Messages

- **Progress Update**:
  ```json
  {
    "job_id": "job-123",
    "status": "in_progress",
    "progress": 75.0,
    "message": "Processing stage 3",
    "timestamp": "2023-01-01T00:00:00Z",
    "metadata": {
      "stage": "stage_3"
    }
  }
  ```

- **Pong Response**:
  ```json
  {
    "type": "pong",
    "timestamp": "2023-01-01T00:00:00Z"
  }
  ```

- **Heartbeat**:
  ```json
  {
    "type": "heartbeat",
    "timestamp": "2023-01-01T00:00:00Z"
  }
  ```

- **Error**:
  ```json
  {
    "type": "error",
    "error": "Job not found"
  }
  ```

## Status Transitions

Jobs progress through the following statuses:

1. **PENDING** - Job created, waiting to be queued
2. **QUEUED** - Job queued in the processing queue
3. **IN_PROGRESS** - Job is actively being processed
4. **COMPLETED** - Job finished successfully
5. **FAILED** - Job failed with an error
6. **CANCELLED** - Job was cancelled

## Integration with Job Lifecycle

The progress channel is automatically integrated with the `ProcessingJobLifecycle` class. When job status is updated through any of these methods, progress updates are automatically broadcast to subscribed clients:

- `ProcessingJobLifecycle.mark_queued()`
- `ProcessingJobLifecycle.mark_started()`
- `ProcessingJobLifecycle.mark_progress()`
- `ProcessingJobLifecycle.mark_completed()`
- `ProcessingJobLifecycle.mark_failed()`

## Usage Examples

### JavaScript Client

```javascript
// Connect to job progress WebSocket
const jobId = 'job-123';
const ws = new WebSocket(`ws://localhost:8000/progress/ws/${jobId}`);

ws.onopen = function(event) {
    console.log('Connected to job progress');
    
    // Send ping to test connection
    ws.send(JSON.stringify({ type: 'ping' }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'progress' || data.job_id) {
        console.log(`Status: ${data.status}`);
        if (data.progress !== undefined) {
            console.log(`Progress: ${data.progress}%`);
        }
        if (data.message) {
            console.log(`Message: ${data.message}`);
        }
    } else if (data.type === 'pong') {
        console.log('Pong received');
    } else if (data.type === 'error') {
        console.error('Error:', data.error);
    }
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};
```

### Python Client (with websockets library)

```python
import asyncio
import json
import websockets

async def monitor_job(job_id: str):
    uri = f"ws://localhost:8000/progress/ws/{job_id}"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            
            if data.get('job_id'):
                print(f"Status: {data['status']}")
                if data.get('progress') is not None:
                    print(f"Progress: {data['progress']:.1f}%")
                if data.get('message'):
                    print(f"Message: {data['message']}")
                print("-" * 30)

# Usage
asyncio.run(monitor_job('job-123'))
```

## Demo Script

A demo script is provided to test the WebSocket functionality:

```bash
python backend/demo_progress_ws.py
```

This script:
1. Creates a demo job
2. Connects to the WebSocket endpoint
3. Simulates job progress through multiple stages
4. Displays real-time progress updates

Make sure the FastAPI server is running first:

```bash
uvicorn backend.app.main:app --reload
```

## Testing

Comprehensive tests are provided in `tests/test_progress_router.py`:

- WebSocket connection handling
- Invalid job ID handling
- Ping/pong heartbeat
- Progress update broadcasting
- Multiple client support
- Error handling
- Connection cleanup

Run tests with:

```bash
pytest tests/test_progress_router.py -v
```

## Architecture

### Components

1. **ProgressRouter**: FastAPI WebSocket endpoint handler
2. **ProgressBroadcaster**: In-memory message broadcasting system
3. **ProgressMessage**: Pydantic model for progress messages
4. **Job Lifecycle Integration**: Automatic progress publishing from job updates

### Broadcasting

The system uses an in-memory broadcaster that maintains:
- Job ID → Set of WebSocket connections mapping
- Thread-safe subscription management
- Automatic cleanup of disconnected clients

### Error Handling

- Invalid job IDs return error messages and close connections
- Malformed JSON is rejected with error responses
- Disconnected clients are automatically removed from subscriptions
- Server exceptions don't affect other connected clients

## Configuration

The WebSocket endpoint is automatically registered when the FastAPI application starts. No additional configuration is required.

## Scalability Considerations

For production deployments with multiple server instances, consider:

1. **Redis Pub/Sub**: Replace in-memory broadcaster with Redis-based broadcasting
2. **Connection Limits**: Implement connection limits per job/client
3. **Message Persistence**: Store progress messages for replay on reconnection
4. **Load Balancing**: Ensure WebSocket connections are properly load balanced

## Security

- WebSocket connections inherit the same security as HTTP endpoints
- Consider implementing authentication for job access control
- Validate job IDs to prevent unauthorized access
- Rate limit WebSocket connections if needed

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the FastAPI server is running
2. **Job Not Found**: Verify the job ID exists before connecting
3. **No Progress Updates**: Check if the job is actually being processed
4. **Connection Timeouts**: Verify network connectivity and firewall settings

### Debug Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('backend.app.api.routes.progress').setLevel(logging.DEBUG)
```