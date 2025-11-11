# Migration Infrastructure Issues and Fixes

## Summary
The project has 38 database migrations, but there are configuration issues that need to be resolved:

### Issues Identified
1. **Revision ID Mismatch (FIXED)** ✅
   - Migrations 031-038 had inconsistent revision IDs
   - Fixed: Changed from full names (e.g., '031_create_admin_roles_table') to numeric IDs (e.g., '031')

2. **Database-Specific Migration Checks (PARTIALLY FIXED)**
   - Migrations 003-022 have proper `_should_run()` checks
   - Migrations 023-034 were missing these checks - **ADDED** but need manual verification
   - Migrations 035-038 have proper checks

3. **Migration 026 (pgvector)**
   - pgvector extension not available on Windows
   - Fixed: Made migration logic conditional, skips if extension unavailable

4. **Migration 022 (Performance Indexes)**
   - team_members indexes incorrectly placed in socrates_auth block
   - Fixed: Moved to socrates_specs block where teams/team_members exist

### Workaround for Quick Setup
Run migrations manually in correct order:

```bash
# 1. Create basic auth tables (001-002)
export DATABASE_URL="postgresql://postgres@localhost:5432/socrates_auth"
alembic upgrade 002

# 2. Create admin tables (031-033)
alembic upgrade 033

# 3. Create specs tables (003-034)
export DATABASE_URL="postgresql://postgres@localhost:5432/socrates_specs"
alembic upgrade head
```

## Files Modified
- `backend/alembic/versions/031-038`: Fixed revision IDs
- `backend/alembic/versions/022`: Fixed migration database targeting
- `backend/alembic/versions/026`: Made pgvector optional
- `backend/alembic/versions/023-034`: Added _should_run() checks

## Next Steps
1. Test migrations with workaround approach above
2. Once verified, update alembic/env.py to handle multi-database migrations better
3. Consider using separate migration branches for each database in future

## Alternative: Skip Migrations
For development purposes, you can also:
1. Create tables manually using SQLAlchemy models
2. Use app.main:app which can auto-create tables if configured
3. Focus on API and business logic, not database migrations
