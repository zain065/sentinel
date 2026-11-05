"""
SENTINEL AI - Main Application Entrypoint
FastAPI application with CORS, database lifecycle, and modular route inclusion.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.database.db import init_db
from app.api.routes import router as api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Smart Sensor Trust and Intrusion Detection System for Urban SCADA Infrastructure. "
        "Provides multi-tier anomaly detection, physical consistency verification, "
        "transparent 0-100 sensor trust scoring, and FDI attack simulation."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration (Enables seamless frontend connectivity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initializes database schema on startup."""
    init_db()


# Include REST API routes under /api
app.include_router(api_router, prefix=settings.API_PREFIX)

# Static Asset Mounts & Root Frontend Route
frontend_path = settings.PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")
    assets_dir = frontend_path / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(str(frontend_path / "index.html"))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

