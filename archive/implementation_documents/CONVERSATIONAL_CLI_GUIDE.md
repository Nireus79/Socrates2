# 🎯 Conversational CLI Guide - Phase 10

**Version:** 1.0
**Status:** Ready for Implementation
**Effort:** 8-10 hours
**Priority:** Enhancement (Phase 10 - Nice to Have)

---

## Overview

The Conversational CLI transforms Socrates from a command-line tool into an **AI-powered interactive assistant**. Users describe what they want in natural language, and Claude interprets their intent to execute actions.

### Key Features

✨ **Natural Language Understanding**
- Users describe actions in plain English
- Claude interprets intent and extracts parameters
- No need to remember command syntax

🎯 **Model Selection**
- Choose between Claude Sonnet (capable), Haiku (fast), or Opus (advanced)
- Switch models during conversation
- `/model` command for quick switching

🔄 **Graceful Menu Navigation**
- `/back` to exit any menu
- `/cancel` to abandon current action
- No "stuck" states

🔗 **Slash Command Support**
- `/help` - Show available commands
- `/model` - Choose AI model
- `/logout` - Exit account
- `/whoami` - Show user info
- `/quit` - Exit application

💬 **Conversational Context**
- System maintains conversation history
- Claude understands context from previous messages
- Natural back-and-forth dialogue

---

## Architecture

### Core Components

```
ConversationalCLI
├── _main_loop()                 # Main interaction loop
├── _handle_slash_command()      # Process /commands
├── _handle_natural_language()   # Process user text
├── _get_intent_from_claude()    # Parse intent with Claude
├── _execute_intent()            # Execute intended operation
├── Menu Management
│   ├── _push_menu()             # Enter menu
│   ├── _pop_menu()              # Exit menu
│   └── menu_stack               # Track navigation
├── Model Selection
│   ├── _select_model()          # Choose model
│   └── AVAILABLE_MODELS         # Model list
└── Operation Handlers
    ├── _mock_register_user()
    ├── _mock_login_user()
    ├── _mock_create_project()
    └── ... (10 total)
```

### Intent Flow

```
User Input
    ↓
Is it a slash command?
    ├─→ YES: _handle_slash_command()
    └─→ NO: _handle_natural_language()
            ↓
        Send to Claude with context
            ↓
        Claude responds with JSON intent
            ↓
        Parse JSON
            ├─→ Is operation?: _execute_intent()
            └─→ Is conversation?: Display response
                ↓
            Update conversation history
                ↓
            Show result to user
```

---

## Available Operations

### User Management

**Register User**
```python
{
    "operation": "register_user",
    "params": {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepass123"
    }
}
```
Usage: "Register a user named John Doe with email john@example.com and password securepass123"

**Login User**
```python
{
    "operation": "login_user",
    "params": {
        "email": "john@example.com",
        "password": "securepass123"
    }
}
```
Usage: "Log me in with my email john@example.com"

**Logout User**
```python
{
    "operation": "logout_user",
    "params": {}
}
```
Usage: "/logout" or "Log me out"

### Project Management

**Create Project**
```python
{
    "operation": "create_project",
    "params": {
        "name": "Mobile App Redesign",
        "description": "Improve user experience on mobile"
    }
}
```
Usage: "Create a project called Mobile App Redesign for improving user experience"

**List Projects**
```python
{
    "operation": "list_projects",
    "params": {}
}
```
Usage: "Show me my projects" or "What projects do I have?"

### Session Management

**Start Session**
```python
{
    "operation": "start_session",
    "params": {
        "project_id": "project-123"
    }
}
```
Usage: "Start a session for my Mobile App project"

**Ask Question**
```python
{
    "operation": "ask_question",
    "params": {
        "question": "What is the target audience?"
    }
}
```
Usage: "In my session, ask: What is the target audience?"

### Analysis & Export

**View Insights**
```python
{
    "operation": "view_insights",
    "params": {
        "project_id": "project-123"
    }
}
```
Usage: "What insights do you have about my project?"

**Export Project**
```python
{
    "operation": "export_project",
    "params": {
        "project_id": "project-123",
        "format": "pdf"  # or "json", "markdown"
    }
}
```
Usage: "Export my project as PDF"

