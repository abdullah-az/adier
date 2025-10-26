# Preview Player Feature (Flutter)

## Overview

The Preview Player is a Flutter implementation that allows users to preview composed video timelines with real-time subtitles, playback controls, and timeline navigation before final export.

## Features

### 1. Video Playback
- Native video player using `video_player` package
- Play/Pause functionality
- Seek controls with visual timeline
- Volume control
- Automatic aspect ratio adjustment
- Loading states and error handling

### 2. Subtitle Overlay
- Real-time subtitle rendering synchronized with video playback
- Subtitles overlaid on video with semi-transparent background
- Automatic timecode synchronization
- Graceful handling when subtitles fail to load

### 3. Timeline Scrubber
- Visual representation of all clips in the timeline
- Color-coded clips for easy identification
- Current playback position indicator (red playhead)
- Active clip highlighting with animation
- Click-to-seek functionality on clips
- Slider for precise seeking
- Timecode display with millisecond precision

### 4. Real-time Progress Updates
- WebSocket integration for live progress tracking
- Automatic state updates when preview generation completes
- Progress bar showing generation percentage
- Status indicators (queued, running, completed, failed, cancelled)
- Retry functionality for failed previews
- Manual refresh option

### 5. Error Handling
- Graceful fallback when preview not ready
- Loading states with spinners
- Error messages with retry options
- Network error handling
- Missing job ID detection

## Technical Implementation

### Architecture

The implementation follows Flutter's Clean Architecture pattern:

```
lib/src/
├── features/preview/
│   ├── preview_player_page.dart          # Main page with WebSocket integration
│   └── widgets/
│       ├── video_player_widget.dart      # Video player wrapper
│       ├── subtitle_overlay_widget.dart   # Subtitle display
│       ├── timeline_scrubber_widget.dart  # Timeline visualization
│       ├── preview_controls_widget.dart   # Play/pause/volume controls
│       └── preview_status_widget.dart     # Job status display
├── data/
│   ├── models/
│   │   └── preview_models.dart            # Data models
│   ├── repositories/
│   │   └── preview_repository.dart        # API calls
│   └── providers/
│       └── preview_provider.dart          # State management
└── core/services/
    └── websocket_service.dart             # WebSocket connection management
```

### Key Components

#### `PreviewPlayerPage`
Main page component that orchestrates the preview experience:
- Fetches job status from backend API via Riverpod provider
- Manages WebSocket connection for real-time updates
- Handles navigation and empty job ID state
- Displays loading/error states appropriately

#### `VideoPlayerWidget`
Simplified video player wrapper:
- Takes a `VideoPlayerController` from parent
- Displays video with proper aspect ratio
- Supports overlay widgets (subtitles)
- Shows loading state while initializing

#### `SubtitleOverlayWidget`
Subtitle display component:
- Finds current subtitle based on playback position
- Renders text with semi-transparent background
- Positioned at bottom of video
- Smooth appearance/disappearance

#### `TimelineScrubberWidget`
Timeline visualization component:
- Clip visualization with proportional widths based on duration
- Color parsing with fallback for invalid colors
- Active clip highlighting with smooth animation
- Red playhead indicator showing current position
- Slider for precise seeking
- Timecode formatting (HH:MM:SS.ms)

#### `PreviewControlsWidget`
Playback control UI:
- Play/pause toggle button
- Volume control with mute toggle
- Volume slider
- Clean, minimal design

#### `PreviewStatusWidget`
Job status display:
- Shows different UI based on job status (ready, processing, failed)
- Progress bar for generating previews
- Handles both 0-1 and 0-100 progress ranges
- Refresh/retry button with loading state
- Error message display

### State Management

#### `PreviewJobNotifier`
StateNotifier that manages preview job state:
- Fetches initial job data
- Provides refresh method for manual updates
- Receives updates from WebSocket
- Updates timeline when provided in WebSocket messages

#### `PreviewJobProvider`
Family provider that creates a PreviewJobNotifier for each project/job combination:
```dart
previewJobProvider((projectId: 'demo', jobId: '123'))
```

#### `SubtitlesProvider`
FutureProvider that fetches subtitles from URL:
```dart
subtitlesProvider(subtitleUrl)
```

### Data Models

#### `TimelineClip`
Represents a single clip in the timeline:
- `id`, `startTime`, `duration`, `sourceFile`
- Optional `label` and `color`
- Computed `endTime` property

#### `SubtitleCue`
Represents a single subtitle:
- `startTime`, `endTime`, `text`

#### `TimelineComposition`
Complete timeline structure:
- List of `TimelineClip`s
- Total `duration`
- Optional `resolution` and `fps`

