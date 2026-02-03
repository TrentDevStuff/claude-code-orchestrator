"""
Claude Code API Service
A flexible, reusable API service that wraps Claude Code CLI for rapid prototyping.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="Claude Code API Service",
    description="API wrapper around Claude Code CLI for rapid prototyping",
    version="0.1.0"
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic models
class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.1.0"
    }

@app.get("/")
def root():
    """Root endpoint with API info"""
    return {
        "name": "Claude Code API Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