---

## Usage Examples

### Example 1: Complete Workflow

```
Socrates: Welcome to Socrates Interactive Mode
Socrates: Type /help for commands or describe what you want

You: Register a user named Alice with email alice@startup.com and password MyPass123!

Socrates: ✓ User "Alice" registered successfully
Socrates: Email: alice@startup.com

You: Create a new project called "SaaS Platform"

Socrates: ✓ Project "SaaS Platform" created
Socrates: Description: No description

You: I want to build a web platform for managing customer relationships

Socrates: That sounds like a comprehensive CRM system. Would you like me to help you:
Socrates: 1. Define key specifications for the CRM
Socrates: 2. Identify missing requirements
Socrates: 3. Start a specification gathering session

You: Start a session

Socrates: ✓ Session started
Socrates: Ready to gather specifications. Ask me questions about your project!

You: What are the main user types?

Socrates: Question recorded
Socrates: Q: What are the main user types?
Socrates: A: [Response from Socratic agent discussing roles like Admin, Sales Rep, Manager]

You: /back

Socrates: ✓ Exited session context
```

### Example 2: Model Selection

```
You: /model

Socrates: Select Model:
         1. Claude Sonnet 4.5 (Most capable)
         2. Claude Haiku 4.5 (Fast & affordable)
         3. Claude Opus 4 (Most advanced)

You: 2

Socrates: ✓ Using claude-haiku-4.5-20251001

You: Now let's continue working on the project specs

Socrates: [Responds using Haiku for faster, more concise answers]
```

### Example 3: Mixed Commands and Natural Language

```
You: /whoami

Socrates: **Email:** alice@startup.com
Socrates: **Name:** Alice
Socrates: **Current Project:** SaaS Platform
Socrates: **Current Model:** Claude Sonnet 4.5

You: Generate an export of my project

Socrates: ✓ Project exported

You: /help

Socrates: [Shows help menu]

You: Log me out and goodbye

Socrates: ✓ Logged out successfully
Socrates: Thanks for using Socrates! Goodbye! 👋
```

---

## Running the Conversational CLI

### Installation

```bash
# Ensure dependencies are installed
pip install anthropic rich

# Or install from requirements
pip install -r requirements-cli.txt
```

### Startup

```bash
# Run the conversational CLI
python conversational_cli.py

# Or from Socrates.py
python Socrates.py --conversational
```

### Configuration

Environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SOCRATES_MODEL="sonnet"  # Default model
export SOCRATES_API_URL="http://localhost:8000"
```

---

## Implementation Details

### JSON Intent Format

Claude returns one of two JSON formats:

**Operation Request:**
```json
{
    "is_operation": true,
    "operation": "operation_name",
    "params": {"param1": "value1", "param2": "value2"},
    "explanation": "Brief explanation of what will happen"
}
```

**Conversation:**
```json
{
    "is_operation": false,
    "response": "Your conversational response here"
}
```

### Context Management

The system maintains:
- **Conversation History** - Full chat history for context
- **User State** - Current user, project, session
- **Menu Stack** - Navigation context for graceful exits
- **Model Selection** - Current Claude model in use

### Error Handling

All operations return standardized responses:

```python
{
    "success": bool,           # Operation succeeded?
    "message": str,            # User-facing message
    "error": str,              # Error message if failed
    "details": str,            # Additional information
}
```

---

## Integration with Socrates.py

### Starting Conversational Mode

Option 1: Direct execution
```bash
python conversational_cli.py
```

Option 2: From Socrates.py main

```python
from archive.implementation_documents.conversational_cli import ConversationalCLI


def main():
    # ... existing code ...

    if args.conversational:
        cli = ConversationalCLI()
        cli.run()
    else:
# ... existing command-line interface ...
```

Option 3: Menu option
```
Socrates: Choose mode:
         1. Command-line mode (traditional)
         2. Conversational mode (AI-powered)

