"""
Shared constants used across all CLI commands.

Centralizes domain definitions, roles, statuses, and common messages.
"""

# ===== DOMAINS =====
DOMAINS = {
    "programming": {
        "name": "Programming",
        "description": "Code generation, technical specifications, software development",
        "icon": "💻",
        "color": "cyan"
    },
    "business": {
        "name": "Business",
        "description": "Business plans, strategies, business requirements, marketing",
        "icon": "📊",
        "color": "magenta"
    },
    "design": {
        "name": "Design",
        "description": "Product design, UX specifications, design guidelines",
        "icon": "🎨",
        "color": "yellow"
    },
    "research": {
        "name": "Research",
        "description": "Research analysis, competitive analysis, market research",
        "icon": "🔬",
        "color": "blue"
    },
    "marketing": {
        "name": "Marketing",
        "description": "Marketing campaigns, positioning, brand strategy",
        "icon": "📢",
        "color": "green"
    },
}

# ===== ROLES =====
ROLES = {
    "owner": {
        "name": "Owner",
        "description": "Full control, can invite/remove members, manage project",
        "permissions": ["edit", "create", "approve", "invite", "remove", "delete"]
    },
    "contributor": {
        "name": "Contributor",
        "description": "Can edit specs, create sessions, answer questions",
        "permissions": ["edit", "create", "answer"]
    },
    "reviewer": {
        "name": "Reviewer",
        "description": "Can review and comment, but cannot edit content",
        "permissions": ["review", "comment"]
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access to project content",
        "permissions": ["view"]
    },
}

# ===== PROJECT STATUSES =====
PROJECT_STATUSES = {
    "active": {
        "name": "Active",
        "icon": "🟢",
        "description": "Project is active and can be worked on"
    },
    "archived": {
        "name": "Archived",
        "icon": "📦",
        "description": "Project is archived, can be restored or permanently deleted"
    },
    "completed": {
        "name": "Completed",
        "icon": "✅",
        "description": "Project is completed"
    },
    "paused": {
        "name": "Paused",
        "icon": "⏸️",
        "description": "Project is temporarily paused"
    },
}

# ===== SESSION MODES =====
SESSION_MODES = {
    "socratic": {
        "name": "Socratic",
        "description": "AI asks questions to guide thinking",
        "color": "cyan"
    },
    "direct": {
        "name": "Direct",
        "description": "Direct conversation with AI assistant",
        "color": "green"
    },
}

# ===== COMMON MESSAGES =====
MESSAGE_SUCCESS = "✓"
MESSAGE_ERROR = "✗"
MESSAGE_WARNING = "⚠"
MESSAGE_INFO = "ℹ"

# ===== ERROR MESSAGES =====
ERROR_NOT_AUTHENTICATED = "Not authenticated. Use /login or /register first."
ERROR_NO_PROJECT = "No project selected. Use /project select first."
ERROR_NO_TEAM = "No team context. This command requires team context."
ERROR_UNKNOWN_COMMAND = "Unknown command. Use /help for available commands."
ERROR_INVALID_ARGS = "Invalid arguments."
ERROR_API_ERROR = "API error: {message}"

# ===== SUCCESS MESSAGES =====
SUCCESS_AUTHENTICATED = "Successfully authenticated!"
SUCCESS_PROJECT_CREATED = "Project created successfully: {name}"
SUCCESS_PROJECT_SELECTED = "Project selected: {name}"
SUCCESS_TEAM_CREATED = "Team created successfully: {name}"
SUCCESS_SESSION_STARTED = "Session started successfully"

# ===== HELP MESSAGES =====
HELP_BACK_COMMAND = "Type '[yellow]/back[/yellow]' to go back"
HELP_QUIT_COMMAND = "Type '[yellow]/exit[/yellow]' or '[yellow]/quit[/yellow]' to exit"
