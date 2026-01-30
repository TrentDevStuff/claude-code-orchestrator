"""
Claude Code API Service
A flexible, reusable API service that wraps Claude Code CLI for rapid prototyping.
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from src.worker_pool import WorkerPool
from src.budget_manager import BudgetManager
from src.auth import AuthManager, initialize_auth
from src.api import router as api_router, initialize_services
from src.websocket import initialize_websocket, websocket_endpoint


# Global service instances
worker_pool = None
budget_manager = None
auth_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes and cleans up worker pool, budget manager, and auth manager.
    """
    global worker_pool, budget_manager, auth_manager

    # Startup: Initialize services
    worker_pool = WorkerPool(max_workers=5)
    worker_pool.start()

    budget_manager = BudgetManager(db_path="data/budgets.db")

    auth_manager = AuthManager(db_path="data/auth.db")

    # Initialize API services
    initialize_services(worker_pool, budget_manager)
    initialize_auth(auth_manager)

    # Initialize WebSocket service
    initialize_websocket(worker_pool, budget_manager)

    print("✓ Worker pool started (max_workers=5)")
    print("✓ Budget manager initialized")
    print("✓ Auth manager initialized")
    print("✓ API services ready")
    print("✓ WebSocket streaming ready")

    yield

    # Shutdown: Cleanup
    if worker_pool:
        worker_pool.stop()
        print("✓ Worker pool stopped")


app = FastAPI(
    title="Claude Code API Service",
    description="API wrapper around Claude Code CLI for rapid prototyping",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


# Basic models
class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "services": {
            "worker_pool": "running" if worker_pool and worker_pool.running else "stopped",
            "budget_manager": "initialized" if budget_manager else "not initialized",
            "auth_manager": "initialized" if auth_manager else "not initialized"
        }
    }


@app.get("/")
def root():
    """Root endpoint with API info"""
    return {
        "name": "Claude Code API Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "batch": "/v1/batch",
            "usage": "/v1/usage",
            "route": "/v1/route",
            "stream": "ws://localhost:8080/v1/stream"
        }
    }


@app.websocket("/v1/stream")
async def stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming chat.

    Protocol:
    - Client sends: {"type": "chat", "model": "haiku", "messages": [...]}
    - Server streams: {"type": "token", "content": "..."}
    - Server finishes: {"type": "done", "usage": {...}, "cost": 0.001}
    """
    await websocket_endpoint(websocket)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8006))  # Use registered port 8006
    uvicorn.run(app, host="0.0.0.0", port=port)
