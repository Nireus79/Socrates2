# Specification Key/Value Migration Strategy

**Date:** November 10, 2025
**Objective:** Migrate from single `content` field to structured `key` and `value` fields

---

## Overview

### Current State
```sql
specifications(
    id, project_id, category, content, source, confidence, ...
)
-- content: "FastAPI web framework for async APIs"
```

### Target State
```sql
specifications(
    id, project_id, category, key, value, content, source, confidence, ...
)
-- key: "api_framework"
-- value: "FastAPI"
-- content: "FastAPI web framework for async APIs" (for complex notes)
```

---

## Migration Phases

### Phase 1: Add Columns (Migration 023)
- Add `key` column (VARCHAR 255, nullable initially)
- Add `value` column (TEXT, nullable initially)
- Create index: `(project_id, category, key)` for fast queries

### Phase 2: Data Migration Script
- Read each specification
- Extract `key` and `value` intelligently from `content` based on category
- Update rows with extracted data
- Validate all specs are populated

### Phase 3: Make Required (Migration 024)
- ALTER: `key` SET NOT NULL
- ALTER: `value` SET NOT NULL
- Only after all data is migrated

### Phase 4: Code Updates
- Update Specification SQLAlchemy model
- Remove spec_db_to_data workaround
- Update socratic.py to use library function
- All code should reference `spec.key` and `spec.value`

---

## Key Extraction Logic

### By Category

#### `goals`
Extract first meaningful phrase (up to 10 words or first period)
```
content: "Build a web app to manage tasks efficiently"
→ key: "primary_goal"
→ value: "Build a web app to manage tasks efficiently"
```

#### `requirements`
Extract requirement statement
```
content: "Support 10k concurrent users with 99.9% uptime"
→ key: "concurrent_users"
→ value: "10k concurrent users"

content: "Support 99.9% uptime"
→ key: "uptime_sla"
→ value: "99.9%"
```

#### `tech_stack`
If structured as "Layer: Technology", use that
```
content: "Backend: FastAPI"
→ key: "api_framework"
→ value: "FastAPI"

content: "PostgreSQL 17 with replication"
→ key: "primary_database"
→ value: "PostgreSQL 17"
```

#### `scalability`
Extract target metric
```
content: "Handle 100k concurrent connections"
→ key: "max_concurrent_connections"
→ value: "100k"

content: "Auto-scale based on CPU usage"
→ key: "scaling_trigger"
→ value: "CPU usage"
```

#### `security`
Extract security requirement
```
content: "JWT tokens with 24-hour expiry"
→ key: "authentication_method"
→ value: "JWT tokens"

content: "Encrypt at rest with AES-256"
→ key: "encryption_at_rest"
→ value: "AES-256"
```

#### `performance`
Extract performance metric
```
content: "API response time < 100ms"
→ key: "api_response_time_target"
→ value: "< 100ms"

content: "Page load time < 2 seconds"
→ key: "page_load_target"
→ value: "< 2 seconds"
```

#### `testing`
Extract test type/requirement
```
content: "80% code coverage minimum"
→ key: "code_coverage_target"
→ value: "80%"

content: "All critical paths tested"
→ key: "critical_path_testing"
→ value: "required"
```

#### `monitoring`
Extract monitoring requirement
```
content: "Real-time dashboards with 5-minute refresh"
→ key: "dashboard_refresh_rate"
→ value: "5 minutes"

content: "Alert on errors > 5% error rate"
→ key: "error_rate_alert_threshold"
→ value: "5%"
```

#### `data_retention`
Extract retention policy
```
content: "Keep user data for 7 years"
→ key: "user_data_retention"
→ value: "7 years"

content: "Delete inactive accounts after 2 years"
→ key: "inactive_account_retention"
→ value: "2 years"
```

#### `disaster_recovery`
Extract DR requirement
```
content: "RTO: 4 hours, RPO: 1 hour"
→ key: "rto"
→ value: "4 hours"

content: "Multi-region backup"
→ key: "backup_strategy"
→ value: "multi-region"
```

---

## Algorithm

