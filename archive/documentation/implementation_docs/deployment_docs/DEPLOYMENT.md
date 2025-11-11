# Socrates - Production Deployment Guide

This guide provides step-by-step instructions for deploying Socrates to production.

## Prerequisites

### Required Software
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for cloning the repository
- A server or cloud instance (minimum 2GB RAM, 2 CPU cores)

### Required Configuration
- PostgreSQL credentials for two databases
- Anthropic API key for Claude integration
- Secure SECRET_KEY for JWT tokens
- Domain name (optional, for HTTPS)

---

## Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/Socrates.git
cd Socrates
```

### 2. Create Environment File

```bash
cp .env.production.example .env.production
```

Edit `.env.production` and fill in all required values:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-...

# Set strong database passwords
AUTH_DB_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
SPECS_DB_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Start Services

```bash
docker-compose --env-file .env.production up -d
```

This will:
- Start PostgreSQL databases (auth and specs)
- Start Redis cache
- Run database migrations automatically
- Start the Socrates API on port 8000

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/api/v1/admin/health

# Expected response:
# {"status":"healthy","databases":{"auth":"connected","specs":"connected"}}

# View logs
docker-compose logs -f socrates-api

# Check all services are running
docker-compose ps
```

### 5. Access API Documentation

Open your browser to:
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Manual Deployment (Without Docker)

### 1. Install Dependencies

#### PostgreSQL 17
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-17 postgresql-contrib

# macOS
brew install postgresql@17
```

#### Python 3.12
```bash
# Ubuntu/Debian
sudo apt install python3.12 python3.12-venv python3-pip

# macOS
brew install python@3.12
```

#### Redis (Optional, for caching)
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
```

### 2. Create Databases

```bash
sudo -u postgres psql

CREATE DATABASE socrates_auth;
CREATE DATABASE socrates_specs;
CREATE USER socrates_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE socrates_auth TO socrates_user;
GRANT ALL PRIVILEGES ON DATABASE socrates_specs TO socrates_user;
\q
```

### 3. Configure Environment

```bash
cd Socrates/backend
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 4. Set Up Python Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run Database Migrations

```bash
# Migrate auth database
export DATABASE_URL="postgresql://socrates_user:your_password@localhost:5432/socrates_auth"
alembic upgrade head

# Migrate specs database
export DATABASE_URL="postgresql://socrates_user:your_password@localhost:5432/socrates_specs"
alembic upgrade head
```

### 6. Start Application

#### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
# Single worker
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers (recommended)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate unique SECRET_KEY (32+ characters)
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules (only allow ports 80, 443, 22)
- [ ] Set `DEBUG=False` in production
- [ ] Restrict CORS_ORIGINS to your frontend domain
- [ ] Use strong database passwords (32+ characters)
- [ ] Rotate API keys regularly

### Performance
- [ ] Configure PostgreSQL for production workload
- [ ] Set up connection pooling (SQLAlchemy default: 5-20 connections)
- [ ] Enable Redis caching (optional but recommended)
- [ ] Configure uvicorn workers (recommend: 2 × CPU cores)
- [ ] Set up CDN for static assets (if applicable)

### Monitoring
- [ ] Configure application logging (LOG_LEVEL=INFO)
- [ ] Set up database backup automation
- [ ] Monitor disk space (especially specs database)
- [ ] Set up health check monitoring (GET /api/v1/admin/health)
- [ ] Configure error tracking (Sentry, etc.)

### Backup Strategy
- [ ] Daily full backup of auth database
- [ ] Hourly incremental backup of specs database
- [ ] Test restore procedures regularly
- [ ] Store backups off-site or in cloud storage

---

## Database Migrations

### Running Migrations

Migrations run automatically when using Docker Compose. For manual deployment:

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@host:5432/database_name"

# Run migrations
cd backend
alembic upgrade head

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1
```

### Creating New Migrations

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description"

