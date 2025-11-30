"""
FastAPI main application.
Configures CORS, includes routers, serves static files and templates.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routers import admin, events, health, match, photos
from app.core.config import settings
from app.core.logging import setup_logging

# Copilot: Create FastAPI app with /healthz and include routers from api. Add CORS for localhost.

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="FindMe - Face-based Event Photo Finder",
    description="API for finding event photos using face recognition",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(events.router, prefix=settings.api_v1_prefix)
app.include_router(photos.router, prefix=settings.api_v1_prefix)
app.include_router(match.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve the HTML UI
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the test UI."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    return HTMLResponse(
        content="<h1>FindMe API</h1><p>Visit /docs for API documentation</p>"
    )


# Serve the Admin Dashboard
@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Serve the admin dashboard."""
    template_path = Path(__file__).parent / "templates" / "admin.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    return HTMLResponse(
        content="<h1>Admin Dashboard</h1><p>Dashboard not found</p>"
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Ensure data directory exists
    settings.ensure_data_dir()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
