# Phase 4: API Integration Guide

**Version:** 1.0
**Date:** November 11, 2025
**Status:** In Progress - Core endpoints implemented

---

## Overview

Phase 4 integrates the repository layer (Phase 3) with FastAPI endpoints to create a complete REST API. This guide documents the API structure, endpoints, and best practices for building additional endpoints.

---

## Architecture

### API Layer → Repository Layer → Database

```
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI HTTP Layer (app/api/*.py)                              │
│ - Request validation (Pydantic)                                │
│ - Permission checks                                             │
│ - Response formatting                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│ Repository Service Container (app/repositories/repository_service.py) │
│ - Unified data access                                          │
│ - Transaction management                                       │
│ - Multi-database coordination                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│ Specialized Repositories (app/repositories/*.py)               │
│ - Domain-specific CRUD operations                             │
│ - Business logic methods                                       │
│ - Query optimization                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│ SQLAlchemy ORM Models (app/models/*.py)                        │
│ - Database schema mapping                                      │
│ - Relationships and constraints                                │
│ - Computed properties                                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│ PostgreSQL Databases                                            │
│ - socrates_auth (6 tables, ~100KB-1MB)                        │
│ - socrates_specs (25 tables, ~1MB-1GB)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Injection Pattern

All API endpoints use FastAPI's `Depends()` to inject the repository service:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db_auth, get_db_specs
from app.repositories import RepositoryService

def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Dependency function to inject repository service into endpoints."""
    return RepositoryService(auth_session, specs_session)

@router.get("/api/v1/projects")
def list_projects(
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
):
    # Use service.projects, service.users, etc.
    projects = service.projects.get_user_projects(current_user.id)
    return projects
```

---

## Implemented Endpoints

### Authentication (`app/api/auth.py`)

#### 1. Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "name": "John",
    "surname": "Doe",
    "username": "johndoe",
    "password": "SecurePass123!",
    "email": "john@example.com"
}

Response 201:
{
    "message": "User registered successfully",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "name": "John",
    "surname": "Doe",
    "email": "john@example.com"
}
```

**Repository Methods Used:**
- `service.users.user_exists_by_username()` - Check duplicate
- `service.users.user_exists_by_email()` - Check duplicate
- `service.users.create_user()` - Create new user
- `service.commit_all()` - Persist changes

#### 2. Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecurePass123!

Response 200:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "8Xk5...random...token...",
    "token_type": "bearer",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "name": "John",
    "surname": "Doe"
}
```

**Repository Methods Used:**
- `service.users.get_by_username()` - Find user
- `service.refresh_tokens.create()` - Store refresh token
- `service.commit_all()` - Persist changes

#### 3. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "8Xk5...random...token..."
}

Response 200:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new...refresh...token...",
    "token_type": "bearer",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "name": "John",
    "surname": "Doe"
}
```

**Repository Methods Used:**
- `validate_refresh_token()` - Validate token
- `service.refresh_tokens.create()` - Store new token
- `service.commit_all()` - Persist changes

#### 4. Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>

Response 200:
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "name": "John",
    "surname": "Doe",
    "email": "john@example.com",
    "is_active": true,
    "is_verified": false,
    "status": "active",
    "role": "user",
    "created_at": "2025-11-06T10:30:00"
}
```

**Note:** Uses `get_current_active_user` dependency (JWT validation)

#### 5. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>

Response 200:
{
    "message": "Logged out successfully"
}
```

**Note:** Client deletes token (JWT is stateless). Could implement token blacklist in future.

---

### Projects (`app/api/projects.py`)

#### 1. Create Project
```http
POST /api/v1/projects
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "My Web App",
    "description": "A FastAPI web application"
}

Response 201:
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Web App",
    "description": "A FastAPI web application",
    "phase": "discovery",
    "maturity_level": 0,
    "status": "active",
    "created_at": "2025-11-11T12:00:00"
}
```

**Repository Methods Used:**
- `service.projects.create_project()` - Create new project
- `service.commit_all()` - Persist changes

#### 2. List User's Projects
```http
GET /api/v1/projects?skip=0&limit=10
Authorization: Bearer <access_token>

Response 200:
{
    "projects": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "My Web App",
            "phase": "discovery",
            "maturity_level": 45,
            "status": "active",
            ...
        }
    ],
    "total": 5,
    "skip": 0,
    "limit": 10
}
```

**Repository Methods Used:**
- `service.projects.get_user_projects()` - Fetch paginated projects
- `service.projects.count_user_projects()` - Get total count

#### 3. Get Project Details
```http
GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>