You: 2
```

---

## Testing

### Unit Tests

Run the test suite:
```bash
pytest test_conversational_cli.py -v
```

### Test Coverage

The test suite covers:
- ✅ Initialization and defaults
- ✅ Menu management (push/pop)
- ✅ User operations (register, login, logout)
- ✅ Project operations (create, list)
- ✅ Session operations (start, ask)
- ✅ Intent parsing (operations and conversations)
- ✅ Full user workflows
- ✅ Error conditions

### Manual Testing Scenarios

1. **User Registration Workflow**
   - Register with full details
   - Register with missing email
   - Verify user state after registration

2. **Login/Logout Flow**
   - Log in with credentials
   - Verify authentication state
   - Log out and verify state reset

3. **Project Management**
   - Create project (must be logged in)
   - List projects
   - Attempt project creation without login (should fail)

4. **Model Selection**
   - Choose different models
   - Verify model switching
   - Confirm conversations use selected model

5. **Menu Navigation**
   - Push multiple menus
   - Exit with /back command
   - Verify cleanup on exit

6. **Intent Parsing**
   - Natural language operation requests
   - Conversational queries
   - Mixed commands and natural language

---

## Future Enhancements

Phase 10.5+ potential improvements:

1. **Real API Integration**
   - Hook to actual backend APIs instead of mocks
   - Real database operations
   - Proper authentication

2. **Advanced Context**
   - Context-aware parameter inference
   - Multi-turn conversation understanding
   - User preference learning

3. **Voice Support**
   - Speech-to-text input
   - Text-to-speech responses
   - Voice-based navigation

4. **Interactive Wizards**
   - Guided workflows for complex operations
   - Step-by-step assistance
   - Confirmation at each step

5. **Customization**
   - User-defined commands
   - Custom response templates
   - Preferred models by operation type

6. **Analytics**
   - Track popular operations
   - User preference analysis
   - Success rate monitoring

---

## Troubleshooting

### "Missing required packages"
```bash
pip install anthropic rich
```

### "API key not found"
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "Claude doesn't understand my intent"
- Be more specific: "Create a project called X" (better than "Make a thing")
- Use operation names if needed: "I want to register_user"
- Check `/help` for examples

### "Menu is stuck"
- Type `/back` to exit any menu
- Type `/cancel` to abort current operation
- Type `/quit` to exit entirely

---

## Architecture Decisions

### Why Claude for Intent Parsing?
- Natural language understanding is Claude's strength
- Handles variations in phrasing gracefully
- Can extract parameters flexibly
- Improves over time with better prompts

### Why Menu Stack?
- Allows graceful exits from any level
- Supports nested operations
- No ambiguous states
- Clean state management

### Why Mock Implementations?
- Allows testing without backend running
- Provides clear interface contracts
- Easy integration point with real APIs
- Good for demonstration purposes

### Why Model Selection?
- Different models suited for different tasks
- Haiku faster for simple operations
- Sonnet better for complex analysis
- Opus for cutting-edge performance
- Lets users optimize cost vs quality

---

## Performance Considerations

### API Calls
- Intent parsing: 1 API call per user input
- Conversation responses: 1 API call if not an operation
- No unnecessary API calls for slash commands

### Memory Usage
- Conversation history kept in memory (10 message limit)
- Menu stack minimal (usually 1-3 items)
- User/project state lightweight (few KB)

### Response Time
- Haiku: ~500-1000ms per request
- Sonnet: ~1000-2000ms per request
- Opus: ~2000-3000ms per request

---

## Security Considerations

### Current Implementation (Mocks)
- No actual authentication
- Passwords not hashed
- Tokens are mock strings

### Production Implementation Needed
- Use actual backend APIs
- Validate authentication tokens
- Hash and salt passwords
- Use HTTPS for API calls
- Rate limit API requests
- Sanitize user inputs

---

## Support & Feedback

For issues or suggestions:
- Check TROUBLESHOOTING section above
- Review test cases for usage patterns
- Examine example workflows
- Check Claude's response for error details

---

## License & Attribution

Part of Socrates project.
Uses Claude API for natural language processing.
Built with FastAPI, Rich TUI, and Anthropic Python SDK.

---

**Status:** Phase 10 Implementation Guide Complete
**Last Updated:** November 9, 2025
**Ready for Implementation:** YES ✅

