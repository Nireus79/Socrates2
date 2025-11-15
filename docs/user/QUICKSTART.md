# Socrates CLI - Quick Start Guide

Get started with Socrates CLI in 5 minutes!

## 1. Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/yourusername/Socrates.git
cd Socrates

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# OR
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run Socrates
python Socrates.py
```

## 2. First Login (1 minute)

```
Welcome to Socrates CLI

Quick Login
===========
Would you like to auto-login? yes

Username: john_doe
Password: ••••••••

✓ Logged in as john_doe
Ready to chat in Direct mode!
```

## 3. Create Your First Project (1 minute)

**Option A: Using Commands**
```
[direct] > /project create MyAPI
✓ Project "MyAPI" created successfully
✓ Project selected
```

**Option B: Using Natural Language**
```
[direct] > create new project MyAPI
✓ Project "MyAPI" created successfully
✓ Project selected
```

## 4. Switch to Socratic Mode (1 minute)

```
[direct] > /mode socratic
✓ Switched to Socratic mode

[socratic] > (ready for questions)

AI: What is the primary purpose of your application?
You: We're building a REST API for managing tasks.

AI: Will it need real-time updates?
You: Yes, we want WebSocket support.

(Continue conversation...)

[socratic] > /mode direct
✓ Switched to Direct mode
```

## 5. Generate Code (1 minute)

```
[direct] > generate code
✓ Code generation started...

[direct] > /code status
Status: In Progress (45%)
Estimated time remaining: 2 minutes

[direct] > /code preview
(Shows generated code with syntax highlighting)

[direct] > /code download
✓ Downloaded: socrates_project_20250101.zip (15.2 MB)
```

---

## Most Useful Commands

```bash
# Authentication
/login              # Login with username/password
/logout             # Logout from session
/whoami             # Show current user

# Projects
/projects           # List all your projects
/project create API # Create new project
/project select API # Switch to project

# Chat Modes
/mode socratic      # Q&A mode (pure conversation)
/mode direct        # Chat + Commands mode

# Code Generation
/code generate      # Generate code from specs
/code preview       # Preview generated code
/code download      # Download generated code

# Documentation
/doc upload file.pdf        # Upload a document
/doc search "API design"    # Search documents
/doc list                   # List all documents

# Help & Information
/help               # Show all commands
/status             # System status
/exit               # Exit Socrates
```

---

## Natural Language Examples

Just type naturally, Socrates understands:

```
You: Create a new project called WebApp
→ /project create WebApp

You: List all my projects
→ /projects

You: Switch to Socratic mode
→ /mode socratic

You: Generate code for a Flask API
→ /code generate

You: Download my code
→ /code download

You: Upload my requirements document
→ /doc upload requirements.pdf
```

---

## Typical Workflow

### Step 1: Gather Requirements (5-10 minutes)

```
[direct] > /mode socratic
[socratic] > (AI asks clarifying questions)
```

### Step 2: Switch to Operations (1-2 minutes)

```
[socratic] > /mode direct
```

### Step 3: Upload Documents (2-3 minutes)

```
[direct] > /doc upload spec.pdf
[direct] > /doc upload wireframes.pdf
```

### Step 4: Generate Code (5-10 minutes)

```
[direct] > /code generate
[direct] > /code preview
[direct] > /code download
```

### Step 5: Export Results (1 minute)

```
[direct] > /export markdown
[direct] > /save my_project_final
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `↑` / `↓` | Navigate command history |
| `Tab` | Autocomplete command |
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit application |

---

## Troubleshooting

### "Authentication Failed"
```
Solution: Check username and password
→ /logout
→ /login
```

### "Project Not Found"
```
Solution: List projects to see exact name
→ /projects
→ /project select <correct_name>
```

### "Generation Failed"
```
Solution: Improve specification clarity
1. Add more context in descriptions
2. Upload reference documents
3. Try again with clearer requirements
```

### "API Timeout"
```
Solution: Try again or check connection
1. Wait a few seconds
2. Check internet connection
3. /status to verify API connection
```

---

## Getting Help

```bash
# In-app help
/help               # General help
/help project       # Project command help

# Enable debug mode for detailed output
/logging on

# Exit Socrates
/exit
```

---

## What's Next?

1. **Read the Full User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
2. **Understand the Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Explore Advanced Features:** [CODE_ORGANIZATION.md](CODE_ORGANIZATION.md)

---

## Key Concepts

### Two Chat Modes

**Socratic Mode:** Pure question-answering for requirements gathering
- No commands
- Natural conversation
- AI guides the discussion

**Direct Mode:** Chat + Commands for execution
- Use commands or natural language
- Execute operations
- Full feature access

### Two-Level Intent Parsing

**Level 1 (Fast):** Pattern matching
- Instant recognition
- No API calls
- Examples: "list projects", "create project X"

**Level 2 (Smart):** Claude-based parsing
- Handles complex requests
- More flexible
- Fallback for unmatched patterns

---

## Session Persistence

Sessions are saved in memory and lost when you exit. To save your work:

```bash
# Save session to file
/save my_session.md

# Later, export project
/export markdown
```

---

## Common Workflows

### Workflow 1: Quick API Generation
```
1. /project create MyAPI
2. /mode socratic (describe API)
3. /mode direct
4. /code generate
5. /code download
```

### Workflow 2: Document-Driven Development
```
1. /doc upload requirements.pdf
2. /doc upload architecture.pdf
3. /mode socratic (discuss specs)
4. /mode direct
5. /code generate
6. /code download
```

### Workflow 3: Iterative Refinement
```
1. /code generate (first version)
2. /code preview (review code)
3. /session note "Feedback: Add error handling"
4. /mode socratic (refine requirements)
5. /mode direct
6. /code generate (improved version)
7. /code download (get final code)
```

---

## Pro Tips

1. **Use Projects Wisely**
   - One project per major feature
   - Keep related specs together
   - Use descriptive names

2. **Bookmark Decisions**
   - `/session note "API versioning strategy"`
   - Useful for future reference

3. **Upload References**
   - Upload design files
   - Share style guides
   - Include existing code examples

4. **Preview Before Download**
   - `/code preview` - See the code
   - `/code status` - Check progress
   - `/code download` - Get final package

5. **Use Natural Language**
   - "create new project" instead of `/project create`
   - "list my projects" instead of `/projects`
   - More natural, equally powerful

---

**Ready to start?** Run `python Socrates.py` and create your first project!

For detailed documentation, see [USER_GUIDE.md](USER_GUIDE.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Questions?** Type `/help` at any time!

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
