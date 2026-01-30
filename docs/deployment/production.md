# Production Deployment

Guidelines for deploying to production.

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance tested
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] API keys rotated
- [ ] SSL certificates valid
- [ ] Database optimized
- [ ] Rate limiting configured
- [ ] Error handling tested
- [ ] Incident response plan ready

## Deployment Strategy

### Blue-Green Deployment

Minimize downtime with parallel environments:

```bash
# Deploy to blue (new)
docker-compose -f docker-compose.blue.yml up -d

# Test blue environment
curl http://localhost:8001/health

# Switch traffic (via Nginx config)
# Update upstream to blue

# Keep green (old) running for quick rollback
# After validation, take down green
```

### Canary Deployment

Gradually roll out to users:

```bash
# 1% of traffic to new version
upstream api {
    server api-old:8000 weight=99;
    server api-new:8000 weight=1;
}

# Monitor metrics, gradually increase if healthy
# 5% traffic
weight=5;

# 50% traffic
weight=50;

# 100% traffic
weight=100;

# Retire old version
```

## Environment Configuration

### Production .env

```bash
# Core
ENVIRONMENT=production
LOG_LEVEL=error  # Reduce noise
DEBUG=false

# Security
JWT_SECRET=$(openssl rand -hex 32)
API_RATE_LIMIT=100
API_TIMEOUT=300

# Database
DATABASE_URL=postgresql://user:password@postgres.prod:5432/claude
DATABASE_POOL_SIZE=20
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://redis.prod:6379
REDIS_PASSWORD=$(openssl rand -hex 32)

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
NEW_RELIC_LICENSE_KEY=...
DATADOG_API_KEY=...
```

## Monitoring & Observability

### Sentry Error Tracking

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://key@sentry.io/project",
    environment="production",
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1
)
```

### Prometheus Metrics

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['localhost:8000']
```

### Alerting

Alert on critical metrics:

```yaml
# alerts.yml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"

- alert: DatabaseDown
  expr: pg_up == 0
  for: 1m
  annotations:
    summary: "Database is down"

- alert: RedisDown
  expr: redis_up == 0
  for: 1m
  annotations:
    summary: "Redis is down"
```

## Database Optimization

### PostgreSQL

```sql
-- Create indexes
CREATE INDEX idx_api_key_id ON api_keys(id);
CREATE INDEX idx_usage_log_timestamp ON usage_log(timestamp DESC);

-- Optimize queries
ANALYZE;
VACUUM FULL;

-- Connection pooling
pg_bouncer.ini:
[databases]
claude_api = host=postgres port=5432 dbname=claude_api
[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

## Scaling Considerations

### Horizontal Scaling

```bash
# With Kubernetes
kubectl scale deployment api --replicas=10

# With Docker Swarm
docker service update --replicas 10 api

# With Docker Compose
docker-compose up -d --scale api=10 --scale redis=1
```

### Vertical Scaling

Increase resource limits:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

## Backup & Disaster Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR=/backups
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/db_$DATE.sql
gzip $BACKUP_DIR/db_$DATE.sql

# Backup Redis
redis-cli BGSAVE
cp /data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb
gzip $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3
aws s3 sync $BACKUP_DIR s3://backups/$(date +%Y-%m)/

# Cleanup old backups
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
```

### Recovery Testing

```bash
# Test database recovery monthly
psql -f $BACKUP_DIR/db_latest.sql.gz test_db

# Test Redis recovery
redis-cli FLUSHDB
redis-cli MODULE LOAD /path/to/redis_$DATE.rdb
```

## Security Hardening

### API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/task")
@limiter.limit("10/minute")
async def execute_task(request: Request):
    pass
```

### API Key Rotation

```python
# Rotate keys every 90 days
def should_rotate_key(key):
    age_days = (now() - key.created_at).days
    return age_days > 90

for key in get_all_keys():
    if should_rotate_key(key):
        new_key = generate_key()
        notify_user(key.owner, new_key)
        schedule_key_revocation(key, days=7)
```

### Secrets Management

```bash
# Use HashiCorp Vault
vault write -data=@api-keys.json secret/claude/prod

# Or AWS Secrets Manager
aws secretsmanager create-secret \
  --name claude/prod/api-key \
  --secret-string file://api-key.txt
```

## Performance Optimization

### Caching Strategy

```python
# Cache API responses
@app.get("/v1/models")
@cache(expire=3600)  # 1 hour
async def get_models():
    return get_available_models()
```

### Database Query Optimization

```python
# Use connection pooling
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### Content Compression

```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

## Compliance & Auditing

### Audit Logging

Log all significant events:

```python
@app.post("/v1/task")
async def execute_task(request: AgenticTaskRequest):
    logger.info({
        "event": "task_executed",
        "api_key": redact_key(api_key),
        "task": request.description,
        "timestamp": now(),
        "user_ip": request.client.host
    })
```

### Data Retention

```python
# Delete old logs after 90 days
from datetime import datetime, timedelta

def cleanup_old_logs():
    cutoff = datetime.now() - timedelta(days=90)
    AuditLog.delete().where(AuditLog.timestamp < cutoff)
```

## Post-Deployment

### Verification Steps

```bash
# 1. Health check
curl https://api.example.com/health

# 2. Database connectivity
curl https://api.example.com/db-check

# 3. Redis connectivity
curl https://api.example.com/redis-check

# 4. Sample API call
curl -H "Authorization: Bearer test-key" \
  https://api.example.com/v1/models

# 5. Monitor metrics
# Check Prometheus, Datadog, etc.
```

### Rollback Plan

```bash
# If issues detected:

# 1. Switch traffic back to green
# Update Nginx upstream

# 2. Investigate issue
docker-compose logs api | grep ERROR

# 3. Fix and redeploy
# Don't re-run without fix

# 4. Post-mortem
# Document what happened
```

## Operational Runbooks

### Common Issues

**Database connection timeout**
- Check PostgreSQL health
- Verify connection pool settings
- Increase timeout

**Memory leak**
- Monitor memory usage
- Check for resource leaks
- Restart service

**High API latency**
- Check query performance
- Review recent changes
- Scale horizontally

## Next Steps

- [Monitoring Guide](monitoring.md)
- [Docker Deployment](docker-compose.md)
- [Security Best Practices](../guides/security-best-practices.md)
