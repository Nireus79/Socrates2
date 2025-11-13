# Socrates Backend API Endpoint Map

**Document Generated:** November 13, 2025
**Platform:** FastAPI
**Total API Modules:** 29
**Total Endpoints:** 150+

## Summary Table

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| auth.py | 5 | User registration, login, token management |
| projects.py | 8 | Project CRUD, archival, status tracking |
| sessions.py | 17 | Socratic conversations, Q&A, modes |
| specifications.py | 15 | Spec creation, approval, versioning |
| documents.py | 6 | Document upload, semantic search, RAG |
| questions.py | 6 | Question management |
| conflicts.py | 4 | Conflict detection and resolution |
| code_generation.py | 4 | Code generation from specs |
| collaboration.py | 8 | Project sharing, team invitations |
| teams.py | 5 | Team management |
| analytics.py | 8 | Metrics and domain analytics |
| quality.py | 3 | Quality analysis and recommendations |
| notifications.py | 2+ | Notification preferences, activity feed |
| search.py | 1 | Full-text search |
| insights.py | 1 | Project analysis (gaps, risks) |
| workflows.py | 5 | Multi-domain workflows |
| domains.py | 5 | Knowledge domain access |
| templates.py | 3 | Project templates |
| github_endpoints.py | 3 | GitHub repo import/analysis |
| admin.py | 3+ | Health check, stats, agents |

## Authentication Module (auth.py)
**Prefix:** /api/v1/auth
- POST /register - Register new user
- POST /login - User login (returns JWT)
- POST /logout - Logout endpoint
- GET /me - Get current user info
- POST /refresh - Refresh access token

## Projects Module (projects.py)
**Prefix:** /api/v1/projects
- POST / - Create project
- GET / - List user projects
- GET /{project_id} - Get project
- PUT /{project_id} - Update project
- PATCH /{project_id} - Partial update
- DELETE /{project_id} - Archive project
- POST /{project_id}/restore - Restore archived
- POST /{project_id}/destroy - Permanently delete
- GET /{project_id}/status - Get status

## Sessions Module (sessions.py)
**Prefix:** /api/v1/sessions (+ nested under projects)
- POST / - Start session
- GET / - List sessions
- GET /{session_id} - Get session
- GET /{session_id}/history - Get conversation history
- POST /{session_id}/end - End session
- GET /{session_id}/mode - Get mode
- POST /{session_id}/mode - Set mode
- POST /{session_id}/next-question - Get next question
- POST /{session_id}/answer - Submit answer
- POST /{session_id}/chat - Send chat message
- POST /{session_id}/pause - Pause session
- POST /{session_id}/resume - Resume session
- GET /projects/{project_id}/sessions - List project sessions
- POST /projects/{project_id}/sessions - Create project session
- GET /projects/{project_id}/sessions/{session_id} - Get project session
- PATCH /projects/{project_id}/sessions/{session_id} - Update project session

## Specifications Module (specifications.py)
**Prefix:** /api/v1/specifications (+ nested under projects)
- GET / - List specifications
- POST / - Create specification
- GET /project/{project_id} - List project specs
- GET /{spec_id} - Get spec details
- PUT /{spec_id} - Update spec
- POST /{spec_id}/approve - Approve spec
- POST /{spec_id}/implement - Mark implemented
- GET /{spec_id}/history - Get version history
- DELETE /{spec_id} - Delete spec
- GET /projects/{project_id}/specifications - Nested list
- POST /projects/{project_id}/specifications - Nested create
- GET /projects/{project_id}/specifications/{spec_id} - Nested get
- DELETE /projects/{project_id}/specifications/{spec_id} - Nested delete

## Documents/Knowledge Base Module (documents.py)
**Prefix:** /api/v1/documents
- POST /upload - Upload document
- GET /{project_id} - List documents
- DELETE /{doc_id} - Delete document
- GET /{project_id}/search - Semantic search
- POST /{project_id}/rag/augment - RAG augment
- POST /{project_id}/rag/extract-specs - Extract with RAG

## Questions Module (questions.py)
**Prefix:** /api/v1/questions
- GET / - List questions
- POST / - Create question
- GET /project/{project_id} - List project questions
- GET /{question_id} - Get question
- PUT /{question_id} - Update question
- POST /{question_id}/answer - Answer question
- DELETE /{question_id} - Delete question

