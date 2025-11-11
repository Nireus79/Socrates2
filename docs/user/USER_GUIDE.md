# Complete User Guide

**Time to read:** 30 minutes
**Level:** Intermediate
**Goal:** Master all Socrates features

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Projects](#projects)
3. [Sessions](#sessions)
4. [Specifications](#specifications)
5. [Teams](#teams)
6. [Workflows](#workflows)
7. [Analysis and Insights](#analysis-and-insights)
8. [Exporting and Sharing](#exporting-and-sharing)
9. [Advanced Features](#advanced-features)

---

## Core Concepts

### The Socratic Method

Socrates uses the **Socratic method** - asking probing questions to guide discovery:

1. **Question** - AI asks a targeted question
2. **Answer** - You provide your answer
3. **Clarify** - AI asks follow-up questions
4. **Synthesize** - AI summarizes the specification
5. **Validate** - You approve or adjust

**Why it works:**
- Uncovers hidden assumptions
- Forces clarity of thought
- Identifies gaps in thinking
- Builds comprehensive specs naturally

### Maturity Scoring

Each project has a **maturity score (0-1)**:
- `0.0-0.3` - Early stage, many unknowns
- `0.3-0.6` - Moderate, some clarity
- `0.6-0.8` - Mature, well-defined
- `0.8-1.0` - Complete, production-ready

The score increases as you gather more specifications.

### Confidence Levels

Each specification has a **confidence score (0-1)**:
- `0.0-0.3` - Uncertain, needs discussion
- `0.3-0.6` - Provisional, may change
- `0.6-0.8` - Solid, unlikely to change
- `0.8-1.0` - Certain, stable

---

## Projects

### Creating a Project

**Via Web UI:**
1. Dashboard → "New Project"
2. Enter project name
3. Add description
4. Set initial maturity (usually 0.0)
5. Create project

**Via API:**
```bash
POST /api/v1/projects
{
  "name": "My Project",
  "description": "Project description",
  "maturity_score": 0.0
}
```

### Project Structure

Each project contains:

```
My Project
├── Specifications (gathered requirements)
├── Sessions (conversations)
├── Team Members (collaborators)
├── Workflows (multi-domain processes)
├── Analysis (AI insights)
└── Exports (documents)
```

### Managing Projects

**Edit Project:**
```
Dashboard → Project → Settings → Edit
```

**Share Project:**
```
Dashboard → Project → Team → Add Member
```

**Delete Project:**
```
Dashboard → Project → Settings → Delete (with confirmation)
```

### Project Visibility

- **Owner** - Full access, can add members, delete
- **Editor** - Can modify specifications, add sessions
- **Viewer** - Read-only access
- **Private** - Only team members can see
- **Shared** - Anyone with link can view

---

## Sessions

### What is a Session?

A **session** is a guided conversation with the AI:
- Focuses on one or more domains
- Asks 10-20 targeted questions
- Builds specifications incrementally
- Takes 15-45 minutes

### Starting a Session

**Step 1: Create Session**
```
Project → New Session
```

**Step 2: Choose Domain(s)**
```
Select from:
- Architecture
- Programming
- Testing
- Data Engineering
- Security
- Business
- DevOps
```

**Step 3: Answer Questions**
```
AI asks → You answer → AI clarifies → Repeat
```

**Step 4: Review Results**
```
View gathered specifications
Adjust confidence scores
Approve and save
```

### Session Types

**Single Domain:**
- Focused on one area
- 10-15 questions
- 20-30 minutes
- Best for: Deep understanding

**Multi-Domain:**
- Covers multiple areas
- 30-40 questions
- 45-60 minutes
- Best for: Comprehensive view

**Follow-up:**
- Continues previous session
- Addresses clarifications
- 5-10 minutes
- Best for: Refinement

### Session Workflow

```
[Start]
   ↓
[Choose Domain(s)]
   ↓
[AI Asks Question]
   ↓
[You Answer]
   ↓
[AI Clarifies?] → Yes → [Answer Clarification] → back to "AI Asks"
   ↓ No
[More Questions?] → Yes → back to "AI Asks"
   ↓ No
[Review Specs]
   ↓
[Approve or Edit]
   ↓
[Save and Complete]
```

### Session Tips

- **Take your time** - Don't rush answers
- **Be specific** - Vague answers lead to vague specs
- **Ask for clarification** - If question is unclear
- **Review before saving** - Check specs accuracy
- **Use confidence scores** - Mark uncertain items

---

## Specifications

### Understanding Specifications

A **specification** is:
- **What:** A single requirement or detail
- **Category:** Which domain it belongs to
- **Confidence:** How certain you are (0-1)
- **Status:** Draft, approved, implemented
- **Session:** Which session created it

### Specification Categories

**Architecture:** System design details
- Components and services
- Communication patterns
- Data flow
- Scalability approach

**Programming:** Implementation details
- Technology stack
- Libraries and frameworks
- Code organization
- Development practices

**Testing:** Quality assurance
- Test types and coverage
- Quality metrics
- Automated testing approach
- Manual testing strategy

**Data:** Data requirements
- Data structures
- ETL processes
- Data quality standards
- Analytics requirements

**Security:** Security requirements
- Authentication method
- Authorization model
- Data protection
- Compliance needs

**Business:** Business context
- Use cases
- User personas
- Business goals
- Success metrics

**DevOps:** Operations details
- Infrastructure
- Deployment strategy
- Monitoring approach
- Disaster recovery

### Managing Specifications

**View All:**
```
Project → Specifications
```

**Filter by Category:**
```
Specifications → Filter → Select Category
```

**Search:**
```
Specifications → Search → Enter keyword
```

**Edit Specification:**
```
Specification → Edit → Update → Save
```

**Update Confidence:**
```
Specification → Change Confidence Score → Save
```

**Delete Specification:**
```
Specification → Delete (with confirmation)
```

### Specification States

- **Draft** - Being discussed
- **Approved** - Team agreed
- **Implemented** - Built/configured
- **Archived** - No longer relevant

---

## Teams

### Team Management

**Add Team Member:**
```
Project → Team → Add Member
Email: user@company.com
Role: owner/editor/viewer
```

**Remove Member:**
```
Project → Team → Member → Remove
```

**Change Role:**
```
Project → Team → Member → Change Role
```

### Roles and Permissions

| Permission | Owner | Editor | Viewer |
|-----------|-------|--------|--------|
| View project | ✅ | ✅ | ✅ |
| Edit specs | ✅ | ✅ | ❌ |
| Start sessions | ✅ | ✅ | ❌ |
| Add members | ✅ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ |

### Team Best Practices

- **Involve stakeholders** - Include all relevant perspectives
- **Clear roles** - Define who decides what
- **Regular review** - Team meetings to discuss specs
- **Document decisions** - Record why specs were chosen
- **Maintain consensus** - Align on important items

---

## Workflows

### What is a Workflow?

A **workflow** executes a defined process across multiple domains:
- Multiple domain questions
- Cross-domain conflict detection
- AI recommendations
- Complete specification generation

### Creating Workflows

**Step 1: Create Workflow**
```
Workflows → New Workflow
```

**Step 2: Choose Domains**
```
Select multiple domains to include:
☑️ Architecture
☑️ Programming
☑️ Testing
☑️ Security
```

**Step 3: Configure**
```
Set workflow name
Add description
Define scope
```

**Step 4: Execute**
```
Run workflow
Answer questions across domains
Review cross-domain analysis
```

**Step 5: Export Results**
```
Export as document
Share with team
Publish to repository
```

### Built-in Workflows

**MVP Definition:**
- Architecture, Programming, Testing
- Creates a runnable MVP spec
- Time: 60 minutes

**Production Ready:**
- All 7 domains
- Complete specification
- Covers all concerns
- Time: 90 minutes

**Security Focused:**
- Security, Architecture, DevOps
- Security-centric specification
- Compliance considerations
- Time: 75 minutes

**Quick Spec:**
- Architecture, Programming
- Fast overview
- Enough for prototyping
- Time: 45 minutes

---

## Analysis and Insights

### Automatic Analysis

Socrates automatically:
- ✅ Detects conflicting specifications
- ✅ Identifies missing categories
- ✅ Highlights assumptions
- ✅ Suggests clarifications
- ✅ Calculates completeness
- ✅ Recommends next steps

### Viewing Analysis

```
Project → Analysis
```

**Shows:**
- Overall project maturity
- Completeness by domain
- Conflicts and warnings
- Suggested actions
- Risk assessment

### Conflict Resolution

When conflicts are detected:

1. **Identify** - AI shows conflicting specs
2. **Understand** - Review both specifications
3. **Discuss** - Talk with team
4. **Decide** - Choose correct version
5. **Update** - Mark one as obsolete
6. **Revalidate** - Resolve conflict

### Recommendations

AI provides recommendations for:
- Missing specifications
- Incomplete domains
- Risky assumptions
- Potential improvements
- Next priorities

---

## Exporting and Sharing

### Export Formats

**Markdown:**
```
Structured document
- Good for GitHub, wikis
- Preserves formatting
- Human-readable
```

**PDF:**
```
Professional document
- Good for printing
- Formatted for distribution
- Includes graphics
```

**JSON:**
```
Machine-readable format
- Good for tools integration
- Complete data
- Structured format
```

**CSV:**
```
Spreadsheet format
- Good for Excel, sheets
- Tabular layout
- Sortable and filterable
```

### How to Export

```
Project → Export
Select format (Markdown, PDF, JSON, CSV)
Choose what to include:
  ☑️ All specifications
  ☑️ Analysis
  ☑️ Team info
  ☑️ History
Download file
```

### Sharing Projects

**Share with Team:**
```
Project → Team → Add Member
```

**Share via Link:**
```
Project → Share → Generate Link
Set permissions (view/edit)
Share URL
```

**Share Document:**
```
Export → Download
Share exported file via email/drive
```

---

## Advanced Features

### Version History

Track changes to specifications:
```
Project → History
View all changes
Revert if needed
Track who changed what
```

### Comments and Notes

Add team discussions:
```
Specification → Comments
Add discussion
Tag team members
Reference decisions
```

### Custom Domains

Create domain-specific questions:
```
Settings → Custom Domains
Add domain name
Define questions
Configure analyzers
```

### Integrations

Connect with tools:
- GitHub (sync specs to repos)
- Jira (create issues from specs)
- Confluence (publish specs)
- Slack (notifications)

### API Access

Use Socrates programmatically:
```python
import requests

# Create project
response = requests.post(
    'https://api.socrates2.com/v1/projects',
    json={'name': 'My Project'},
    headers={'Authorization': 'Bearer token'}
)
```

See [API Reference](../developer/API_REFERENCE.md) for details.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New project |
| `Ctrl+K` | Search |
| `Ctrl+E` | Export |
| `Ctrl+/` | Help |
| `?` | Keyboard shortcuts |

---

## FAQ

**Q: How long should a session take?**
A: 20-45 minutes depending on complexity. Don't rush.

**Q: Can I redo a session?**
A: Yes, you can mark old specs as archived and redo sessions.

**Q: How do I know if specs are complete?**
A: Check the maturity score and analysis recommendations.

**Q: Can team members see all projects?**
A: Only projects they're added to, based on their role.

**Q: How do I prevent conflicts?**
A: Involve all stakeholders in sessions and reviews.

More: See [FAQ](FAQ.md)

---

**[← Back to Documentation Index](../INDEX.md)**
