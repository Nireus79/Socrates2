# Socrates CLI - User Guide

Complete guide to using Socrates CLI for interactive specification gathering and project development.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Project Management](#project-management)
4. [Chat Modes](#chat-modes)
5. [Commands Reference](#commands-reference)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Socrates.git
cd Socrates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Socrates
python Socrates.py
```

### First Launch

On first launch, you'll see:
```
╭─────────────────────────────────────────╮
│      Welcome to Socrates CLI v1.0.0     │
│   Interactive Specification Generator   │
╰─────────────────────────────────────────╯

Quick Login
===========
Would you like to auto-login? (yes/no):
```

Choose `yes` for quick setup or `no` for manual authentication.

---

## Authentication

### Quick Login (Recommended)

When prompted, enter your credentials:
```
Username: john_doe
Password: ••••••••
```

The system remembers you for this session.

### Register New Account

```
/register

Enter your details:
- Username: Choose unique username
- Password: Strong password (8+ chars)
- Email: Valid email address (used for recovery)
```

### Logout

```
/logout

Your session ends and you're returned to login screen.
```

### View Current User

```
/whoami

Shows:
- Username
- Email
- Registration date
- Last login
```

---

## Project Management

### Create Project

**Command:**
```
/project create ProjectName
```

**Natural Language:**
```
create new project MyAPI
make a project called DataPipeline
new project called WebApp
```

**Result:** New empty project created and selected.

### List Projects

**Command:**
```
/projects
```

Shows all your projects with:
- Project name
- Description
- Last modified
- Maturity score

### Select Project

**Command:**
```
/project select ProjectName
```

**Natural Language:**
```
select project MyAPI
open project WebApp
go to project DataPipeline
```

### Manage Project

```
/project manage

Options:
1. Rename project
2. Delete project
3. Archive project
4. Change description
5. Update settings
```

---

## Chat Modes

### Socratic Mode (Q&A)

Best for: Interactive specification gathering

**Activate:**
```
/mode socratic
```

**How it works:**
- AI asks targeted questions
- You answer naturally
- No commands in this mode
- Pure conversational flow

**Example:**
```
AI: What is the primary purpose of your application?
You: We're building a task management tool for teams.

AI: Will it support real-time collaboration?
You: Yes, we want multiple users editing the same task simultaneously.
```

**Exit:**
```
/mode direct    (Switch to Direct mode)
/exit           (End session)
```

### Direct Mode (Chat + Commands)

Best for: Development, document management, code generation

**Activate:**
```
/mode direct
```

**How it works:**
- Mix commands and chat
- Natural language parsing
- Execute operations
- Full CLI feature access

**Example:**
```
You: List all projects
System: Executes /projects command

You: I want to generate code
System: Parses intent and runs /code generate

You: Show me the code preview
System: Displays generated code
```

### Switching Modes

Current mode shown in prompt:
```
[socratic] > _     (Socratic mode)
[direct]   > _     (Direct mode)
```

Switch anytime:
```
/mode socratic    # Switch to Socratic
/mode direct      # Switch to Direct
```

---

## Commands Reference

### Project Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/projects` | List all projects | List all my projects |
| `/project create NAME` | Create new project | Create new project MyAPI |
| `/project select NAME` | Switch to project | Select project MyAPI |
| `/project manage` | Manage project | /project manage |

### Session Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/session start` | Start new session | Begin session |
| `/session end` | End current session | End session |
| `/sessions` | List all sessions | Show sessions |
| `/history` | View session history | History |

### LLM Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/llm list` | List available models | List models |
| `/llm current` | Show selected model | Which model? |
| `/llm select PROVIDER MODEL` | Select model | Use claude-3-sonnet |
| `/llm update` | Update deprecated models | Update old models |
| `/llm costs` | Show model pricing | How much? |
| `/llm usage DAYS` | Show usage stats | Usage last 7 days |

### Document Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/doc upload PATH` | Upload document | Upload my_spec.pdf |
| `/doc list` | List documents | Show documents |
| `/doc search QUERY` | Search documents | Search for API design |
| `/doc delete ID` | Delete document | Delete doc_123 |

### GitHub Integration

| Command | Purpose | Example |
|---------|---------|---------|
| `/fetch github status` | Check connection | Is GitHub connected? |
| `/fetch github connect` | Connect GitHub account | Setup GitHub |
| `/fetch github REPO` | Import from GitHub | Import anthropic/claude |

### Code Generation

| Command | Purpose | Example |
|---------|---------|---------|
| `/code generate` | Generate code | Generate application code |
| `/code list` | List generations | Show code generations |
| `/code status [ID]` | Check status | Status of gen_123 |
| `/code preview [ID]` | Preview code | Preview latest |
| `/code download [ID]` | Download code | Download gen_456 |

### Configuration

| Command | Purpose | Example |
|---------|---------|---------|
| `/config` | Edit settings | Configuration |
| `/logging on/off` | Enable debug logs | Debug logging on |
| `/theme dark/light` | Switch theme | Theme dark |
| `/format json/markdown` | Output format | Format JSON |

### Utility Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/status` | System status | Status |
| `/stats` | Statistics | Show stats |
| `/help` | Show help | Help |
| `/exit` | Quit application | Exit |

---

## Advanced Features

### Natural Language Intent Parsing

Socrates understands natural language and converts it to commands:

**Examples:**
```
"Create a new project called TaskManager"
→ /project create TaskManager

"List all available models"
→ /llm list

"Show me the code preview"
→ /code preview

"Search documents for API design"
→ /doc search API design
```

**Confidence Levels:**
- **High (95%):** Exact pattern match
- **Medium (85%):** Partial match with ID
- **Low (70%):** Requires confirmation

### Session Bookmarks

Mark important points in conversation:
```
/session bookmark
Bookmarked: Session point #5 at 14:32:15
```

Later jump back:
```
/session branch #5
Restored session branch #5
```

### Session Notes

Add annotations:
```
/session note "Discussed API versioning strategy"
→ Note added to session

/session note list
→ Shows all notes in session
```

### Export & Save

**Save session to file:**
```
/save my_session_notes.md

Saved to:
~/.socrates/sessions/my_session_notes.md (2.5 MB)
```

**Export project:**
```
/export markdown
```

Supported formats:
- `markdown` - Human-readable
- `json` - Structured data
- `csv` - Spreadsheet format
- `pdf` - Professional document

### Code Generation Workflow

1. **Generate:** Describe what you want
   ```
   /code generate
   Generating Flask API with authentication...
   ```

2. **Status:** Check progress
   ```
   /code status
   Status: In Progress (35%)
   ```

3. **Preview:** See the generated code
   ```
   /code preview
   (Shows syntax-highlighted preview)
   ```

4. **Download:** Get the complete package
   ```
   /code download
   Downloading: socrates_project_20240101.zip (15.2 MB)
   ```

---

## Troubleshooting

### Common Issues

#### "Authentication Failed"

**Cause:** Wrong credentials or connection issue

**Solution:**
```
1. Check username and password
2. Verify internet connection
3. Try /logout then /login again
```

#### "Project Not Found"

**Cause:** Project doesn't exist or wrong name

**Solution:**
```
/projects                    # List all projects
/project select ProjectName  # Use exact name
```

#### "API Timeout"

**Cause:** Server slow or network issue

**Solution:**
```
1. Wait a moment and retry
2. Check internet connection
3. Try again with different endpoint
```

#### "Generation Failed"

**Cause:** Invalid specifications or API error

**Solution:**
```
1. Review specifications clarity
2. Reduce scope of request
3. Try simpler code generation first
```

### Getting Help

**In-app help:**
```
/help              # General help
/help project      # Project command help
/help llm          # LLM command help
```

**Debug mode:**
```
/logging on
(Now runs with detailed output)
```

**Contact support:**
```
Email: support@socrates.dev
Website: https://socrates.dev/support
Docs: https://docs.socrates.dev
```

---

## Tips & Tricks

### Efficient Workflow

1. **Start with Socratic Mode** - Gather clear requirements
2. **Switch to Direct Mode** - Execute operations
3. **Upload Documents** - Add context with files
4. **Generate Code** - Get implementation
5. **Export** - Share results

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit application |
| `↑` / `↓` | Command history |
| `Tab` | Command autocomplete |

### Best Practices

1. **Clear Specifications**
   - Describe intent, not implementation
   - Provide context and constraints
   - Give examples of expected behavior

2. **Iterative Development**
   - Start with MVP (minimum viable product)
   - Generate and test
   - Refine based on results

3. **Documentation**
   - Bookmark important decisions
   - Add notes for future reference
   - Export final specifications

4. **Code Review**
   - Always preview generated code
   - Test thoroughly before using
   - Modify as needed

---

## Performance Tips

### Faster Operations

1. **Cache LLM Models**
   ```
   /llm select claude-3-sonnet
   (Model cached, future selections faster)
   ```

2. **Batch Operations**
   ```
   Upload multiple documents at once
   Search across all documents
   ```

3. **Use Sessions**
   - Maintain context across operations
   - Faster follow-up requests
   - Better suggestions

### Memory Management

- Close unused sessions: `/session end`
- Clear old documents: `/doc delete DOC_ID`
- Export and save regularly

---

## FAQ

**Q: Can I use Socrates offline?**
A: No, Socrates requires API backend connection.

**Q: How long are sessions kept?**
A: Sessions timeout after 15 minutes of inactivity.

**Q: Can I share projects?**
A: Currently no, projects are user-scoped. Future versions will support sharing.

**Q: What models are available?**
A: See `/llm list` for available models and pricing.

**Q: How is my data stored?**
A: Data stored on secure servers with encryption. See privacy policy.

**Q: Can I use my own API key?**
A: Set `ANTHROPIC_API_KEY` environment variable.

---

## Feedback

Found a bug or have suggestions?

- **GitHub Issues:** https://github.com/socrates/issues
- **Email:** feedback@socrates.dev
- **Twitter:** @SocratesCLI

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
