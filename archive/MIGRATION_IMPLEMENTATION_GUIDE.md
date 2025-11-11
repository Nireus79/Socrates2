# Migration Implementation Guide

**Version:** 1.0
**Date:** November 11, 2025
**Status:** Production Ready

---

## Quick Start

### Run All Migrations

```bash
cd backend
python scripts/run_migrations_safe.py
```

Expected output:
```
✅ socrates_auth: 002 (head)
✅ socrates_specs: 009 (head)
```

### Check Migration Status

```bash
python scripts/run_migrations_safe.py --check-status
```

### Run Individual Database Migrations

```bash
# AUTH database only
python scripts/run_migrations_safe.py --auth-only

# SPECS database only
python scripts/run_migrations_safe.py --specs-only
```

---

## Architecture Overview

### Two-Database Design

Socrates uses **Alembic branching** for multi-database migrations:

```
DATABASE: socrates_auth
├── 001: Initial Auth Schema (users, refresh_tokens)
└── 002: Admin Management (admin_roles, admin_users, admin_audit_logs)

DATABASE: socrates_specs
├── 003: Core Specification Tables
├── 004: Generated Content
├── 005: Tracking & Analytics
├── 006: Collaboration & Sharing
├── 007: API & LLM Integration
├── 008: Analytics & Search
└── 009: Activity & Project Management
```

### Alembic Branching Commands

```bash
# Upgrade to latest AUTH migrations
alembic upgrade auth@head

# Upgrade to latest SPECS migrations
alembic upgrade specs@head

# View migration history
alembic history

# Check current revision
alembic current
```

---

## Migration Files Structure

Each migration file follows this template:

```python
"""
[Module Description]

Revision ID: [number]
Revises: [previous number or None]
Create Date: 2025-11-11

[Detailed description of tables created and purposes]

Tables created:
- [table_name]: [description]

Target Database: socrates_auth or socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '[number]'
down_revision = '[previous number or None]'
branch_labels = ('[branch]',)  # Only on first migration of branch
depends_on = None


def upgrade() -> None:
    """Create tables for this migration."""
    # op.create_table() calls
    # op.create_index() calls
    pass


def downgrade() -> None:
    """Drop tables created by this migration."""
    # op.drop_table() calls
    pass
```

---

## Key Design Patterns

### 1. UUID Primary Keys

All tables use PostgreSQL UUID type with server-side generation:

```python
sa.Column(
    'id',
    postgresql.UUID(as_uuid=True),
    primary_key=True,
    server_default=sa.text('gen_random_uuid()'),
    nullable=False,
    comment='Unique identifier (UUID)'
)
```

**Benefits:**
- Distributed system ready
- Better security than sequential IDs
- No table locking during inserts

### 2. Timezone-Aware Timestamps

All timestamps are timezone-aware with server defaults:

```python
sa.Column(
    'created_at',
    sa.DateTime(timezone=True),
    nullable=False,
    server_default=sa.func.now(),
    comment='Creation timestamp'
)
```

**Benefits:**
- Consistent across regions
- Multi-region deployment ready
- Server-managed (no client clock skew)

### 3. Foreign Key Strategies

**CASCADE Delete:** For dependent data that should be deleted with parent
```python
sa.ForeignKeyConstraint(
    ['project_id'],
    ['projects.id'],
    ondelete='CASCADE'
)
```

**RESTRICT Delete:** For critical/audit data that must be preserved
```python
sa.ForeignKeyConstraint(
    ['role_id'],
    ['admin_roles.id'],
    ondelete='RESTRICT'
)
```

**SET NULL:** For optional references
```python
sa.ForeignKeyConstraint(
    ['project_id'],
    ['projects.id'],
    ondelete='SET NULL'
)
```

### 4. Cross-Database References (No FK Constraint)

References to other database tables are documented but not enforced:

```python
sa.Column(
    'user_id',
    postgresql.UUID(as_uuid=True),
    nullable=False,
    comment='Reference to users.id in socrates_auth (no FK - cross-database)'
)
```

**Application Responsibility:**
- Validate user_id exists in socrates_auth.users
- Handle cascade deletes in application code
- Document in comments clearly

### 5. JSONB for Flexible Data

Use JSONB for metadata and flexible fields:

```python
sa.Column(
    'metadata',
    postgresql.JSONB(astext_type=sa.Text()),
    nullable=True,
    server_default=sa.text("'{}'::jsonb"),
    comment='Flexible metadata storage'
)
```