# Create empty migration
alembic revision -m "description"
```

**Important:** Socrates uses two databases. When creating migrations:
1. Determine which database the migration targets (auth or specs)
2. Add `_should_run()` function to check database URL
3. Test migration on both databases

Example:
```python
def _should_run():
    """Only run this migration for socrates_auth database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url

def upgrade():
    if not _should_run():
        return
    # Migration code here
```

---

## Troubleshooting

### Health Check Fails

```bash
# Check logs
docker-compose logs socrates-api

# Check database connectivity
docker-compose exec postgres-auth psql -U socrates_auth_user -d socrates_auth -c "SELECT 1"
docker-compose exec postgres-specs psql -U socrates_specs_user -d socrates_specs -c "SELECT 1"

# Restart services
docker-compose restart
```

### Database Connection Errors

**Error:** `FATAL: password authentication failed`

**Solution:**
1. Verify passwords in `.env.production` match docker-compose.yml
2. Check PostgreSQL logs: `docker-compose logs postgres-auth`
3. Recreate services: `docker-compose down && docker-compose up -d`

### Migration Errors

**Error:** `Target database is not up to date`

**Solution:**
```bash
# Check current version
alembic current

# Show pending migrations
alembic heads

# Run missing migrations
alembic upgrade head
```

**Error:** `Can't locate revision identified by 'xyz'`

**Solution:**
This usually means migrations were run in wrong order. Reset and retry:
```bash
# Backup data first!
alembic downgrade base
alembic upgrade head
```

### Port Already in Use

**Error:** `bind: address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop conflicting service or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Out of Memory

If the application crashes with OOM errors:
1. Increase server RAM (minimum 2GB)
2. Reduce uvicorn workers: `--workers 2`
3. Configure PostgreSQL `shared_buffers` and `work_mem`
4. Enable swap space

---

## Scaling

### Horizontal Scaling

To handle more traffic, run multiple API instances behind a load balancer:

```yaml
# docker-compose.yml (add multiple API services)
services:
  socrates-api-1:
    <<: *api-service

  socrates-api-2:
    <<: *api-service

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - socrates-api-1
      - socrates-api-2
```

### Database Scaling

For large deployments:
- **Read replicas:** Configure PostgreSQL streaming replication
- **Connection pooling:** Use PgBouncer or connection pool middleware
- **Partitioning:** Partition large tables (llm_usage_tracking, conversation_history)

---

## Updating to New Version

### Docker Compose Method

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Migrations run automatically
```

### Manual Method

```bash
# Pull latest code
git pull origin main

# Activate virtual environment
source backend/.venv/bin/activate

# Update dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
export DATABASE_URL="postgresql://..."
alembic upgrade head

# Restart application
# (depends on your process manager: systemd, supervisor, pm2, etc.)
```

---

## CI/CD Pipeline

Socrates includes a GitHub Actions CI/CD pipeline (`.github/workflows/ci-cd.yml`).

### Automated Checks
- **Lint:** flake8, black, isort
- **Tests:** pytest with coverage
- **Security:** Trivy vulnerability scanning
- **Build:** Docker image creation

### Deployment Trigger
Pipeline automatically deploys to production when:
- Code is pushed to `main` branch
- All tests pass
- Security scan passes

### Required Secrets

Configure in GitHub Settings → Secrets:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `DEPLOY_HOST` - Production server IP/hostname (optional)
- `DEPLOY_USER` - SSH username (optional)
- `DEPLOY_SSH_KEY` - SSH private key (optional)

---

## HTTPS Setup (Nginx + Let's Encrypt)

### 1. Install Nginx

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/socrates2`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/socrates2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Get SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

Certbot automatically configures HTTPS and renewal.

---

## Support

For issues or questions:
- **GitHub Issues:** https://github.com/your-org/Socrates/issues
- **Documentation:** https://docs.socrates2.com
- **Email:** support@socrates2.com

---

## License

See LICENSE file for details.