Response 200:
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Web App",
    "description": "A FastAPI web application",
    "phase": "discovery",
    "maturity_level": 45,
    "status": "active",
    "created_at": "2025-11-11T12:00:00"
}
```

**Repository Methods Used:**
- `service.projects.get_by_id()` - Fetch project by UUID

**Permission Check:** Endpoint verifies user owns project

#### 4. Update Project
```http
PUT /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Updated Project Name",
    "description": "Updated description",
    "phase": "specification",
    "maturity_level": 50
}

Response 200:
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    ...
}
```

**Repository Methods Used:**
- `service.projects.get_by_id()` - Verify ownership
- `service.projects.update()` - Update fields
- `service.projects.update_project_phase()` - Update phase
- `service.projects.update_project_status()` - Update status
- `service.projects.update_maturity_level()` - Update maturity
- `service.commit_all()` - Persist changes

#### 5. Delete (Archive) Project
```http
DELETE /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>

Response 204: No Content
```

**Repository Methods Used:**
- `service.projects.get_by_id()` - Verify project exists
- `service.projects.archive_project()` - Archive project
- `service.commit_all()` - Persist changes

#### 6. Get Project Status
```http
GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/status
Authorization: Bearer <access_token>

Response 200:
{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "phase": "discovery",
    "maturity_level": 45
}
```

**Repository Methods Used:**
- `service.projects.get_by_id()` - Fetch project

---

## Best Practices for New Endpoints

### 1. Always Use Dependency Injection

```python
@router.post("/api/v1/something")
def create_something(
    request: CreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
):
    # Never import or use database directly
    # Always use service.repositories
    ...
```

### 2. Validate Permissions Early

```python
def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
):
    resource = service.resources.get_by_id(UUID(resource_id))

    if not resource:
        raise HTTPException(404, "Not found")

    # Check ownership/permissions BEFORE processing
    if resource.owner_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    return resource
```

### 3. Use Try/Except for Transaction Safety

```python
@router.post("")
def create_something(
    request: CreateRequest,
    service: RepositoryService = Depends(get_repository_service)
):
    try:
        result = service.something.create(...)
        service.commit_all()  # Only commit on success
        return result

    except HTTPException:
        service.rollback_all()
        raise  # Re-raise HTTP errors

    except Exception as e:
        service.rollback_all()
        raise HTTPException(500, "Server error") from e
```

### 4. Use Response Models (Pydantic)

```python
from pydantic import BaseModel

class ResourceResponse(BaseModel):
    id: str
    name: str
    created_at: str

    class Config:
        from_attributes = True  # SQLAlchemy model compatibility

@router.get("/{id}", response_model=ResourceResponse)
def get_resource(...) -> ResourceResponse:
    # Return model instance, Pydantic handles serialization
    return resource
```

### 5. Validate UUIDs Properly

```python
from uuid import UUID

@router.get("/{resource_id}")
def get_resource(resource_id: str, ...):
    try:
        resource_uuid = UUID(resource_id)
    except ValueError:
        raise HTTPException(400, f"Invalid UUID format: {resource_id}")

    resource = service.resources.get_by_id(resource_uuid)
```

### 6. Use Proper HTTP Status Codes

```python
from fastapi import status

# Create
@router.post("", status_code=status.HTTP_201_CREATED)
def create(...) -> Response:

# Delete
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete(...) -> None:

# Get
@router.get("")
def list(...) -> Response:

# Update
@router.put("")
def update(...) -> Response:
```

### 7. Pagination for List Endpoints

```python
from fastapi import Query

@router.get("")
def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RepositoryService = Depends(get_repository_service)
):
    items = service.resources.list(skip=skip, limit=limit)
    total = service.resources.count()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

---

## Repository Methods Reference

### User Repository
```python
service.users.create_user()
service.users.get_by_email()
service.users.get_by_username()
service.users.get_active_users()
service.users.user_exists_by_email()
service.users.user_exists_by_username()
service.users.verify_user()
service.users.deactivate_user()
service.users.activate_user()
service.users.update_password()
```

### Project Repository
```python
service.projects.create_project()
service.projects.get_by_id()
service.projects.get_user_projects()
service.projects.get_user_active_projects()
service.projects.get_active_projects()
service.projects.update()
service.projects.update_project_phase()
service.projects.update_project_status()
service.projects.update_maturity_level()
service.projects.archive_project()
service.projects.count_user_projects()
```

### Session Repository
```python
service.sessions.create_session()
service.sessions.get_project_sessions()
service.sessions.get_user_sessions()
service.sessions.get_active_sessions()
service.sessions.increment_message_count()
service.sessions.close_session()
service.sessions.count_project_sessions()
```

