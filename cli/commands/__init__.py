"""
CLI Command modules.

Each module in this package contains a CommandHandler subclass that implements
a specific command (e.g., /auth, /project, /session, /team, etc.).

Commands are auto-discovered by CommandRegistry and routed by name.

Modules:
- auth: Authentication commands (/auth register, login, logout, whoami)
- projects: Project management (/project create, select, manage, etc.)
- sessions: Session management (/session start, select, end, etc.)
- teams: Team management (/team create, invite, list, etc.)
- collaboration: Team collaboration features (/collaboration status, etc.)
- domain: Domain discovery (/domain list, info, etc.)
- template: Template system (/template list, info, apply, etc.)
- documents: Document management (/document upload, search, etc.)
- specifications: Specification management (/spec list, create, approve, etc.)
- questions: Question management (/question list, answer, etc.)
- workflows: Workflow management (/workflow list, create, etc.)
- code_generation: Code generation (/codegen generate, etc.)
- export: Export functionality (/export format, download, etc.)
- admin: Admin functions (/admin health, stats, etc.)
- analytics: Analytics (/analytics overview, etc.)
- quality: Quality gates (/quality metrics, etc.)
- notifications: Notifications (/notification preferences, etc.)
- conflicts: Conflict resolution (/conflict detect, resolve, etc.)
- search: Search (/search query, etc.)
- insights: Insights (/insights project, etc.)
- github: GitHub integration (/github import, analyze, etc.)
- config: Configuration (/config set, get, reset, etc.)
- system: System commands (help, clear, exit, etc.)
"""

# Commands are auto-discovered by registry, no need to import here
