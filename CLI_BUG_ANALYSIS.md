# Socrates CLI Bug Analysis & Fixes

## Issue Reported

User tried to create a project and got:

```bash
[dim]🤔[/dim] > /project create

Create New Project

Project name: Test1
Description (optional) ():
✗ Failed: Not Found
```

## Root Cause Analysis

### Bug #1: HTTP Error Status Not Checked ⚠️ **CRITICAL**

**Location:** `Socrates.py:98-112` (_request method)

**Problem:**
```python
def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling"""
    url = f"{self.base_url}{endpoint}"
    kwargs.setdefault('headers', self._headers())

    try:
        response = requests.request(method, url, **kwargs)
        return response  # ← Returns response regardless of status code!
    except requests.exceptions.ConnectionError:
        ...
```

When a request gets a 404 Not Found (or any HTTP error), the response is still returned normally. Then `.json()` is called on it, which parses the error message:

```json
{
  "detail": "Not Found"
}
```

Then the CLI code does:
```python
result = self.api.create_project(name, description)  # Returns {"detail": "Not Found"}
if result.get("success"):  # False, because no "success" field
    ...
else:
    print(f"✗ Failed: {result.get('message')}")  # message is None!
```

Since `result.get('message')` is None (FastAPI uses '

detail', not 'message'), it prints nothing or tries other fields.

**Impact:** All API calls silently fail with HTTP errors, showing confusing messages to users.

---

### Bug #2: Inconsistent Error Message Field Names

**Location:** Multiple places in `Socrates.py`

**Problem:**
FastAPI returns errors in `detail` field, but CLI checks for `message` field:

```python
# CLI expects:
result.get('message')

# FastAPI returns:
{"detail": "Not Found"}
```

**Affected code:**
- Line 357: `result.get('message', 'Unknown error')`
- Line 477: `result.get('message')`
- Line 496: Used in multiple error handlers

---

### Bug #3: Missing HTTP Status Codes in Error Messages

**Problem:** When API returns 404, 401, 403, etc., the user just sees "Failed: Not Found" without context about why (authentication, authorization, not found, etc.).

---

## The Fix

### Fix #1: Check HTTP Status Codes

```python
def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling"""
    url = f"{self.base_url}{endpoint}"
    kwargs.setdefault('headers', self._headers())

    try:
        response = requests.request(method, url, **kwargs)

        # NEW: Check HTTP status and raise exception for errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail') or error_data.get('message', 'Unknown error')
            except:
                error_msg = response.text or f"HTTP {response.status_code}"

            # Provide helpful error messages
            if response.status_code == 401:
                self.console.print("[red]✗ Unauthorized: Please login first[/red]")
            elif response.status_code == 403:
                self.console.print("[red]✗ Forbidden: You don't have permission[/red]")
            elif response.status_code == 404:
                self.console.print(f"[red]✗ Not Found: {error_msg}[/red]")
                self.console.print("[yellow]  Check that the backend is running and endpoints are correct[/yellow]")
            else:
                self.console.print(f"[red]✗ HTTP {response.status_code}: {error_msg}[/red]")

            raise HTTPException(response.status_code, error_msg)

        return response

    except requests.exceptions.ConnectionError:
        self.console.print("[red]Error: Cannot connect to Socrates backend[/red]")
        self.console.print(f"[yellow]Make sure the server is running at {self.base_url}[/yellow]")
        raise
    except HTTPException:
        raise  # Re-raise our HTTP exceptions
    except Exception as e:
        self.console.print(f"[red]Request error: {e}[/red]")
        raise


class HTTPException(Exception):
    """Custom HTTP exception for better error handling"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")
```

### Fix #2: Update Error Message Extraction

All error handlers should check both `detail` and `message`:

```python
# Instead of:
result.get('message', 'Unknown error')

# Use:
result.get('detail') or result.get('message', 'Unknown error')
```

**Locations to update:**
- Line 357 (cmd_register)
- Line 477 (cmd_project create)
- Line 496 (cmd_project select)
- All other error handlers

### Fix #3: Better Error Handling in Commands

```python
def cmd_project(self, args: List[str]):
    ...
    if subcommand == "create":
        ...
        try:
            result = self.api.create_project(name, description)

            # Backend returns {"success": true, "project_id": "...", "project": {...}}
            if result.get("success"):
                project_id = result.get("project_id")
                self.console.print(f"[green]✓ Project created: {project_id}[/green]")
                ...
            else:
                # If success=false, there should be an error field
                error = result.get('detail') or result.get('message') or result.get('error', 'Unknown error')
                self.console.print(f"[red]✗ Failed: {error}[/red]")

        except HTTPException as e:
            # HTTP errors are already printed by _request
            pass
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if self.debug:
                import traceback
                traceback.print_exc()
```

---

## Why "Not Found" Occurred

Possible reasons:

1. **Backend Not Running**
   - Solution: Start backend with `cd backend && uvicorn app.main:app --reload`

2. **Wrong API URL**
   - Check `SOCRATES_API_URL` environment variable
   - Default is `http://localhost:8000`

3. **Not Authenticated**
   - 404 might actually be 401/403 but error handling is broken
   - Solution: Login first with `/login`

4. **Router Not Properly Mounted**
   - Check `backend/app/main.py` includes `app.include_router(projects.router)`
   - Check `backend/app/api/projects.py` has `router = APIRouter(prefix="/api/v1/projects")`

5. **Database Not Initialized**
   - Run migrations: `cd backend && alembic upgrade head`

---

## Testing the Fix

After applying fixes, test this workflow:

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. In another terminal, run CLI
python Socrates.py

# 3. Test registration
/register
Email: test@example.com
Password: password123

# Should see: ✓ Account created successfully!

# 4. Test login
/login
Email: test@example.com
Password: password123

# Should see: ✓ Logged in successfully as test@example.com

# 5. Test project creation
/project create
Project name: Test Project
Description: Test

# Should see: ✓ Project created: abc-123-...
```

---

## Comprehensive Test

Run the new workflow tester:

```bash
python test_cli_workflow.py --verbose
```

This will:
1. Test registration
2. Test login
3. Test project creation
4. Test listing projects
5. Identify exact issues with detailed error messages
6. Show HTTP status codes and responses

---

## Files to Update

1. **Socrates.py**
   - Add HTTPException class
   - Update _request() to check status codes
   - Update all error handlers to use `detail` or `message`
   - Add better error messages with context

2. **Test Files**
   - ✅ Created: `test_cli_workflow.py` - Comprehensive workflow tests
   - ✅ Created: `run_all_tests.py` - Master test runner

---

## Summary

**Root Cause:** HTTP errors (404, 401, 403) are not being detected, so error responses are parsed as success responses.

**Solution:**
1. Check `response.status_code` in `_request()`
2. Raise exceptions for HTTP errors
3. Show helpful error messages with status codes
4. Handle both `detail` and `message` error fields

**Impact:** After fix, users will see:
- Clear error messages (not just "Not Found")
- HTTP status codes (404, 401, etc.)
- Helpful suggestions (e.g., "Please login first")
- Better debugging information

**Priority:** CRITICAL - Affects all API calls
