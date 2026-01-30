# Claude Code API Service

A flexible, reusable local API service that enables any prototype or application to use Claude Code CLI as the LLM provider.

## Overview

This service wraps Claude Code CLI with a REST + WebSocket API, enabling:
- **Cost Optimization**: Use Claude Code Max subscription instead of separate API costs
- **Model Routing**: Automatic routing to Haiku/Sonnet/Opus based on task complexity
- **Parallel Execution**: Multiple concurrent Claude sessions via worker pool
- **Budget Management**: Per-project token budgets and usage tracking
- **Rapid Prototyping**: Drop-in LLM provider for any application

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server will start at `http://localhost:8080`

### API Documentation

Visit `http://localhost:8080/docs` for interactive API documentation.

### Health Check

```bash
curl http://localhost:8080/health
```

## Development Status

**Current Phase**: Bootstrap skeleton complete
**Next Phase**: Feature implementation via orchestrator

## Features (Planned)

1. ✅ Basic FastAPI skeleton
2. ⏳ Worker Pool Manager
3. ⏳ Model Auto-Router
4. ⏳ Budget Manager
5. ⏳ REST API Endpoints
6. ⏳ WebSocket Streaming
7. ⏳ Authentication Middleware
8. ⏳ Token Tracking
9. ⏳ Redis Integration
10. ⏳ Python Client Library
11. ⏳ Documentation

## Architecture

```
Client Apps → FastAPI Server → Worker Pool → Claude CLI
                    ↓
                  Redis (caching, queue)
                    ↓
                SQLite (usage tracking)
```

## Built With

- **FastAPI**: Modern Python web framework
- **Claude Code CLI**: LLM inference engine
- **Redis**: Caching and queueing
- **SQLite**: Usage tracking and budgets

## License

MIT
