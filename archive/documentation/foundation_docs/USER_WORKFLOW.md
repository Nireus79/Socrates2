# My Understanding: User Workflow

**Purpose:** Demonstrate understanding of HOW users interact with Socrates, step-by-step, with concrete examples

---

## Workflow 1: Starting a New Project (Socratic Mode)

### Step 1: User Creates Project

**User Action:**
```bash
POST /api/projects
{
  "name": "E-commerce Platform",
  "description": "Online store for handmade crafts",
  "project_type": "solo"
}
```

**System Response:**
```json
{
  "success": true,
  "project_id": "proj_abc123",
  "phase": "discovery",
  "maturity_score": 0.0,
  "message": "Project created. Starting Socratic questioning to gather requirements."
}
```

**What Happens Internally:**
1. ProjectManagerAgent creates project
2. Initializes empty specifications
3. Sets phase to "discovery"
4. Creates first session in SOCRATIC mode

---

### Step 2: System Asks First Question

**System Action:**
```
POST /api/sessions/sess_xyz789/question
```

**System Response (to user):**
```json
{
  "question_id": "q_001",
  "text": "What is the primary goal you're trying to achieve with this e-commerce platform?",
  "category": "goals",
  "context": "Understanding your main objective helps us prioritize features and design decisions."
}
```

**What Happens Internally:**
1. OrchestOrator routes to SocraticCounselorAgent
2. SocraticCounselorAgent calls `generate_question` action
3. Agent loads project context (name, description, current specs)
4. Agent loads user context (preferred_communication_style, etc.)
5. Agent builds prompt for Claude API:
   ```
   Project: E-commerce Platform for handmade crafts
   Phase: Discovery (maturity: 0%)
   Specs gathered so far: None
   User communication style: concise

   Generate next question to gather requirements.
   Focus on: goals (not yet covered)
   Keep question concise and direct.
   ```
6. Claude generates question
7. **Quality Control runs:**
   - Checks for solution bias (none found)
   - Checks for leading patterns (none found)
   - Quality score: 0.95 (high quality)
8. Question saved to database
9. Returned to user

---

### Step 3: User Answers Question

**User Action:**
```
POST /api/sessions/sess_xyz789/answer
{
  "question_id": "q_001",
  "answer": "I want to help local artisans sell their products online. They struggle with technology, so the platform needs to be super simple for them to list products and manage orders."
}
```

**What Happens Internally:**

**3.1: Spec Extraction**
1. ContextAnalyzerAgent receives answer
2. Calls Claude API to extract structured specs:
   ```
   User answer: "I want to help local artisans sell their products online..."

   Extract structured specifications from this answer.
   Return JSON format:
   {
     "goals": [...],
     "requirements": [...],
     "constraints": [...],
     "user_segments": [...]
   }
   ```
3. Claude extracts:
   ```json
   {
     "goals": [
       "Help local artisans sell products online",
       "Simplify technology barrier for artisans"
     ],
     "requirements": [
       "Simple product listing interface",
       "Order management system"
     ],
     "constraints": [
       "Must be user-friendly for non-technical users"
     ],
     "user_segments": [
       "Local artisans (sellers)",
       "Buyers of handmade crafts"
     ]
   }
   ```

**3.2: Conflict Detection (Real-Time)**
1. ConflictDetectionService checks each extracted spec against existing database
2. For each new spec:
   - Query: `SELECT * FROM specifications WHERE project_id = 'proj_abc123' AND category = 'goals'`
   - Compare new "Help local artisans..." with existing goals
   - No existing goals yet → No conflict
3. All specs marked as conflict-free

**3.3: Save Specs**
1. Specs saved to database:
   ```sql
   INSERT INTO specifications (project_id, category, key, value, source, confidence)
   VALUES
     ('proj_abc123', 'goals', 'primary_goal', 'Help local artisans...', 'socratic_question', 0.9),
     ('proj_abc123', 'requirements', 'product_listing', 'Simple product listing...', 'socratic_question', 0.85),
     ...
   ```

