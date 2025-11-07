# Socrates CLI User Guide

A powerful command-line interface for the Socrates specification gathering system, inspired by Claude Code.

## Quick Start

### 1. Installation

```bash
# Install CLI dependencies
pip install -r cli-requirements.txt

# Make Socrates.py executable (optional, Linux/Mac)
chmod +x Socrates.py
```

### 2. Start Backend Server

```bash
# In one terminal, start the backend
cd backend
uvicorn app.main:app --reload
```

### 3. Launch CLI

```bash
# In another terminal, run the CLI
python Socrates.py

# Or with custom API URL
python Socrates.py --api-url http://localhost:8000

# Enable debug mode
python Socrates.py --debug
```

## Features

### 🎨 Beautiful Terminal UI
- Color-coded output for better readability
- Tables for listing projects and sessions
- Panels for formatted text
- Progress spinners for API calls
- Markdown rendering support

### 💬 Two Chat Modes

#### Socratic Mode (🤔)
The AI asks thoughtful questions to help you think deeply about requirements:
- Structured questioning process
- Extracts specifications automatically
- Guides you through requirement gathering
- Requires an active session

#### Direct Mode (💬)
Chat directly with the AI for:
- Quick questions
- Clarifications
- General discussion
- No session required

Toggle between modes with `/mode`

### 📝 Command History
- All commands and inputs are saved
- Press Up/Down arrows to navigate history
- Auto-suggestions based on history
- History stored in `~/.socrates/history.txt`

### 🔐 Session Management
- Login once, stay authenticated
- Token stored securely in `~/.socrates/config.json`
- Auto-reconnect on restart

## Available Commands

### Authentication

```bash
/register               # Create new account
/login                  # Login to existing account
/logout                 # Logout and clear credentials
/whoami                 # Show current user and context
```

### Project Management

```bash
/projects               # List all your projects
/project create         # Create new project (interactive)
/project select <id>    # Select project to work with
/project info           # Show current project details
/project delete <id>    # Delete project (confirmation required)
```

### Session Management

```bash
/session start          # Start Socratic questioning session
/session end            # End current session (shows stats)
/sessions               # List all sessions for current project
/history                # Show conversation history
```

### Chat Modes

```bash
/mode                   # Toggle between socratic/direct modes
/mode socratic          # Switch to Socratic questioning
/mode direct            # Switch to direct chat
```

### System Commands

```bash
/help                   # Show help message
/clear                  # Clear screen
/debug                  # Toggle debug mode
/exit                   # Exit CLI
/quit                   # Same as /exit
```

## Typical Workflow

### Workflow 1: Socratic Specification Gathering

```bash
# 1. Login
/login
Email: you@example.com
Password: ********

# 2. Create a project
/project create
Project name: Task Management API
Description: A REST API for managing tasks

# 3. Start a Socratic session
/session start

# 4. Answer questions
> I want to build a task management system for teams

[Socrates asks follow-up questions]

> Yes, we need authentication and team collaboration

[Continue conversation until complete]

# 5. End session
/session end
```

### Workflow 2: Direct Chat Mode

```bash
# 1. Login and select project
/login
/project select abc123

# 2. Switch to direct mode
/mode direct

# 3. Chat directly
> What are the best practices for REST API authentication?

> How should I structure my database for this project?

> Can you help me write a specification for the user login endpoint?
```

### Workflow 3: Mixed Mode Usage

```bash
# Start with Socratic questioning
/mode socratic
/session start
> [Answer questions to gather requirements]

# Switch to direct for clarification
/mode direct
> Can you explain more about that last specification?

# Back to Socratic
/mode socratic
> [Continue with structured questions]

# End session
/session end
```

## Configuration

Configuration is stored in `~/.socrates/`:

```
~/.socrates/
├── config.json         # User settings and auth token
└── history.txt         # Command history
```

### config.json Format

```json
{
  "access_token": "eyJ...",
  "user_email": "you@example.com"
}
```

### Environment Variables

```bash
# Set custom API URL
export SOCRATES_API_URL=http://localhost:8000

# Then run CLI
python Socrates.py
```

## Prompt Indicators

The CLI prompt shows your current context:

```bash
# Not logged in
socrates 🤔 >

# Logged in, no project
socrates 💬 >

# Project selected (direct mode)
MyProject 💬 >

# Project selected + active session (socratic mode)
MyProject session 🤔 >
```

**Indicators:**
- 🤔 = Socratic mode (thoughtful questioning)
- 💬 = Direct mode (direct chat)
- `session` = Active Socratic session

## Keyboard Shortcuts

- `Ctrl+C` - Cancel current input (shows reminder to use /exit)
- `Ctrl+D` - Exit CLI
- `Up/Down` - Navigate command history
- `Tab` - Auto-complete commands (when available)

## Tips & Tricks

### 1. Quick Project Switching
```bash
# List projects and note IDs
/projects

# Quick switch
/project select abc123
```

### 2. Review Before Ending Session
```bash
# Check what you've discussed
/history

# Then end if satisfied
/session end
```

### 3. Use Direct Mode for Exploration
```bash
/mode direct
> What features should I consider for this type of application?
> What are common security concerns?
> How do other systems handle this?
```

### 4. Combine Modes Effectively
- Start with **Socratic mode** for structured requirement gathering
- Switch to **direct mode** when you need clarification
- Return to **Socratic mode** to continue systematic questioning

### 5. Save Token for Quick Access
Once logged in, your token is saved. Next time just run:
```bash
python Socrates.py
# Already logged in!
```

## Troubleshooting

### Connection Refused
```
Error: Cannot connect to Socrates backend
```

**Solution:** Make sure the backend is running:
```bash
cd backend
uvicorn app.main:app --reload
```

