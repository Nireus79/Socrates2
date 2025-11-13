# CLI Architecture for Non-Coding Projects

## Problem

Current CLI architecture assumes code-focused projects, but Socrates should equally support:
- **Solo users**: Business planning, product design, research, marketing strategy
- **Teams**: Collaborative design thinking, business development, product research

## Solution: Domain-Aware, Team-First Architecture

### Key Changes to Architecture

#### 1. Domain-Aware Project Creation

**Current (Code-Focused):**
```
/project create
→ Enter name
→ Enter description
→ Create with default settings
```

**New (Domain-Aware):**
```
/project create
→ Select template or domain first:
   [1] Business/Strategy (Business domain)
   [2] Product Design (Design domain)
   [3] Software/Code (Programming domain)
   [4] Research/Analysis (Research domain)
   [5] Marketing/Brand (Marketing domain)
   [6] Custom workflow
→ Enter project name
→ Enter description
→ Apply template (if chosen)
→ Invite team members (optional)
→ Create with domain-specific settings
```

#### 2. Team as First-Class Feature

**Current (Code-Solo):**
```
/project create → solo creation
/team create → afterthought, separate workflow
```

**New (Team-First):**
```
/project create
→ Working solo or with team? [solo/team]
→ If team:
   - Create team now
   - Invite members with emails
   - Set roles (owner, contributor, reviewer)
   - Create shared project
→ Project automatically shared with team
```

#### 3. Domain-Specific Sessions

**Current (Generic):**
```
/session start
→ Start Socratic questioning
→ Get code-related questions
```

**New (Domain-Specific):**
```
/session start
→ Which domain?
   [1] Programming (code generation)
   [2] Business (strategy/planning)
   [3] Design (product/UX)
   [4] Research (analysis)
   [5] Marketing (strategy/positioning)
→ Which workflow?
   [1] Socratic questioning (AI asks)
   [2] Direct conversation (you ask)
   [3] Custom
→ Domain-specific questions loaded
→ Output tailored to domain
```

#### 4. Domain Registry as Discovery Tool

**New Commands:**
```
/domain list
→ Shows all available domains with descriptions:
   Programming - Generate code, technical specs
   Business - Business plans, strategies, requirements
   Design - Product design, UX specs, design docs
   Research - Research summaries, competitive analysis
   Marketing - Marketing plans, positioning, campaigns

/domain info <domain>
→ Shows:
   - What this domain does
   - Available workflows
   - Question types
   - Output formats (documents, code, specs, etc.)
   - Example projects using this domain

/template list [domain]
→ Shows templates organized by domain:
   Business:
     - Startup business plan
     - Product launch strategy
     - Market analysis
   Design:
     - Product design workflow
     - UX research process
     - Brand guideline
   etc.

/template info <template>
→ Shows what's included in template
   - Initial questions
   - Required sections
   - Typical timeline
   - Output format
```

#### 5. Team-Aware CLI Workflows

**Team Management Commands:**
```
/team create <name>
→ Create team with name
→ Generate team ID/invite code

/team list
→ Show all teams you're part of
→ Show your role in each

/team invite <email> [team_id]
→ Invite person to team
→ Send email invitation
→ Set role when joining

/team member list [team_id]
→ Show all team members
→ Show their roles (owner, contributor, reviewer)
→ Show activity

/project share <project_id> <team_id>
→ Share existing project with team
→ Set collaboration mode (edit, review, view)

/collaboration status [project_id]
→ Show who's working on what
→ Show recent changes by team members
→ Show active sessions
```

#### 6. Flexible Output Based on Domain

**Non-Coding Projects Generate Different Outputs:**

**Business Domain:**
```
/project export [format] [project_id]
→ Format options:
   - markdown: Business plan document
   - docx: Word document with formatting
   - pdf: PDF with branding
   - json: Structured data
   - presentation: Slide deck structure
```

**Design Domain:**
```
/project export [format] [project_id]
→ Format options:
   - markdown: Design specification
   - figma: Figma design export (future)
   - pdf: Design presentation
   - json: Design tokens/specs
```