**3.4: Maturity Update**
1. MaturityCalculator recalculates:
   ```python
   # 10 categories: goals, requirements, tech_stack, scalability, security, ...
   # Current coverage:
   goals: 10/10 (1 goal extracted)
   requirements: 2/10 (2 requirements extracted)
   tech_stack: 0/10
   scalability: 0/10
   ...

   total_maturity = (10 + 2 + 0 + 0 + ...) / 100 = 12%
   ```
2. Project updated: `maturity_score = 12.0`

**System Response (to user):**
```json
{
  "success": true,
  "specs_extracted": 4,
  "conflicts_detected": 0,
  "maturity_score": 12.0,
  "next_question": {
    "question_id": "q_002",
    "text": "Who are the primary users of this platform, and what are their key characteristics?",
    "category": "user_segments"
  }
}
```

---

### Step 4: User Answers Second Question (with Conflict)

**User Action:**
```
POST /api/sessions/sess_xyz789/answer
{
  "question_id": "q_002",
  "answer": "The sellers are local artisans who want to sell internationally to buyers worldwide."
}
```

**What Happens Internally:**

**4.1: Spec Extraction**
Claude extracts:
```json
{
  "goals": [
    "Enable international sales"
  ],
  "requirements": [
    "Multi-currency support",
    "International shipping integration"
  ]
}
```

**4.2: Conflict Detection → CONFLICT FOUND!**
1. ConflictDetectionService checks:
   - Query existing: `SELECT * FROM specifications WHERE category = 'goals'`
   - Existing goal: "Help **local** artisans sell products online"
   - New goal: "Enable **international** sales"
2. Conflict detected:
   ```python
   conflict_type = ConflictType.REQUIREMENTS
   explanation = "Previous answer emphasized 'local artisans', but now mentions 'international sales'. Scale may differ."
   ```
3. Conflict saved to database:
   ```sql
   INSERT INTO conflicts (project_id, conflict_type, old_spec_id, new_spec_value, detected_at, resolution)
   VALUES ('proj_abc123', 'REQUIREMENTS', 'spec_001', 'Enable international sales', NOW(), 'PENDING')
   ```

**System Response (to user) → STOPS AND ASKS:**
```json
{
  "success": false,
  "conflict_detected": true,
  "conflict": {
    "conflict_id": "conf_001",
    "type": "REQUIREMENTS",
    "old_spec": {
      "key": "primary_goal",
      "value": "Help local artisans sell products online",
      "source": "Question #1"
    },
    "new_spec": {
      "value": "Enable international sales to buyers worldwide",
      "source": "Question #2"
    },
    "explanation": "Your previous answer mentioned 'local artisans' selling products, but now you're describing international sales. Should this platform support local-only sales, international sales, or both?",
    "options": {
      "keep_old": "Keep focus on local sales only",
      "replace": "Replace with international sales focus",
      "merge": "Support both local and international",
      "clarify": "Let me explain further"
    }
  }
}
```

---

### Step 5: User Resolves Conflict

**User Action:**
```
POST /api/conflicts/conf_001/resolve
{
  "resolution": "merge",
  "clarification": "Local artisans creating products, but selling to both local and international buyers. Platform needs to support both."
}
```

**What Happens Internally:**

1. ConflictResolutionService processes resolution
2. Updates specifications:
   ```sql
   UPDATE specifications
   SET value = 'Help local artisans sell to both local and international buyers'
   WHERE id = 'spec_001';

   INSERT INTO specifications (project_id, category, key, value)
   VALUES ('proj_abc123', 'requirements', 'multi_currency', 'Support multiple currencies', ...);
   ```
3. Marks conflict as resolved:
   ```sql
   UPDATE conflicts
   SET resolution = 'MERGE', resolved_at = NOW(), resolved_by = 'user_123'
   WHERE id = 'conf_001';
   ```