#### `PreviewJob`
Job processing state:
- Job status (queued, running, completed, failed, cancelled)
- URLs for proxy video and subtitles
- Timeline composition
- Progress percentage
- Error message

#### `JobStatus`
Enum with conversion from string for API compatibility

### Services

#### `WebSocketService`
Reusable WebSocket connection manager:
- Connects to backend endpoint
- Parses JSON messages
- Provides callbacks for messages, errors, and disconnection
- Automatic cleanup on disposal

## API Integration

### Backend Endpoints

1. **Job Status**: `GET /api/projects/{project_id}/jobs/{job_id}`
   - Fetches current job status and results
   - Returns timeline, proxy URL, and status

2. **Job Events (WebSocket)**: `ws://[host]/api/projects/{project_id}/jobs/{job_id}/events`
   - Real-time updates via WebSocket
   - Progress notifications
   - Status changes
   - Completion notifications

3. **Subtitles**: `GET [subtitle_url]`
   - Fetches subtitle data (JSON array of cues)

### Query Parameters

The preview player accepts URL parameters:
- `project`: Project identifier (default: "demo")
- `job`: Job ID (required)

Example: `/preview?project=my-project&job=550e8400-e29b-41d4-a716-446655440000`

## Configuration

### Environment Variables

Ensure `AppConstants.apiBaseUrl` is set to your backend API:
```dart
static const String apiBaseUrl = 'http://localhost:8000/api';
```

## Dependencies

- `video_player: ^2.9.2` - Video playback
- `web_socket_channel: ^3.0.1` - WebSocket connections
- `flutter_hooks: ^0.20.5` - React-like hooks for Flutter
- `hooks_riverpod: ^2.6.1` - State management with hooks
- `go_router: ^14.7.1` - Navigation

## Usage

### Navigation

Navigate to preview from code:
```dart
context.push('/preview?project=demo&job=550e8400-e29b-41d4-a716-446655440000');
```

Or use the button on the home page.

### Playback Controls

- **Play/Pause**: Click play/pause button
- **Volume**: Click volume icon to mute/unmute, or use slider
- **Seek**: Use timeline scrubber slider or click on clip
- **Jump to Clip**: Click on any clip in the timeline

## Error Scenarios

### Preview Not Ready
- Shows status bar with generation progress
- Auto-updates via WebSocket when ready
- Manual refresh available

### Generation Failed
- Shows error message
- Provides retry button
- Displays error details if available

### Network Errors
- Displays connection error message
- Provides manual refresh option
- Maintains last known state

### No Job ID
- Shows informational message
- Instructs user to provide job query parameter

## Browser/Platform Compatibility

- **Mobile**: Android and iOS
- **Desktop**: Windows, macOS, Linux
- **Web**: Modern browsers with HTML5 video support

## Performance Considerations

1. **Video Controller Management**: Uses hooks for proper lifecycle management
2. **Subtitle Loading**: Async loading with error handling
3. **Timeline Rendering**: Optimized with `LayoutBuilder` and `Expanded` widgets
4. **WebSocket**: Automatic cleanup on widget disposal
5. **State Updates**: Efficient state updates via Riverpod

## Testing

The preview player can be tested by:
1. Starting the backend API
2. Creating a preview job via API
3. Navigating to `/preview?project=demo&job=[job_id]`
4. Verifying video playback, subtitles, timeline, and controls

## Future Enhancements

Potential improvements:
1. Keyboard shortcuts (Space for play/pause, arrow keys for seeking)
2. Fullscreen mode
3. Playback speed control
4. Quality switching (proxy vs high-quality)
5. Thumbnail preview on timeline hover
6. Download options
7. Share preview links
8. Commenting/annotation at timestamps
9. Better mobile touch controls
10. Accessibility improvements

## Troubleshooting

### Video Won't Load
- Check `AppConstants.apiBaseUrl` configuration
- Verify backend is running and accessible
- Check network connectivity
- Ensure proxy video URL is valid and accessible

### Subtitles Not Appearing
- Verify subtitle URL in job response
- Check subtitle data format (JSON array)
- Ensure timecodes match video duration
- Check for CORS issues

### WebSocket Connection Fails
- Verify backend supports WebSocket
- Check for proxy/firewall blocking WebSocket
- Ensure job ID is valid
- Check backend logs

### Timeline Not Syncing
- Verify timeline data in job response
- Check clip durations and start times
- Ensure video duration matches timeline duration
- Try refreshing the preview

## Development Notes

- Uses `flutter_hooks` for lifecycle management instead of StatefulWidget
- WebSocket connection is established on page load and cleaned up on disposal
- Video controller is memoized to prevent recreation on rebuilds
- Subtitle overlay is rebuilt on every position change for smooth updates
- Timeline scrubber uses flex layout for proportional clip widths
