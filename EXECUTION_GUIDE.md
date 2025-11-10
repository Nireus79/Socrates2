# Complete Execution Guide: Bug Fixes & Migration

**Date:** November 10, 2025
**Status:** All code changes complete. Ready for execution.

---

## WHAT'S BEEN DONE (Code Changes)

### ✅ Bug #2 Fix (Timestamp Issue) - COMPLETE
- [x] Added `conversation_db_to_api_message()` function to `core/models.py`
- [x] Updated `direct_chat.py _load_conversation_context()` to use conversion function
- [x] Result: Timestamp no longer leaks to Anthropic API

### ✅ Bug #1 Migration (Key/Value) - CODE COMPLETE
- [x] Created migration strategy document: `SPECIFICATION_KEY_VALUE_MIGRATION.md`
- [x] Created Alembic migration 023: `add_key_value_to_specifications.py`
- [x] Created Alembic migration 024: `make_key_value_required.py`
- [x] Created data migration script: `scripts/migrate_specifications_to_key_value.py`
- [x] Updated Specification model with key/value columns
- [x] Updated core/models.py spec_db_to_data() for migration compatibility
- [x] socratic.py is already configured to use library's specs_db_to_data

---

## WHAT YOU NEED TO DO NEXT (In Order)

### PHASE 1: Database Backup (CRITICAL!)

**Step 1.1: Backup both databases**

```bash
# Create timestamped backup
cd C:\Users\themi\PycharmProjects\Socrates2

# Backup PostgreSQL databases
pg_dump socrates_auth > backup_auth_$(date +%Y%m%d_%H%M%S).sql
pg_dump socrates_specs > backup_specs_$(date +%Y%m%d_%H%M%S).sql

# Keep these files safe!
```

**Why:** If anything goes wrong, you can restore from backup.

---

### PHASE 2: Apply Migrations

**Step 2.1: Run migration 023 (add columns)**

```bash
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Run the migration that adds key/value columns (nullable)
alembic upgrade +1

# Verify it worked
alembic current
```

**Expected output:**
```
...
023_add_key_value_to_specifications

INFO [alembic.runtime.migration] Done
```

**What happened:**
- ✓ Columns `key` and `value` added as nullable
- ✓ Index created for fast queries
- ✓ Safe to rollback if needed (columns are nullable)

---

### PHASE 3: Data Migration

**Step 3.1: Run data migration script (DRY RUN first)**

```bash
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# DRY RUN - shows what would happen without making changes
python scripts/migrate_specifications_to_key_value.py --dry-run

# Review the output - does the key/value extraction look good?
```

**Look for:**
- Specifications being processed
- Intelligent key extraction based on category
- No errors or exceptions

**Example output:**
```
================================================================================
Specification Key/Value Migration
================================================================================
Total specifications in database: 1
Dry run: True
Sample mode (first 50): False

Processing: 1 specifications

[1/1] Spec ID: 546bc328-d5ad-4dd6-86d2-9766e497c785
  Category: discovery
  Content: Testing Socrates...
  → Key: testing_socrates
  → Value: Testing Socrates
```

---

**Step 3.2: Run data migration script (ACTUAL)**

```bash
# If dry-run looked good, run the actual migration
python scripts/migrate_specifications_to_key_value.py

# Script will:
# 1. Extract key/value from content
# 2. Populate database
# 3. Validate results
# 4. Print summary report
```

**Expected output:**
```
================================================================================
Migration Summary
================================================================================
Total processed:      1
With content:         1
Already have key:     0
Migrated:             1
Skipped (no content): 0
Errors:               0

================================================================================
Validation Report
================================================================================
Key/Value Coverage:
  Total specs:        1
  With key:           1 (100.0%)
  With value:         1 (100.0%)
  ✓ All specs have key and value
```

---

**Step 3.3: Verify migration results**

```bash
# Connect to database and check a few specs
psql -U postgres -d socrates_specs

# Run this SQL
SELECT id, category, key, value, content
FROM specifications
LIMIT 5;

# You should see: key and value columns populated!
```

---

### PHASE 4: Make Columns Required

**Step 4.1: Run migration 024 (make NOT NULL)**

```bash
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Run migration that makes key/value NOT NULL
# (Safe because we just populated them all)
alembic upgrade +1

# Verify
alembic current
```

**Expected output:**
```
024_make_key_value_required
```

**What happened:**
- ✓ key and value columns now required (NOT NULL)
- ✓ Database enforces structured specifications
- ✓ Impossible to create spec without key and value

