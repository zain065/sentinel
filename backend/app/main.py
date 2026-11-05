"""
SENTINEL AI - Main Application Entrypoint
FastAPI application with CORS, database lifecycle, and modular route inclusion.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


# Include REST API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "problem_statement": "Problem 40: Urban Sensor Network Trustworthiness & FDI Detection",
        "documentation": "/docs",
        "health_check": f"{settings.API_PREFIX}/health",
        "dataset_status": f"{settings.API_PREFIX}/dataset/status",
        "sensors": f"{settings.API_PREFIX}/sensors"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
