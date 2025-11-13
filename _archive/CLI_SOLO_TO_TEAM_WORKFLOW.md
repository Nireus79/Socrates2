# CLI Solo-to-Team Project Workflow

## Question: How Does CLI Handle Solo vs Team Projects?

The user is asking: **Does a project start as solo and team members get added by administrator, or what?**

This is a critical architectural decision that affects:
- Project creation workflow
- Permission model
- Team member management
- Collaboration features
- Data access and sharing

---

## Proposed Model: Flexible Solo-to-Team Transition

### Principle: **Start Simple, Grow Organically**

A project can:
1. **Start as solo** - Single user working alone
2. **Grow to team** - Same user adds team members later
3. **Start as team** - User creates team+project together
4. **Scale to organization** - Admin manages teams at org level

---

## Project Types in Socrates

### Type 1: Solo Project

**Definition:** Project owned and worked on by a single user

**Created via:**
```
/project create
→ "Working solo or with team? [solo/team]"
→ Choose: solo
→ Project created, only you can access
```

**Permissions:**
- Owner: Can do everything
- Others: No access (by default)

**Can become team project?** YES
```
Owner later decides: /project add-member alice@company.com
→ Project becomes team project
→ Alice gets access with specified role
```

**Example Use Cases:**
- Individual learning project
- Solo business planning
- Personal research
- Private prototype

### Type 2: Team Project

**Definition:** Project owned by user/team, worked on by multiple people

**Created via (Option A - Create solo, then add team):**
```
/project create
→ Solo project created first
→ /project add-member alice@company.com
→ /project add-member bob@company.com
→ Gradually becomes team project
```

**Created via (Option B - Create with team from start):**
```
/team create "Product Team"
→ Team created

/project create
→ "Which team owns this? [personal/Product Team]"
→ Choose: Product Team
→ Project auto-shared with all team members
→ Everyone has access immediately
```

**Permissions:**
- Owner: Full control, can invite/remove members, change roles
- Contributors: Can edit project, add specs, create sessions
- Reviewers: Can review specs, but can't modify
- Viewers: Read-only access

**Can become solo again?** YES (kind of)
```
Owner removes all members:
/project remove-member alice@company.com
/project remove-member bob@company.com
→ Back to solo project
```

**Example Use Cases:**
- Product design team collaboration
- Business strategy planning with partners
- Development team working on API specs
- Research team analyzing market

### Type 3: Organization Project

**Definition:** Project managed by organization administrator

**Created via (Admin-managed):**
```
/admin team create "Engineering Team"
→ Admin creates team

/admin team invite alice@company.com "Engineering Team"
/admin team invite bob@company.com "Engineering Team"
→ Admin invites members

Users then:
/team list
→ See "Engineering Team" they belong to

/project create
→ Create projects within team context
→ Owned by team, not individual
```

**Note:** This is future scope (Phase 2+), not required for MVP

---

## CLI Workflows: The Complete Picture

### Scenario 1: Solo User Learning Socrates

```
Day 1: Learn as individual
$ python Socrates.py
/register
→ Create account

/domain list
→ Explore domains

/template list business
→ Find "Startup Business Plan" template

/project create
→ "Working solo or with team? [solo/team]"
→ Choose: solo
→ Name: "My SaaS Idea"
→ Solo project created
→ Only you can access

/session start
→ Socratic questions for business planning
→ Build business plan specification

/export markdown my-saas-idea
→ Download business plan as markdown
→ Share with trusted advisors (outside Socrates)

Status: SOLO PROJECT
```

### Scenario 2: Solo → Team Transition