```python
def extract_key_value(content: str, category: str) -> tuple[str, str]:
    """
    Intelligently extract key and value from content based on category.

    Strategy:
    1. If content has ":", split on first colon (structured data)
    2. Otherwise, extract first meaningful phrase as key
    3. Whole content (or phrase) as value
    """

    if not content:
        return (f"unspecified_{category}", "")

    content = content.strip()

    # Strategy 1: Structured data (key: value)
    if ':' in content:
        parts = content.split(':', 1)
        key_part = parts[0].strip()
        value_part = parts[1].strip() if len(parts) > 1 else content

        # Convert key to snake_case
        key = key_part.lower().replace(' ', '_')
        key = ''.join(c for c in key if c.isalnum() or c == '_')
        return (key, value_part)

    # Strategy 2: Extract meaningful phrases
    # For different categories, use different extraction logic
    if category == 'tech_stack':
        # First 2-3 words are the value
        words = content.split()[:3]
        value = ' '.join(words)
        key = f"{category}_{words[0].lower()}"
    else:
        # Extract first meaningful phrase
        # Take first 3-5 words or up to period/comma
        for delimiter in ['. ', ', ', ' and ', ' or ']:
            if delimiter in content:
                value = content.split(delimiter)[0].strip()
                break
        else:
            words = content.split()[:5]
            value = ' '.join(words)

        # Generate key from first few words
        key_words = value.split()[:3]
        key = '_'.join(key_words).lower()
        key = ''.join(c for c in key if c.isalnum() or c == '_')

    # Ensure key is reasonable length
    key = key[:50] if key else f"spec_{category}"
    value = value[:1000] if len(value) > 1000 else value

    return (key, value)
```

---

## Safety Measures

### Before Running Script

1. **Backup Database**
   ```bash
   pg_dump socrates_specs > backup_specs_$(date +%Y%m%d_%H%M%S).sql
   pg_dump socrates_auth > backup_auth_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test in Staging**
   - Run migration on test database first
   - Validate extraction quality

### During Migration

1. **Validation Checks**
   - Every spec has key and value populated
   - No NULL key or value after migration
   - Sample random specs for quality

2. **Logging**
   - Log each spec processed
   - Log any extraction issues
   - Generate summary report

3. **Rollback Plan**
   - If validation fails, rollback migration
   - Columns are nullable, so safe to rollback
   - Restore from backup if needed

---

## Verification Queries

After migration, verify:

```sql
-- Check all specs have key and value
SELECT COUNT(*) as total,
       COUNT(key) as with_key,
       COUNT(value) as with_value
FROM specifications;
-- Should be: total = with_key = with_value

-- Check for duplicates (same key in same project/category)
SELECT project_id, category, key, COUNT(*) as count
FROM specifications
WHERE is_current = true
GROUP BY project_id, category, key
HAVING COUNT(*) > 1;
-- Should return: no rows (no duplicates)

-- Sample specs to verify quality
SELECT project_id, category, key, value, content
FROM specifications
WHERE is_current = true
ORDER BY created_at DESC
LIMIT 20;
-- Visually verify extraction quality
```

---

## Timeline

| Phase | Task | Time | Dependencies |
|-------|------|------|---|
| 1 | Create migration 023 | 15 min | - |
| 2 | Run migration 023 | 5 min | Migration 023 |
| 3 | Create migration script | 30 min | - |
| 4 | Run migration script | 10 min | Migration 023 |
| 5 | Validate data | 15 min | Migration script |
| 6 | Create migration 024 | 15 min | Validation |
| 7 | Run migration 024 | 5 min | Migration 024 |
| 8 | Update code | 60 min | All migrations |
| 9 | Test | 30 min | Code updates |
| **TOTAL** | | **~185 min** | |

---

## Rollback Plan

If anything goes wrong:

```bash
# 1. Rollback migration 024 (if applied)
cd backend
alembic downgrade -1  # Removes NOT NULL constraint

# 2. Run data migration again if needed
# (script is idempotent)

# 3. Rollback migration 023
alembic downgrade -1  # Drops key/value columns

# 4. Restore from backup if needed
psql socrates_specs < backup_specs_TIMESTAMP.sql
```

