"""
FastAPI application for Knowledge Forge backend.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import journey, chat, session
from .streaming import stream_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.

    SSE Graceful Shutdown Solution
    ==============================
    Problem: SSE connections block uvicorn shutdown, causing Ctrl-C to hang.

    Root cause (deadlock):
    1. Ctrl-C triggers uvicorn graceful shutdown
    2. Uvicorn waits for SSE connections to close
    3. SSE generators block on queue.get() waiting for events
    4. Lifespan shutdown (which could signal queues) only runs AFTER connections close
    5. Deadlock: connections wait for signal, lifespan waits for connections

    Solution:
    - Register signal handlers via loop.add_signal_handler() during startup
    - These handlers run IMMEDIATELY when SIGINT arrives (before uvicorn's wait)
    - Handler closes all SSE streams (puts None in queues to unblock generators)
    - Handler schedules a clean exit after a brief delay for streams to close
    - Uses sys.exit(0) instead of re-raising SIGINT to avoid traceback noise

    Why other approaches failed:
    - Lifespan shutdown: runs too late (after connections close)
    - asyncio.wait_for timeout: uvicorn still waits for generator completion
    - --timeout-graceful-shutdown: doesn't help if connections don't close
    - os.kill(SIGINT): works but produces ugly CancelledError tracebacks
    """
    loop = asyncio.get_running_loop()
    shutdown_triggered = False

    def handle_shutdown_signal():
        """Close all SSE streams immediately on SIGINT/SIGTERM."""
        nonlocal shutdown_triggered
        if shutdown_triggered:
            return  # Prevent re-entry
        shutdown_triggered = True

        print("\n[shutdown] Closing all SSE streams...")
        stream_manager.close_all_streams()

        # Remove our handlers
        loop.remove_signal_handler(signal.SIGINT)
        loop.remove_signal_handler(signal.SIGTERM)

        # Schedule clean exit after brief delay for streams to close
        # Using sys.exit avoids the CancelledError tracebacks from os.kill(SIGINT)
        async def delayed_exit():
            await asyncio.sleep(0.1)  # Let streams finish closing
            print("[shutdown] Exiting...")
            sys.exit(0)

        asyncio.create_task(delayed_exit())

    # Register signal handlers that run in the event loop
    loop.add_signal_handler(signal.SIGINT, handle_shutdown_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown_signal)

    yield

    # Shutdown complete (handlers already removed in signal handler)

# =============================================================================
# Create FastAPI App
# =============================================================================

app = FastAPI(
    title="Knowledge Forge API",
    description="Backend API for Knowledge Forge learning platform",
    version="0.1.0",
    lifespan=lifespan,
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