**Benefits:**
- Schema evolution without migrations
- Queryable in SQL
- Index support for common fields

### 6. Comprehensive Indexing

Index strategy:
- All PK/FK columns
- All status/state columns
- All date/timestamp columns
- All frequently filtered columns
- Composite indexes for common combinations

```python
op.create_index('ix_table_column', 'table', ['column'])
op.create_index('ix_table_composite', 'table', ['col1', 'col2'])
```

---

## Common Operations

### Creating a New Migration

```bash
cd backend
alembic revision --message "add new feature"
```

This creates a new migration file: `alembic/versions/010_add_new_feature.py`

Edit the file with your changes:

```python
def upgrade() -> None:
    """Add new feature table."""
    op.create_table(
        'new_feature',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, ...),
        # Add more columns
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_new_feature_id', 'new_feature', ['id'])


def downgrade() -> None:
    """Remove new feature table."""
    op.drop_table('new_feature')
```

### Running Specific Migration

```bash
# Run to specific revision
alembic upgrade 005

# Run N migrations forward
alembic upgrade +3

# Rollback N migrations
alembic downgrade -1
```

### Adding a Column to Existing Table

```python
def upgrade() -> None:
    """Add new column to users table."""
    op.add_column(
        'users',
        sa.Column(
            'new_field',
            sa.String(255),
            nullable=True,
            comment='New field description'
        )
    )


def downgrade() -> None:
    """Remove new field from users."""
    op.drop_column('users', 'new_field')
```

### Adding an Index

```python
def upgrade() -> None:
    """Add index for performance."""
    op.create_index(
        'ix_users_email_created_at',
        'users',
        ['email', 'created_at']
    )


def downgrade() -> None:
    """Remove index."""
    op.drop_index('ix_users_email_created_at', table_name='users')
```

---

## Common Errors and Solutions

### Error: "Can't execute this migration for SQLite"

**Cause:** Using PostgreSQL-specific features with SQLite
**Solution:** Ensure environment is PostgreSQL, not SQLite

### Error: "Foreign key constraint fails"

**Cause:** Attempting to delete parent before children
**Solution:** Use CASCADE delete or delete children first

### Error: "Duplicate column name"

**Cause:** Column added twice in migration
**Solution:** Check for idempotency - migrations can be run multiple times

### Error: "Password authentication failed"

**Cause:** Database connection URL incorrect
**Solution:** Check DATABASE_URL_AUTH and DATABASE_URL_SPECS environment variables

### Error: "ARRAY type requires explicit type specification"

**Cause:** Using ARRAY without specifying element type
**Solution:** Use `postgresql.ARRAY(sa.String())` not just `ARRAY`

---

## Testing Migrations

### Unit Test Example

```python
import pytest
from sqlalchemy import inspect
from app.core.database import auth_engine, specs_engine


def test_auth_migrations():
    """Verify AUTH database schema after migrations."""
    inspector = inspect(auth_engine)

    # Check tables exist
    tables = inspector.get_table_names()
    assert 'users' in tables
    assert 'refresh_tokens' in tables
    assert 'admin_roles' in tables

    # Check columns
    user_columns = {col['name'] for col in inspector.get_columns('users')}
    assert 'id' in user_columns
    assert 'email' in user_columns
    assert 'hashed_password' in user_columns


def test_specs_migrations():
    """Verify SPECS database schema after migrations."""
    inspector = inspect(specs_engine)

    # Check all core tables exist
    tables = inspector.get_table_names()
    core_tables = ['projects', 'sessions', 'questions', 'specifications']
    for table in core_tables:
        assert table in tables


def test_cross_database_refs():
    """Verify cross-database references are documented."""
    # Check that projects.user_id references users.id
    inspector = inspect(specs_engine)
    projects_fks = inspector.get_foreign_keys('projects')

    # Note: Will be empty since cross-db FKs aren't enforced
    # Application must validate
    assert projects_fks == []
```

### Integration Test Example

