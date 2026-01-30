# Deployment with Docker Compose

Complete deployment setup for the Claude Code API.

## Overview

Deploy the full stack with Docker Compose:
- **API Service** - FastAPI backend
- **Redis** - Caching and queue management
- **Database** - SQLite (can upgrade to PostgreSQL)

## Quick Start

### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: claude-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/api.db
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: claude-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis-data:
```

### 2. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create data directory
RUN mkdir -p /data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Start Services

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps
```

## Configuration

### Environment Variables

Create `.env` file:

```
# API Configuration
ENVIRONMENT=production
LOG_LEVEL=info
API_PORT=8000

# Database
DATABASE_URL=sqlite:///data/api.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:password@postgres:5432/claude_api

# Redis
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your-secure-password

# API Keys
CLAUDE_API_KEY=sk-proj-your-key
ADMIN_API_KEY=sk-admin-your-key

# Security
JWT_SECRET=your-jwt-secret-key
CORS_ORIGINS=["http://localhost:3000", "https://example.com"]

# Limits
MAX_REQUEST_SIZE=10485760  # 10MB
API_RATE_LIMIT=100
API_TIMEOUT=300
```

### Load Environment

Update docker-compose.yml:

```yaml
services:
  api:
    env_file: .env
```

## Advanced Configuration

### PostgreSQL Instead of SQLite

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: claude-postgres
    environment:
      POSTGRES_USER: claude
      POSTGRES_PASSWORD: secure-password
      POSTGRES_DB: claude_api
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  api:
    environment:
      DATABASE_URL=postgresql://claude:secure-password@postgres:5432/claude_api
    depends_on:
      - postgres
      - redis

volumes:
  postgres-data:
```

### Nginx Reverse Proxy

```yaml
services:
  nginx:
    image: nginx:alpine
    container_name: claude-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

  api:
    # Remove ports mapping when behind Nginx
    # ports:
    #   - "8000:8000"
    environment:
      - API_PORT=8000
```

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name api.example.com;

        client_max_body_size 10M;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check endpoint
        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }
}
```

### Logging

Configure centralized logging:

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=api"

  redis:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Monitoring

### Health Checks

The API provides health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "uptime": 3600
}
```

### Prometheus Metrics

Expose metrics for monitoring:

```bash
curl http://localhost:8000/metrics
```

### Docker Health Dashboard

View container health:

```bash
docker-compose ps

# Or detailed:
docker inspect claude-api --format='{{.State.Health.Status}}'
```

## Scaling

### Horizontal Scaling

Run multiple API instances:

```yaml
services:
  api:
    deploy:
      replicas: 3

  nginx:
    # Balances traffic to 3 API instances
    upstream api {
        server api:8000;
        server api:8001;
        server api:8002;
    }
```

### Load Balancing

Use Docker's built-in load balancing:

```bash
# Start 3 API replicas
docker-compose up -d --scale api=3
```

## Backup & Recovery

### Database Backup

```bash
# Backup SQLite database
docker-compose exec api sqlite3 /data/api.db ".backup /data/backup.db"

# Backup to local machine
docker cp claude-api:/data/api.db ./backup/api.db

# Restore
docker cp ./backup/api.db claude-api:/data/api.db
docker-compose restart api
```

### Redis Backup

```bash
# Create Redis snapshot
docker-compose exec redis redis-cli BGSAVE

# Backup RDB file
docker cp claude-redis:/data/dump.rdb ./backup/dump.rdb
```

### Automated Backups

Add backup service:

```yaml
services:
  backup:
    image: alpine:latest
    volumes:
      - ./data:/data
      - ./backup:/backup
    command: |
      sh -c "
      while true; do
        cp -v /data/api.db /backup/api.db.$(date +%s)
        # Keep only last 7 days
        find /backup -name 'api.db.*' -mtime +7 -delete
        sleep 86400
      done
      "
    restart: unless-stopped
```

## Security

### API Key Management

Store API keys in environment variables, not code:

```yaml
services:
  api:
    environment:
      # Use .env file, never hardcode
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
```

### Network Security

Restrict external access:

```yaml
services:
  redis:
    ports: []  # No external access
    expose:
      - 6379

  api:
    ports:
      - "8000:8000"  # Or behind Nginx only
```

### SSL/TLS

Use Let's Encrypt with Certbot:

```bash
# Generate certificate
certbot certonly --standalone -d api.example.com

# Copy to container
cp -r /etc/letsencrypt/live/api.example.com ./ssl/
```

Update nginx.conf for HTTPS:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Verify configuration
docker-compose config

# Test image build
docker build .
```

### Database Connection Error

```bash
# Check database file exists
docker-compose exec api ls -la /data/

# Check SQLite integrity
docker-compose exec api sqlite3 /data/api.db "PRAGMA integrity_check;"
```

### Redis Connection Error

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Optimize Redis
docker-compose exec redis redis-cli INFO memory

# Configure memory limit
environment:
  - REDIS_MEMORY_LIMIT=256mb
```

## Production Checklist

- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable SSL/TLS certificates
- [ ] Configure daily backups
- [ ] Set up monitoring/alerting
- [ ] Configure log rotation
- [ ] Set resource limits (CPU, memory)
- [ ] Enable health checks
- [ ] Configure auto-restart policies
- [ ] Review security settings
- [ ] Test disaster recovery
- [ ] Document operational procedures
- [ ] Set up monitoring dashboards

## Next Steps

- [Production Deployment](production.md)
- [Monitoring](monitoring.md)
- [Security Best Practices](../guides/security-best-practices.md)
