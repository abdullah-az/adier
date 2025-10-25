# Preview Player Implementation

## Overview

The Preview Player is a feature that allows users to preview composed video timelines with real-time subtitles, playback controls, and timeline navigation before final export.

## Features

### 1. Video Playback
- HTML5 video player with custom controls
- Play/Pause functionality
- Seek controls with visual timeline
- Volume control with mute toggle
- Fullscreen mode
- Playback speed control
- Quality switching (proxy vs. high-quality timeline)

### 2. Subtitle Overlay
- Real-time subtitle rendering synchronized with video playback
- Support for SRT and VTT subtitle formats
- Subtitles overlaid on video with customizable styling
- Automatic parsing and timecode synchronization

### 3. Timeline Scrubber
- Visual representation of all clips in the timeline
- Color-coded clips for easy identification
- Current playback position indicator (red playhead)
- Active clip highlighting
- Click-to-seek functionality
- Transition indicators between clips
- Timecode display with millisecond precision

### 4. Real-time Progress Updates
- Server-Sent Events (SSE) integration for live progress tracking
- Automatic refresh when preview generation completes
- Progress bar showing generation percentage
- Status indicators (queued, running, completed, failed)
- Retry functionality for failed previews

### 5. Timeline Information
- Total duration display
- Resolution information
- Audio track information
- Clip count and details
- Individual clip navigation

### 6. Error Handling
- Graceful fallback when preview not ready
- Loading states with spinners
- Error messages with retry options
- Network error handling
- Missing preview detection

## Technical Implementation

### Components

#### `PreviewPlayer` (`src/pages/PreviewPlayer.tsx`)
Main page component that orchestrates the preview experience:
- Fetches job status from backend API
- Manages video playback state
- Handles SSE connections for real-time updates
- Coordinates between child components

#### `VideoPlayer` (`src/components/VideoPlayer.tsx`)
Custom video player with controls:
- HTML5 video element wrapper
- Custom control UI
- Subtitle overlay rendering
- Loading and error states
- Mouse interaction handling

#### `TimelineScrubber` (`src/components/TimelineScrubber.tsx`)
Timeline visualization component:
- Clip visualization with proportional widths
- Playhead position tracking
- Click-to-seek functionality
- Active clip highlighting
- Transition indicators

#### `PreviewStatusBar` (`src/components/PreviewStatusBar.tsx`)
Status display for preview generation:
- Job status indicators
- Progress bar
- Error messages
- Retry controls

### Hooks

#### `useVideoPlayer` (`src/hooks/useVideoPlayer.ts`)
Custom hook for video player state management:
- Video element ref management
- Playback state tracking
- Control methods (play, pause, seek, volume, playback rate)
- Event listener setup/cleanup

#### `useEventSource` (`src/hooks/useEventSource.ts`)
Custom hook for SSE connections:
- EventSource lifecycle management
- Connection state tracking
- Message parsing
- Error handling
- Automatic cleanup

### Types

#### `src/types/preview.ts`
TypeScript interfaces for preview data:
- `TimelineClip` - Individual clip configuration
- `TimelineComposition` - Timeline composition settings
- `SubtitleCue` - Subtitle timing and text
- `PreviewMedia` - Media asset information
- `TimelinePreview` - Complete preview data
- `JobStatus` - Job processing status
- `PreviewPlayerState` - Player state

### Utilities

#### `src/utils/subtitles.ts`
Subtitle parsing utilities:
- SRT format parser
- VTT format parser
- Timecode conversion
- Subtitle loading from URL

## API Integration

### Backend Endpoints Used

1. **Job Status**: `GET /projects/{project_id}/jobs/{job_id}`
   - Fetches current job status and results
   - Returns timeline, proxy, and export information

2. **Job Events (SSE)**: `GET /projects/{project_id}/jobs/{job_id}/events`
   - Real-time updates via Server-Sent Events
   - Progress notifications
   - Status changes
   - Completion notifications

3. **Storage Access**: `GET /storage/{relative_path}`
   - Serves video files
   - Serves subtitle files
   - Serves thumbnails

### Query Parameters

The preview player accepts the following URL parameters:

- `project`: Project identifier (default: "demo")
- `job`: Job ID for the timeline composition job (required)

Example: `/preview?project=my-project&job=550e8400-e29b-41d4-a716-446655440000`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_URL=http://localhost:8000
```

This configures the backend API URL for fetching preview data.

## Usage

### Navigation

Access the preview player via:
1. Direct URL: `/preview?project=PROJECT_ID&job=JOB_ID`
2. Navigation menu: Click "معاينة" (Preview) in the navbar

### Playback Controls

- **Play/Pause**: Click video or play button
- **Seek**: Drag timeline slider or click on timeline
- **Volume**: Click volume icon or adjust slider
- **Fullscreen**: Click maximize button
- **Quality**: Select from dropdown (proxy/timeline)

### Timeline Navigation

- **View Clips**: Scroll through clip buttons below timeline
- **Jump to Clip**: Click on clip button or timeline segment
- **Current Position**: Red playhead shows current time
- **Active Clip**: Highlighted in blue

## Error Scenarios

### Preview Not Ready
- Shows status bar with generation progress
- Auto-updates via SSE when ready
- Displays loading state

### Generation Failed
- Shows error message
- Provides retry button
- Logs error details

### Network Errors
- Displays connection error message
- Provides manual refresh option
- Maintains last known state

## Browser Compatibility

- Modern browsers with HTML5 video support
- EventSource (SSE) support required
- Recommended: Chrome, Firefox, Safari, Edge (latest versions)

## Performance Considerations

1. **Proxy Quality**: Default to proxy for faster loading
2. **Subtitle Parsing**: Async loading to avoid blocking
3. **Timeline Rendering**: Optimized for large clip counts
4. **SSE Connection**: Automatic cleanup on unmount
5. **Video Buffering**: Browser native buffering

## Future Enhancements

Potential improvements for the preview player:

1. **Multi-quality Streaming**: HLS/DASH adaptive streaming
2. **Keyboard Shortcuts**: Space for play/pause, arrow keys for seeking
3. **Thumbnail Preview**: Hover over timeline to see thumbnails
4. **Clip Trimming**: Edit in/out points directly in preview
5. **Comment/Annotation**: Add notes at specific timestamps
6. **Export Options**: Download specific quality directly from preview
7. **Share Links**: Generate shareable preview links
8. **Collaborative Review**: Real-time commenting with team

## Troubleshooting

### Video Won't Load
- Check API_URL environment variable
- Verify backend is running
- Check browser console for CORS errors
- Ensure video file exists in storage

### Subtitles Not Appearing
- Verify subtitle file exists and is accessible
- Check subtitle format (SRT/VTT)
- Ensure timecodes are correct
- Check browser console for parsing errors

### SSE Connection Fails
- Verify backend supports SSE
- Check for proxy/firewall blocking
- Ensure job ID is valid
- Check backend logs for errors

### Timeline Not Syncing
- Verify clip metadata is correct
- Check duration calculations
- Ensure transition timings are valid
- Refresh page to reset state