```
Day 5: Want to add co-founder to project
/project list
→ Shows "My SaaS Idea" (solo, only you)

/project select 1
→ Select "My SaaS Idea"

/project add-member sarah@company.com
→ Invite co-founder
→ Optional: Set role (contributor/reviewer/viewer)
→ Sarah gets email invitation

/project add-member investor@company.com
→ Optional: Add investor as reviewer
→ Investor can see specs, can comment
→ But can't modify

Status: NOW A TEAM PROJECT
→ Sarah sees project in her list
→ Investor sees project in their list (read-only)

Day 6: Collaborate
Sarah:
/project list
→ Sees "My SaaS Idea" (shared with her, she's contributor)

/project select "my-saas-idea"
→ Select shared project

/session start
→ Continues Socratic session
→ Her answers merged with yours

/collaboration status
→ Shows both you and Sarah online
→ Shows contributions from each

Investor:
/project list
→ Sees "My SaaS Idea" (shared, read-only)

/specification list my-saas-idea
→ Can read specs
→ Can add comments/reviews
→ Cannot modify

/project archive my-saas-idea
→ NOT ALLOWED (not owner)
→ Investor can't delete/modify
```

### Scenario 3: Team Created First

```
Day 1: Organize team, then work
/team create "Product Team"
→ Team ID: team_xyz
→ Invite code: ABC123

/team invite alice@company.com team_xyz
/team invite bob@company.com team_xyz
→ Invitations sent

Day 2: Alice and Bob accept invitations
/team list
→ Shows "Product Team"

Day 3: Owner creates project for team
/project create
→ Name: "Feature Redesign"
→ Domain: Design
→ Team: Product Team
→ Project auto-shared with all team members

All three members:
/project list
→ See "Feature Redesign" (team project)
→ Alice and Bob are contributors
→ Can all edit

/session start
→ Same collaborative session
→ Real-time collaboration

/collaboration status
→ All three online
→ Each person's contributions visible
```

### Scenario 4: Adding/Removing Team Members

```
Current setup: Project with 3 team members

Owner:
/project member-add email@newperson.com
→ person added as contributor
→ Gets access immediately
→ Email invitation sent

/project member-remove old@person.com
→ person removed
→ Loses access to project
→ Can still see in history if needed

/project member-role sarah@company.com reviewer
→ Sarah's role changed from contributor to reviewer
→ Now can only comment/review, not edit

/project member-list
→ Shows all team members and their roles
```

---

## Permission Model

### Role-Based Access Control (RBAC)

| Action | Owner | Contributor | Reviewer | Viewer |
|--------|-------|-------------|----------|--------|
| **Edit project** | ✅ | ✅ | ❌ | ❌ |
| **Create sessions** | ✅ | ✅ | ❌ | ❌ |
| **Answer questions** | ✅ | ✅ | ❌ | ❌ |
| **Create specs** | ✅ | ✅ | ❌ | ❌ |
| **Edit specs** | ✅ | ✅ | ❌ | ❌ |
| **Approve specs** | ✅ | ⚠️* | ✅ | ❌ |
| **Review/comment** | ✅ | ✅ | ✅ | ✅ |
| **View project** | ✅ | ✅ | ✅ | ✅ |
| **Invite members** | ✅ | ❌ | ❌ | ❌ |
| **Remove members** | ✅ | ❌ | ❌ | ❌ |
| **Change roles** | ✅ | ❌ | ❌ | ❌ |
| **Delete project** | ✅ | ❌ | ❌ | ❌ |
| **Archive project** | ✅ | ❌ | ❌ | ❌ |

*Contributors can mark specs as "complete" but not formally "approve"

---

## CLI Commands for Managing Solo/Team Transitions

### Project Creation (Domain-Aware)

```
/project create
→ Name: "My Project"
→ Domain: [business/design/code/research]
→ Working solo or with team? [solo/team]

  If solo:
    → Project created, private to you

  If team:
    → Create new team or use existing? [new/existing]

    If new:
      → Team name: "My Team"
      → Team created
      → Project shared with team

    If existing:
      → Which team? [list of your teams]
      → Select team
      → Project shared with team members
```

### Solo Project Commands

```
/project list [solo]
→ Shows only your solo projects

/project add-member <email> [project_id] [role]
→ Invite person to solo project
→ Makes it a team project
→ Optional: Set role (contributor/reviewer/viewer)
→ Default role: contributor

/project remove-member <email> [project_id]
→ Remove person from project
→ If last member is you: reverts to solo
→ Otherwise: stays team project
```