---

### PHASE 5: Test Everything

**Step 5.1: Start the backend server**

```bash
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Start FastAPI server
python -m uvicorn app.main:app --reload

# Should start successfully on http://localhost:8000
```

---

**Step 5.2: Test Socratic Mode (Question Generation)**

Using the CLI (Socrates.py):

```bash
# In another terminal
cd C:\Users\themi\PycharmProjects\Socrates2

python Socrates.py

# Commands:
/login
# Enter credentials

/project select
# Select your test project

/session start
# Start a new session

# Try to get a question
# (This was failing before - should work now!)
```

**What to look for:**
- ✓ No error about 'Specification' object has no attribute 'key'
- ✓ Question is generated successfully
- ✓ Maturity score is shown

---

**Step 5.3: Test Direct Chat Mode (Timestamp Fix)**

Using the CLI:

```bash
/mode
# Switch to direct chat mode

# Send a message
hi

# What to look for:
# ✓ No error about "messages.0.timestamp: Extra inputs..."
# ✓ Response received from Claude
# ✓ Conversation continues naturally
```

---

**Step 5.4: Verify Spec Extraction Works**

```bash
# In direct chat, send a specification-related message
I need a PostgreSQL database with JSON support

# The system should:
# ✓ Extract spec with key='primary_database', value='PostgreSQL'
# ✓ Show "specs_extracted: 1"
# ✓ Update maturity score
```

---

### PHASE 6: If Something Goes Wrong (Rollback Plan)

**If migrations fail:**

```bash
cd C:\Users\themi\PycharmProjects\Socrates2\backend

# Rollback last migration
alembic downgrade -1

# Check what's current
alembic current

# Rollback more if needed
alembic downgrade -2
```

**If data migration fails:**

```bash
# 1. The script is safe - it won't corrupt data
# 2. You can run it again after fixing issues
# 3. It's idempotent (safe to run multiple times)

python scripts/migrate_specifications_to_key_value.py --sample
# Test with just 50 specs first
```

**If you need to restore from backup:**

```bash
# Stop the server first!

# Restore database
psql socrates_specs < backup_specs_TIMESTAMP.sql

# Rollback all migrations
cd backend
alembic downgrade base

# Start fresh
```

---

## Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| Backup | Database backup | 5 min | Ready |
| Migrate | Run migration 023 | 2 min | Ready |
| Data | Data migration script | 5-10 min | Ready |
| Verify | Check database | 5 min | Ready |
| Migrate | Run migration 024 | 2 min | Ready |
| Test | Start server | 2 min | Ready |
| Test | Socratic mode | 5 min | Ready |
| Test | Direct chat mode | 5 min | Ready |
| **TOTAL** | | **~30 min** | - |

---

## Quick Reference: Files Changed

### Bug #2 Fix
- `backend/app/core/models.py` - Added `conversation_db_to_api_message()`
- `backend/app/agents/direct_chat.py` - Updated `_load_conversation_context()`

### Bug #1 Migration
- `backend/alembic/versions/023_add_key_value_to_specifications.py` - New migration
- `backend/alembic/versions/024_make_key_value_required.py` - New migration
- `backend/scripts/migrate_specifications_to_key_value.py` - New script
- `backend/app/models/specification.py` - Added key/value columns
- `backend/app/core/models.py` - Updated spec_db_to_data() for compatibility

### Documentation
- `SPECIFICATION_KEY_VALUE_MIGRATION.md` - Complete migration strategy
- `MISMATCH_ANALYSIS.md` - Deep analysis of both bugs
- `MIGRATION_AND_FIX_PLAN.md` - Original planning document
- `EXECUTION_GUIDE.md` - This file

---

## Success Criteria

After completing all steps, verify:

- ✅ Direct chat mode works without timestamp errors
- ✅ Socratic mode generates questions without key attribute errors
- ✅ All specifications have key and value populated
- ✅ Questions are generated successfully
- ✅ Spec extraction works in both modes
- ✅ Maturity score updates correctly
- ✅ Database queries by category/key work efficiently

---

## Questions or Issues?

Refer to:
1. `SPECIFICATION_KEY_VALUE_MIGRATION.md` - Migration details
2. `MISMATCH_ANALYSIS.md` - Why bugs happened
3. Migration validation queries in migration strategy doc
4. Rollback plan above

---

**You're almost there!** The heavy lifting is done. Now just execute the steps in order.

Good luck! 🚀
