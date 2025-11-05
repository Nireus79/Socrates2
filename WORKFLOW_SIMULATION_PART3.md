# User Workflow Simulation - Part 3: Direct Chat & Conflict Detection

**Continued from Part 2:** Maturity at 9%, 10 specs gathered through Socratic questioning.

---

## 8. Toggle to Direct Chat Mode

### User Action:
```bash
> /toggle

Reason: I want to add some specific technical requirements quickly without Q&A
```

### System Internal Processing:

**Step 1: SessionService updates mode**
```python
# Location: backend/app/services/session_service.py
def toggle_mode(session_id, reason=None):
    session = db.query(Session).get(session_id)

    # Toggle mode
    new_mode = 'direct_chat' if session.mode == 'socratic' else 'socratic'

    session.mode = new_mode
    session.updated_at = datetime.utcnow()
    db.commit()

    # Log the toggle
    history = ConversationHistory(
        id=uuid4(),
        session_id=session_id,
        type='mode_toggle',
        content=f'Switched from {session.mode} to {new_mode}. Reason: {reason}',
        created_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()

    return {'success': True, 'new_mode': new_mode}
```

**Step 2: Database State**
```sql
-- Table: sessions (updated)
UPDATE sessions
SET mode = 'direct_chat', updated_at = '2025-11-05 14:40:00'
WHERE id = 'sess_001';

-- Table: conversation_history (log toggle)
INSERT INTO conversation_history (id, session_id, type, content, created_at)
VALUES ('msg_005', 'sess_001', 'mode_toggle',
        'Switched from socratic to direct_chat. Reason: I want to add some specific...',
        '2025-11-05 14:40:00');
```

### User Feedback:
```
✅ Mode switched: Socratic → Direct Chat

In Direct Chat mode you can:
  • Provide specifications directly
  • Add multiple requirements at once
  • System still extracts structured specs
  • System still detects conflicts
  • System still updates maturity

The system will NOT ask follow-up questions unless it detects critical vagueness.

Type your requirements: _
```

---

## 9. Direct Chat Input (User Adds Tech Stack)

### User Action:
```bash
Your message: We need to support mobile payments via Stripe. The platform should use
React for frontend and Django for backend. We want it to be lightning fast, so let's use
SQLite for the database since it's faster. Also need user authentication with email/password.
```

### System Internal Processing:

**Step 1: Save user message**
```sql
INSERT INTO conversation_history (id, session_id, type, content, role, created_at)
VALUES ('msg_006', 'sess_001', 'message',
        'We need to support mobile payments via Stripe. The platform should use React...',
        'user', '2025-11-05 14:41:00');
```

**Step 2: ContextAnalyzerAgent extracts specifications**
```python
# Location: backend/app/agents/context_analyzer.py
def _extract_specifications(self, data):
    # Build prompt
    prompt = f"""
User message in Direct Chat:
"{data['message']}"

Extract ALL specifications mentioned.
Format: {{specifications: [...], completeness_score: 0-1}}
"""

    # Claude extracts:
    extracted = {
        "specifications": [
            {
                "category": "tech_stack",
                "key": "frontend",
                "value": "React",
                "confidence": 0.95
            },
            {
                "category": "tech_stack",
                "key": "backend",
                "value": "Django",
                "confidence": 0.95
            },
            {
                "category": "tech_stack",
                "key": "database",
                "value": "SQLite",
                "confidence": 0.95
            },
            {
                "category": "tech_stack",
                "key": "payment_provider",
                "value": "Stripe",
                "confidence": 0.95
            },
            {
                "category": "requirements",
                "key": "mobile_payments",
                "value": "Support mobile payments via Stripe",
                "confidence": 0.9
            },
            {
                "category": "requirements",
                "key": "performance",
                "value": "Lightning fast performance",
                "confidence": 0.85
            },
            {
                "category": "requirements",
                "key": "authentication",
                "value": "User authentication with email/password",
                "confidence": 0.95
            }
        ],
        "completeness_score": 0.8
    }

    # Save all specs
    saved_specs = []
    for spec in extracted['specifications']:
        spec_record = Specification(
            id=uuid4(),
            project_id=data['project_id'],
            category=spec['category'],
            key=spec['key'],
            value=spec['value'],
            source='direct_chat',
            confidence=spec['confidence'],
            created_at=datetime.utcnow()
        )
        db.add(spec_record)
        saved_specs.append(spec_record)

    db.commit()
    # Now we have spec_011 through spec_017

    return {
        'success': True,
        'specs_extracted': 7,
        'specifications': saved_specs
    }
```