**Research Domain:**
```
/project export [format] [project_id]
→ Format options:
   - markdown: Research report
   - pdf: Professional report
   - json: Structured findings
   - html: Interactive report
```

**Programming Domain:**
```
/project export [format] [project_id]
→ Format options:
   - code: Generated source code (.zip)
   - markdown: Technical specs
   - pdf: Architecture document
   - json: Specification structure
```

#### 7. Non-Coding Session Workflows

**Business Planning Session (Solo):**
```
/session start
→ Domain: Business
→ Workflow: Business Planning
→ Mode: Socratic Questioning

Questions asked by AI:
1. What problem are you solving?
2. Who is your target market?
3. What's your unique value proposition?
4. What are your revenue streams?
5. What's your go-to-market strategy?
...

Output: Business plan specification
```

**Product Design Session (Team):**
```
/session start
→ Domain: Design
→ Workflow: Product Design
→ Mode: Socratic Questioning
→ Team collaboration enabled

Questions:
1. What user problem are we solving?
2. Who are our primary users?
3. What are the key user journeys?
4. What are our design principles?
5. What are success metrics?
...

Output: Product specification + design guidelines
Each team member can contribute answers
See real-time team collaboration
```

**Research Session (Team):**
```
/session start
→ Domain: Research
→ Workflow: Competitive Analysis
→ Mode: Direct Chat (research-focused)
→ Team collaboration enabled

You can ask:
- Comparative questions
- Analysis requests
- Synthesis questions
- Research recommendations

Output: Research report with findings
```

### Modified Command Structure

Instead of just:
```
/project
/session
/document
/specification
```

We need:
```
/domain          (NEW - domain discovery)
/template        (ENHANCE - show templates by domain)
/project         (ENHANCE - domain-aware creation, team-aware)
/session         (ENHANCE - domain-specific workflows)
/team            (NEW - team management)
/collaboration   (NEW - team collaboration status)
/specification   (ENHANCE - domain-specific specs)
/export          (ENHANCE - domain-specific formats)
```

### Implementation in Modular Architecture

The command module structure should be:

```python
cli/commands/
├── domain.py          (NEW - domain discovery)
├── team.py            (NEW - team management)
├── collaboration.py   (NEW - team collaboration)
├── projects.py        (ENHANCE - domain-aware)
├── sessions.py        (ENHANCE - domain-aware)
├── templates.py       (NEW - template system)
├── specifications.py  (ENHANCE - domain-specific)
├── export.py          (ENHANCE - domain-specific formats)
├── documents.py       (NEW - knowledge base)
├── workflows.py       (NEW - workflow management)
...
```

Each command handler can access:
- Current project's domain
- Current team context
- Available domains and workflows
- Domain-specific question sets

### Context Management

CLI State should track:
```python
{
    "current_user": {...},
    "current_project": {
        "id": "...",
        "domain": "business",        # ← DOMAIN-AWARE
        "team_id": "...",            # ← TEAM-AWARE
        "template_used": "..."
    },
    "current_team": {...},           # ← TEAM CONTEXT
    "current_session": {
        "id": "...",
        "domain": "business",        # ← Domain for this session
        "workflow": "business_plan",
        "mode": "socratic"
    }
}
```

### Help System Enhancement

**Main help should show domain info:**
```
/help
→ Shows available domains FIRST
→ Shows typical workflows SECOND
→ Shows commands by category THIRD
→ Shows examples for different use cases
```

**Domain-specific help:**
```
/help business
→ What is Business domain?
→ What can you do with it?
→ Example workflows
→ Example questions
→ Available templates

/help design
→ What is Design domain?
→ What can you do with it?
→ Example workflows
→ Etc.
```

### Examples for Non-Coding Use Cases

#### Use Case 1: Solo Business Planning

