# Socrates API Reference

**API Version:** 1.0
**Base URL:** `https://api.socrates.app/api/v1`
**Format:** JSON
**Authentication:** Bearer JWT Token

---

## Authentication

### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Login User

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "refresh_token_value"
}
```

### Refresh Token

```http
POST /auth/refresh
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "access_token": "new_token...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Projects

### Create Project

```http
POST /projects
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "My Project",
  "description": "Project description",
  "maturity_score": 0.0
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Project",
  "description": "Project description",
  "maturity_score": 0.0,
  "owner_id": "user_id",
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### List Projects

```http
GET /projects?skip=0&limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "project_id_1",
    "name": "Project 1",
    "description": "...",
    "maturity_score": 0.5,
    "owner_id": "user_id",
    "created_at": "2025-11-11T10:00:00Z",
    "updated_at": "2025-11-11T10:00:00Z"
  },
  // ... more projects
]
```

### Get Project

```http
GET /projects/{project_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "project_id",
  "name": "My Project",
  "description": "...",
  "maturity_score": 0.5,
  "owner_id": "user_id",
  "team_members": [
    {
      "user_id": "user_1",
      "email": "user@example.com",
      "role": "owner"
    }
  ],
  "specifications_count": 15,
  "sessions_count": 3,
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### Update Project

```http
PATCH /projects/{project_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "maturity_score": 0.6
}
```

**Response (200 OK):**
```json
{
  "id": "project_id",
  "name": "Updated Name",
  "description": "Updated description",
  "maturity_score": 0.6,
  // ... other fields
}
```

### Delete Project

```http
DELETE /projects/{project_id}
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

---

## Specifications

### Create Specification

```http
POST /projects/{project_id}/specifications
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "category": "Architecture",
  "key": "system_pattern",
  "value": "Microservices",
  "confidence": 0.9,
  "description": "System uses microservices architecture"
}
```

**Response (201 Created):**
```json
{
  "id": "spec_id",
  "project_id": "project_id",
  "category": "Architecture",
  "key": "system_pattern",
  "value": "Microservices",
  "confidence": 0.9,
  "description": "System uses microservices architecture",
  "status": "draft",
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### List Specifications

```http
GET /projects/{project_id}/specifications?category=Architecture&skip=0&limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "spec_id",
    "project_id": "project_id",
    "category": "Architecture",
    "key": "system_pattern",
    "value": "Microservices",
    "confidence": 0.9,
    "status": "draft",
    "created_at": "2025-11-11T10:00:00Z"
  },
  // ... more specs
]
```

### Get Specification

```http
GET /projects/{project_id}/specifications/{spec_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "spec_id",
  "project_id": "project_id",
  "category": "Architecture",
  "key": "system_pattern",
  "value": "Microservices",
  "confidence": 0.9,
  "description": "...",
  "status": "draft",
  "session_id": "session_id",
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### Update Specification

```http
PATCH /projects/{project_id}/specifications/{spec_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "value": "Updated Value",
  "confidence": 0.95,
  "status": "approved"
}
```

**Response (200 OK):**
```json
{
  "id": "spec_id",
  "project_id": "project_id",
  "category": "Architecture",
  "key": "system_pattern",
  "value": "Updated Value",
  "confidence": 0.95,
  "status": "approved",
  // ... other fields
}
```

### Delete Specification

```http
DELETE /projects/{project_id}/specifications/{spec_id}
Authorization: Bearer {access_token}
```

**Response (204 No Content)**

---

## Sessions

### Create Session

```http
POST /projects/{project_id}/sessions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Initial Requirements",
  "description": "First conversation",
  "domains": ["architecture", "programming"],
  "status": "active"
}
```

**Response (201 Created):**
```json
{
  "id": "session_id",
  "project_id": "project_id",
  "name": "Initial Requirements",
  "description": "First conversation",
  "domains": ["architecture", "programming"],
  "status": "active",
  "current_question": {
    "text": "What is your system architecture pattern?",
    "domain": "architecture"
  },
  "progress": 0,
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### List Sessions

```http
GET /projects/{project_id}/sessions?skip=0&limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "session_id",
    "project_id": "project_id",
    "name": "Initial Requirements",
    "domains": ["architecture", "programming"],
    "status": "active",
    "progress": 0,
    "created_at": "2025-11-11T10:00:00Z"
  },
  // ... more sessions
]
```

### Get Session

```http
GET /projects/{project_id}/sessions/{session_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": "session_id",
  "project_id": "project_id",
  "name": "Initial Requirements",
  "description": "First conversation",
  "domains": ["architecture", "programming"],
  "status": "active",
  "current_question": {
    "text": "What is your system architecture pattern?",
    "domain": "architecture",
    "question_number": 1,
    "total_questions": 15
  },
  "progress": 6.67,
  "specifications_created": 0,
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### Submit Answer

```http
POST /projects/{project_id}/sessions/{session_id}/answer
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "answer": "We're using a microservices architecture with Docker containers"
}
```

**Response (200 OK):**
```json
{
  "session_id": "session_id",
  "answer_stored": true,
  "next_question": {
    "text": "How do your microservices communicate?",
    "domain": "architecture",
    "question_number": 2,
    "total_questions": 15
  },
  "progress": 13.33,
  "specifications_created": 1
}
```

### Get Session Messages

```http
GET /projects/{project_id}/sessions/{session_id}/messages
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "msg_id_1",
    "session_id": "session_id",
    "role": "assistant",
    "content": "What is your system architecture pattern?",
    "timestamp": "2025-11-11T10:00:00Z"
  },
  {
    "id": "msg_id_2",
    "session_id": "session_id",
    "role": "user",
    "content": "We're using a microservices architecture...",
    "timestamp": "2025-11-11T10:01:00Z"
  },
  // ... more messages
]
```

---

## Workflows

### Create Workflow

```http
POST /workflows
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Complete Spec",
  "description": "Full specification workflow",
  "domains": ["architecture", "programming", "testing", "security", "devops"],
  "project_id": "project_id",
  "status": "active"
}
```

**Response (201 Created):**
```json
{
  "id": "workflow_id",
  "name": "Complete Spec",
  "description": "Full specification workflow",
  "domains": ["architecture", "programming", "testing", "security", "devops"],
  "project_id": "project_id",
  "status": "active",
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### List Workflows

```http
GET /workflows?skip=0&limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "workflow_id",
    "name": "Complete Spec",
    "domains": ["architecture", "programming", "testing"],
    "status": "active",
    "created_at": "2025-11-11T10:00:00Z"
  },
  // ... more workflows
]
```

### Execute Workflow

```http
POST /workflows/{workflow_id}/execute
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "project_id",
  "input_data": {
    "context": "Building an e-commerce platform"
  }
}
```

**Response (202 Accepted):**
```json
{
  "workflow_id": "workflow_id",
  "execution_id": "exec_id",
  "status": "processing",
  "progress": 0,
  "estimated_completion": "2025-11-11T10:30:00Z"
}
```

### Get Workflow Results

```http
GET /workflows/{workflow_id}/results
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "workflow_id": "workflow_id",
  "execution_id": "exec_id",
  "status": "completed",
  "progress": 100,
  "specifications": [
    {
      "id": "spec_id",
      "category": "Architecture",
      "key": "...",
      "value": "...",
      "confidence": 0.9
    },
    // ... more specs
  ],
  "analysis": {
    "completeness": 0.95,
    "conflicts": [],
    "recommendations": ["..."]
  },
  "completed_at": "2025-11-11T10:30:00Z"
}
```

---

## Questions

### List Questions

```http
GET /questions?domain=architecture&category=design&skip=0&limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "q_id_1",
    "text": "What is your system architecture pattern?",
    "domain": "architecture",
    "category": "design",
    "template_id": "arch_pattern",
    "confidence": 0.9
  },
  // ... more questions
]
```

### Get Domains

```http
GET /domains
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "architecture",
    "name": "Architecture",
    "description": "System design and structure",
    "questions_count": 20,
    "icon": "🏗️"
  },
  {
    "id": "programming",
    "name": "Programming",
    "description": "Implementation details",
    "questions_count": 18,
    "icon": "💻"
  },
  // ... more domains
]
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing authentication token"
}
```

### 403 Forbidden
```json
{
  "detail": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Requests per minute:** 60
- **Requests per hour:** 1,000
- **Requests per day:** 10,000

**Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1731320460
```

---

## SDK & Client Libraries

### Python SDK

```python
from socrates2 import SocratesClient

client = SocratesClient(api_token="your_token")

# Create project
project = client.projects.create(
    name="My Project",
    description="Project description"
)

# Start session
session = client.sessions.create(
    project_id=project.id,
    domains=["architecture", "programming"]
)

# Submit answer
result = client.sessions.submit_answer(
    project_id=project.id,
    session_id=session.id,
    answer="Our architecture uses microservices"
)
```

### JavaScript/TypeScript SDK

```typescript
import { SocratesAPI } from 'socrates2-sdk';

const client = new SocratesAPI({ apiToken: 'your_token' });

// Create project
const project = await client.projects.create({
  name: 'My Project',
  description: 'Project description'
});

// Start session
const session = await client.sessions.create({
  projectId: project.id,
  domains: ['architecture', 'programming']
});

// Submit answer
const result = await client.sessions.submitAnswer({
  projectId: project.id,
  sessionId: session.id,
  answer: 'Our architecture uses microservices'
});
```

---

**[← Back to Documentation Index](../INDEX.md)**
