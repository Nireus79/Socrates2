# Implementation Phase 4: Polish & Optimization

**Duration:** 2+ weeks (ongoing)
**Priority:** 🔵 LOW-MEDIUM - Post-launch improvements
**Team Size:** 1-2 developers
**Effort:** 80+ hours
**Prerequisite:** Phase 1, 2, 3 completion (or parallel)

---

## Phase Objectives

1. **Performance optimization** (database, caching, API)
2. **Security hardening** (auth, data protection, auditing)
3. **Documentation completion** (API docs, user guides, dev docs)
4. **Testing expansion** (additional coverage, edge cases)
5. **Monitoring & observability** (logging, metrics, alerting)

---

## Tasks Breakdown

### Task 1: Performance Optimization (Week 1-2)
**Effort:** 30 hours | **Owner:** Developer 1

#### 1.1 Database Query Optimization
**Current Issues:**
- N+1 queries in some endpoints
- Missing database indexes
- Inefficient joins

**Implementation:**

```python
# Add database indexes
class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default='active', index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Composite index for common queries
    __table_args__ = (
        Index('ix_project_user_status', 'user_id', 'status'),
        Index('ix_project_created', 'created_at'),
    )

# Use eager loading to prevent N+1
class ProjectWithRelations(BaseModel):
    id: str
    name: str
    sessions: List[Session] = []

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get project with eager-loaded relations."""
    # Use joinedload to fetch relations in single query
    project = db_specs.query(Project).options(
        joinedload(Project.sessions),
        joinedload(Project.specifications)
    ).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        'success': True,
        'project': project.to_dict(include_relations=True)
    }

# Use query result caching
from functools import lru_cache
from datetime import datetime, timedelta

class QueryCache:
    """Simple query cache."""
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str):
        """Get cached value."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.utcnow() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value):
        """Set cached value."""
        expiry = datetime.utcnow() + timedelta(seconds=self.ttl)
        self.cache[key] = (value, expiry)

query_cache = QueryCache(ttl_seconds=300)

@router.get("/projects")
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """List projects with caching."""
    cache_key = f"projects_{current_user.id}_{skip}_{limit}"
    cached = query_cache.get(cache_key)

    if cached:
        return cached

    projects = db_specs.query(Project).filter(
        Project.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    result = {
        'success': True,
        'projects': [p.to_dict() for p in projects],
        'total': db_specs.query(Project).filter(
            Project.user_id == current_user.id
        ).count()
    }

    query_cache.set(cache_key, result)
    return result
```

**Subtasks:**
- [ ] Identify slow queries (use query logging)
- [ ] Add database indexes for common filters
- [ ] Use eager loading for related objects
- [ ] Implement query result caching
- [ ] Optimize joins
- [ ] Use pagination where needed
- [ ] Test query performance

**Database Index Strategy:**
```sql
-- User-based filtering
CREATE INDEX ix_project_user_id ON projects(user_id);
CREATE INDEX ix_session_user_id ON sessions(user_id);
CREATE INDEX ix_specification_user_id ON specifications(user_id);

-- Status filtering
CREATE INDEX ix_project_status ON projects(status);
CREATE INDEX ix_session_status ON sessions(status);

-- Date filtering
CREATE INDEX ix_project_created ON projects(created_at);
CREATE INDEX ix_session_created ON sessions(created_at);

-- Composite indexes for common queries
CREATE INDEX ix_project_user_status ON projects(user_id, status);
CREATE INDEX ix_session_project_status ON sessions(project_id, status);
```

**Success Criteria:**
- Query response time < 200ms
- N+1 queries eliminated
- Caching working properly
- Tests passing

---

#### 1.2 API Response Optimization
**Implementation:**

```python
# Use field selection
@router.get("/projects")
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    fields: str = None,  # "id,name,created_at"
    current_user: User = Depends(get_current_active_user)
):
    """List projects with optional field selection."""
    query = db_specs.query(Project).filter(
        Project.user_id == current_user.id
    ).offset(skip).limit(limit)

    projects = query.all()

    if fields:
        field_list = [f.strip() for f in fields.split(',')]
        results = []
        for p in projects:
            data = p.to_dict()
            filtered_data = {k: v for k, v in data.items() if k in field_list}
            results.append(filtered_data)
    else:
        results = [p.to_dict() for p in projects]

    return {
        'success': True,
        'projects': results,
        'total': db_specs.query(Project).filter(
            Project.user_id == current_user.id
        ).count()
    }

# Enable gzip compression
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Add response caching headers
from fastapi.responses import Response

@router.get("/projects")
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """List projects with cache headers."""
    projects = db_specs.query(Project).filter(
        Project.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    response_data = {
        'success': True,
        'projects': [p.to_dict() for p in projects]
    }

    # Allow browser caching for 5 minutes
    response = Response(
        content=json.dumps(response_data),
        media_type="application/json"
    )
    response.headers["Cache-Control"] = "max-age=300, public"
    response.headers["ETag"] = hashlib.md5(
        json.dumps(response_data).encode()
    ).hexdigest()

    return response
```

