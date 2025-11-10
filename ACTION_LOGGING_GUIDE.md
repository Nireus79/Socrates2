# Action Logging - User Guide

## Overview

The Socrates2 application now has comprehensive action logging that tracks all major workflow operations. You can monitor your background server processes in real-time by observing the action logs.

## Quick Start

### Running the Server with Logging Enabled (Default)

```bash
cd backend
python -m uvicorn app.main:app --reload
```

You'll see logs like:
```
14:23:45 - [ACTION] ✓ AUTH: User logged in (user: 550e8400...) | username=johndoe
14:23:46 - [ACTION] ✓ SESSION: Session started (socratic) | project_name=MyProject
14:23:47 - [ACTION] ✓ QUESTION: Question generated (goals) | quality_score=0.95
14:23:48 - [ACTION] ✓ SPECS: Specifications extracted and saved (5 extracted) | question_category=goals
14:23:49 - [ACTION] ✓ CONFLICT: No conflicts detected (0 found)
```

### Disabling Logging at Startup

In your `.env` file:
```ini
ACTION_LOGGING_ENABLED=false
ACTION_LOG_LEVEL=INFO
```

Then run the server - no action logs will be printed.

## Runtime Control (Without Restart)

### Check Current Logging Status

```bash
curl http://localhost:8000/api/v1/admin/logging/action \
  -H "Authorization: Bearer <admin_token>"
```

Response:
```json
{
  "enabled": true,
  "message": "Action logging is currently enabled"
}
```

### Enable Logging

```bash
curl -X POST http://localhost:8000/api/v1/admin/logging/action \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Disable Logging

```bash
curl -X POST http://localhost:8000/api/v1/admin/logging/action \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## Log Types

The system logs these action categories:

### 1. **AUTH** - Authentication Actions
- User registration
- Login/logout
- Token refresh

Example:
```
✓ AUTH: User registered | user_id=550e8400..., username=johndoe
✓ AUTH: User logged in | user_id=550e8400..., username=johndoe
✓ AUTH: Token refreshed | user_id=550e8400..., username=johndoe
```

### 2. **SESSION** - Session Management
- Session start
- Mode changes

Example:
```
✓ SESSION: Session started (socratic) | project_name=MyProject
✓ SESSION: Mode changed (direct_chat) | session_id=abc123...
```

### 3. **QUESTION** - Question Generation
- New Socratic questions
- Question quality scores

Example:
```
✓ QUESTION: Question generated (goals) | quality_score=0.95
✓ QUESTION: Question generated (requirements) | quality_score=0.88
```

### 4. **SPECS** - Specification Extraction
- Specs extracted and saved
- Maturity score updates
- Specification counts

Example:
```
✓ SPECS: Specifications extracted and saved (5 extracted) | question_category=goals
⊢ PROGRESS: Project maturity updated: 45% → 52% (5 specs extracted)
```

### 5. **CONFLICT** - Conflict Detection
- Conflicts detected
- No conflicts found
- Conflict counts and severity

Example:
```
✓ CONFLICT: Conflicts detected (2 found) | severity=['HIGH', 'MEDIUM']
✓ CONFLICT: No conflicts detected (0 found)
```

### 6. **LLM** - Language Model Operations
- API calls
- Model names
- Token counts

Example:
```
✓ LLM: Question generation (claude-sonnet-4-5-20250929) | tokens=250
✓ LLM: Specification extraction (claude-sonnet-4-5-20250929) | tokens=180
```

### 7. **PROJECT** - Project Operations
- Project creation
- Project updates

Example:
```
✓ PROJECT: Project created (MyProject) | user_id=550e8400...
✓ PROJECT: Project updated (MyProject) | maturity_score=65%
```

### 8. **DB** - Database Operations
- CRUD operations
- Table operations
- Row counts

Example:
```
✓ DB: Specification saved (specifications) | rows=5
✓ DB: Conflict saved (conflicts) | rows=2
```

### 9. **ERROR** - Failures and Errors
- Failed operations
- Error messages
- Context information

Example:
```
✗ ERROR: Failed to extract specifications | Invalid JSON response (parsing error)
✗ ERROR: Failed to generate question | Database error
```

### 10. **PROGRESS** - Multi-Step Operations
- Progress tracking
- Step counts and percentages
- Duration measurements

Example:
```
→ ACTION: Extracting specifications (started) | question_id=abc123...
⊢ PROGRESS: Processing specs (1/5) [20%] | category=goals
✓ ACTION: Extracting specifications (completed in 2.34s)
```

## Configuration Settings

In `.env`:

```ini
# Enable/disable action logging
ACTION_LOGGING_ENABLED=true

# Log level for action logs
# Options: INFO (default), DEBUG, WARNING
ACTION_LOG_LEVEL=INFO
```

## Output Format

Each log line follows this format:
```
HH:MM:SS - [ACTION] [STATUS] [CATEGORY]: [Action] [Details]
```

Components:
- **HH:MM:SS**: Current time
- **[ACTION]**: Log category marker
- **[STATUS]**: Success/failure indicator
  - `✓` = Successful operation
  - `✗` = Failed operation
  - `⚠` = Warning
  - `→` = Operation started
  - `⊢` = Progress update
- **[CATEGORY]**: Type of operation (AUTH, SPECS, QUESTION, etc.)
- **[Action]**: Description of what was done
- **[Details]**: Additional context (counts, names, scores, etc.)

## Use Cases

### 1. **Monitoring in Real-Time**
Watch the server console to see what's happening:
```bash
python -m uvicorn app.main:app --reload
```

### 2. **Reducing Log Volume**
In production, disable logs to reduce console output:
```ini
ACTION_LOGGING_ENABLED=false
```

### 3. **Debugging Issues**
Enable detailed logging to investigate problems:
```ini
ACTION_LOGGING_ENABLED=true
ACTION_LOG_LEVEL=DEBUG
```

### 4. **Selective Logging**
Enable at startup but disable for specific operations via API:
```bash
# Start with logging enabled
# Later disable it
curl -X POST http://localhost:8000/api/v1/admin/logging/action \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"enabled": false}'
```

## Performance Considerations

- **Enabled**: Minimal overhead (< 1% performance impact)
- **Disabled**: Zero overhead - NullHandler prevents all I/O
- **Runtime Toggle**: Instant, no restart required
- **Safe**: Thread-safe global state management

## Tips

1. **Watch Specifications Flow**: Monitor the SPECS logs to see how specifications are extracted
2. **Track Question Quality**: Check QUESTION logs for quality scores
3. **Monitor Conflicts**: CONFLICT logs show if requirements contradict
4. **Debug Errors**: Check ERROR logs when operations fail
5. **Check Progress**: PROGRESS logs show multi-step operation status

## Troubleshooting

### No action logs appearing?

1. Check if logging is enabled:
   ```bash
   curl http://localhost:8000/api/v1/admin/logging/action -H "Authorization: Bearer <token>"
   ```

2. Check your `.env` file:
   ```ini
   ACTION_LOGGING_ENABLED=true
   ```

3. Make sure it's a typo (should be `true` not `True`)

4. Restart the server to apply `.env` changes

### Too many logs?

Disable at startup:
```ini
ACTION_LOGGING_ENABLED=false
```

Or disable via API:
```bash
curl -X POST http://localhost:8000/api/v1/admin/logging/action \
  -d '{"enabled": false}' \
  -H "Authorization: Bearer <token>"
```

### Want more details?

Set log level to DEBUG (shows more verbose output):
```ini
ACTION_LOG_LEVEL=DEBUG
```

---

**Status**: Action logging system is fully integrated and production-ready!
