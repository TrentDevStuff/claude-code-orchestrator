"""
Claude Code API Service
A flexible, reusable API service that wraps Claude Code CLI for rapid prototyping.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from src.worker_pool import WorkerPool
from src.budget_manager import BudgetManager
from src.api import router as api_router, initialize_services


# Global service instances
worker_pool = None
budget_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes and cleans up worker pool and budget manager.
    """
    global worker_pool, budget_manager

    # Startup: Initialize services
    worker_pool = WorkerPool(max_workers=5)
    worker_pool.start()

    budget_manager = BudgetManager(db_path="data/budgets.db")

    # Initialize API services
    initialize_services(worker_pool, budget_manager)

    print("✓ Worker pool started (max_workers=5)")
    print("✓ Budget manager initialized")
    print("✓ API services ready")

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
            "budget_manager": "initialized" if budget_manager else "not initialized"
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
            "route": "/v1/route"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