### Module Not Found
```
Error: Missing required package: rich
```

**Solution:** Install CLI dependencies:
```bash
pip install -r cli-requirements.txt
```

### Unauthorized / Token Expired
```
401 Unauthorized
```

**Solution:** Login again:
```bash
/logout
/login
```

### Cannot Start Session
```
No project selected
```

**Solution:** Create or select a project first:
```bash
/project create
# OR
/project select <id>
```

## Advanced Usage

### Custom API URL

```bash
# Development server
python Socrates.py --api-url http://localhost:8000

# Staging server
python Socrates.py --api-url https://staging.socrates.example.com

# Production server
python Socrates.py --api-url https://api.socrates.example.com
```

### Debug Mode

```bash
# Start with debug enabled
python Socrates.py --debug

# Or toggle during session
/debug
```

Debug mode shows:
- Full stack traces for errors
- API request/response details
- Detailed error messages

### Scripting with Socrates CLI

While the CLI is primarily interactive, you can pipe commands:

```bash
# Note: This is a basic example, full scripting support may vary
echo -e "/login\nuser@example.com\npassword\n/projects" | python Socrates.py
```

## Examples

### Example 1: Creating Your First Project

```
$ python Socrates.py

╔═══════════════════════════════════════════════════════════════╗
║                    SOCRATES CLI v1.0                          ║
║          AI-Powered Specification Gathering                   ║
╚═══════════════════════════════════════════════════════════════╝

Please /login or /register to get started

socrates 🤔 > /register

Register New Account

Email: alice@example.com
Full name: Alice Developer
Password: ********
Confirm password: ********

✓ Account created successfully!
User ID: 550e8400-e29b-41d4-a716-446655440000

Please login with /login

socrates 🤔 > /login

Login

Email: alice@example.com
Password: ********

✓ Logged in successfully as alice@example.com

socrates 🤔 > /project create

Create New Project

Project name: E-commerce Platform
Description (optional): A full-featured online store with cart, checkout, and inventory

✓ Project created: 7c9e6679-7425-40de-944b-e6f3a3a8e3a0
Selected project: E-commerce Platform

E-commerce Platform 🤔 > /session start

✓ Session started: b3f4a3c2-1234-5678-9012-a1b2c3d4e5f6

Ready to begin Socratic questioning!
Just type your thoughts and press Enter to continue the conversation.

Socrates:
╔════════════════════════════════════════════════════════════╗
║ Let's start by understanding the core of your e-commerce  ║
║ platform. What is the primary problem you're trying to    ║
║ solve for your users?                                      ║
╚════════════════════════════════════════════════════════════╝

E-commerce Platform session 🤔 > I want to help small businesses sell online without technical knowledge

[...conversation continues...]
```

### Example 2: Using Direct Mode

```
E-commerce Platform 💬 > /mode direct

✓ Switched to direct mode 💬
Direct mode: Direct conversation with AI assistant

E-commerce Platform 💬 > What are the essential features for a minimal viable e-commerce platform?

Socrates:
╔════════════════════════════════════════════════════════════╗
║ For a minimal viable e-commerce platform, focus on these  ║
║ essential features:                                        ║
║                                                            ║
║ 1. Product Management                                      ║
║    - Add/edit/delete products                             ║
║    - Product images and descriptions                       ║
║    - Inventory tracking                                    ║
║                                                            ║
║ 2. Shopping Cart                                           ║
║    - Add to cart                                          ║
║    - Update quantities                                     ║
║    - Cart persistence                                      ║
║                                                            ║
║ 3. Checkout Process                                        ║
║    - Shipping information                                  ║
║    - Payment integration (Stripe/PayPal)                   ║
║    - Order confirmation                                    ║
║                                                            ║
║ [... more details ...]                                     ║
╚════════════════════════════════════════════════════════════╝

E-commerce Platform 💬 > Great! Can you help me spec out the product management API?

[...continues...]
```

## Comparison: Socratic vs Direct Mode

| Feature | Socratic Mode 🤔 | Direct Mode 💬 |
|---------|------------------|----------------|
| **Style** | Asks questions | Answers questions |
| **Goal** | Extract requirements | Provide information |
| **Session** | Required | Not required |
| **Structure** | Guided conversation | Freeform chat |
| **Best For** | Initial requirements | Clarifications, details |
| **Specs** | Automatic extraction | On-demand extraction |

## FAQ

**Q: Can I use both modes in the same project?**
A: Yes! You can switch between modes anytime with `/mode`. This is actually recommended - use Socratic mode to gather requirements, then direct mode for clarifications.

**Q: Do I lose my progress if I close the CLI?**
A: No, all your projects, sessions, and specifications are stored in the backend database. Just login again to continue.

**Q: Can multiple users work on the same project?**
A: Currently, projects are private to each user. Team collaboration features are coming in Phase 8 (teams, project sharing, permissions).

**Q: How do I export my specifications?**
A: Export features are available through the API (Phase 9). Future CLI versions will include `/export` commands.

**Q: What happens if I end a session early?**
A: You can always start a new session and continue. Previous sessions and their extracted specifications are preserved.

**Q: Can I edit specifications after they're extracted?**
A: Not directly in the CLI yet. Use the API endpoints or wait for Phase 9 features.

## Getting Help

- Type `/help` anytime in the CLI
- Check API documentation at `http://localhost:8000/docs`
- Report issues at: `https://github.com/yourusername/Socrates2/issues`

## Next Steps

After gathering specifications with Socrates CLI:

1. **Review Specifications** - Use the API or Phase 9 export features
2. **Generate Code** - Use Phase 4 code generation endpoints
3. **Quality Checks** - Run Phase 5 quality control
4. **Iterate** - Start new sessions to refine specs

---

**Happy specification gathering! 🚀**