**Step 3: ConflictDetectorAgent checks for conflicts**
```python
# Location: backend/app/agents/conflict_detector.py
def _detect_conflicts(self, data):
    project_id = data['project_id']

    # Load ALL specifications for this project
    all_specs = db.query(Specification).filter_by(
        project_id=project_id
    ).all()

    # Build a map of specs by category
    specs_by_category = {}
    for spec in all_specs:
        if spec.category not in specs_by_category:
            specs_by_category[spec.category] = []
        specs_by_category[spec.category].append(spec)

    conflicts = []

    # Check new spec: spec_013 (database = SQLite)
    sqlite_spec = [s for s in all_specs if s.key == 'database'][0]

    # Check against goals
    expansion_spec = [s for s in all_specs if s.key == 'market_scope_expansion'][0]

    # CONFLICT DETECTED!
    # SQLite = single-user only
    # Expansion to national = multi-user required

    conflict_analysis = {
        "type": "technology",
        "severity": "high",
        "spec_a": sqlite_spec,
        "spec_b": expansion_spec,
        "reason": "SQLite is single-user database, incompatible with multi-user e-commerce platform needed for national expansion",
        "detection_method": "technology_compatibility_check"
    }

    # Call Claude API for detailed conflict analysis
    prompt = f"""
Analyze this potential technology conflict:

Specification A: {sqlite_spec.value} (category: {sqlite_spec.category})
Specification B: {expansion_spec.value} (category: {expansion_spec.category})

Does this create a conflict? Explain why or why not.
If conflict exists, provide:
1. Why it's a problem
2. Impact severity
3. Recommended solutions (3-4 options)
"""

    # Claude responds:
    conflict_detail = {{
        "is_conflict": True,
        "explanation": "SQLite is a file-based, single-process database. It cannot handle concurrent connections from multiple users. An e-commerce platform expanding nationally will have hundreds or thousands of simultaneous users (buyers browsing, sellers updating inventory, admins managing). This is fundamentally incompatible with SQLite's architecture.",
        "severity": "high",
        "impact": [
            "System will fail under concurrent load",
            "Data corruption risk with multiple writers",
            "Cannot scale beyond single server",
            "Transaction failures during high traffic"
        ],
        "solutions": [
            {
                "option": "A",
                "solution": "Use PostgreSQL",
                "pros": ["Handles thousands of concurrent connections", "ACID compliant", "Production-ready", "Excellent for e-commerce"],
                "cons": ["Slightly more complex setup than SQLite"],
                "recommendation_score": 0.95
            },
            {
                "option": "B",
                "solution": "Use MySQL",
                "pros": ["Handles concurrent connections", "Widely used for e-commerce", "Good performance"],
                "cons": ["Less extensible than PostgreSQL", "Weaker JSON support"],
                "recommendation_score": 0.75
            },
            {
                "option": "C",
                "solution": "Keep SQLite, remove expansion goal",
                "pros": ["Simple setup", "Good for prototype"],
                "cons": ["Cannot expand", "Abandons core business goal"],
                "recommendation_score": 0.10
            },
            {
                "option": "D",
                "solution": "Use MongoDB (NoSQL)",
                "pros": ["Scales horizontally", "Flexible schema"],
                "cons": ["No ACID transactions (critical for payments)", "Overkill for relational data"],
                "recommendation_score": 0.40
            }
        ]
    }}

    # Save conflict to database
    conflict_record = Conflict(
        id=uuid4(),
        project_id=project_id,
        type='technology',
        severity='high',
        status='unresolved',
        spec_a_id=sqlite_spec.id,
        spec_b_id=expansion_spec.id,
        description=conflict_detail['explanation'],
        impact=json.dumps(conflict_detail['impact']),
        solutions=json.dumps(conflict_detail['solutions']),
        detected_at=datetime.utcnow()
    )

    db.add(conflict_record)
    db.commit()

    conflicts.append(conflict_record)

    return {
        'conflicts_found': len(conflicts),
        'conflicts': [
            {
                'id': str(c.id),
                'type': c.type,
                'severity': c.severity,
                'description': c.description,
                'spec_a': {'id': c.spec_a_id, 'value': sqlite_spec.value},
                'spec_b': {'id': c.spec_b_id, 'value': expansion_spec.value},
                'solutions': json.loads(c.solutions)
            }
            for c in conflicts
        ]
    }
```

