# Monitoring & Observability

Set up comprehensive monitoring for production.

## Key Metrics to Monitor

### Application Metrics

- **Request count** - requests/second
- **Error rate** - errors as % of requests
- **Response time** - p50, p95, p99 latencies
- **Token usage** - tokens/minute
- **Cost** - $USD/hour

### Infrastructure Metrics

- **CPU usage** - % utilized
- **Memory usage** - GB/percentage
- **Disk I/O** - read/write operations
- **Network** - bandwidth in/out
- **Database connections** - active/max

### Business Metrics

- **Active API keys** - number of keys in use
- **Task success rate** - % completed vs failed
- **Average task cost** - $ per task
- **Daily active users** - unique API keys

## Monitoring Tools

### Prometheus + Grafana

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

### Configure Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Grafana Dashboards

Create dashboard for key metrics:

```json
{
  "dashboard": {
    "title": "Claude Code API",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {"expr": "rate(http_requests_total[5m])"}
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {"expr": "rate(http_requests_total{status=~\"5..\"}[5m])"}
        ]
      },
      {
        "title": "Response Time (p99)",
        "targets": [
          {"expr": "histogram_quantile(0.99, http_request_duration_seconds_bucket)"}
        ]
      },
      {
        "title": "Token Usage",
        "targets": [
          {"expr": "rate(tokens_used_total[5m])"}
        ]
      }
    ]
  }
}
```

## Alerting

### Prometheus Alerts

```yaml
# alerts.yml
groups:
  - name: api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate ({{ $value | humanizePercentage }})"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses ({{ $value }}s)"

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis cache is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container memory usage is 90%+"
```

## Logging

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "extra": record.__dict__
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Log Aggregation

```python
# Elasticsearch + Logstash + Kibana
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Log Rotation

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    '/var/log/api.log',
    maxBytes=100_000_000,  # 100MB
    backupCount=10  # Keep 10 files
)
logger.addHandler(handler)
```

## Health Checks

### Liveness Probe

```python
@app.get("/health")
async def health():
    """Endpoint for health checks."""
    return {"status": "healthy"}
```

### Readiness Probe

```python
@app.get("/ready")
async def readiness():
    """Check if service is ready to handle requests."""
    # Check database
    try:
        db.execute("SELECT 1")
    except Exception:
        return {"status": "not_ready"}, 503

    # Check Redis
    try:
        redis.ping()
    except Exception:
        return {"status": "not_ready"}, 503

    return {"status": "ready"}
```

### Kubernetes Probes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
  - name: api
    image: claude-api:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10

    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
```

## Performance Profiling

### CPU Profiling

```python
from py_spy import spy

# Collect CPU profile
spy("python main.py", duration=60, output="cpu.svg", format="flamegraph")
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def execute_task():
    # Function to profile
    pass
```

### Database Query Profiling

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    if total_time > 0.1:  # Log slow queries
        logger.warning(f"Slow query ({total_time}s): {statement}")
```

## Incident Response

### On-Call Setup

- PagerDuty/OpsGenie for escalation
- Slack integration for alerts
- Runbooks for common issues

### Incident Runbook

```markdown
# Incident: High API Error Rate

## Detection
- Alert: HighErrorRate
- Error rate > 5% for 5 minutes

## Initial Response (5 min)
1. Check Sentry for error patterns
2. Check database/Redis connectivity
3. Review recent deployments

## Troubleshooting (10 min)
1. Check application logs
2. Check infrastructure metrics
3. Run health checks

## Resolution (15 min)
- Restart service if hung
- Rollback recent changes if needed
- Increase resources if capacity issue

## Post-Incident (next day)
- Review root cause
- Implement fix
- Update monitoring/alerting
```

## Dashboards

### Real-time Dashboard

```python
# Simple HTTP metrics server
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_TIME = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

TOKEN_USAGE = Counter(
    'tokens_used_total',
    'Total tokens used'
)

@app.middleware("http")
async def track_metrics(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_TIME.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

## Monitoring Best Practices

1. **Monitor the right metrics** - Focus on user impact
2. **Alert intelligently** - Avoid alert fatigue
3. **Use automation** - Auto-remediate when possible
4. **Test alerting** - Verify alerts actually trigger
5. **Document runbooks** - Make incident response faster
6. **Review regularly** - Adjust metrics based on learnings
7. **Correlate events** - Link metrics to deployments/changes
8. **Plan capacity** - Monitor trends for growth

## See Also

- [Production Deployment](production.md)
- [Docker Deployment](docker-compose.md)
- [Security Best Practices](../guides/security-best-practices.md)
