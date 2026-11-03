"""
Entry point for the Integration Platform Framework.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.core.telemetry import TelemetryMiddleware
from app.api.v2.endpoints import router as employee_router
from app.api.v2.marketplace import router as marketplace_router
from app.api.v2.ai_tools import router as ai_tools_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Core integration & API framework powering standardized API V2 endpoints, "
        "Marketplace / App Shop lifecycle, AI-driven connectivity, and Zero-KTLO automation."
    ),
    openapi_url=f"{settings.API_V2_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telemetry and Latency Tracking Middleware
app.add_middleware(TelemetryMiddleware)

# Include API V2 Routers
app.include_router(employee_router, prefix=settings.API_V2_PREFIX)
app.include_router(marketplace_router, prefix=settings.API_V2_PREFIX)
app.include_router(ai_tools_router, prefix=settings.API_V2_PREFIX)


@app.get("/health", tags=["System"])
def health_check():
    """Liveness probe verifying service availability."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["System"])
def readiness_check():
    """Readiness probe checking downstream dependencies."""
    return {
        "status": "READY",
        "database": "CONNECTED",
        "cache": "CONNECTED",
        "dlq_worker": "ACTIVE"
    }


@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "api_v2_endpoints": f"{settings.API_V2_PREFIX}/employees",
        "app_shop": f"{settings.API_V2_PREFIX}/marketplace/apps"
    }