**Step 4: Update maturity (before conflict resolution)**
```python
# Tech stack: 4 new specs (React, Django, SQLite, Stripe) → 40%
# Requirements: 3 new specs (payments, performance, auth) → 40%

# Overall: (40 + 40 + 20 + 20 + 40 + 0 + 0 + 0 + 0 + 0) / 10 = 16%
```

**Step 5: Database State**
```sql
-- Table: specifications (7 new specs)
INSERT INTO specifications (...)
VALUES
  ('spec_011', 'proj_001', 'tech_stack', 'frontend', 'React', 'direct_chat', 0.95, ...),
  ('spec_012', 'proj_001', 'tech_stack', 'backend', 'Django', 'direct_chat', 0.95, ...),
  ('spec_013', 'proj_001', 'tech_stack', 'database', 'SQLite', 'direct_chat', 0.95, ...),
  ('spec_014', 'proj_001', 'tech_stack', 'payment_provider', 'Stripe', 'direct_chat', 0.95, ...),
  ('spec_015', 'proj_001', 'requirements', 'mobile_payments', 'Support mobile payments via Stripe', 'direct_chat', 0.9, ...),
  ('spec_016', 'proj_001', 'requirements', 'performance', 'Lightning fast performance', 'direct_chat', 0.85, ...),
  ('spec_017', 'proj_001', 'requirements', 'authentication', 'User authentication with email/password', 'direct_chat', 0.95, ...);

-- Table: conflicts (1 conflict detected)
INSERT INTO conflicts (id, project_id, type, severity, status, spec_a_id, spec_b_id, description, impact, solutions, detected_at)
VALUES ('conflict_001', 'proj_001', 'technology', 'high', 'unresolved',
        'spec_013', 'spec_005',
        'SQLite is a file-based, single-process database. It cannot handle concurrent connections...',
        '["System will fail under concurrent load", "Data corruption risk..."]',
        '[{"option": "A", "solution": "Use PostgreSQL", ...}]',
        '2025-11-05 14:41:00');

-- Table: maturity_tracking (updated)
UPDATE maturity_tracking
SET score = 40.0, last_updated = '2025-11-05 14:41:00'
WHERE project_id = 'proj_001' AND category = 'tech_stack';

UPDATE maturity_tracking
SET score = 40.0, last_updated = '2025-11-05 14:41:00'
WHERE project_id = 'proj_001' AND category = 'requirements';
```

