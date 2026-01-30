# Redis Cache and Queue

## Overview

The `RedisCache` class provides Redis-backed caching and queuing functionality for the Claude Code API Service. It handles response caching with TTL and request queuing with graceful fallback when Redis is unavailable.

## Features

- **Response Caching**: Store API responses with configurable TTL
- **Request Queuing**: FIFO queue for task management
- **Graceful Degradation**: Operations fail gracefully when Redis is unavailable
- **Connection Management**: Automatic connection retry and health checks
- **Error Handling**: Comprehensive error handling for Redis and JSON errors

## Installation

Redis is already included in `requirements.txt`:

```
redis==5.0.1
```

To install Redis server:

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

## Basic Usage

```python
from src.cache import RedisCache

# Initialize cache (will connect to localhost:6379)
cache = RedisCache()

# Check connection
if cache.is_connected():
    print("Redis is available")
```

## API Reference

### Initialization

```python
cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    socket_timeout=5.0,
    socket_connect_timeout=5.0
)
```

### Caching Operations

#### cache_response(prompt_hash, response, ttl=3600)

Cache a response with TTL.

```python
import hashlib

prompt = "What is 2+2?"
prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

response = {
    "completion": "4",
    "usage": {"input_tokens": 10, "output_tokens": 5},
    "cost": 0.001
}

# Cache for 1 hour (default)
cache.cache_response(prompt_hash, response)

# Cache for 10 minutes
cache.cache_response(prompt_hash, response, ttl=600)
```

**Returns:** `True` if cached successfully, `False` otherwise

#### get_cached_response(prompt_hash)

Retrieve a cached response.

```python
cached = cache.get_cached_response(prompt_hash)

if cached:
    print(f"Cache hit: {cached['completion']}")
else:
    print("Cache miss - fetch from API")
```

**Returns:** `Dict[str, Any]` if found, `None` otherwise

### Queue Operations

#### queue_request(request_data)

Add a request to the queue (FIFO).

```python
request = {
    "task_id": "abc-123",
    "prompt": "Analyze this data",
    "model": "sonnet",
    "priority": "high"
}

cache.queue_request(request)
```

**Returns:** `True` if queued successfully, `False` otherwise

#### dequeue_request()

Remove and return the next request from the queue.

```python
next_request = cache.dequeue_request()

if next_request:
    process_request(next_request)
else:
    print("Queue is empty")
```

**Returns:** `Dict[str, Any]` if queue not empty, `None` otherwise

#### get_queue_length()

Get the current queue length.

```python
length = cache.get_queue_length()
print(f"Queue has {length} items")
```

**Returns:** `int` number of items in queue

### Utility Operations

#### clear_cache()

Clear all cached responses.

```python
cache.clear_cache()
```

#### clear_queue()

Clear all queued requests.

```python
cache.clear_queue()
```

#### close()

Close the Redis connection.

```python
cache.close()
```

## Integration Example

```python
from src.cache import RedisCache
from src.worker_pool import WorkerPool
import hashlib

# Initialize components
cache = RedisCache()
pool = WorkerPool(max_workers=5)

def process_request(prompt, model="sonnet"):
    # Check cache first
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cached = cache.get_cached_response(prompt_hash)

    if cached:
        print("Cache hit!")
        return cached

    # Cache miss - process with worker pool
    print("Cache miss - processing...")
    task_id = pool.submit(prompt, model=model)
    result = pool.get_result(task_id)

    # Cache the result
    if result.status == "completed":
        response = {
            "completion": result.completion,
            "usage": result.usage,
            "cost": result.cost
        }
        cache.cache_response(prompt_hash, response, ttl=3600)

    return response

# Use it
result = process_request("What is the capital of France?")
print(result["completion"])
```

## Error Handling

The cache handles errors gracefully:

- **Connection errors**: Operations return `False`/`None` without raising exceptions
- **Redis errors**: Logged and handled gracefully
- **JSON errors**: Invalid data is caught and logged
- **Expired data**: Automatically cleaned up on access

```python
# Safe to use even if Redis is down
cache = RedisCache()

# These won't raise exceptions
success = cache.cache_response("key", {"data": "value"})  # Returns False if Redis down
cached = cache.get_cached_response("key")  # Returns None if Redis down
```

## Testing

Run the tests:

```bash
# All cache tests
pytest tests/test_cache.py -v

# Specific test
pytest tests/test_cache.py::test_cache_and_retrieve -v

# With coverage
pytest tests/test_cache.py --cov=src.cache
```

## Performance Considerations

- **Cache TTL**: Default 3600s (1 hour). Adjust based on data freshness needs.
- **Queue size**: Monitor queue length to prevent memory issues.
- **Connection pooling**: Redis client handles connection pooling internally.
- **Timeout settings**: Adjust socket timeouts for slow networks.

## Configuration

For production, configure via environment variables:

```bash
export REDIS_HOST=redis.example.com
export REDIS_PORT=6379
export REDIS_PASSWORD=secret
export REDIS_DB=0
```

Then in your code:

```python
import os

cache = RedisCache(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    db=int(os.getenv("REDIS_DB", 0))
)
```

## Monitoring

Check Redis connection:

```python
if cache.is_connected():
    print("✓ Redis connected")
    print(f"Queue length: {cache.get_queue_length()}")
else:
    print("✗ Redis unavailable - operating in fallback mode")
```

## Troubleshooting

### Connection Refused

```
RedisConnectionError: Connection refused
```

**Solution**: Ensure Redis server is running:

```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis
redis-server
```

### Authentication Failed

```
RedisConnectionError: NOAUTH Authentication required
```

**Solution**: Provide password:

```python
cache = RedisCache(password="your_redis_password")
```

### Timeout Issues

If operations are timing out, increase timeout values:

```python
cache = RedisCache(
    socket_timeout=10.0,
    socket_connect_timeout=10.0
)
```