**Subtasks:**
- [ ] Add field selection to list endpoints
- [ ] Implement response compression (gzip)
- [ ] Add HTTP caching headers
- [ ] Implement ETags for cache validation
- [ ] Reduce response payload size
- [ ] Test response performance

**Success Criteria:**
- Response times < 100ms
- Payload size reduced 30%+
- Compression working
- Tests passing

---

#### 1.3 Caching Strategy
**Implementation:**

```python
import redis

class CacheManager:
    """Manage distributed caching with Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str):
        """Get cached value."""
        return self.redis.get(key)

    def set(self, key: str, value: str, ttl_seconds: int = 300):
        """Set cached value with TTL."""
        self.redis.setex(key, ttl_seconds, value)

    def delete(self, key: str):
        """Delete cached value."""
        self.redis.delete(key)

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern."""
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

# Usage
cache = CacheManager()

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with caching."""
    cache_key = f"project:{project_id}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from database
    project = db_specs.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = {
        'success': True,
        'project': project.to_dict()
    }

    # Cache for 5 minutes
    cache.set(cache_key, json.dumps(result), ttl_seconds=300)

    return result

# Invalidate cache on update
@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update project and invalidate cache."""
    project = db_specs.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update
    project.name = request.name
    db_specs.commit()

    # Invalidate caches
    cache.delete(f"project:{project_id}")
    cache.invalidate_pattern(f"projects:{current_user.id}:*")

    return {'success': True, 'project': project.to_dict()}
```

**Dependencies to add:**
```
redis>=4.5.0
```

**Subtasks:**
- [ ] Install Redis
- [ ] Implement CacheManager
- [ ] Add caching to read endpoints
- [ ] Add cache invalidation on writes
- [ ] Monitor cache hit rate
- [ ] Test caching behavior

**Success Criteria:**
- Cache hit rate > 70%
- Performance improved 50%+
- Cache invalidation working
- Tests passing

---

### Task 2: Security Hardening (Week 2-3)
**Effort:** 25 hours | **Owner:** Developer 2

#### 2.1 Authentication & Authorization
**Current State:** JWT implemented, needs hardening

**Implementation:**

```python
from datetime import datetime, timedelta
from typing import Optional
import secrets

class SecurityEnhancements:
    """Security hardening measures."""

    # 1. Add token blacklisting for logout
    class TokenBlacklist:
        def __init__(self):
            self.blacklisted = set()

        def add(self, token: str):
            """Blacklist token."""
            self.blacklisted.add(token)

        def is_blacklisted(self, token: str) -> bool:
            """Check if token is blacklisted."""
            return token in self.blacklisted

    # 2. Implement refresh token rotation
    def create_tokens(self, user_id: str) -> Dict[str, str]:
        """Create access and refresh tokens."""
        access_token = self._create_access_token(user_id)
        refresh_token = self._create_refresh_token(user_id)

        # Store refresh token in database
        db_auth.add(RefreshToken(
            user_id=user_id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        ))
        db_auth.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    def _create_access_token(self, user_id: str) -> str:
        """Create short-lived access token."""
        payload = {
            'sub': str(user_id),
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(minutes=30),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    def _create_refresh_token(self, user_id: str) -> str:
        """Create long-lived refresh token."""
        token = secrets.token_urlsafe(32)
        return token

    # 3. Implement rate limiting
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)

    @limiter.limit("100/minute")
    @router.post("/auth/login")
    async def login(credentials: LoginRequest):
        """Rate-limited login endpoint."""
        # Implementation
        pass

    @limiter.limit("5/minute")
    @router.post("/auth/register")
    async def register(request: RegisterRequest):
        """Rate-limited registration endpoint."""
        # Implementation
        pass

    # 4. Add request signing for sensitive operations
    def verify_request_signature(
        self,
        request_body: str,
        signature: str,
        user_secret: str
    ) -> bool:
        """Verify request was signed by user."""
        expected_signature = hmac.new(
            user_secret.encode(),
            request_body.encode(),
            hashlib.sha256
        ).hexdigest()
        return secrets.compare_digest(signature, expected_signature)

    # 5. Implement MFA support
    class MFAManager:
        def generate_mfa_secret(self) -> str:
            """Generate MFA secret."""
            return pyotp.random_base32()

        def verify_totp(self, secret: str, token: str) -> bool:
            """Verify TOTP token."""
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)

        def generate_backup_codes(self) -> List[str]:
            """Generate backup codes."""
            return [
                secrets.token_urlsafe(8) for _ in range(10)
            ]
```

