"""FastAPI application entry point."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.config import get_settings
from app.monitoring.metrics import setup_metrics
from app.monitoring.telemetry import setup_telemetry

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

settings = get_settings()

app = FastAPI(
    title="AI Agent Platform",
    description="Enterprise-grade Agentic AI orchestration platform",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    setup_telemetry(settings)
    setup_metrics(__version__)


@app.get("/")
async def root():
    return {
        "name": "AI Agent Platform",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
