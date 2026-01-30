# Deployment Guide - Claude Code API Service

Production deployment guide for the Claude Code API Service.

## Docker Deployment

### Using Docker Compose (Recommended)

The repository includes a complete `docker-compose.yml` setup.

**1. Build and start:**

```bash
docker-compose up -d
```

This starts:
- Claude API Service (port 8080)
- Redis (port 6379)

**2. Check status:**

```bash
docker-compose ps
docker-compose logs -f claude-api
```

**3. Stop:**

```bash
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t claude-api-service .

# Run container
docker run -d \
  --name claude-api \
  -p 8080:8080 \
  -v ~/.claude:/root/.claude \
  -e MAX_WORKERS=10 \
  claude-api-service
```

**Mount Claude CLI credentials:**
```bash
-v ~/.claude:/root/.claude
```

This ensures the container can access your Claude CLI authentication.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | API server port |
| `MAX_WORKERS` | 5 | Worker pool size |
| `DATABASE_PATH` | data/budgets.db | SQLite database path |
| `REDIS_URL` | redis://localhost:6379 | Redis connection URL |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Example `.env` file:**

```bash
PORT=8080
MAX_WORKERS=10
DATABASE_PATH=/data/budgets.db
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
```

## Production Considerations

### 1. Worker Pool Sizing

Set `MAX_WORKERS` based on your server resources:

```python
# main.py
worker_pool = WorkerPool(max_workers=int(os.getenv("MAX_WORKERS", 10)))
```

**Recommendations:**
- **Small server (2 CPU)**: 3-5 workers
- **Medium server (4 CPU)**: 8-10 workers
- **Large server (8+ CPU)**: 15-20 workers

### 2. Database Persistence

Ensure the SQLite database is persisted:

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data
```

Or use an external database (PostgreSQL/MySQL) for production.

### 3. Redis Configuration

For production, configure Redis persistence:

```yaml
# docker-compose.yml
redis:
  image: redis:alpine
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

### 4. Reverse Proxy (Nginx)

Put the API behind Nginx for:
- SSL/TLS termination
- Load balancing
- Request throttling

**Example Nginx config:**

```nginx
upstream claude_api {
    server localhost:8080;
}

server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://claude_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
    }
}
```

### 5. Monitoring

Add health check monitoring:

```bash
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 6. Logging

Configure structured logging for production:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### 7. Rate Limiting

Add rate limiting middleware:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

@app.post("/v1/chat/completions")
@limiter.limit("100/minute")
def chat_completion(request: Request, ...):
    ...
```

### 8. Authentication

Add API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

@app.post("/v1/chat/completions")
def chat_completion(request: ..., api_key: str = Depends(verify_api_key)):
    ...
```

## Kubernetes Deployment

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claude-api
  template:
    metadata:
      labels:
        app: claude-api
    spec:
      containers:
      - name: claude-api
        image: claude-api-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: MAX_WORKERS
          value: "10"
        - name: DATABASE_PATH
          value: "/data/budgets.db"
        - name: REDIS_URL
          value: "redis://redis:6379"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: claude-config
          mountPath: /root/.claude
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: claude-api-data
      - name: claude-config
        secret:
          secretName: claude-credentials
```

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: claude-api
spec:
  selector:
    app: claude-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Scaling

### Horizontal Scaling

The API is stateless and can be scaled horizontally:

```bash
# Docker Compose
docker-compose up --scale claude-api=5

# Kubernetes
kubectl scale deployment claude-api --replicas=10
```

**Shared state:**
- Redis for caching
- Shared SQLite database (or use PostgreSQL/MySQL)

### Vertical Scaling

Increase `MAX_WORKERS` for more concurrent Claude CLI processes:

```bash
# Environment variable
MAX_WORKERS=20 python main.py

# Docker
docker run -e MAX_WORKERS=20 claude-api-service
```

## Security

### 1. API Keys

Require API keys for all requests:

```python
API_KEYS = set(os.getenv("API_KEYS", "").split(","))

async def verify_api_key(api_key: str = Header(...)):
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401)
```

### 2. HTTPS Only

Enforce HTTPS in production:

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
```

### 3. CORS

Configure CORS restrictively:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 4. Rate Limiting

Protect against abuse:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@limiter.limit("100/minute")
@app.post("/v1/chat/completions")
def endpoint(...):
    ...
```

## Backup & Recovery

### Database Backups

```bash
# Backup SQLite database
sqlite3 data/budgets.db ".backup 'backups/budgets-$(date +%Y%m%d).db'"

# Restore
cp backups/budgets-20260130.db data/budgets.db
```

### Redis Persistence

Configure Redis to persist data:

```bash
# redis.conf
appendonly yes
appendfsync everysec
```

## Troubleshooting

### High Memory Usage

- Reduce `MAX_WORKERS`
- Check for memory leaks in Claude CLI processes
- Monitor with: `docker stats`

### Slow Response Times

- Check worker pool utilization: GET `/health`
- Increase `MAX_WORKERS`
- Check Redis connection
- Monitor Claude CLI process times

### Database Lock Errors

- Use connection pooling
- Consider PostgreSQL for high concurrency
- Increase timeout in SQLite

### Worker Pool Exhaustion

- Increase `MAX_WORKERS`
- Add request queuing
- Implement rate limiting

## Performance Optimization

### 1. Redis Caching

Cache frequent prompts:

```python
import redis
cache = redis.Redis(host='localhost', port=6379)

# Check cache before API call
cached = cache.get(f"prompt:{hash(prompt)}")
if cached:
    return json.loads(cached)
```

### 2. Connection Pooling

Reuse HTTP connections:

```python
import httpx
client = httpx.Client()  # Reuse across requests
```

### 3. Async Workers

Use async for I/O-bound operations:

```python
async def process_batch(prompts):
    tasks = [process_prompt(p) for p in prompts]
    return await asyncio.gather(*tasks)
```

## Monitoring Metrics

Track these key metrics:

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| Response time (p95) | <5s | Increase workers |
| Error rate | <1% | Check logs |
| Worker utilization | <80% | Scale up |
| Budget usage | <90% | Alert users |
| Queue depth | <10 | Scale workers |

## Cost Management

### Budget Alerts

Set up budget alerts:

```python
async def check_budget_alert(project_id):
    usage = await budget_manager.get_usage(project_id)
    if usage.remaining and usage.remaining < 1000:
        send_alert(f"Low budget: {usage.remaining} tokens remaining")
```

### Auto-Scaling Based on Cost

```python
if monthly_cost > COST_THRESHOLD:
    # Force cheaper models
    DEFAULT_MODEL = "haiku"
```

## Example Production Stack

```
Internet
   ↓
Cloudflare (CDN, DDoS protection)
   ↓
Nginx (SSL termination, load balancing)
   ↓
Claude API Service (3 replicas)
   ↓
Redis (caching)
   ↓
PostgreSQL (persistent storage)
```

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** - Development setup
- **[API Reference](API_REFERENCE.md)** - API documentation
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Client Library](CLIENT_LIBRARY.md)** - Python client
