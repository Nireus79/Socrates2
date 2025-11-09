# PERFORMANCE REQUIREMENTS

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟢 LOW - Monitor from Phase 0, optimize as needed

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Response Time Targets](#response-time-targets)
3. [Database Performance](#database-performance)
4. [LLM Call Optimization](#llm-call-optimization)
5. [Caching Strategy](#caching-strategy)
6. [Connection Pooling](#connection-pooling)
7. [Load Testing](#load-testing)

---

## OVERVIEW

**Goal:** Fast, responsive system that scales with users.

### Performance Philosophy

1. **Fast Enough**: Don't over-optimize prematurely
2. **Measure First**: Profile before optimizing
3. **User-Perceived**: Optimize what users notice most
4. **Graceful Degradation**: Slow is better than broken

---

## RESPONSE TIME TARGETS

### API Endpoints

| Endpoint Type | Target | Max Acceptable | Notes |
|---------------|--------|----------------|-------|
| **Authentication** | < 100ms | 200ms | Login, register, token refresh |
| **CRUD Operations** | < 200ms | 500ms | Create/read/update/delete projects, specs |
| **LLM Calls** | < 5s | 10s | Socratic questions, spec extraction |
| **Conflict Detection** | < 1s | 3s | Run after spec changes |
| **Quality Control** | < 2s | 5s | Validation, path analysis |
| **Project Generation** | < 5min | 10min | Complete project generation |

### Frontend

| Interaction | Target | Max Acceptable |
|-------------|--------|----------------|
| **Page Load** | < 2s | 3s |
| **Navigation** | < 100ms | 300ms |
| **Form Submit** | < 500ms | 1s |
| **LLM Response** | < 5s | 10s |

---

## DATABASE PERFORMANCE

### Query Optimization

```python
# ✅ GOOD: Use indexes
# Query with indexed column
projects = db.query(Project).filter(
    Project.user_id == user_id  # Indexed
).all()

# ✅ GOOD: Limit results
projects = db.query(Project).filter(
    Project.user_id == user_id
).limit(20).all()

# ✅ GOOD: Select only needed columns
projects = db.query(Project.id, Project.name).filter(
    Project.user_id == user_id
).all()

# ❌ BAD: N+1 query problem
for project in projects:
    specs = db.query(Specification).filter(
        Specification.project_id == project.id  # N queries!
    ).all()

# ✅ GOOD: Eager loading
projects = db.query(Project).options(
    joinedload(Project.specifications)  # 1 query
).filter(Project.user_id == user_id).all()
```

### Index Strategy

```sql
-- Primary indexes (already covered in DATABASE_SCHEMA_COMPLETE.md)
-- Foreign key indexes (for joins)
-- Filtered indexes (for WHERE clauses)

-- Example: Fast query for active projects
CREATE INDEX idx_projects_user_active
ON projects(user_id)
WHERE archived_at IS NULL;

-- Example: Fast query for open conflicts
CREATE INDEX idx_conflicts_project_status
ON conflicts(project_id)
WHERE status = 'open';
```

### Query Monitoring

```python
# middleware/query_monitor.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
import time

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - context._query_start_time

    # Log slow queries (> 1 second)
    if total > 1.0:
        logger.warning(
            "Slow query detected",
            extra={
                "duration": total,
                "query": statement,
                "params": params
            }
        )
```

---

## LLM CALL OPTIMIZATION

### Strategies

1. **Minimize Calls**: Batch related questions
2. **Cache Results**: Reuse similar prompts
3. **Async Calls**: Don't block on LLM responses
4. **Streaming**: Stream responses for better UX

### Implementation

```python
# services/llm_optimizer.py
from functools import lru_cache
import hashlib

class LLMOptimizer:
    """Optimize LLM API calls."""

    def __init__(self, llm_service):
        self.llm = llm_service
        self.cache = {}

    def generate_cached(self, prompt: str, **kwargs):
        """
        Generate with caching.

        Cache similar prompts (useful for repeated questions).
        """
        # Create cache key
        cache_key = self._cache_key(prompt, **kwargs)

        # Check cache
        if cache_key in self.cache:
            logger.info("LLM cache hit")
            return self.cache[cache_key]

        # Call LLM
        response = self.llm.generate(prompt, **kwargs)

        # Cache result
        self.cache[cache_key] = response

        return response

    def _cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key for prompt."""
        key_data = f"{prompt}|{sorted(kwargs.items())}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def generate_async(self, prompt: str, **kwargs):
        """Generate asynchronously (non-blocking)."""
        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.generate,
            prompt,
            **kwargs
        )

        return response
```

---

## CACHING STRATEGY

### What to Cache

✅ **Cache:**
- LLM responses for common prompts
- User session data (Redis)
- Frequently accessed projects
- Maturity calculations (expensive)

❌ **Don't Cache:**
- User-specific data (privacy)
- Real-time data (conflicts, specs)
- Authentication tokens (security)

### Redis for Session Caching (Optional Phase 3+)

```python
# config/redis.py
import redis
from config.settings import settings

# Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

# Cache session data
def cache_session(session_id: str, data: dict, ttl: int = 3600):
    """Cache session data for TTL seconds."""
    redis_client.setex(
        f"session:{session_id}",
        ttl,
        json.dumps(data)
    )

def get_cached_session(session_id: str) -> dict:
    """Get cached session data."""
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None
```

---

## CONNECTION POOLING

### SQLAlchemy Connection Pool

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # Minimum connections
    max_overflow=20,       # Maximum additional connections
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Test connections before using
)
```

---

## LOAD TESTING

### Load Testing Script

```python
# scripts/load_test.py
"""
Load test Socrates2 API.

Tests:
- Authentication
- Project creation
- Socratic questioning
- Conflict detection
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"

def login():
    """Login and get token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    return response.json()["access_token"]

def create_project(token):
    """Create project."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/projects",
        json={"name": "Load Test Project"},
        headers=headers
    )
    return response.json()["id"]

def load_test(num_users=10, requests_per_user=100):
    """Run load test."""
    print(f"Load testing with {num_users} users, {requests_per_user} requests each...")

    start_time = time.time()
    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = []

        for user in range(num_users):
            for req in range(requests_per_user):
                future = executor.submit(login)
                futures.append(future)

        for future in as_completed(futures):
            try:
                future.result()
                success += 1
            except Exception as e:
                failed += 1
                print(f"Request failed: {e}")

    elapsed = time.time() - start_time
    total_requests = success + failed
    rps = total_requests / elapsed

    print(f"\nResults:")
    print(f"Total requests: {total_requests}")
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Duration: {elapsed:.2f}s")
    print(f"Requests/second: {rps:.2f}")

if __name__ == "__main__":
    load_test(num_users=10, requests_per_user=100)
```

### Load Testing Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Concurrent Users** | 100 | Simultaneous active users |
| **Requests/Second** | 200 | Peak load capacity |
| **Error Rate** | < 0.1% | Failed requests |
| **P95 Latency** | < 500ms | 95th percentile response time |
| **P99 Latency** | < 2s | 99th percentile response time |

---

## PERFORMANCE MONITORING

### Metrics to Track

```python
# middleware/performance_middleware.py
from prometheus_client import Histogram, Counter
import time

# Metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'status']
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

llm_call_duration = Histogram(
    'llm_call_duration_seconds',
    'LLM API call duration',
    ['provider']
)

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Track request performance."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Record metrics
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(duration)

    # Log slow requests
    if duration > 2.0:
        logger.warning(
            "Slow request",
            extra={
                "duration": duration,
                "method": request.method,
                "path": request.url.path
            }
        )

    return response
```

---

## OPTIMIZATION CHECKLIST

Before production:

- [ ] Database indexes created for common queries
- [ ] Connection pooling configured
- [ ] Slow query logging enabled
- [ ] LLM call caching implemented
- [ ] Load testing completed (100+ concurrent users)
- [ ] Performance monitoring configured
- [ ] P95 latency < 500ms for API calls
- [ ] P99 latency < 2s for API calls
- [ ] Error rate < 0.1% under load

---

**Document Status:** ✅ Complete
**Date:** November 5, 2025
