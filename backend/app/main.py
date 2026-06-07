"""Lead Gen Agent — FastAPI Application Entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_router
from app.config import settings
from app.core.errors import AppError, app_error_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info(f"Starting Lead Gen Agent — environment: {settings.environment}")
    yield
    logger.info("Shutting down Lead Gen Agent")


app = FastAPI(
    title="Lead Gen Agent API",
    description="AI-powered lead generation, scoring, and outreach API",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── Middleware ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───

@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError):
    return await app_error_handler(request, exc)


# ─── Routes ───

app.include_router(api_router)


# ─── Health Check ───

@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint — API info."""
    return {
        "name": "Lead Gen Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }