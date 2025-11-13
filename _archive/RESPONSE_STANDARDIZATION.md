# API Response Standardization System

## Problem Solved

**Before:**
- API endpoints returned raw responses with inconsistent formats
- CLI expected wrapped responses with `success`/`message` fields
- Error handling was scattered across endpoints (raw HTTPException)
- Logging was inconsistent
- Result: "Failed: None" error in CLI

**After:**
- All API responses use unified `ResponseWrapper` format
- Consistent error logging across the system
- CLI can reliably parse all responses
- Single source of truth for response formatting

---

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Project created successfully",
  "data": {
    "id": "550e8400-...",
    "project_id": "550e8400-...",
    "name": "Test Project",
    "description": "...",
    "phase": "discovery",
    "maturity_level": 0,
    "status": "active",
    "created_at": "2025-11-13T..."
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Validation failed for field 'name'",
  "detail": "Invalid value for 'name': Field cannot be empty",
  "status_code": 400,
  "field": "name"
}
```

---

## Implementation Details

### ResponseWrapper Service
**File:** `backend/app/services/response_service.py`

Provides static methods for wrapping responses:
- `success(data, message)` - Wrap successful response
- `error(error_code, message, status_code, detail)` - Wrap error with logging
- `validation_error(field, reason, value)` - Validation errors
- `not_found(resource_type, resource_id)` - 404 errors
- `unauthorized(message)` - 401 errors
- `forbidden(message)` - 403 errors
- `conflict(message, detail)` - 409 errors
- `internal_error(message, exception)` - 500 errors

### Updated Endpoints
**File:** `backend/app/api/projects.py`

#### `POST /api/v1/projects` (create_project)
- Returns `ResponseWrapper.success()` on success
- Returns `ResponseWrapper.internal_error()` on exception
- Includes both `id` and `project_id` fields for CLI compatibility

#### `GET /api/v1/projects/{project_id}` (get_project)
- Returns `ResponseWrapper.success()` on success
- Returns `ResponseWrapper.validation_error()` for invalid UUID format
- Returns `ResponseWrapper.not_found()` if project doesn't exist
- Returns `ResponseWrapper.forbidden()` for permission denied
- Returns `ResponseWrapper.internal_error()` on unexpected errors

### Updated CLI Handler
**File:** `Socrates.py` (lines 1261-1282)

```python
if result.get("success"):
    project_id = result.get("data", {}).get("project_id")
    # ... success handling
else:
    error_msg = result.get('message') or result.get('detail') or 'Unknown error'
    print(f"✗ Failed: {error_msg}")
```

---

## Benefits

1. **Consistency** - All API responses follow the same format
2. **Logging** - Errors are automatically logged with context
3. **Client-Friendly** - CLI can reliably parse responses
4. **Type-Safe** - Pydantic models for response validation
5. **Maintainability** - Single place to change response format
6. **Error Context** - Errors include code, message, and detail
7. **Debugging** - Exception details logged for troubleshooting

---

## Migration Path

### Phase 1 (Complete)
- ✅ Created `ResponseWrapper` service
- ✅ Updated `create_project` endpoint
- ✅ Updated `get_project` endpoint
- ✅ Updated CLI to parse new format

### Phase 2 (Next)
- Update remaining project endpoints
- Update all other API endpoints (sessions, specifications, etc.)
- Add integration tests for response format
- Update API documentation

### Phase 3
- Create response middleware for auto-wrapping
- Update error handlers to use ResponseWrapper
- Add metrics/telemetry for response times

---

## Testing

Test the new format with:

```bash
# Create project (CLI)
python Socrates.py project create

# Or via curl (with valid token):
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "..."}'

# Get project
curl -X GET http://localhost:8000/api/v1/projects/{project_id} \
  -H "Authorization: Bearer <token>"
```

---

## Error Codes

- `VALIDATION_ERROR` - Invalid input data (400)
- `NOT_FOUND` - Resource not found (404)
- `UNAUTHORIZED` - Not authenticated (401)
- `FORBIDDEN` - Access denied (403)
- `CONFLICT` - Resource already exists or conflict (409)
- `INTERNAL_SERVER_ERROR` - Unexpected error (500)

---

## Next Steps

1. Run tests to verify responses work correctly
2. Update remaining endpoints to use ResponseWrapper
3. Add API documentation with response format examples
4. Monitor CLI for consistent error handling
5. Migrate get_project CLI handler to new format