### User Feedback:
```
✅ Message received and analyzed.

Specifications extracted (7 new specs):
  • Tech stack: React (frontend), Django (backend), SQLite (database), Stripe (payments)
  • Requirements: Mobile payments, Lightning fast performance, Email/password auth

Maturity updated: 9% → 16%
  • Tech stack: 0% → 40% (+40%)
  • Requirements: 10% → 40% (+30%)

⚠️⚠️⚠️ CONFLICT DETECTED! (High Severity) ⚠️⚠️⚠️

═══════════════════════════════════════════════════════════

Conflict ID: conflict_001
Type: Technology Incompatibility
Severity: HIGH
Status: UNRESOLVED

Problem:
You specified SQLite as the database, but you also stated you want to
expand nationally.

SQLite is a file-based, single-process database. It cannot handle concurrent
connections from multiple users. An e-commerce platform expanding nationally
will have hundreds or thousands of simultaneous users (buyers browsing, sellers
updating inventory, admins managing).

This is fundamentally incompatible with SQLite's architecture.

Conflicting Specifications:
  ┌─ Specification A (spec_013)
  │  Category: Tech Stack
  │  Value: SQLite
  │  Added: Just now (direct chat)
  │
  └─ Specification B (spec_005)
     Category: Goals
     Value: Expand to national (whole country)
     Added: 4 minutes ago (socratic question)

Impact if not resolved:
  • System will fail under concurrent load
  • Data corruption risk with multiple writers
  • Cannot scale beyond single server
  • Transaction failures during high traffic

Recommended Solutions:
───────────────────────────────────────────────────────────

Option A: Use PostgreSQL (Recommended: 95%)
  ✓ Handles thousands of concurrent connections
  ✓ ACID compliant for safe transactions
  ✓ Production-ready and battle-tested
  ✓ Excellent for e-commerce platforms
  ✗ Slightly more complex setup than SQLite

Option B: Use MySQL (Score: 75%)
  ✓ Handles concurrent connections well
  ✓ Widely used for e-commerce
  ✓ Good performance
  ✗ Less extensible than PostgreSQL
  ✗ Weaker JSON support (if needed later)

Option C: Keep SQLite, remove expansion goal (Score: 10%)
  ✓ Simple setup
  ✓ Good for small prototype
  ✗ Cannot expand beyond local
  ✗ Abandons your core business goal

Option D: Use MongoDB (NoSQL) (Score: 40%)
  ✓ Scales horizontally
  ✓ Flexible schema
  ✗ No ACID transactions (CRITICAL for payments)
  ✗ Overkill for relational e-commerce data

═══════════════════════════════════════════════════════════

⚠️ You must resolve this conflict before advancing to Analysis phase.

What would you like to do?
  1 - Accept Option A (PostgreSQL) [RECOMMENDED]
  2 - Accept Option B (MySQL)
  3 - Accept Option C (Keep SQLite, remove expansion)
  4 - Accept Option D (MongoDB)
  5 - Provide alternative solution
  6 - Get more details about options

Your choice: _
```

---

## Summary of Part 3

### What Happened:
1. ✅ User toggled to Direct Chat mode
2. ✅ User added 7 specs in one message (tech stack + requirements)
3. ✅ Specs extracted from free-form text
4. 🔴 **CONFLICT DETECTED** (Technology incompatibility: SQLite vs National expansion)
5. ✅ Conflict analyzed by Claude API
6. ✅ 4 solution options generated with pros/cons
7. ✅ User prompted to resolve before proceeding

### Database State After Part 3:

**socrates_specs additions:**
- 7 new specification records (spec_011 through spec_017)
- 1 conflict record (conflict_001, unresolved)
- 2 conversation_history records (mode toggle, user message)
- maturity_tracking updated (tech_stack 40%, requirements 40%)

### Critical Feature: Conflict Detection

**How it works:**
1. Every time specs are added, ConflictDetectorAgent runs
2. Checks new specs against ALL existing specs
3. Uses Claude API for deep conflict analysis
4. Generates multiple solution options with scores
5. **BLOCKS** phase advancement until resolved

**Types of conflicts checked:**
- ✅ Technology (demonstrated: SQLite incompatibility)
- ⏳ Requirements (contradicting requirements)
- ⏳ Timeline (over-subscribed schedule)
- ⏳ Resources (insufficient capacity)

### Key System Behaviors:

1. **Real-time detection** - Conflict found immediately after spec added
2. **Detailed analysis** - Claude explains WHY it's a problem
3. **Impact assessment** - Shows consequences of ignoring
4. **Multiple solutions** - 4 options with scoring
5. **User choice** - System recommends, user decides
6. **Blocking gate** - Cannot advance phase with unresolved conflicts

### Agents Used:
1. **SessionService** - Mode toggling
2. **ContextAnalyzerAgent** - Extracted 7 specs from free-form text
3. **ConflictDetectorAgent** - Detected SQLite incompatibility
4. **Claude API** - Conflict analysis, solution generation

### Next: Part 4
- User resolves conflict (chooses PostgreSQL)
- Specification updated
- Conflict marked resolved
- User continues adding specs
- More maturity progress

---

**Reference:**
- [WORKFLOW_SIMULATION_PART2.md](./WORKFLOW_SIMULATION_PART2.md) - Previous part
- [VISION.md](./VISION.md) - Conflict detection requirement (lines 54-62)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - ConflictDetectorAgent design