```
User starts CLI:
$ python Socrates.py

✓ Logged in as john@example.com

/template list
→ Shows Business templates
  - Startup Business Plan
  - Product Launch Strategy
  - Market Entry Analysis

/project create
→ Choose template: "Startup Business Plan"
→ Name: "My SaaS Idea"
→ Domain: Business (auto-selected from template)
→ Created successfully

/session start
→ Domain: Business
→ Workflow: Startup Planning
→ Mode: Socratic Questioning

AI: "What problem does your product solve?"
User: "Small businesses struggle with scheduling"

AI: "Who would pay to solve this? What customer segment?"
User: "Restaurant owners managing staff schedules"

AI: "What's your unique angle compared to existing tools?"
...continues questioning...

/project export markdown my-saas-idea
→ Generates: "Business_Plan_SaaS.md"
→ Contains: Market analysis, business model, financial projections
```

#### Use Case 2: Team Design Collaboration

```
User A starts CLI:
/team create "Product Team"
→ Team created: team_xyz

/team invite alice@company.com team_xyz
/team invite bob@company.com team_xyz

/project create "Feature Redesign"
→ Domain: Design
→ Team: Product Team
→ Project created and automatically shared

All three start CLI simultaneously:

User A: /session start
→ Domain: Design, Workflow: Design Thinking
→ Mode: Socratic

AI asks: "What user problem are we solving?"
All three can see and contribute to answers
→ Real-time collaboration shown

/collaboration status
→ Shows all team members active
→ Shows what each is working on
→ Shows recent contributions

/specification list
→ Shows design specs being built collaboratively
→ Can see who contributed what

/project export json feature-redesign
→ Generates design spec that all contributed to
```

#### Use Case 3: Team Research Project

```
/team create "Market Research"
/team invite researcher1@company.com
/team invite researcher2@company.com

/project create "Competitive Analysis"
→ Domain: Research
→ Team: Market Research
→ Template: Competitive Landscape Analysis

/session start
→ Domain: Research
→ Workflow: Competitive Analysis
→ Mode: Direct Chat (free-form conversation)

User 1: "Search for SaaS competitors in scheduling"
AI: Returns competitive landscape

User 2: "What are their pricing models?"
AI: Analyzes pricing

User 1: "How do we differentiate?"
AI: Synthesis of competitive advantages

/project export pdf competitive-analysis
→ Generates professional research report
→ Shows all researcher contributions
→ Includes citations
```

## Integration with Modular CLI Architecture

The domain-aware approach **enhances** the modular architecture:

1. **Each command knows project domain**
   - When `/session start` runs, knows if it's Business/Design/etc.
   - Loads domain-specific question sets
   - Displays domain-appropriate outputs

2. **Team context passed to all handlers**
   - Commands can show team-specific info
   - Collaboration commands work together
   - Shared project state across team members

3. **Template system bootstraps projects**
   - Template selection → determines domain
   - Domain determines initial questions
   - Reduces friction for non-coders

4. **Workflows are domain-specific**
   - Business domain workflows != Programming workflows
   - Each domain has appropriate question sequences
   - Outputs match domain context

## Success Criteria for Non-Coding Projects

After implementation:
- ✅ Solo user can create business plan in < 5 minutes
- ✅ Team can create shared design spec collaboratively
- ✅ Research project exports professional report
- ✅ Domain selection clear from project creation
- ✅ All 5+ domains equally usable from CLI
- ✅ Team collaboration seamless from day 1
- ✅ Outputs appropriate to domain (not just code)

## Conclusion

The modular CLI architecture works perfectly for non-coding projects **IF we make it domain-aware and team-first**.

Current architecture: Good foundation
Needed changes:
1. Domain selection in project creation
2. Team creation as core feature (not afterthought)
3. Domain-specific question sets and workflows
4. Flexible output formats per domain
5. Team collaboration surfaced in every workflow
6. Domain registry as user discovery tool

This makes Socrates equally powerful for:
- **Solo user planning business strategy**
- **Team designing product together**
- **Researchers analyzing market landscape**
- **Developers generating code**
- **Any structured thinking project**
