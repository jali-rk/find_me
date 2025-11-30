# FindMe - Face-based Event Photo Finder

**Phase 1 MVP**: Local proof of concept for face-based event photo retrieval.

## Overview

FindMe allows photographers to upload event photos and guests to find photos containing their face by uploading a selfie. The system uses face detection and embedding generation (InsightFace) with vector similarity search (FAISS) to match faces across photos.

## Features

- ✅ Face detection and embedding generation using InsightFace (ArcFace)
- ✅ Vector similarity search using FAISS (cosine similarity)
- ✅ Per-event data persistence (photos, index, metadata)
- ✅ Bulk photo upload with multi-status responses
- ✅ Selfie matching with similarity scores and bounding boxes
- ✅ Clean FastAPI architecture with typed responses
- ✅ Simple HTML test interface

## Tech Stack

- **Runtime**: Python 3.10+
- **Web**: FastAPI, Uvicorn
- **ML**: InsightFace (ArcFace), onnxruntime
- **Vector Index**: FAISS (CPU)
- **Image Processing**: Pillow, numpy
- **Code Quality**: Ruff, Black, mypy
- **Testing**: pytest

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Configuration and logging
│   ├── api/                 # API routers and endpoints
│   ├── domain/              # Pydantic models
│   ├── services/            # Business logic
│   ├── utils/               # Helper functions
│   ├── templates/           # HTML UI
│   └── static/              # CSS, JS
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── pyproject.toml          # Project configuration
└── .env.example            # Environment template
```

## Installation

1. **Clone the repository**:
   ```bash
   cd /Users/jaliya/Projects/FindMe/backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

## Usage

### Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### Using the Web Interface

1. **Create Event**: Click "Create New Event" to generate an event ID
2. **Upload Photos**: Select event ID and upload multiple event photos
3. **Match Selfie**: Upload a selfie to find matching photos

### Using the API

#### 1. Create an Event
```bash
curl -X POST http://localhost:8000/api/v1/events
```

Response:
```json
{
  "event_id": "01HX...",
  "data_dir": "./data/events/01HX..."
}
```

#### 2. Upload Photos
```bash
curl -X POST http://localhost:8000/api/v1/events/{event_id}/photos \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg"
```

#### 3. Match Selfie
```bash
curl -X POST http://localhost:8000/api/v1/events/{event_id}/match \
  -F "selfie=@my_selfie.jpg"
```

#### 4. Retrieve Photo
```bash
curl http://localhost:8000/api/v1/events/{event_id}/photos/{photo_id} \
  -o photo.jpg
```

## API Endpoints

- `GET /healthz` - Health check
- `POST /api/v1/events` - Create new event
- `POST /api/v1/events/{event_id}/photos` - Upload photos
- `POST /api/v1/events/{event_id}/match` - Match selfie
- `GET /api/v1/events/{event_id}/photos/{photo_id}` - Get photo

## Configuration

Edit `.env` to customize:

```env
DATA_DIR=./data                          # Data storage directory
FACE_MODEL_NAME=antelopev2               # InsightFace model
EMBEDDING_DIM=512                        # Embedding dimension
FACE_MATCH_THRESHOLD=0.35                # Min similarity score
MAX_UPLOAD_MB=15                         # Max file size
ALLOWED_IMAGE_TYPES=jpeg,jpg,png,webp   # Allowed formats
LOG_LEVEL=INFO                           # Logging level
```

## Data Storage

Each event creates a directory structure:

```
data/events/{event_id}/
├── photos/              # Original uploaded images
├── index.faiss          # FAISS vector index
└── metadata.jsonl       # Face metadata (one JSON per line)
```

Metadata format:
```json
{"face_id":"...", "photo_id":"...", "path":"photos/abc.jpg", 
 "bbox":[x,y,w,h], "embedding_id":N, "width":W, "height":H}
```

## Development

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type check
mypy app/services/ app/domain/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_health.py
```

## How It Works

1. **Photo Upload**: Images are processed, faces detected, embeddings generated and added to FAISS index
2. **Selfie Matching**: Selfie faces are detected, embeddings compared against index using cosine similarity
3. **Result Ranking**: Matches above threshold are aggregated by photo, sorted by score
4. **Persistence**: Index and metadata saved to disk for restart persistence

## Limitations (Phase 1)

- Local only (no cloud storage)
- No authentication/authorization
- No database (file-based storage)
- Single server instance
- CPU-only inference

## Future Phases

- Cloud deployment (S3, CDN)
- Database integration
- Authentication and payment
- Mobile apps
- GPU acceleration
- Advanced clustering

## License

Copyright © 2025. All rights reserved.

## Support

For issues or questions about this Phase 1 MVP, please refer to the project documentation.
