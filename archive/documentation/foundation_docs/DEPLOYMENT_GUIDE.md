# DEPLOYMENT GUIDE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟢 LOW - Complete before production deployment

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [DigitalOcean App Platform (Recommended)](#digitalocean-app-platform-recommended)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup Strategy](#backup-strategy)
9. [Rollback Procedure](#rollback-procedure)

---

## OVERVIEW

**Goal:** Deploy Socrates to production reliably and securely.

### Recommended Platform

**DigitalOcean App Platform** - Simple, scalable, managed

**Why:**
- ✅ Easy deployment (Git integration)
- ✅ Managed PostgreSQL (backups, scaling)
- ✅ Auto-scaling
- ✅ SSL/TLS included
- ✅ Affordable ($12-25/month for MVP)

---

## DEPLOYMENT OPTIONS

### Option 1: DigitalOcean App Platform (Recommended)

**Pros:**
- Easiest deployment
- Managed database
- Auto-scaling
- Built-in monitoring

**Cons:**
- Vendor lock-in (moderate)
- Less control than bare metal

**Cost:** ~$17/month (MVP)
- App: $12/month
- PostgreSQL: $15/month (shared)

---

### Option 2: Docker + VPS

**Pros:**
- Full control
- Portable
- Can move to any cloud

**Cons:**
- More setup
- Manual scaling
- More maintenance

**Cost:** ~$12-24/month
- VPS: $12-24/month (4GB RAM)
- Self-managed PostgreSQL

---

## DIGITALOCEAN APP PLATFORM (RECOMMENDED)

### Step 1: Create App

```bash
# 1. Push code to GitHub
git push origin master

# 2. Go to DigitalOcean → Apps → Create App
# 3. Connect GitHub repository
# 4. Select branch: master
# 5. Configure build settings
```

### Step 2: Configure Build

```yaml
# .do/app.yaml (auto-generated, customize if needed)
name: socrates
services:
  - name: web
    github:
      repo: Nireus79/Socrates
      branch: master
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    http_port: 8000
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL_AUTH
        value: ${db_auth.DATABASE_URL}
      - key: DATABASE_URL_SPECS
        value: ${db_specs.DATABASE_URL}

databases:
  - name: db-auth
    engine: PG
    version: "15"
    size: db-s-dev-database
  - name: db-specs
    engine: PG
    version: "15"
    size: db-s-dev-database
```

### Step 3: Configure Environment Variables

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generate-32-char-secret>
JWT_SECRET_KEY=<generate-32-char-secret>
ANTHROPIC_API_KEY=<your-api-key>
CORS_ORIGINS=https://yourfrontend.com
```

### Step 4: Run Migrations

```bash
# Connect to app console
doctl apps create-deployment <app-id>

# Or run migration job
doctl apps run <app-id> --command "alembic upgrade head"
```

### Step 5: Deploy

```bash
# Deploy automatically on git push
git push origin master

# Or manual deploy
doctl apps create-deployment <app-id>
```

---

## DOCKER DEPLOYMENT

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL_AUTH=postgresql://postgres:password@db-auth:5432/socrates_auth
      - DATABASE_URL_SPECS=postgresql://postgres:password@db-specs:5432/socrates_specs
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db-auth
      - db-specs

  db-auth:
    image: postgres:15
    environment:
      - POSTGRES_DB=socrates_auth
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - auth-data:/var/lib/postgresql/data

  db-specs:
    image: postgres:15
    environment:
      - POSTGRES_DB=socrates_specs
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - specs-data:/var/lib/postgresql/data

volumes:
  auth-data:
  specs-data:
```

### Deploy

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f app

# Run migrations
docker-compose exec app alembic upgrade head

# Stop
docker-compose down
```

---

## ENVIRONMENT CONFIGURATION

### Production .env

```bash
# Production environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Database (managed PostgreSQL)
DATABASE_URL_AUTH=<managed-postgres-url-auth>
DATABASE_URL_SPECS=<managed-postgres-url-specs>

# Security (generated, never commit)
SECRET_KEY=<32-char-secret>
JWT_SECRET_KEY=<32-char-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM API
ANTHROPIC_API_KEY=<production-api-key>

# CORS
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

---

## DATABASE SETUP

### Managed PostgreSQL (DigitalOcean)

```bash
# 1. Create managed PostgreSQL cluster
doctl databases create socrates-db-auth --engine pg --version 15 --size db-s-1vcpu-1gb

# 2. Create second database cluster
doctl databases create socrates-db-specs --engine pg --version 15 --size db-s-1vcpu-2gb

# 3. Get connection strings
doctl databases connection socrates-db-auth
doctl databases connection socrates-db-specs

# 4. Create databases
psql <connection-string-auth> -c "CREATE DATABASE socrates_auth;"
psql <connection-string-specs> -c "CREATE DATABASE socrates_specs;"

# 5. Run migrations
export DATABASE_URL_AUTH=<connection-string-auth>
export DATABASE_URL_SPECS=<connection-string-specs>
alembic upgrade head
```

---

## MONITORING & LOGGING

### Application Monitoring

```python
# config/monitoring.py
from prometheus_client import Counter, Histogram
import logging

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
llm_calls = Counter('llm_calls_total', 'Total LLM API calls', ['provider'])

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/socrates/app.log'),
        logging.StreamHandler()
    ]
)
```

### DigitalOcean Monitoring

- Built-in metrics (CPU, memory, requests)
- Log aggregation
- Alerts on errors/downtime

---

## BACKUP STRATEGY

### Database Backups

**DigitalOcean Managed PostgreSQL:**
- Automatic daily backups (7 days retention)
- Point-in-time recovery
- Manual backups before major changes

**Manual Backup:**

```bash
# Backup auth database
pg_dump <database-url-auth> > backup_auth_$(date +%Y%m%d).sql

# Backup specs database
pg_dump <database-url-specs> > backup_specs_$(date +%Y%m%d).sql

# Upload to S3/Spaces
aws s3 cp backup_*.sql s3://socrates-backups/
```

---

## ROLLBACK PROCEDURE

### Application Rollback

```bash
# DigitalOcean: Rollback to previous deployment
doctl apps update <app-id> --deployment-id <previous-deployment-id>

# Docker: Rollback to previous image
docker-compose pull app:previous-tag
docker-compose up -d
```

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Restore from backup (if needed)
psql <database-url> < backup_auth_20251105.sql
```

---

**Document Status:** ✅ Complete
**Date:** November 5, 2025
