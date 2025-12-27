# Technical Requirement Document (TRD) - AI Video Captioning SaaS Platform

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [AI Logic](#ai-logic)
5. [UI/UX Guidelines](#uiux-guidelines)
6. [Scalability & Performance](#scalability--performance)
7. [Security Considerations](#security-considerations)
8. [Deployment Strategy](#deployment-strategy)

## Executive Summary

The AI Video Captioning SaaS platform is designed to provide automated Arabic video captioning with multimodal AI analysis. The system accepts video uploads with optional contextual prompts, processes them using advanced AI models, and provides styled captions with export capabilities.

### Core Features
- Video upload with optional contextual prompting
- Arabic transcription using multimodal AI
- Styling presets for captions
- Preview and export functionality
- RTL support for Arabic content

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   User Client   │────│   CDN/Edge CDN   │────│  API Gateway     │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                    │
                           ┌──────────────────┐
                           │  Load Balancer   │
                           └──────────────────┘
                                    │
        ┌─────────────────────────────────────────────────────────────┐
        │                    Microservices Layer                      │
        │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
        │  │   Auth Service  │  │  Media Service  │  │ AI Service   │ │
        │  └─────────────────┘  └─────────────────┘  └──────────────┘ │
        │         │                       │                  │        │
        │         ▼                       ▼                  ▼        │
        │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
        │  │  User Database  │  │  Media Storage  │  │  AI Workers  │ │
        │  └─────────────────┘  └─────────────────┘  └──────────────┘ │
        └─────────────────────────────────────────────────────────────┘
                                    │
                           ┌──────────────────┐
                           │   CDN for Output │
                           └──────────────────┘
                                    │
                    ┌─────────────────────────────┐
                    │      Video CDN Storage      │
                    └─────────────────────────────┘
```

### Technology Stack

#### Frontend (Next.js/React)
- **Framework**: Next.js 14+ with App Router
- **State Management**: Zustand/Redux Toolkit
- **UI Library**: Tailwind CSS with custom RTL components
- **Video Player**: ReactPlayer or Video.js with custom caption rendering
- **File Upload**: React-dropzone with chunked upload capability
- **Internationalization**: next-i18next for Arabic RTL support

#### Backend (Python/FastAPI)
- **Framework**: FastAPI with async support
- **Authentication**: JWT with refresh tokens
- **Database**: PostgreSQL with Prisma ORM
- **Message Queue**: Celery with Redis
- **File Storage**: AWS S3 or MinIO
- **Caching**: Redis
- **API Documentation**: Swagger/OpenAPI

#### AI Pipeline
- **Audio Transcription**: OpenAI Whisper API or Whisper.cpp
- **Multimodal Analysis**: OpenAI GPT-4 Vision or similar
- **Video Processing**: FFmpeg for rendering and encoding
- **NLP Processing**: spaCy Arabic models for text processing
- **Model Serving**: Hugging Face Inference API or self-hosted models

### Service Components

1. **Authentication Service**
   - User registration/login
   - JWT token management
   - Role-based access control

2. **Media Service**
   - Video upload and validation
   - File storage management
   - Video metadata extraction

3. **AI Processing Service**
   - Audio extraction from video
   - Transcription using Whisper
   - Context integration with LLM
   - Caption styling application

4. **Rendering Service**
   - Video rendering with hard-coded subtitles
   - Format conversion
   - Quality optimization

## Database Schema

### User Entity
```sql
users
├── id (UUID, Primary Key)
├── email (VARCHAR, Unique, Not Null)
├── password_hash (VARCHAR, Not Null)
├── first_name (VARCHAR)
├── last_name (VARCHAR)
├── phone (VARCHAR)
├── subscription_tier (ENUM: free, premium, enterprise)
├── storage_used (BIGINT)
├── storage_limit (BIGINT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
└── is_active (BOOLEAN)
```

### Project Entity
```sql
projects
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key → users.id)
├── title (VARCHAR, Not Null)
├── description (TEXT)
├── status (ENUM: processing, completed, failed)
├── original_video_url (VARCHAR)
├── processed_video_url (VARCHAR)
├── thumbnail_url (VARCHAR)
├── transcription_json (JSONB)
├── styling_config (JSONB)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
└── completed_at (TIMESTAMP)
```

### Asset Entity
```sql
assets
├── id (UUID, Primary Key)
├── project_id (UUID, Foreign Key → projects.id)
├── type (ENUM: original_video, processed_video, thumbnail, audio, transcript)
├── url (VARCHAR, Not Null)
├── file_size (BIGINT)
├── mime_type (VARCHAR)
├── duration (INTEGER) -- in seconds
├── created_at (TIMESTAMP)
└── expires_at (TIMESTAMP)
```

### Transcription Entity
```sql
transcriptions
├── id (UUID, Primary Key)
├── project_id (UUID, Foreign Key → projects.id)
├── text_content (TEXT)
├── segments (JSONB) -- Array of {start, end, text, confidence}
├── language (VARCHAR, Default: 'ar')
├── ai_context (TEXT) -- User-provided context
├── processing_metadata (JSONB)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### Styling Preset Entity
```sql
styling_presets
├── id (UUID, Primary Key)
├── name (VARCHAR, Not Null)
├── description (TEXT)
├── config (JSONB) -- Font, color, animation settings
├── is_default (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### User Styling Preference Entity
```sql
user_styling_preferences
├── id (UUID, Primary Key)
├── user_id (UUID, Foreign Key → users.id)
├── preset_id (UUID, Foreign Key → styling_presets.id)
├── is_favorite (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

## AI Logic

### Multimodal Analysis Process

1. **Audio Extraction**
   - Use FFmpeg to extract audio from video
   - Convert to appropriate format (WAV, 16kHz) for transcription

2. **Initial Transcription**
   - Use OpenAI Whisper API for Arabic audio transcription
   - Generate time-stamped segments

3. **Context Integration**
   - Pass user-provided context to GPT-4 or similar LLM
   - Use context to correct transcription errors
   - Enhance sentiment alignment and terminology

4. **Post-Processing**
   - Apply Arabic language processing for accuracy
   - Highlight specific keywords based on user intent
   - Generate confidence scores for each segment

### Context Integration with LLM

```python
def integrate_context_with_transcription(
    transcription_segments: List[dict], 
    user_context: str
) -> List[dict]:
    """
    Integrates user context with transcription to improve accuracy
    """
    # Prepare prompt for LLM
    prompt = f"""
    User Context: {user_context}
    
    Transcription Segments: {json.dumps(transcription_segments, ensure_ascii=False)}
    
    Please review and improve the transcription accuracy by:
    1. Correcting any transcription errors
    2. Enhancing sentiment alignment based on context
    3. Highlighting important keywords from the context
    4. Maintaining Arabic language standards
    
    Return the corrected segments in the same format.
    """
    
    # Call LLM API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert Arabic language assistant for video transcription."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # Parse and return corrected segments
    corrected_segments = json.loads(response.choices[0].message.content)
    return corrected_segments
```

### Keyword Highlighting Based on User Intent

```python
def highlight_keywords_in_transcription(
    transcription_segments: List[dict], 
    user_context: str
) -> List[dict]:
    """
    Identifies and marks important keywords based on user context
    """
    # Extract important terms from context
    keyword_extraction_prompt = f"""
    From the following context, extract important keywords that should be highlighted in the transcription:
    
    Context: {user_context}
    
    Return the keywords as a JSON array.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": keyword_extraction_prompt}
        ]
    )
    
    important_keywords = json.loads(response.choices[0].message.content)
    
    # Mark keywords in transcription segments
    for segment in transcription_segments:
        for keyword in important_keywords:
            # Use regex to find and mark keywords in Arabic text
            pattern = r'\b' + re.escape(keyword) + r'\b'
            # Add highlighting metadata to the segment
            segment['highlighted_keywords'] = segment['highlighted_keywords'] or []
            if re.search(pattern, segment['text'], re.IGNORECASE):
                segment['highlighted_keywords'].append({
                    'keyword': keyword,
                    'positions': [m.span() for m in re.finditer(pattern, segment['text'])]
                })
    
    return transcription_segments
```

## UI/UX Guidelines

### Editor Dashboard Design

#### Main Layout Components
1. **Video Preview Panel** (60% width)
   - Video player with playback controls
   - Timeline with transcription segments
   - Real-time preview of caption styling

2. **Caption Editing Panel** (25% width)
   - Editable text fields for each segment
   - Context input area
   - Segment timing controls

3. **Styling Panel** (15% width)
   - Preset selection
   - Custom styling options
   - Animation controls

#### Arabic (RTL) Support Requirements

1. **Text Direction**
   - All text fields support RTL input
   - Proper Arabic font rendering
   - Bidirectional text handling

2. **Layout Direction**
   - Right-aligned controls
   - RTL navigation patterns
   - Mirrored interface elements

3. **Typography Considerations**
   - Arabic-optimized fonts (Amiri, Cairo, etc.)
   - Proper letter spacing and line height
   - Kashida handling for justified text

#### Key UI Components

1. **Video Upload Component**
   - Drag-and-drop interface
   - Progress indicators
   - File type validation
   - Context input field

2. **Timeline Component**
   - Visual representation of transcription segments
   - Drag-to-edit timing
   - Playback synchronization
   - RTL-aligned time markers

3. **Styling Preset Selector**
   - Gallery view of available presets
   - Live preview of each style
   - Customization controls
   - Save as favorite option

4. **Caption Editor**
   - Segment-by-segment editing
   - Auto-save functionality
   - Spell-check for Arabic
   - Synchronization with video playback

### Accessibility Considerations

- Keyboard navigation support
- Screen reader compatibility
- High contrast mode
- Font size adjustment
- Focus indicators for RTL navigation

## Scalability & Performance

### Handling Large Video Files

1. **Chunked Upload**
   - Break large videos into smaller chunks
   - Resume interrupted uploads
   - Parallel upload of chunks

2. **Progressive Processing**
   - Process video in segments
   - Stream processing where possible
   - Asynchronous job queues

3. **Storage Optimization**
   - Tiered storage (hot/cold)
   - Video compression
   - Format optimization

### Microservice Scaling

1. **Horizontal Scaling**
   - Auto-scaling based on queue length
   - Container orchestration (Kubernetes)
   - Load balancing

2. **Database Scaling**
   - Read replicas for database
   - Connection pooling
   - Caching layer (Redis)

3. **CDN Distribution**
   - Global content delivery
   - Edge caching for static assets
   - Adaptive streaming

### Performance Optimization

1. **Caching Strategy**
   - API response caching
   - Database query caching
   - Asset caching

2. **Asynchronous Processing**
   - Background job processing
   - Real-time progress updates
   - Non-blocking operations

## Security Considerations

### Data Protection
- End-to-end encryption for video files
- Secure token management
- Data retention policies

### Access Control
- Role-based permissions
- API rate limiting
- Input validation and sanitization

### Compliance
- GDPR compliance for user data
- SOC 2 compliance for security
- Data residency requirements

## Deployment Strategy

### Infrastructure
- Containerized deployment (Docker)
- Orchestration (Kubernetes)
- Infrastructure as Code (Terraform)

### CI/CD Pipeline
- Automated testing
- Blue-green deployments
- Rollback capabilities

### Monitoring
- Application performance monitoring
- Error tracking
- Resource utilization metrics