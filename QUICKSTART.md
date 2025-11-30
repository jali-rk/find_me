# FindMe Project - Quick Reference

## 🎯 Getting Started

### 1. Setup (First Time)
```bash
cd backend
./setup.sh
```

### 2. Start Server
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 3. Access Application
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## 📋 API Quick Reference

### Create Event
```bash
curl -X POST http://localhost:8000/api/v1/events
```

### Upload Photos
```bash
curl -X POST http://localhost:8000/api/v1/events/{event_id}/photos \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg"
```

### Match Selfie
```bash
curl -X POST http://localhost:8000/api/v1/events/{event_id}/match \
  -F "selfie=@selfie.jpg"
```

## 🧪 Development Commands

### Run Tests
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/test_health.py    # Run specific test
```

### Code Quality
```bash
black app/ tests/              # Format code
ruff check app/ tests/         # Lint code
mypy app/services/ app/domain/ # Type check
```

## 📁 Key Files

- `app/main.py` - FastAPI application entry point
- `app/core/config.py` - Configuration settings
- `app/api/routers/` - API endpoints
- `app/services/` - Business logic
- `app/templates/index.html` - Web UI

## 🔧 Configuration (.env)

```env
DATA_DIR=./data
FACE_MODEL_NAME=antelopev2
EMBEDDING_DIM=512
FACE_MATCH_THRESHOLD=0.35
MAX_UPLOAD_MB=15
LOG_LEVEL=INFO
```

## 📦 Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── core/         # Config, logging
│   ├── api/          # API routes
│   ├── domain/       # Pydantic models
│   ├── services/     # Business logic
│   ├── utils/        # Helpers
│   ├── templates/    # HTML
│   └── static/       # CSS
├── tests/            # Test suite
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## ✅ Acceptance Criteria

- [x] Health check endpoint works
- [x] Can create events
- [x] Can upload photos with face detection
- [x] Can match selfies
- [x] Results sorted by similarity score
- [x] Data persists on disk
- [x] Tests pass

## 🎓 How It Works

1. **Upload Photos**: Faces detected → embeddings generated → FAISS index updated
2. **Match Selfie**: Selfie faces detected → compare against index → return matches
3. **Persistence**: Index and metadata saved to `data/events/{event_id}/`

## 🚀 Next Steps

To test the application:

1. Start the server
2. Open http://localhost:8000 in your browser
3. Create a new event
4. Upload some photos with faces
5. Upload a selfie to find matching photos

## 📝 Notes

- Phase 1 is local-only (no cloud services)
- No authentication required
- CPU-based inference
- Images stored on disk
- FAISS index for vector search