```python
def test_full_migration_workflow():
    """Test complete migration execution."""
    from app.core.database import auth_session, specs_session
    from app.models import User, Project

    # Create test user
    user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='hashed_pwd',
        name='Test',
        surname='User'
    )
    auth_session.add(user)
    auth_session.commit()

    # Create test project
    project = Project(
        user_id=user.id,
        name='Test Project',
        description='Test',
        phase='discovery',
        status='active'
    )
    specs_session.add(project)
    specs_session.commit()

    # Verify both databases work
    assert auth_session.query(User).filter_by(email='test@example.com').first()
    assert specs_session.query(Project).filter_by(name='Test Project').first()
```

---

## Environment Setup

### Required Environment Variables

```bash
# Database URLs (two separate databases)
DATABASE_URL_AUTH=postgresql://postgres:password@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres:password@localhost:5432/socrates_specs

# Alembic configuration
export DATABASE_URL=$DATABASE_URL_AUTH  # For running individual branch migrations
```

### Local Development Setup

```bash
# Create local databases
createdb socrates_auth
createdb socrates_specs

# Run migrations
python scripts/run_migrations_safe.py

# Verify
python scripts/run_migrations_safe.py --check-status
```

### Docker Setup

```dockerfile
# In your Dockerfile or docker-compose.yml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_PASSWORD: postgres
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"

  backend:
    depends_on:
      - postgres
    environment:
      DATABASE_URL_AUTH: postgresql://postgres:postgres@postgres:5432/socrates_auth
      DATABASE_URL_SPECS: postgresql://postgres:postgres@postgres:5432/socrates_specs
    command: sh -c "
      psql -h postgres -U postgres -c 'CREATE DATABASE socrates_auth;' || true &&
      psql -h postgres -U postgres -c 'CREATE DATABASE socrates_specs;' || true &&
      python scripts/run_migrations_safe.py
    "
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Backup both databases
- [ ] Review migration code
- [ ] Test migrations in staging
- [ ] Verify migration reversal works
- [ ] Have rollback plan ready

### Deployment Steps

```bash
# 1. Backup databases
pg_dump socrates_auth > socrates_auth_backup.sql
pg_dump socrates_specs > socrates_specs_backup.sql

# 2. Run migrations
python scripts/run_migrations_safe.py

# 3. Verify
python scripts/run_migrations_safe.py --check-status

# 4. Monitor logs
tail -f logs/migration.log
```

### Rollback Procedure

```bash
# If migration fails, rollback:
alembic downgrade auth@previous_version
alembic downgrade specs@previous_version

# Or restore from backup:
psql socrates_auth < socrates_auth_backup.sql
psql socrates_specs < socrates_specs_backup.sql
```

---

## Troubleshooting

### Check Migration History

```bash
# View all migrations
alembic history

# Current version
alembic current

# Detailed history
alembic history --verbose
```

### Debug Migration Issues

```bash
# Set SQL echo to see actual SQL
export SQLALCHEMY_ECHO=1
python scripts/run_migrations_safe.py

# Check database directly
psql socrates_auth -c "\dt"  # List tables
psql socrates_specs -c "\dt"  # List tables
```

### Common Database Issues

```bash
# Check connections
psql socrates_auth -c "SELECT version();"

# List indexes
\di

# Check table structure
\d+ table_name

# View constraints
\d table_name
```

---

## Best Practices

1. **Always use transactions** - Alembic wraps migrations in transactions
2. **Test reversibility** - Always write downgrade() that undoes upgrade()
3. **Document changes** - Use descriptive docstrings
4. **Index strategically** - Add indexes for filtered/joined columns
5. **Validate data** - Check referential integrity in code, not DB
6. **Use server defaults** - Let database manage timestamps
7. **Version control** - Always commit migration files
8. **Review before deploy** - Get peer review of migrations
9. **Communicate changes** - Notify team of schema changes
10. **Monitor performance** - Check query plans after migrations

---

## Related Documentation

- `DATABASE_SCHEMA_REFERENCE.md` - Complete schema documentation
- `MIGRATION_REDESIGN_COMPLETE.md` - Redesign summary
- `MIGRATION_AUDIT_REPORT.md` - Initial audit findings
- `backend/alembic/versions/` - All migration files

---

## Support

For issues or questions:
1. Check `DATABASE_SCHEMA_REFERENCE.md` for table definitions
2. Review migration files in `backend/alembic/versions/`
3. Check Alembic documentation: https://alembic.sqlalchemy.org/
4. Review SQLAlchemy DDL docs: https://docs.sqlalchemy.org/

---

**Last Updated:** November 11, 2025
**Maintained By:** Socrates Team