**System Response:**
```json
{
  "success": true,
  "message": "Conflict resolved. Specifications updated.",
  "updated_specs": [
    "Primary goal updated to reflect both local and international sales",
    "Added requirement: Multi-currency support",
    "Added requirement: International shipping integration"
  ],
  "maturity_score": 18.0,
  "next_question": {
    "question_id": "q_003",
    "text": "What specific features do sellers need to list their products effectively?"
  }
}
```

---

### Step 6: Maturity Reaches 60% → Phase Transition

**After 20 Questions:**

- Maturity score: 61.0%
- Coverage:
  - goals: ✅ 10/10
  - requirements: ✅ 7/10
  - user_segments: ✅ 9/10
  - tech_stack: ⚠️ 3/10 (not enough)
  - scalability: ✅ 6/10
  - security: ✅ 5/10
  - performance: ⚠️ 4/10
  - testing: ⚠️ 2/10
  - monitoring: ⚠️ 1/10
  - disaster_recovery: ⚠️ 0/10

**System Notification:**
```json
{
  "milestone_reached": "ANALYSIS_PHASE",
  "message": "You've reached 61% maturity. Ready to move to Analysis phase for architecture design?",
  "coverage_report": {
    "strong_areas": ["goals", "user_segments", "scalability"],
    "weak_areas": ["tech_stack", "monitoring", "disaster_recovery"],
    "recommendation": "Consider answering a few more questions about technical infrastructure before proceeding."
  },
  "options": {
    "proceed_to_analysis": "Move to architecture design phase",
    "continue_discovery": "Answer more questions to strengthen weak areas"
  }
}
```

**User Action:**
```
POST /api/projects/proj_abc123/phase/transition
{
  "target_phase": "analysis"
}
```

**What Happens:**
1. Phase changes: `discovery → analysis`
2. ArchitectureOptimizerAgent activates
3. System generates architecture recommendations based on specs

---

## Workflow 2: Direct Chat Mode

### Step 1: User Switches to Chat Mode

**User Action:**
```
POST /api/sessions/sess_xyz789/mode
{
  "mode": "chat"
}
```

**System Response:**
```json
{
  "success": true,
  "mode": "chat",
  "message": "Switched to direct chat mode. You can now explain your project freely. I'll extract specifications and detect conflicts in real-time."
}
```

---

### Step 2: User Explains Project Freely

**User Action:**
```
POST /api/sessions/sess_xyz789/chat
{
  "message": "Alright, so here's what I'm thinking. The sellers need a really simple dashboard where they can upload photos, write descriptions, set prices. No complicated stuff. And buyers should be able to browse by category, search, and checkout with Stripe or PayPal. Oh, and I want automatic email notifications when someone makes a purchase."
}
```

**What Happens Internally:**

**2.1: ChatAgent Processes**
1. ChatAgent receives message
2. Calls Claude API to:
   - Respond conversationally
   - Extract specs in background

**2.2: Spec Extraction (Background)**
Claude extracts:
```json
{
  "requirements": [
    "Seller dashboard with photo upload",
    "Product description editor",
    "Price setting interface",
    "Category-based browsing",
    "Search functionality",
    "Checkout integration with Stripe and PayPal",
    "Automatic email notifications on purchase"
  ],
  "tech_stack": [
    "Stripe (payment processor)",
    "PayPal (payment processor)"
  ]
}
```

**2.3: Conflict Detection**
- No conflicts detected

**2.4: Save Specs**
- 7 requirements added
- 2 tech stack items added
- Maturity updated: 61% → 68%

**System Response (Conversational + Spec Summary):**
```json
{
  "response": "Got it! A simple seller dashboard with photo uploads and product management, plus category browsing and search for buyers. You want Stripe and PayPal for payments, with automatic email notifications.\n\nJust to clarify: should sellers be able to manage their own shipping rates, or will the platform handle that centrally?",
  "specs_extracted": 7,
  "conflicts_detected": 0,
  "maturity_score": 68.0
}
```

