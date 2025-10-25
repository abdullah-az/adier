# Video Editing App

A modern video editing application built with Flutter and FastAPI, designed to provide an intuitive and powerful video editing experience with AI-powered features.

## 🎯 Project Vision

This application aims to democratize video editing by providing a cross-platform solution that combines the power of professional editing tools with an intuitive user interface. Users can:

- Edit videos with precision and ease
- Apply filters, effects, and transitions
- Leverage AI-powered features for intelligent video processing
- Export in multiple formats and quality settings
- Collaborate and share projects seamlessly

## 🏗️ Architecture

This is a multiproject repository with a clean separation between frontend and backend:

```
.
├── frontend/          # Flutter mobile/desktop application
├── backend/           # FastAPI REST API service
├── media/             # Sample assets and test media (gitignored)
├── docs/              # Architecture documentation and design specs
└── README.md          # This file
```

## 🛠️ Tech Stack

### Frontend
- **Flutter** - Cross-platform UI framework (iOS, Android, Web, Desktop)
- **Dart** - Programming language
- **Provider/Riverpod** - State management (TBD)
- **video_player** - Video playback and preview
- **ffmpeg_kit_flutter** - Video processing and encoding

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3.11+** - Programming language
- **FFmpeg** - Video processing engine
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings
- **PostgreSQL/MySQL** - Primary database (TBD)
- **Redis** - Caching and job queue (optional)
- **Celery** - Asynchronous task processing (optional)

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and static file serving (production)

## 🚀 Getting Started

### Prerequisites

- **Backend**: Python 3.11+, pip, virtualenv
- **Frontend**: Flutter SDK 3.x+, Dart 3.x+
- **System**: FFmpeg installed and available in PATH
- **Optional**: Docker and Docker Compose for containerized deployment

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. API documentation can be accessed at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Flutter dependencies:
   ```bash
   flutter pub get
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoint configuration
   ```

4. Run the app:
   ```bash
   # For mobile
   flutter run
   
   # For web
   flutter run -d chrome
   
   # For desktop
   flutter run -d macos    # or windows/linux
   ```

## 📋 Development Workflow

1. **Feature Development**: Create feature branches from `main`
2. **Code Standards**: Follow the language-specific style guides (PEP 8 for Python, Effective Dart for Flutter)
3. **Testing**: Write unit and integration tests for new features
4. **Documentation**: Update relevant docs when changing architecture or APIs
5. **Pull Requests**: Submit PRs with clear descriptions and link to related issues

## 📚 Documentation

Additional documentation can be found in the `/docs` directory:

- `architecture.md` - System architecture and design decisions
- `api.md` - API endpoints and schemas
- `deployment.md` - Deployment guides and infrastructure setup
- `contributing.md` - Contribution guidelines

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
flutter test
```

## 🐳 Docker Deployment

Build and run the entire stack with Docker Compose:

```bash
docker-compose up --build
```

This will start:
- Backend API on port 8000
- Frontend web app on port 8080
- Database on port 5432 (PostgreSQL) or 3306 (MySQL)

## 📝 License

TBD

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines in `/docs/contributing.md` before submitting pull requests.

## 📧 Contact

For questions or support, please open an issue on the repository.
