"""
FastAPI application for Knowledge Forge backend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import journey, chat, session

# =============================================================================
# Create FastAPI App
# =============================================================================

app = FastAPI(
    title="Knowledge Forge API",
    description="Backend API for Knowledge Forge learning platform",
    version="0.1.0",
)

# =============================================================================
# CORS Middleware
# =============================================================================

# Allow requests from frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Include Routers
# =============================================================================

app.include_router(journey.router, prefix="/api/journey", tags=["journey"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(session.router, prefix="/api/session", tags=["session"])
# Alias: /api/sessions (with 's') for frontend compatibility
app.include_router(session.router, prefix="/api/sessions", tags=["session"], include_in_schema=False)


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "knowledge-forge-api"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Knowledge Forge API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