---

### Step 3: User Continues Conversation (with Contradiction)

**User Action:**
```
POST /api/sessions/sess_xyz789/chat
{
  "message": "Sellers manage their own shipping. Also, I changed my mind about PayPal—let's just use Stripe for now to keep it simple."
}
```

**What Happens Internally:**

**3.1: Spec Extraction**
```json
{
  "requirements": [
    "Sellers manage their own shipping rates"
  ],
  "tech_stack": [
    "Stripe (payment processor) - ONLY"
  ]
}
```

**3.2: Conflict Detection → CONFLICT!**
- Previous spec: "Stripe and PayPal"
- New spec: "Just Stripe"
- Conflict type: TECHNOLOGY

**System Response (In Conversation):**
```json
{
  "response": "Hold on—earlier you mentioned wanting both Stripe *and* PayPal for checkout, but now you're saying just Stripe. Should I remove PayPal from the plan, or did you want to keep it as a future option?",
  "conflict_detected": true,
  "conflict": {
    "type": "TECHNOLOGY",
    "old_value": "Stripe and PayPal",
    "new_value": "Stripe only",
    "quick_resolve": true,
    "options": {
      "stripe_only": "Use only Stripe (remove PayPal)",
      "keep_both": "Keep both Stripe and PayPal",
      "stripe_now_paypal_later": "Stripe for MVP, PayPal in future"
    }
  }
}
```

**User Action:**
```
POST /api/sessions/sess_xyz789/chat
{
  "message": "Yeah, remove PayPal. Just Stripe for now."
}
```

**System Updates:**
- Removes PayPal from tech_stack
- Keeps Stripe
- Adds note: "Future consideration: PayPal integration"
- Conflict resolved

---

## Workflow 3: Code Generation After Maturity Reached

### Step 1: User Requests Code Generation

**Prerequisites:**
- Maturity score: 100% (all categories covered)
- Phase: Implementation
- No pending conflicts

**User Action:**
```
POST /api/projects/proj_abc123/generate
{
  "scope": "full",
  "format": "complete_project"
}
```

---

### Step 2: Quality Control Blocks (Not Ready)

**What Happens Internally:**

1. OrchestOrator routes to CodeGeneratorAgent
2. **Quality Control runs BEFORE code generation:**

```python
# PathOptimizer evaluates readiness
assessment = quality_analyzer.analyze_readiness(project_id)

# Finds gaps:
gaps = [
    "No testing strategy defined",
    "Monitoring/logging not specified",
    "Disaster recovery plan missing"
]

# Generates paths:
paths = path_optimizer.compare_paths("generate_code", project_id)

# Path 1: Generate now (risky)
# - Direct cost: 5000 tokens
# - Rework cost: 3000 tokens (due to missing specs)
# - Total: 8000 tokens
# - Risk: HIGH

# Path 2: Fill gaps first, then generate
# - Gap filling: 1000 tokens
# - Generation: 5000 tokens
# - Rework: 0 tokens
# - Total: 6000 tokens
# - Risk: LOW

# Quality control BLOCKS
is_blocking = True
```

**System Response (Blocked):**
```json
{
  "success": false,
  "blocked_by": "quality_control",
  "reason": "Project not ready for code generation",
  "gaps": [
    {
      "category": "testing",
      "severity": "high",
      "missing": "No testing strategy defined (unit tests, integration tests, e2e tests)"
    },
    {
      "category": "monitoring",
      "severity": "medium",
      "missing": "Monitoring and logging strategy not specified"
    },
    {
      "category": "disaster_recovery",
      "severity": "high",
      "missing": "No disaster recovery or backup plan"
    }
  ],
  "recommendation": {
    "action": "fill_gaps",
    "estimated_time": "5-10 minutes",
    "estimated_cost": "1000 tokens",
    "benefit": "Reduces rework cost by 3000 tokens (saves 2000 tokens total)"
  },
  "options": {
    "fill_gaps_automatically": "Let me ask questions to fill these gaps",
    "fill_gaps_chat": "I'll explain these areas in chat mode",
    "force_generate": "Generate code anyway (not recommended)"
  }
}
```