## Conflicts Module (conflicts.py)
**Prefix:** /api/v1/conflicts
- GET /project/{project_id} - List conflicts
- GET /{conflict_id} - Get conflict details
- GET /{conflict_id}/options - Get resolution options
- POST /{conflict_id}/resolve - Resolve conflict

## Code Generation Module (code_generation.py)
**Prefix:** /api/v1/code
- POST /generate - Generate code
- GET /{generation_id}/status - Check status
- GET /{generation_id}/download - Download ZIP
- GET /project/{project_id}/generations - List generations

## Collaboration Module (collaboration.py)
**Prefix:** /api/v1/collaboration
- POST /projects/{project_id}/invite - Invite collaborator
- GET /invitations - Get user invitations
- POST /invitations/{invitation_id}/accept - Accept invitation
- POST /invitations/{invitation_id}/decline - Decline invitation
- GET /projects/{project_id}/collaborators - List collaborators
- DELETE /projects/{project_id}/collaborators/{user_id} - Remove collaborator

## Teams Module (teams.py)
**Prefix:** /api/v1/teams
- POST / - Create team
- GET / - List user teams
- GET /{team_id} - Get team
- PUT /{team_id} - Update team
- DELETE /{team_id} - Delete team

## Analytics Module (analytics.py)
**Prefix:** /api/v1/analytics
- GET / - Overall analytics
- GET /domains/{domain_id} - Domain analytics
- GET /domains/{domain_id}/metrics - Domain metrics
- GET /domains/top/{limit} - Top domains
- GET /workflows/{workflow_id} - Workflow analytics
- GET /quality-summary - Quality summary
- POST /export - Export data
- DELETE / - Clear all data

## Quality Control Module (quality.py)
**Prefix:** /quality
- GET /project/{project_id}/metrics - Quality metrics
- GET /project/{project_id}/analysis - Quality analysis
- GET /project/{project_id}/recommendations - Recommendations

## Notifications Module (notifications.py)
**Prefix:** /api/v1/notifications
- GET /preferences - Get preferences
- POST /preferences - Update preferences
- GET /projects/{project_id}/activity - Activity feed

## Search Module (search.py)
**Prefix:** /api/v1/search
- GET / - Full-text search

## Insights Module (insights.py)
**Prefix:** /api/v1/insights
- GET /{project_id} - Get project insights

## Workflows Module (workflows.py)
**Prefix:** /api/v1/workflows
- POST / - Create workflow
- GET / - List workflows
- GET /{workflow_id} - Get workflow
- POST /{workflow_id}/add-domain - Add domain
- DELETE /{workflow_id}/remove-domain - Remove domain

## Domains Module (domains.py)
**Prefix:** /api/v1/domains
- GET / - List domains
- GET /{domain_id} - Get domain
- GET /{domain_id}/questions - Get questions
- GET /{domain_id}/exporters - Get exporters
- GET /{domain_id}/rules - Get conflict rules

## Templates Module (templates.py)
**Prefix:** /api/v1/templates
- GET / - List templates
- GET /{template_id} - Get template
- POST /{template_id}/apply - Apply template

## GitHub Integration Module (github_endpoints.py)
**Prefix:** /api/v1/github
- POST /import - Import repo
- POST /analyze - Analyze repo
- GET /repos - List repos

## Admin Module (admin.py)
**Prefix:** /api/v1/admin
- GET /health - Health check
- GET /stats - System stats
- GET /agents - List agents
- POST /logging/action - Toggle logging

## Authentication Requirements
- JWT Bearer Token required for most endpoints
- Public endpoints: /auth/register, /auth/login, /admin/health
- Admin endpoints: /admin/stats, /admin/agents (require admin role)

## Response Format
Success: {success: true, data: {...}, message: "..."}
Error: {success: false, error: "...", status_code: 400}

## Total Statistics
- API Modules: 29
- Total Endpoints: 150+
- HTTP Methods: GET, POST, PUT, PATCH, DELETE
- API Version: v1
- Pagination: Yes (skip/limit)

