# Socrates CLI

A beautiful, Claude Code-inspired command-line interface for the Socrates specification gathering system.

![Socrates CLI](https://img.shields.io/badge/Socrates-CLI-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

✨ **Two Chat Modes**
- 🤔 **Socratic Mode**: Thoughtful questioning to extract requirements
- 💬 **Direct Mode**: Direct conversation for quick questions

🎨 **Beautiful Terminal UI**
- Color-coded output
- Tables and panels
- Progress indicators
- Command history with auto-suggestions

🔐 **Session Management**
- Persistent authentication
- Project context awareness
- Session history tracking

📦 **Full Feature Set**
- User authentication (register/login)
- Project management (create/list/select/delete)
- Session management (start/end/history)
- Specification extraction
- Real-time conversation

## Quick Start

### Installation

```bash
# 1. Install CLI dependencies
pip install -r cli-requirements.txt

# 2. Start backend server (in separate terminal)
cd backend
uvicorn app.main:app --reload

# 3. Run CLI
python Socrates.py
```

### First Time Setup

```bash
# Register account
/register

# Login
/login

# Create project
/project create

# Start Socratic session
/session start

# Start chatting!
I want to build a task management API...
```

## Command Reference

### Quick Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/mode` | Toggle chat mode (Socratic ↔ Direct) |
| `/login` | Login |
| `/project create` | Create project |
| `/session start` | Start Socratic session |
| `/history` | View conversation |
| `/exit` | Quit |

See [CLI_GUIDE.md](CLI_GUIDE.md) for complete documentation.

## Chat Modes

### Socratic Mode (Default) 🤔

The AI asks thoughtful questions to help you think deeply about your requirements:

```
Socrates: What problem are you trying to solve?
You: I need a system to manage customer support tickets

Socrates: Interesting. What are the main pain points with current solutions?
You: Current tools are too complex and expensive for small teams

✓ Extracted 2 specification(s):
  • User requirement: Simple ticket management for small teams
  • Cost constraint: Must be affordable for small businesses
```

### Direct Mode 💬

Chat directly with the AI for quick questions:

```
You: What are the best practices for REST API authentication?

Socrates:
╔═══════════════════════════════════════════════════════╗
║ Here are the main approaches for REST API auth:      ║
║                                                       ║
║ 1. JWT (JSON Web Tokens)                            ║
║    - Stateless, scalable                             ║
║    - Good for microservices                          ║
║    ...                                               ║
╚═══════════════════════════════════════════════════════╝
```

## Examples

### Example 1: New Project Setup

```bash
$ python Socrates.py

socrates 🤔 > /register
Email: dev@example.com
Full name: Developer Name
Password: ********

✓ Account created successfully!

socrates 🤔 > /login
✓ Logged in successfully

socrates 🤔 > /project create
Project name: Mobile App API
Description: Backend for iOS app

✓ Project created
Selected project: Mobile App API

Mobile App API 🤔 > /session start
✓ Session started

Socrates: Let's explore your mobile app...
```

### Example 2: Mode Switching

```bash
# Start with structured questioning
MyProject 🤔 > /session start
[Answer Socratic questions]

# Switch to direct for clarification
MyProject 🤔 > /mode direct
✓ Switched to direct mode 💬

MyProject 💬 > Can you explain that concept more?
[Get detailed explanation]

# Back to Socratic
MyProject 💬 > /mode socratic
✓ Switched to socratic mode 🤔
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Socrates CLI                       │
│  ┌──────────────┐    ┌─────────────────────────┐  │
│  │   Terminal   │◄───│  Rich UI Components     │  │
│  │   Interface  │    │  • Tables               │  │
│  └──────┬───────┘    │  • Panels               │  │
│         │            │  • Progress             │  │
│         ▼            └─────────────────────────┘  │
│  ┌──────────────┐                                 │
│  │   Command    │                                 │
│  │   Handler    │                                 │
│  └──────┬───────┘                                 │
│         │                                          │
│         ▼                                          │
│  ┌──────────────┐                                 │
│  │   API        │                                 │
│  │   Client     │                                 │
│  └──────┬───────┘                                 │
└─────────┼─────────────────────────────────────────┘
          │ HTTP/JSON
          ▼
┌─────────────────────────────────────────────────────┐
│              Socrates Backend API                   │
│         (FastAPI + PostgreSQL + Anthropic)          │
└─────────────────────────────────────────────────────┘
```

## Configuration

Config stored in `~/.socrates/`:
- `config.json` - Auth token and settings
- `history.txt` - Command history

```json
{
  "access_token": "eyJ...",
  "user_email": "you@example.com"
}
```

## Requirements

- Python 3.11+
- Backend server running (FastAPI)
- PostgreSQL database configured

## Dependencies

```
requests>=2.31.0        # HTTP client
rich>=13.7.0           # Terminal UI
prompt-toolkit>=3.0.43  # Interactive prompts
```

Install with:
```bash
pip install -r cli-requirements.txt
```

## Troubleshooting

### Backend Not Running
```
Error: Cannot connect to Socrates backend
```
**Fix:** Start backend server:
```bash
cd backend && uvicorn app.main:app --reload
```

### Missing Dependencies
```
Error: Missing required package
```
**Fix:** Install CLI requirements:
```bash
pip install -r cli-requirements.txt
```

### Token Expired
```
401 Unauthorized
```
**Fix:** Re-login:
```bash
/logout
/login
```

## Advanced Usage

### Custom API URL
```bash
python Socrates.py --api-url http://production.example.com
```

### Debug Mode
```bash
python Socrates.py --debug
```

### Environment Variable
```bash
export SOCRATES_API_URL=http://localhost:8000
python Socrates.py
```

## Keyboard Shortcuts

- `Ctrl+C` - Cancel input (reminder to use /exit)
- `Ctrl+D` - Exit CLI
- `↑/↓` - Navigate command history
- `Tab` - Auto-complete (future)

## Prompt Indicators

```
socrates 🤔 >              # Not logged in, Socratic mode
socrates 💬 >              # Not logged in, Direct mode
MyProject 🤔 >             # Project selected, Socratic
MyProject session 🤔 >     # Active session, Socratic
MyProject 💬 >             # Project selected, Direct
```

## Roadmap

- [ ] Tab completion for commands
- [ ] Export commands (`/export markdown`)
- [ ] Inline specification editing
- [ ] Search conversation history
- [ ] Multi-line input support
- [ ] Syntax highlighting for code
- [ ] File upload for context
- [ ] Team collaboration commands

## Contributing

Contributions welcome! Please check the main project README for guidelines.

## Documentation

- [Complete CLI Guide](CLI_GUIDE.md) - Full documentation with examples
- [Backend API Docs](http://localhost:8000/docs) - FastAPI Swagger UI
- [Main Project README](README.md) - Project overview

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for developers who love the command line**

*Inspired by Claude Code's elegant CLI design*