---

### Step 3: User Fills Gaps

**User Action:**
```
POST /api/projects/proj_abc123/generate
{
  "action": "fill_gaps_chat"
}
```

**System Switches to Chat:**
```json
{
  "mode": "chat",
  "message": "Let's cover these missing areas:\n\n1. Testing: Do you want automated tests included in the codebase? If so, what level (unit tests only, or integration/e2e tests too)?\n\n2. Monitoring: Should the platform include logging and monitoring (e.g., error tracking, performance metrics)?\n\n3. Disaster recovery: How should data backups be handled, and what's acceptable downtime in case of failure?"
}
```

**User Explains:**
```
POST /api/sessions/sess_xyz789/chat
{
  "message": "Yes to all. Include unit tests and integration tests using pytest. For monitoring, use standard Python logging with log levels. For backups, daily automated PostgreSQL backups to S3, and we can tolerate up to 1 hour of downtime for recovery."
}
```

**Specs Extracted:**
- Testing: pytest, unit + integration tests
- Monitoring: Python logging with levels
- Disaster recovery: Daily backups to S3, 1hr RTO

**Maturity: 100% (all gaps filled)**

---

### Step 4: Code Generation (Approved)

**User Action:**
```
POST /api/projects/proj_abc123/generate
{
  "scope": "full"
}
```

**What Happens Internally:**

1. **Quality Control runs again:**
   - All gaps filled ✅
   - Coverage complete ✅
   - No conflicts ✅
   - Risk level: LOW ✅
   - **APPROVED**

2. **CodeGeneratorAgent activates:**

```python
# Load ALL specifications from database
specs = db.get_all_specifications(project_id='proj_abc123')

# Build comprehensive prompt
prompt = f"""
Generate a complete e-commerce platform based on these specifications:

GOALS:
{specs.goals}

REQUIREMENTS:
{specs.requirements}

TECH STACK:
{specs.tech_stack}

ARCHITECTURE:
{specs.architecture}

TESTING:
{specs.testing}

MONITORING:
{specs.monitoring}

... (all 10 categories)

Generate:
1. Project structure
2. Database schema
3. Backend API (FastAPI)
4. Frontend (if specified)
5. Tests (pytest)
6. Docker configuration
7. Deployment scripts
8. README with setup instructions
"""

# Call Claude API (large prompt)
code = claude_client.call(prompt, max_tokens=15000)

# Save generated code
db.save_generated_code(project_id, code)
```

3. **Code Saved and Returned:**

**System Response:**
```json
{
  "success": true,
  "generated_files": 47,
  "structure": {
    "backend": ["app/", "models/", "routes/", "services/", "tests/"],
    "frontend": ["src/", "components/", "pages/"],
    "infrastructure": ["docker-compose.yml", "Dockerfile", "deploy.sh"],
    "docs": ["README.md", "API.md", "SETUP.md"]
  },
  "download_url": "/api/projects/proj_abc123/code/download",
  "repository_url": "https://github.com/user/ecommerce-platform (if GitHub integration enabled)"
}
```

---

## Workflow 4: Team Collaboration

### Step 1: User Adds Team Member

**User Action (Project Owner):**
```
POST /api/projects/proj_abc123/collaborators
{
  "email": "developer@example.com",
  "role": "backend_developer",
  "permissions": ["read_specs", "answer_questions", "generate_code"]
}
```

**System Response:**
```json
{
  "success": true,
  "collaborator_id": "collab_456",
  "message": "Invitation sent to developer@example.com"
}
```

---

### Step 2: Collaborator Joins and Gets Role-Specific Questions