### Team Project Commands

```
/project list [team]
→ Shows only team projects

/project list [team_id]
→ Shows projects for specific team

/project member-list [project_id]
→ Shows all team members on this project
→ Shows their roles
→ Shows when they joined

/project member-add <email> [project_id] [role]
→ Add person to existing team project
→ Must be member of team first
→ Or: invite to team first, then add to project

/project member-remove <email> [project_id]
→ Remove person from project
→ They stay in team, just lose project access

/project member-role <email> [project_id] [role]
→ Change role: contributor/reviewer/viewer
→ Only owner can change roles
```

### Team Commands

```
/team create <name>
→ Create new team
→ Team ID auto-generated
→ You are owner

/team list
→ Shows all teams you belong to
→ Shows your role in each

/team info <team_id>
→ Shows team details
→ Shows all members
→ Shows all projects in team

/team invite <email> [team_id]
→ Invite person to team
→ Person sees team in their list after accepting
→ Can then be added to team projects

/team member-list [team_id]
→ Shows all team members
→ Shows their roles

/team member-add <email> [team_id] [role]
→ Add person to team
→ Optional email invitation sent
→ Default role: member (can create projects)

/team member-remove <email> [team_id]
→ Remove person from team
→ They lose access to all team projects

/team member-role <email> [team_id] [role]
→ Change person's role in team
→ Roles: owner, member, viewer
→ Only team owner can change roles
```

---

## State Transitions Diagram

```
                    ┌─────────────────┐
                    │  Solo Project   │
                    │   (You only)    │
                    └────────┬────────┘
                             │
                             │ /project add-member
                             │
                             ▼
                    ┌─────────────────┐
                    │  Team Project   │
                    │ (Multiple users)│
                    └────────┬────────┘
                             │
                             │ /project remove-member (all but you)
                             │
                             ▼
                    ┌─────────────────┐
                    │  Solo Project   │
                    │   (Back to you) │
                    └─────────────────┘
```

---

## Context in CLI State

The CLI tracks:

```python
{
    "user": {
        "id": "...",
        "email": "user@company.com",
        "teams": ["team_xyz", "team_abc"]  # Teams they belong to
    },

    "current_project": {
        "id": "...",
        "name": "My SaaS Idea",
        "domain": "business",

        # CRITICAL: Is this solo or team?
        "is_team_project": False,  # or True
        "team_id": None,           # or "team_xyz"
        "owner_id": "...",         # Who owns it?
        "members": [],             # or [alice, bob]

        # Can current user modify?
        "is_owner": True,          # Can I edit/add members?
        "role": "owner",           # or contributor, reviewer, viewer
        "can_edit": True,
        "can_add_members": True,
        "can_delete": True
    },

    "current_team": {
        "id": "team_xyz",
        "name": "Product Team",
        "members": [alice, bob, charlie],
        "my_role": "owner"         # My role in team
    }
}
```

---

## Key Decision Points

### Decision 1: Who Can Add Team Members?

**Options:**
1. **Only Project Owner** - Security, clear responsibility
2. **Any Contributor** - Easier, but can be chaotic
3. **Owner + Admins** - Hybrid approach

**Recommendation:** Only project owner
- Clear responsibility
- Security: owner controls who sees project
- If project shared to team, team owner controls members
- Later: Org admins can override

### Decision 2: Solo vs Team at Project Creation

**Options:**
1. **Always ask** - "Solo or team?" at creation
2. **Detect from context** - If team selected, auto-team
3. **Default to solo** - Ask only if they want team
4. **Smart default** - If user has teams, ask; if not, solo

**Recommendation:** Ask explicitly
```
/project create
→ Name, description, domain
→ "Working solo or with team? [solo/team]"
→ Clear, explicit, prevents confusion
```

### Decision 3: Can Solo Project Become Team?

**Options:**
1. **Yes, easily** - `/project add-member` converts it
2. **Only via creation** - Must recreate as team project
3. **Manual conversion** - `/project convert-to-team`

