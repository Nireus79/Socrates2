# Getting Started with Socrates2

**Time to read:** 15 minutes
**Level:** Beginner
**Goal:** Get Socrates2 running and create your first project

---

## What is Socrates2?

Socrates2 is an **AI-powered specification and requirements gathering system** that helps you:
- 📋 Gather requirements systematically using Socratic questioning
- 🏗️ Build comprehensive specifications across multiple knowledge domains
- 🤖 Get AI-powered analysis and recommendations
- 👥 Collaborate with teams on projects
- 📊 Track project maturity and progress

Think of it as a **smart assistant that guides you through building perfect specifications**.

---

## 5-Minute Quick Start

### 1. Create Account
```bash
# Visit the Socrates2 interface or API
POST /api/v1/auth/register
{
  "email": "you@example.com",
  "password": "SecurePassword123!",
  "full_name": "Your Name"
}
```

### 2. Create Your First Project
```bash
POST /api/v1/projects
{
  "name": "My First Project",
  "description": "Building a web application",
  "maturity_score": 0.0
}
```

### 3. Start a Conversation Session
```bash
POST /api/v1/projects/{project_id}/sessions
{
  "name": "Initial Requirements Gathering",
  "description": "First conversation with Socrates",
  "status": "active"
}
```

### 4. Gather Specifications
The AI will guide you through questions about:
- 🏗️ **Architecture** - System design and structure
- 💻 **Programming** - Technology stack and implementation
- ✅ **Testing** - Quality assurance strategy
- 📊 **Data** - Data engineering and pipelines
- 🔒 **Security** - Security and compliance
- 💼 **Business** - Business requirements
- 🚀 **DevOps** - Deployment and operations

---

## Key Concepts

### 📁 Projects
A **project** is your main organizational unit. It contains:
- Specifications (requirements)
- Sessions (conversations)
- Team members
- Analysis and metrics

### 💬 Sessions
A **session** is a conversation with the AI. Each session:
- Asks domain-specific questions
- Gathers your answers
- Builds specifications incrementally
- Provides AI insights

### 📝 Specifications
**Specifications** are the requirements you've gathered:
- Organized by category
- Assigned confidence scores
- Linked to sessions
- Analyzed for conflicts

### 🔄 Workflows
**Workflows** let you:
- Work across multiple domains in one workflow
- Get cross-domain analysis
- Identify conflicts between domains
- Execute comprehensive gathering processes

---

## Common Tasks

### Task 1: Create a New Project

1. **Log in** to Socrates2
2. **Click "New Project"**
3. **Fill in:**
   - Project name
   - Description
   - Initial maturity score (0-1)
4. **Click "Create"**
5. **See your empty project dashboard**

### Task 2: Start Your First Session

1. **Go to your project**
2. **Click "New Session"**
3. **Choose domain** (e.g., "Architecture")
4. **Click "Start Conversation"**
5. **Answer the AI's questions**
6. **Review gathered specifications**

### Task 3: Add a Team Member

1. **Go to Project Settings**
2. **Click "Add Member"**
3. **Enter their email**
4. **Select role** (owner, editor, viewer)
5. **Send invitation**

### Task 4: Review Your Specifications

1. **Go to "Specifications"**
2. **Filter by category** (optional)
3. **Review each specification**
4. **Check confidence scores**
5. **Export or share** as needed

---

## Understanding Domains

Socrates2 has 7 knowledge domains:

### 1. 🏗️ Architecture
System design, patterns, scalability
- Components and services
- Communication patterns
- Data flow
- System constraints

### 2. 💻 Programming
Technology stack, implementation details
- Languages and frameworks
- Libraries and dependencies
- Code organization
- Development practices

### 3. ✅ Testing
Quality assurance and testing strategy
- Unit tests
- Integration tests
- Test coverage
- Quality metrics

### 4. 📊 Data Engineering
Data models, pipelines, analytics
- Data structures
- ETL processes
- Analytics requirements
- Data quality

### 5. 🔒 Security
Security architecture and requirements
- Authentication and authorization
- Data protection
- Compliance requirements
- Security testing

### 6. 💼 Business
Business requirements and context
- Use cases
- User personas
- Business goals
- ROI and value

### 7. 🚀 DevOps
Deployment, monitoring, operations
- Infrastructure requirements
- Deployment strategy
- Monitoring and alerting
- Backup and disaster recovery

---

## Workflow Example

**Scenario:** Building an e-commerce platform

```
1. Create Project: "Online Store Platform"
2. Start Session (Architecture)
   - Questions about system design
   - Gather architecture specs
3. Start Session (Programming)
   - Questions about tech stack
   - Gather implementation specs
4. Start Session (Security)
   - Questions about security requirements
   - Gather security specs
5. Create Workflow (Architecture + Programming + Security)
   - Cross-domain analysis
   - Identify conflicts
   - Get recommendations
6. Review and finalize specifications
7. Export to document or share with team
```

---

## Tips & Best Practices

### ✅ Do This

- **Start with Architecture** - Understand the system design first
- **Answer honestly** - More accurate answers = better results
- **Be specific** - Vague answers lead to vague specifications
- **Review regularly** - Check specifications after each session
- **Use confidence scores** - They indicate certainty level
- **Collaborate** - Get team input on requirements

### ❌ Don't Do This

- **Skip domains** - Each domain provides critical insights
- **Rush through questions** - Take time to think through answers
- **Ignore conflicts** - Address contradictions immediately
- **Forget context** - Always consider the bigger picture
- **Isolate decisions** - Team input improves outcomes

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New project |
| `Ctrl+S` | Save specifications |
| `Ctrl+E` | Export |
| `Ctrl+?` | Help |

---

## Troubleshooting

### "I can't log in"
- Check email/password spelling
- Reset password if forgotten
- Check internet connection

### "Session won't start"
- Ensure project is created first
- Check network connection
- Try refreshing the page

### "Questions seem off-topic"
- You're in the right domain
- Answer questions honestly
- Provide more context if needed

### "Can't add team member"
- Verify their email address
- Ensure they have an account
- Check your permissions

👉 **Need more help?** See [FAQ](FAQ.md) or [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)

---

## Next Steps

1. **[User Guide](USER_GUIDE.md)** - Learn all features (30 min)
2. **[Tutorials](TUTORIALS.md)** - Follow step-by-step examples
3. **[API Reference](../developer/API_REFERENCE.md)** - If using API directly

---

**[← Back to Documentation Index](../INDEX.md)**