### Question Repository
```python
service.questions.create_question()
service.questions.get_project_questions()
service.questions.get_pending_questions()
service.questions.get_answered_questions()
service.questions.answer_question()
service.questions.skip_question()
service.questions.resolve_question()
service.questions.count_pending_questions()
```

### Team Repository
```python
service.teams.create_team()
service.teams.get_user_teams()
service.teams.get_active_teams()
service.teams.increment_member_count()
service.teams.decrement_member_count()
service.teams.archive_team()

service.team_members.add_member()
service.team_members.get_team_members()
service.team_members.get_user_teams_as_member()
service.team_members.update_member_role()
service.team_members.remove_member()
service.team_members.is_team_member()
service.team_members.get_member_role()
```

---

## Common Patterns

### Create and Return
```python
@router.post("", response_model=ResourceResponse, status_code=201)
def create_resource(request: CreateRequest, service: RepositoryService = ...):
    resource = service.resources.create(
        field1=request.field1,
        field2=request.field2
    )
    service.commit_all()
    return ResourceResponse.from_orm(resource)
```

### Update with Partial Fields
```python
@router.put("/{id}", response_model=ResourceResponse)
def update_resource(id: str, request: UpdateRequest, service: RepositoryService = ...):
    resource = service.resources.get_by_id(UUID(id))

    if request.field1 is not None:
        resource = service.resources.update(UUID(id), field1=request.field1)
    if request.field2 is not None:
        resource = service.resources.update(UUID(id), field2=request.field2)

    service.commit_all()
    return ResourceResponse.from_orm(resource)
```

### List with Filtering
```python
@router.get("")
def list_resources(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    service: RepositoryService = ...
):
    if status:
        items = service.resources.list_by_field("status", status, skip=skip, limit=limit)
    else:
        items = service.resources.list(skip=skip, limit=limit)

    return {"items": items}
```

---

## Testing API Endpoints

### Using curl
```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "surname": "Doe",
    "username": "johndoe",
    "password": "SecurePass123!",
    "email": "john@example.com"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=SecurePass123!"

# List projects
curl -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <access_token>"

# Create project
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Test project"
  }'
```

### Using Python Requests
```python
import requests

BASE_URL = "http://localhost:8000"
token = None

# Register
response = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
    "name": "John",
    "surname": "Doe",
    "username": "johndoe",
    "password": "SecurePass123!",
    "email": "john@example.com"
})
user_id = response.json()["user_id"]

# Login
response = requests.post(f"{BASE_URL}/api/v1/auth/login", data={
    "username": "johndoe",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]

# List projects
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
projects = response.json()["projects"]

# Create project
response = requests.post(f"{BASE_URL}/api/v1/projects", headers=headers, json={
    "name": "My Project",
    "description": "Test project"
})
project = response.json()
```

---

## Error Handling

### Standard HTTP Status Codes
- **400 Bad Request** - Invalid input (validation error, malformed UUID)
- **401 Unauthorized** - Missing/invalid authentication
- **403 Forbidden** - Authenticated but no permission
- **404 Not Found** - Resource doesn't exist
- **409 Conflict** - Duplicate resource (email/username)
- **500 Internal Server Error** - Unexpected error

### Example Error Responses
```python
# 400 Bad Request
HTTPException(
    status_code=400,
    detail="Username must be 3-50 characters"
)

# 404 Not Found
HTTPException(
    status_code=404,
    detail="Project not found: 550e8400-..."
)

# 403 Forbidden
HTTPException(
    status_code=403,
    detail="Permission denied: only project owner can update"
)

# 409 Conflict
HTTPException(
    status_code=409,
    detail="Email already registered"
)
```

---

## Next Steps

### Phase 4 Continuation
1. **Questions Endpoints** - CRUD for questions with status tracking
2. **Specifications Endpoints** - CRUD for specifications with versioning
3. **Team Endpoints** - Team management and membership
4. **Sessions Endpoints** - Session management and message tracking
5. **Conversation Endpoints** - Conversation history tracking

### Phase 5 (Testing & Integration)
1. **Unit Tests** - Test individual repository methods
2. **Integration Tests** - Test API endpoints end-to-end
3. **Authentication Tests** - JWT token validation
4. **Permission Tests** - Verify permission checks
5. **Error Handling Tests** - Test all error conditions

---

## Files Modified/Created

**Modified:**
- `app/api/auth.py` - Refactored to use RepositoryService
- `app/api/projects.py` - Refactored to use RepositoryService

**Documentation:**
- `PHASE_4_API_INTEGRATION_GUIDE.md` - This file

---

**Last Updated:** November 11, 2025
**Status:** Core endpoints complete, additional endpoints in progress