**Recommendation:** Easy conversion via `/project add-member`
- Organic growth pattern
- User starts simple, adds collaborators later
- No friction or recreating

### Decision 4: Team Ownership

**Options:**
1. **User owns project, team doesn't** - User is central
2. **Team owns project, user doesn't** - Team is central
3. **Both** - User + Team can own

**Recommendation:** User is initial owner
- User creates team and project
- User invites others
- User controls access
- Later: Can transfer ownership to team/org
- Flexible: Works for solo and team

### Decision 5: Admin Role Needed?

**For MVP:** No organization admin
- Users create own teams
- Users invite own members
- Works for small groups

**For Scale (Phase 2+):** Yes, org admin
- Admin manages org teams
- Admin manages org members
- Admin controls access policies
- Users self-serve within org structure

---

## Typical User Journeys

### Journey 1: Solo User (No Team)
```
1. /register
2. /project create (solo)
3. /session start
4. Work alone
5. /export
6. Done

No team involvement
```

### Journey 2: Solo → Collaboration
```
1. /register
2. /project create (solo)
3. /session start
4. Work alone for days/weeks
5. /project add-member alice@company.com
   → Project becomes team project
6. /collaboration status
   → Now working with Alice
7. /export
   → Both contributed
```

### Journey 3: Team from Start
```
1. /register
2. /team create "Product Team"
3. /team invite alice@company.com
4. Alice /register + accepts invite
5. /project create (team: "Product Team")
6. /session start (collaborative)
7. Both contribute to same project
8. /export
```

### Journey 4: Multiple Teams
```
1. /register
2. /team create "Team A"
3. /team create "Team B"
4. /team invite people to each
5. /project create team=A
6. /project create team=B
7. Different projects in different teams
8. Work separately or together
```

---

## CLI Workflow Overview

```
AUTHENTICATION
├─ /register (create account)
├─ /login (authenticate)
└─ /logout (sign out)

TEAM MANAGEMENT (NEW)
├─ /team create [name]
├─ /team list
├─ /team invite [email]
├─ /team member-list
├─ /team member-add/remove/role
└─ /team info

PROJECT MANAGEMENT (ENHANCED)
├─ /project create [solo/team]
├─ /project list [solo/team/team_id]
├─ /project select
├─ /project info
├─ /project add-member [email] [role]       ← SOLO→TEAM
├─ /project remove-member [email]           ← TEAM→SOLO
├─ /project member-list
├─ /project member-role [email] [role]
├─ /project manage [actions]
├─ /project archive/restore/destroy
└─ /project share [team_id]

COLLABORATION (NEW)
├─ /collaboration status
├─ /collaboration activity
├─ /collaboration members
└─ /collaboration notifications

SESSION & WORK (UNCHANGED)
├─ /session start
├─ /session select
├─ /session end
└─ /history

EXPORT (ENHANCED)
├─ /export [format]
└─ Shows contributors if team project
```

---

## Summary: Solo-to-Team Model

**For your question: "Does project start as solo and team members are added?"**

**Answer: YES, with flexibility**

1. **Projects CAN start solo**
   - User creates solo project
   - Only they have access
   - Can work alone indefinitely

2. **Projects CAN start as team**
   - User creates team first
   - Invites team members
   - Creates team project
   - All share from day 1

3. **Projects CAN transition**
   - Start solo, add members later
   - Easy conversion: `/project add-member`
   - Organic growth pattern

4. **Ownership is clear**
   - Project owner controls access
   - Only owner can add/remove members
   - Owner is source of truth

5. **Roles enable flexibility**
   - Contributor: Can edit
   - Reviewer: Can comment/review
   - Viewer: Read-only
   - Owner: Control everything

6. **This handles both**
   - Solo developers working alone
   - Teams collaborating together
   - Flexible transitions between them

**In the CLI:**
- When creating project: "Solo or team? [solo/team]"
- Easy to switch: `/project add-member` converts solo → team
- Team features optional, not mandatory
- Same platform works for both

This model is **inclusive** (supports both solo and team), **flexible** (can transition), and **clear** (obvious who controls what).