**Dependencies to add:**
```
slowapi>=0.1.9
pyotp>=2.9.0
python-hmac>=0.1.0
```

**Subtasks:**
- [ ] Implement token blacklisting
- [ ] Implement refresh token rotation
- [ ] Add rate limiting to auth endpoints
- [ ] Add request signing (optional)
- [ ] Implement MFA support (optional)
- [ ] Test security measures

**Success Criteria:**
- Token blacklisting working
- Rate limiting enforced
- MFA optional but available
- Security tests passing

---

#### 2.2 Data Protection
**Implementation:**

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class DataEncryption:
    """Encrypt sensitive data."""

    def __init__(self, master_key: str):
        # Derive encryption key from master key
        salt = os.urandom(16)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext."""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext."""
        return self.cipher.decrypt(ciphertext.encode()).decode()

# Encrypt sensitive fields
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    key_encrypted = Column(String, nullable=False)  # Encrypted
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_key(self, plaintext_key: str, encryptor: DataEncryption):
        """Store encrypted key."""
        self.key_encrypted = encryptor.encrypt(plaintext_key)

    def get_key(self, encryptor: DataEncryption) -> str:
        """Retrieve decrypted key."""
        return encryptor.decrypt(self.key_encrypted)

# Implement audit logging
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    changes = Column(JSON)  # What changed
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'timestamp': self.timestamp.isoformat()
        }

# Log all important actions
def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    changes: Dict = None,
    request: Request = None
):
    """Log audit trail."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get('user-agent') if request else None
    )
    db_auth.add(audit)
    db_auth.commit()
```

**Subtasks:**
- [ ] Implement data encryption for sensitive fields
- [ ] Add encryption key management
- [ ] Implement audit logging
- [ ] Log all user actions
- [ ] Create audit log viewing endpoint
- [ ] Test encryption/decryption
- [ ] Test audit logging

**Success Criteria:**
- Sensitive data encrypted at rest
- Audit trail complete
- Encryption working properly
- Tests passing

---

#### 2.3 HTTPS & CORS
**Implementation:**

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS.split(",")
)

# Configure HTTPS
if settings.ENVIRONMENT == "production":
    # Force HTTPS
    @app.middleware("http")
    async def redirect_to_https(request: Request, call_next):
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url, status_code=301)
        return await call_next(request)

    # Add security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
```

**Subtasks:**
- [ ] Configure CORS properly
- [ ] Add trusted host middleware
- [ ] Configure HTTPS redirect
- [ ] Add security headers
- [ ] Test security headers

**Success Criteria:**
- CORS working correctly
- HTTPS enforced in production
- Security headers present
- Tests passing

---

### Task 3: Documentation (Week 3)
**Effort:** 20 hours | **Owner:** Developer 1

#### 3.1 API Documentation
**Implementation:**

```python
# FastAPI auto-generates OpenAPI docs
# Available at /docs (Swagger) and /redoc (ReDoc)

# Add endpoint descriptions
@router.post("/projects")
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new project.

    - **name**: Project name (required, 1-100 characters)
    - **description**: Project description (optional)
    - **template**: Project template name (optional)

    Returns:
    - **project_id**: UUID of created project
    - **success**: Boolean indicating success

    Example:
    ```json
    {
        "name": "My Project",
        "description": "A test project",
        "template": "web-api"
    }
    ```
    """
    # Implementation
    pass

