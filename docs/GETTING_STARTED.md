# Getting Started - Claude Code API Service

A quick guide to get up and running with the Claude Code API Service in minutes.

## What is Claude Code API Service?

A local REST API that wraps Claude Code CLI, enabling any application to use Claude as an LLM provider with:
- **Cost optimization** through Claude Code Max subscription
- **Intelligent model routing** (Haiku/Sonnet/Opus)
- **Worker pool** for parallel execution
- **Budget management** per project
- **Usage tracking** and analytics

## Prerequisites

- **Python 3.10+**
- **Claude Code CLI** installed and authenticated
- **Redis** (optional, for caching)

### Install Claude Code CLI

```bash
# Follow instructions at https://claude.com/code
# Or use homebrew (Mac)
brew install anthropics/claude-code/claude
```

Authenticate:
```bash
claude auth login
```

### Install Redis (Optional)

```bash
# Mac
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/claude-code-api-service.git
cd claude-code-api-service
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `aiosqlite` - Budget tracking database
- `redis` - Caching (optional)

### 3. Environment Setup (Optional)

Create a `.env` file for custom configuration:

```bash
# .env
MAX_WORKERS=5
PORT=8080
DATABASE_PATH=data/budgets.db
REDIS_URL=redis://localhost:6379
```

### 4. Start the Server

```bash
python main.py
```

You should see:
```
✓ Worker pool started (max_workers=5)
✓ Budget manager initialized
✓ API services ready
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Quick Start Guide

### Your First API Call

Test with curl:

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain what a REST API is in one sentence."}
    ],
    "project_id": "demo"
  }'
```

Response:
```json
{
  "id": "abc123...",
  "model": "sonnet",
  "content": "A REST API is a web service architecture...",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 32,
    "total_tokens": 47
  },
  "cost": 0.000525,
  "project_id": "demo"
}
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "messages": [
            {"role": "user", "content": "What is FastAPI?"}
        ],
        "project_id": "my-app"
    }
)

data = response.json()
print(f"Response: {data['content']}")
print(f"Cost: ${data['cost']:.6f}")
```

### Check Usage

```bash
curl "http://localhost:8080/v1/usage?project_id=demo&period=month"
```

## Interactive Documentation

FastAPI provides automatic interactive documentation:

**Swagger UI:** http://localhost:8080/docs
- Try endpoints directly in your browser
- See request/response schemas
- Test different parameters

**ReDoc:** http://localhost:8080/redoc
- Clean, readable API reference
- Organized by endpoint

## Core Concepts

### 1. Model Auto-Selection

Don't specify a model? The API automatically selects the best one:

```python
# Simple task → Haiku
{"messages": [{"role": "user", "content": "List Python files"}]}

# Complex task → Sonnet
{"messages": [{"role": "user", "content": "Analyze and refactor this codebase"}]}

# Large context → Opus
{"messages": [{"role": "user", "content": "Review this 50k line codebase"}], "max_tokens": 15000}
```

Override with explicit model:
```python
{"messages": [...], "model": "haiku"}  # Force Haiku
```

### 2. Project-Based Budgets

Track usage separately per project:

```python
# Different projects, independent budgets
{"messages": [...], "project_id": "chatbot"}
{"messages": [...], "project_id": "code-analyzer"}
{"messages": [...], "project_id": "research-tool"}
```

Check usage:
```bash
curl "http://localhost:8080/v1/usage?project_id=chatbot&period=month"
```

### 3. Worker Pool for Parallel Execution

The API manages a pool of Claude CLI processes:

```python
# Submit multiple requests - they run in parallel
import concurrent.futures
import requests

def ask_claude(question):
    response = requests.post(
        "http://localhost:8080/v1/chat/completions",
        json={"messages": [{"role": "user", "content": question}]}
    )
    return response.json()

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    questions = ["What is Python?", "What is Rust?", "What is Go?"]
    results = list(executor.map(ask_claude, questions))
```

Or use the built-in batch endpoint:
```python
response = requests.post(
    "http://localhost:8080/v1/batch",
    json={
        "prompts": [
            {"prompt": "What is Python?", "id": "q1"},
            {"prompt": "What is Rust?", "id": "q2"},
            {"prompt": "What is Go?", "id": "q3"}
        ]
    }
)
```

### 4. Budget Enforcement

Set monthly token limits per project:

```python
from src.budget_manager import BudgetManager
import asyncio

async def set_budget():
    budget_manager = BudgetManager(db_path="data/budgets.db")

    # Set 100k token monthly limit
    await budget_manager.set_budget(
        project_id="my-app",
        monthly_limit=100000,
        name="My Application"
    )

asyncio.run(set_budget())
```

Requests that exceed budget return `429` status.

## Next Steps

### Run Examples

```bash
# Basic usage examples
python examples/api_usage.py

# Build a chatbot
python examples/simple_chatbot.py

# Batch document processing
python examples/batch_processor.py

# Code analyzer with model routing
python examples/code_analyzer.py
```

### Read the Documentation

- **[API Reference](API_REFERENCE.md)** - Complete endpoint documentation
- **[Client Library](CLIENT_LIBRARY.md)** - Python client with async support
- **[Deployment Guide](DEPLOYMENT.md)** - Docker, production setup
- **[Architecture](ARCHITECTURE.md)** - System design and components

### Configure for Your Use Case

**High throughput:**
```python
# main.py
worker_pool = WorkerPool(max_workers=10)  # Increase workers
```

**Strict budget control:**
```python
# Set aggressive limits
await budget_manager.set_budget(
    project_id="strict-project",
    monthly_limit=10000  # Small budget
)
```

**Custom model routing:**
```python
# src/model_router.py
# Modify auto_select_model() function
```

## Health Checks

Monitor API status:

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": {
    "worker_pool": "running",
    "budget_manager": "initialized"
  }
}
```

## Common Issues

### "Services not initialized" error

The worker pool takes ~1 second to start. Wait a moment after starting the server.

### "Task failed: Process exited with code 1"

Claude CLI error. Check:
- Claude CLI is installed: `which claude`
- Authenticated: `claude auth status`
- Model access: Try `claude -p "Hello" --model sonnet`

### "Budget exceeded" (429)

Your project hit its monthly token limit. Options:
1. Increase budget
2. Use cheaper models (Haiku)
3. Wait until next month
4. Use different project_id

### Port 8080 already in use

Change port:
```python
# main.py
uvicorn.run(app, host="0.0.0.0", port=8081)
```

## Getting Help

- **Issues:** GitHub Issues
- **Docs:** http://localhost:8080/docs
- **Logs:** Check console output for errors

## Quick Reference

```bash
# Start server
python main.py

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'

# Batch processing
curl -X POST http://localhost:8080/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"prompts": [{"prompt": "Task 1"}, {"prompt": "Task 2"}]}'

# Check usage
curl "http://localhost:8080/v1/usage?project_id=demo"

# Health check
curl http://localhost:8080/health

# Interactive docs
open http://localhost:8080/docs
```

## What's Next?

You're ready to start building! Try:
1. **Build a chatbot** - See `examples/simple_chatbot.py`
2. **Process documents in batch** - See `examples/batch_processor.py`
3. **Create a code analyzer** - See `examples/code_analyzer.py`
4. **Deploy to production** - See `DEPLOYMENT.md`
5. **Use the Python client** - See `CLIENT_LIBRARY.md`

Happy building! 🚀