**Collaborator Action:**
```
POST /api/sessions (new session)
{
  "project_id": "proj_abc123",
  "user_id": "user_789",
  "mode": "socratic"
}
```

**System Behavior:**
- Detects user role: `backend_developer`
- Generates role-specific questions:

**Question for Backend Developer:**
```json
{
  "question_id": "q_050",
  "text": "What database indexes should be created for the product search functionality to ensure fast queries?",
  "category": "technical_implementation",
  "role_specific": "backend_developer"
}
```

**vs.**

**Question for Frontend Developer (different role):**
```json
{
  "question_id": "q_051",
  "text": "What user interactions should trigger loading states on the product listing page?",
  "category": "user_experience",
  "role_specific": "frontend_developer"
}
```

---

### Step 3: Inter-Member Conflict Detected

**Backend Developer Answers:**
```
POST /api/sessions/sess_abc123/answer
{
  "answer": "We should use MySQL for the database because I have more experience with it."
}
```

**System Detects Conflict:**
- Previous spec (from owner): `tech_stack.database = "PostgreSQL"`
- New spec (from developer): `tech_stack.database = "MySQL"`
- Conflict type: TECHNOLOGY (inter-member)

**System Response:**
```json
{
  "conflict_detected": true,
  "conflict": {
    "type": "TECHNOLOGY",
    "member_conflict": true,
    "old_spec": {
      "value": "PostgreSQL",
      "specified_by": "owner@example.com (Project Owner)",
      "role": "product_owner"
    },
    "new_spec": {
      "value": "MySQL",
      "specified_by": "developer@example.com (Backend Developer)",
      "role": "backend_developer"
    },
    "explanation": "Team members disagree on database choice. Project owner specified PostgreSQL, but backend developer suggests MySQL.",
    "resolution_options": {
      "keep_postgresql": "Keep PostgreSQL (owner's choice)",
      "switch_to_mysql": "Switch to MySQL (developer's preference)",
      "discuss": "Notify both members to discuss",
      "owner_decides": "Let owner make final decision"
    }
  }
}
```

**System Notifies Both Members:**
- Email/notification sent to owner
- Conflict marked as `PENDING_TEAM_RESOLUTION`

---

## Workflow 5: Switching Between Modes Mid-Session

### User in Socratic Mode, Switches to Chat

**Current State:**
- Mode: Socratic
- Questions asked: 15
- Maturity: 45%

**User Action:**
```
POST /api/sessions/sess_xyz789/mode
{
  "mode": "chat"
}
```

**System Response:**
```json
{
  "success": true,
  "mode_switched": "socratic → chat",
  "message": "Switched to chat mode. Feel free to explain anything, and I'll continue extracting specifications.",
  "context_preserved": true,
  "maturity_score": 45.0
}
```

**User Can Now:**
- Explain freely in paragraphs
- Ask questions back to system
- Provide specs in any order
- System still extracts specs and detects conflicts

**Switching Back:**
```
POST /api/sessions/sess_xyz789/mode
{
  "mode": "socratic"
}
```

**System:**
```json
{
  "mode_switched": "chat → socratic",
  "message": "Switched back to Socratic mode. I'll continue asking structured questions.",
  "next_question": {
    "text": "You mentioned payment processing earlier. Should the platform support subscription-based payments in addition to one-time purchases?"
  }
}
```

---

## Summary: Key User Workflow Principles

1. **Persistent Context:** All specs stored, never forgotten across sessions
2. **Real-Time Conflict Detection:** System stops and asks user to resolve contradictions
3. **Maturity-Gated:** Can't generate code until enough specs gathered
4. **Quality Control Gates:** System blocks premature decisions
5. **Mode Flexibility:** Switch between Socratic and Chat anytime
6. **Team Aware:** Different questions per role, inter-member conflict resolution
7. **Conversational:** In chat mode, feels like conversation but extracts specs in background

---

**Next:** Read MY_UNDERSTANDING_SYSTEM_WORKFLOW.md for internal processing details