# OpenAPI/Swagger configuration
app = FastAPI(
    title="Socrates API",
    description="AI-Powered Specification Gathering API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)
```

**Subtasks:**
- [ ] Add descriptions to all endpoints
- [ ] Document request/response schemas
- [ ] Add example requests/responses
- [ ] Document authentication
- [ ] Document error codes
- [ ] Generate API reference guide
- [ ] Test API documentation

**Success Criteria:**
- All endpoints documented
- Examples provided
- Schemas clear
- Docs accessible

---

#### 3.2 User Guides
**Files to create:**
- `docs/QUICK_START.md` - Getting started guide
- `docs/CLI_USAGE.md` - CLI command reference
- `docs/API_USAGE.md` - API usage guide
- `docs/WORKFLOWS.md` - Common workflows
- `docs/TROUBLESHOOTING.md` - Common issues
- `docs/FAQ.md` - Frequently asked questions

**Subtasks:**
- [ ] Create quick start guide
- [ ] Create CLI usage guide
- [ ] Create API usage guide
- [ ] Document workflows
- [ ] Create troubleshooting guide
- [ ] Create FAQ
- [ ] Add screenshots/examples

**Success Criteria:**
- Comprehensive user guides
- Clear examples
- Easy to follow
- Covers common tasks

---

#### 3.3 Developer Documentation
**Files to create:**
- `docs/ARCHITECTURE.md` - System architecture
- `docs/DEVELOPMENT.md` - Development setup
- `docs/CONTRIBUTING.md` - Contributing guide
- `docs/DATABASE.md` - Database schema
- `docs/API_DESIGN.md` - API design patterns

**Subtasks:**
- [ ] Document architecture
- [ ] Document development setup
- [ ] Create contributing guide
- [ ] Document database schema
- [ ] Document design patterns
- [ ] Add code examples

**Success Criteria:**
- Architecture clear
- Development setup easy
- Contributing guidelines clear
- Design patterns documented

---

### Task 4: Testing Expansion (Week 3-4)
**Effort:** 20 hours | **Owner:** Developer 2

#### 4.1 Additional Unit Tests
**Coverage targets:**
- All models: 100%
- All services: 95%+
- All utilities: 100%

**Test files to create:**
```
tests/
├── test_models.py          # All model tests
├── test_security.py        # Security feature tests
├── test_caching.py         # Cache behavior tests
├── test_performance.py     # Performance tests
└── test_error_handling.py  # Error scenario tests
```

**Subtasks:**
- [ ] Write model tests
- [ ] Write security tests
- [ ] Write cache tests
- [ ] Write error handling tests
- [ ] Achieve 90%+ coverage
- [ ] Run coverage reports

**Success Criteria:**
- Coverage > 90%
- All tests passing
- Edge cases covered
- Performance tests pass

---

#### 4.2 Edge Case Testing
**Test scenarios:**
- Empty/null inputs
- Large datasets
- Concurrent operations
- Network failures
- Authorization edge cases

**Subtasks:**
- [ ] Test empty inputs
- [ ] Test large datasets
- [ ] Test concurrent access
- [ ] Test network failures
- [ ] Test permission edge cases
- [ ] Document edge cases

**Success Criteria:**
- All edge cases tested
- Behavior documented
- Tests passing
- No regressions

---

### Task 5: Monitoring & Observability (Week 4+)
**Effort:** 15 hours | **Owner:** Ongoing**

#### 5.1 Logging
**Implementation:**

```python
import logging
from logging.handlers import RotatingFileHandler
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure file logging
log_handler = RotatingFileHandler(
    "logs/socrates.log",
    maxBytes=10485760,  # 10MB
    backupCount=10
)
log_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger("socrates")
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User created", user_id=user_id, email=email)
logger.warning("High API latency detected", latency_ms=5000)
logger.error("Database connection failed", error=str(e), exc_info=True)
```

**Subtasks:**
- [ ] Configure structured logging
- [ ] Set up log rotation
- [ ] Add logging to all endpoints
- [ ] Add logging to agents
- [ ] Configure log levels
- [ ] Test logging output

**Success Criteria:**
- Logs structured and queryable
- Rotation working
- Performance not impacted
- Tests passing

---

#### 5.2 Metrics & Monitoring
**Implementation:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_counter = Counter(
    'socrates_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'socrates_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_sessions = Gauge(
    'socrates_active_sessions',
    'Number of active sessions'
)

# Add middleware to track metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    request_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

# Expose metrics for Prometheus
from prometheus_client import generate_latest

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
```

**Dependencies to add:**
```
prometheus-client>=0.17.0
```

**Subtasks:**
- [ ] Install prometheus-client
- [ ] Define key metrics
- [ ] Add metric tracking
- [ ] Expose metrics endpoint
- [ ] Configure Prometheus scraping
- [ ] Test metrics collection

**Success Criteria:**
- Metrics exposed
- Scraping working
- Performance not impacted
- Tests passing

---

#### 5.3 Health Checks
**Implementation:**

```python
class HealthChecker:
    """Check system health."""

    async def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            db_auth.execute("SELECT 1")
            db_specs.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def check_llm(self) -> bool:
        """Check LLM connectivity."""
        try:
            # Quick test call
            response = await llm_provider.generate_text("test")
            return bool(response)
        except Exception:
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        return {
            'status': 'healthy',
            'checks': {
                'database': await self.check_database(),
                'llm': await self.check_llm(),
                'memory': self._check_memory(),
                'disk': self._check_disk()
            },
            'timestamp': datetime.utcnow().isoformat()
        }

@router.get("/health")
async def health_check(checker: HealthChecker = Depends()):
    """Health check endpoint."""
    health = await checker.get_health_status()
    status_code = 200 if health['status'] == 'healthy' else 503
    return JSONResponse(status_code=status_code, content=health)
```

**Subtasks:**
- [ ] Implement health checks
- [ ] Check all critical services
- [ ] Expose health endpoint
- [ ] Configure alerting
- [ ] Test health checks

**Success Criteria:**
- All services checked
- Health endpoint working
- Alerts configured
- Tests passing

---

## Phase Deliverables

### Code Changes
- [ ] Database indexes and query optimization
- [ ] Caching layer with Redis
- [ ] Security hardening (auth, encryption, audit)
- [ ] Rate limiting
- [ ] Enhanced logging and metrics

### Documentation
- [ ] API reference documentation
- [ ] User guides (3+ documents)
- [ ] Developer guides (3+ documents)
- [ ] Troubleshooting guide
- [ ] FAQ

### Tests
- [ ] 100+ additional unit tests
- [ ] Edge case tests
- [ ] Performance tests
- [ ] Security tests
- [ ] 90%+ code coverage

### Infrastructure
- [ ] Redis caching setup
- [ ] Prometheus monitoring
- [ ] Log aggregation
- [ ] Health check endpoints

### Dependencies to Add
```
redis>=4.5.0
slowapi>=0.1.9
pyotp>=2.9.0
prometheus-client>=0.17.0
structlog>=23.1.0
cryptography>=41.0.0
```

---

## Success Criteria

### Must Have
- ✅ Performance improved 50%+
- ✅ Security hardened significantly
- ✅ Comprehensive documentation
- ✅ 90%+ test coverage
- ✅ Health checks operational

### Should Have
- ✅ Caching implemented
- ✅ Monitoring active
- ✅ Metrics exposed
- ✅ Logging structured

### Nice to Have
- ✅ Advanced security features
- ✅ Performance benchmarks
- ✅ Comprehensive guides

---

## Timeline

| Week | Task | Status |
|------|------|--------|
| 1-2 | Performance optimization | 🔄 |
| 2-3 | Security hardening | 🔄 |
| 3 | Documentation | 🔄 |
| 3-4 | Testing expansion | 🔄 |
| 4+ | Monitoring & observability | 🔄 |

---

## Continuous Improvements

Phase 4 is ongoing and can continue indefinitely:

### Ongoing Tasks
- Performance monitoring and tuning
- Security patches and updates
- Documentation updates
- Test coverage expansion
- Dependency updates
- Bug fixes and improvements

### Metrics to Track
- API response time (target < 200ms)
- Cache hit rate (target > 70%)
- Error rate (target < 0.1%)
- Test coverage (target > 95%)
- Security incidents (target = 0)

---

## Notes for Production

### Pre-Deployment Checklist
- [ ] Security review complete
- [ ] Performance testing passed
- [ ] Documentation reviewed
- [ ] Tests passing with >90% coverage
- [ ] Monitoring configured
- [ ] Health checks operational
- [ ] Backup/disaster recovery plan
- [ ] Rollback plan documented

### Post-Deployment Monitoring
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor resource usage
- [ ] Check security logs
- [ ] Verify backups

### Update Procedure
1. Run tests
2. Check security
3. Verify documentation
4. Deploy to staging
5. Test thoroughly
6. Deploy to production
7. Monitor closely

---

**End of IMPLEMENTATION_PHASE_4.md**
