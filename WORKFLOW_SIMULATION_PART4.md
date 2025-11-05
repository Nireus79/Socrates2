# User Workflow Simulation - Part 4: Conflict Resolution & Maturity Building

**Continued from Part 3:** Conflict detected (SQLite vs National expansion), user must resolve.

---

## 10. Conflict Resolution

### User Action:
```bash
Your choice: 1

Reason: Makes sense. We definitely need multi-user support for an e-commerce platform.
PostgreSQL is the right choice.
```

### System Internal Processing:

**Step 1: ConflictDetectorAgent resolves conflict**
```python
# Location: backend/app/agents/conflict_detector.py
def _resolve_conflict(self, data):
    conflict_id = data['conflict_id']
    chosen_option = data['option']  # 'A'
    reason = data['reason']

    # 1. Load conflict
    conflict = db.query(Conflict).get(conflict_id)

    solutions = json.loads(conflict.solutions)
    chosen_solution = [s for s in solutions if s['option'] == chosen_option][0]

    # 2. Update the conflicting specification
    # spec_013 (database: SQLite) → PostgreSQL
    spec = db.query(Specification).get(conflict.spec_a_id)

    old_value = spec.value
    spec.value = chosen_solution['solution']
    spec.updated_at = datetime.utcnow()
    spec.resolution_note = f"Changed from {old_value} due to conflict with national expansion goal"

    db.commit()

    # 3. Mark conflict as resolved
    conflict.status = 'resolved'
    conflict.resolution = chosen_solution['solution']
    conflict.resolution_reason = reason
    conflict.resolved_at = datetime.utcnow()

    db.commit()

    # 4. Log resolution in conversation history
    resolution_log = ConversationHistory(
        id=uuid4(),
        session_id=data['session_id'],
        type='conflict_resolution',
        content=f"Conflict resolved: Changed database from {old_value} to PostgreSQL. Reason: {reason}",
        metadata={
            'conflict_id': str(conflict.id),
            'old_value': old_value,
            'new_value': spec.value,
            'chosen_option': chosen_option
        },
        created_at=datetime.utcnow()
    )

    db.add(resolution_log)
    db.commit()

    # 5. Re-check for new conflicts (none in this case)
    new_conflicts = _detect_conflicts({'project_id': conflict.project_id})

    return {
        'success': True,
        'conflict_resolved': True,
        'spec_updated': {
            'id': str(spec.id),
            'old_value': old_value,
            'new_value': spec.value
        },
        'new_conflicts': new_conflicts['conflicts']
    }
```

**Step 2: Database State**
```sql
-- Table: specifications (updated)
UPDATE specifications
SET value = 'PostgreSQL',
    updated_at = '2025-11-05 14:43:00',
    resolution_note = 'Changed from SQLite due to conflict with national expansion goal'
WHERE id = 'spec_013';

-- Table: conflicts (resolved)
UPDATE conflicts
SET status = 'resolved',
    resolution = 'PostgreSQL',
    resolution_reason = 'Makes sense. We definitely need multi-user support...',
    resolved_at = '2025-11-05 14:43:00'
WHERE id = 'conflict_001';

-- Table: conversation_history (log resolution)
INSERT INTO conversation_history (id, session_id, type, content, metadata, created_at)
VALUES ('msg_007', 'sess_001', 'conflict_resolution',
        'Conflict resolved: Changed database from SQLite to PostgreSQL. Reason: Makes sense...',
        '{"conflict_id": "conflict_001", "old_value": "SQLite", "new_value": "PostgreSQL", "chosen_option": "A"}',
        '2025-11-05 14:43:00');
```

### User Feedback:
```
✅ Conflict resolved!

Updated Specification:
  • Database: SQLite → PostgreSQL ✓

Resolution recorded:
  Changed to PostgreSQL for multi-user support needed for national expansion.

Checking for new conflicts... ✓ No new conflicts detected.

All conflicts resolved (1 total)

Current Status:
  • Maturity: 16%
  • Unresolved conflicts: 0
  • Phase: Discovery

You can continue adding specifications, or check status with /status

Continue in Direct Chat mode: _
```

---

## 11. User Continues Adding Specs

### User Action:
```bash
Your message: Artisans should be able to upload product photos (up to 5 per product).
Buyers should be able to search products by category and filter by price range. We need
an admin dashboard for us to monitor sales and manage disputes between buyers and sellers.
```

### System Internal Processing:

**Step 1: Extract specifications**
```python
# ContextAnalyzerAgent extracts:
extracted = {
    "specifications": [
        {
            "category": "requirements",
            "key": "product_photos",
            "value": "Product photo upload (up to 5 per product)",
            "confidence": 0.95
        },
        {
            "category": "requirements",
            "key": "product_search",
            "value": "Search products by category",
            "confidence": 0.9
        },
        {
            "category": "requirements",
            "key": "price_filtering",
            "value": "Filter products by price range",
            "confidence": 0.9
        },
        {
            "category": "requirements",
            "key": "admin_dashboard",
            "value": "Admin dashboard for sales monitoring",
            "confidence": 0.9
        },
        {
            "category": "requirements",
            "key": "dispute_management",
            "value": "Manage disputes between buyers and sellers",
            "confidence": 0.85
        },
        {
            "category": "tech_stack",
            "key": "file_storage",
            "value": "File storage system (for photos)",
            "confidence": 0.8
        },
        {
            "category": "tech_stack",
            "key": "search_functionality",
            "value": "Search and filtering system",
            "confidence": 0.8
        }
    ]
}

# Save specs: spec_018 through spec_024
```

**Step 2: Check conflicts**
```python
# ConflictDetectorAgent checks all new specs
# No conflicts found - all compatible with existing specs
```

**Step 3: Update maturity**
```python
# Requirements: 5 more specs (total 8) → 80%
# Tech stack: 2 more specs (total 6) → 60%

# Overall: (40 + 80 + 20 + 20 + 60 + 0 + 0 + 0 + 0 + 0) / 10 = 22%
```

**Step 4: Database State**
```sql
-- 7 new specifications
INSERT INTO specifications (...)
VALUES
  ('spec_018', 'proj_001', 'requirements', 'product_photos', 'Product photo upload...', ...),
  ('spec_019', 'proj_001', 'requirements', 'product_search', 'Search products by category', ...),
  ('spec_020', 'proj_001', 'requirements', 'price_filtering', 'Filter products by price range', ...),
  ('spec_021', 'proj_001', 'requirements', 'admin_dashboard', 'Admin dashboard...', ...),
  ('spec_022', 'proj_001', 'requirements', 'dispute_management', 'Manage disputes...', ...),
  ('spec_023', 'proj_001', 'tech_stack', 'file_storage', 'File storage system...', ...),
  ('spec_024', 'proj_001', 'tech_stack', 'search_functionality', 'Search and filtering...', ...);
```

### User Feedback:
```
✅ Specifications extracted (7 new specs):
  • Requirements: Product photos (5 per product), Search by category, Price filtering,
                  Admin dashboard, Dispute management
  • Tech stack: File storage, Search functionality

✓ No conflicts detected

Maturity updated: 16% → 22%
  • Requirements: 40% → 80% (+40%) 🎯 Almost complete!
  • Tech stack: 40% → 60% (+20%)

Great progress! Requirements category is almost complete.

Still missing coverage:
  • Scalability: 0% ⚠️ (How many users? Traffic expectations?)
  • Security: 0% ⚠️ (HTTPS? Data encryption? PCI compliance for payments?)
  • Testing: 0% ⚠️ (Testing strategy? Quality assurance?)
  • Deployment: 0% ⚠️ (Cloud provider? CI/CD pipeline?)
  • Monitoring: 0% ⚠️ (Error tracking? Performance monitoring?)
  • Team structure: 0% ⚠️ (Solo project? Team size?)
  • Timeline: 0% ⚠️ (Deadlines? Milestones?)

⚠️ Need 60% overall maturity to advance to Analysis phase (currently at 22%)

Recommendations:
  • /toggle to Socratic mode for guided questions on missing areas
  • Continue in Direct Chat with focused input on missing categories
  • /status to see detailed breakdown

Continue: _
```

---

## 12. Check Status

### User Action:
```bash
> /status
```

### System Internal Processing:

**Step 1: Calculate detailed status**
```python
# Location: backend/app/services/maturity_service.py
def get_project_status(project_id):
    project = db.query(Project).get(project_id)

    # Get all maturity scores
    maturity = db.query(MaturityTracking).filter_by(
        project_id=project_id
    ).all()

    maturity_by_category = {m.category: m.score for m in maturity}

    # Count specifications per category
    specs = db.query(Specification).filter_by(project_id=project_id).all()
    specs_by_category = {}
    for spec in specs:
        specs_by_category[spec.category] = specs_by_category.get(spec.category, 0) + 1

    # Count conflicts
    all_conflicts = db.query(Conflict).filter_by(project_id=project_id).all()
    unresolved = [c for c in all_conflicts if c.status == 'unresolved']
    resolved = [c for c in all_conflicts if c.status == 'resolved']

    # Calculate overall maturity
    overall = sum(maturity_by_category.values()) / len(maturity_by_category)

    # Check if can advance phase
    can_advance = overall >= 60 and len(unresolved) == 0

    return {
        'project_id': str(project.id),
        'project_name': project.name,
        'phase': project.phase,
        'overall_maturity': round(overall, 1),
        'can_advance': can_advance,
        'categories': [
            {
                'name': cat,
                'score': round(maturity_by_category[cat], 1),
                'spec_count': specs_by_category.get(cat, 0),
                'status': 'complete' if maturity_by_category[cat] >= 80 else
                         'good' if maturity_by_category[cat] >= 60 else
                         'needs_work' if maturity_by_category[cat] > 0 else
                         'missing'
            }
            for cat in sorted(maturity_by_category.keys())
        ],
        'conflicts': {
            'total': len(all_conflicts),
            'resolved': len(resolved),
            'unresolved': len(unresolved)
        },
        'total_specs': len(specs),
        'time_in_phase': (datetime.utcnow() - project.created_at).total_seconds() / 60
    }
```

### User Feedback:
```
════════════════════════════════════════════════════════════
                    PROJECT STATUS REPORT
════════════════════════════════════════════════════════════

Project: E-commerce Platform (proj_001)
Owner: john_developer
Created: 12 minutes ago

Phase: Discovery (1 of 4)
Overall Maturity: 22.0% ⚠️ (Need ≥60% to advance)

Can advance to Analysis? ❌ No
  Reason: Maturity below 60% threshold

════════════════════════════════════════════════════════════
                   CATEGORY BREAKDOWN
════════════════════════════════════════════════════════════

✅ Requirements: 80% (8 specs) - Almost done!
   Specs: mobile_payments, performance, authentication, product_photos,
          product_search, price_filtering, admin_dashboard, dispute_management

✅ Tech stack: 60% (6 specs) - Good progress
   Specs: frontend (React), backend (Django), database (PostgreSQL),
          payment_provider (Stripe), file_storage, search_functionality

⚠️ Goals: 40% (4 specs) - Needs more
   Specs: primary_goal, market_scope_start, market_scope_expansion,
          product_categories

⚠️ User segments: 20% (2 specs) - Needs more
   Specs: sellers, sellers_detail

⚠️ Constraints: 20% (2 specs) - Needs more
   Specs: ux_simplicity, tech_literacy

❌ Scalability: 0% (0 specs) - MISSING
   Needed: Expected users, traffic patterns, growth projections

❌ Security: 0% (0 specs) - MISSING ⚠️ CRITICAL
   Needed: HTTPS, encryption, PCI compliance, auth security, data protection

❌ Testing: 0% (0 specs) - MISSING
   Needed: Testing strategy, QA process, coverage requirements

❌ Deployment: 0% (0 specs) - MISSING
   Needed: Cloud provider, CI/CD, hosting, infrastructure

❌ Monitoring: 0% (0 specs) - MISSING
   Needed: Error tracking, performance monitoring, logging

❌ Team structure: 0% (0 specs) - MISSING
   Needed: Team size, roles, responsibilities

❌ Timeline: 0% (0 specs) - MISSING
   Needed: Deadlines, milestones, launch date

════════════════════════════════════════════════════════════
                      CONFLICT STATUS
════════════════════════════════════════════════════════════

Total conflicts: 1
  ✅ Resolved: 1 (SQLite → PostgreSQL)
  ✓ Unresolved: 0

════════════════════════════════════════════════════════════
                   PROGRESS SUMMARY
════════════════════════════════════════════════════════════

Total specifications: 24
Time in Discovery phase: 12 minutes
Sessions: 1 (Direct Chat mode)

What you've accomplished:
  ✓ Strong requirements coverage (80%)
  ✓ Good tech stack foundation (60%)
  ✓ All conflicts resolved
  ✓ Clear goals and user segments defined

What's still needed:
  ⚠️ 7 categories have zero coverage
  ⚠️ Security is critical for e-commerce (PCI compliance required)
  ⚠️ Scalability needs definition before architecture
  ⚠️ 38 percentage points to reach 60% threshold

════════════════════════════════════════════════════════════
                     RECOMMENDATIONS
════════════════════════════════════════════════════════════

Option 1: Focused approach (30-40 min to 60%)
  /toggle → Switch to Socratic mode
  System will guide through missing categories with targeted questions
  Estimated: 15-20 questions to reach 60%

Option 2: Bulk input (15-20 min to 60%)
  Continue in Direct Chat mode
  Provide comprehensive details on:
    • Security requirements
    • Scalability expectations
    • Testing strategy
    • Deployment preferences
    • Monitoring needs
    • Team info
    • Timeline

Option 3: Hybrid approach (25-30 min to 60%)
  Use Direct Chat for areas you know
  /toggle for Socratic on complex areas (security, scalability)

════════════════════════════════════════════════════════════

Choose approach or continue adding specs: _
```

---

## Summary of Part 4

### What Happened:
1. ✅ Conflict resolved (User chose PostgreSQL)
2. ✅ Specification updated (SQLite → PostgreSQL)
3. ✅ Conflict marked resolved in database
4. ✅ User added 7 more specs (requirements + tech stack)
5. ✅ No new conflicts detected
6. ✅ Maturity increased (16% → 22%)
7. ✅ Detailed status report generated

### Database State After Part 4:

**socrates_specs updates:**
- 1 specification updated (spec_013: SQLite → PostgreSQL)
- 7 new specification records (spec_018 through spec_024)
- 1 conflict resolved (conflict_001)
- 2 conversation_history records (resolution log, user message)
- Total specs: 24
- Total conflicts: 1 (all resolved)

### Current Maturity Breakdown:
```
Requirements: 80% (8 specs) ✅
Tech stack: 60% (6 specs) ✅
Goals: 40% (4 specs) ⚠️
User segments: 20% (2 specs) ⚠️
Constraints: 20% (2 specs) ⚠️
Scalability: 0% ❌
Security: 0% ❌
Testing: 0% ❌
Deployment: 0% ❌
Monitoring: 0% ❌
Team structure: 0% ❌
Timeline: 0% ❌

Overall: 22%
```

### Key System Features Demonstrated:

1. **Conflict Resolution Flow:**
   - User presented with options
   - User chooses solution
   - Spec automatically updated
   - Conflict marked resolved
   - Resolution logged for audit

2. **Continuous Conflict Checking:**
   - After resolution, system re-checks
   - No new conflicts from PostgreSQL choice
   - Always validates entire spec set

3. **Intelligent Status Reporting:**
   - Category-by-category breakdown
   - Identifies missing areas
   - Estimates time to goals
   - Suggests next actions

4. **Maturity Tracking:**
   - Dynamic calculation after each spec
   - Clear thresholds (60% to advance)
   - Identifies which categories need work

### Agents Used:
1. **ConflictDetectorAgent** - Resolution, re-checking
2. **ContextAnalyzerAgent** - Continued spec extraction
3. **MaturityService** - Status calculation
4. **ProjectManagerAgent** - Status reporting

### Next: Part 5
- User continues to 60% maturity (fast-forward)
- Phase advancement (Discovery → Analysis)
- Phase gate verification
- System prepares for Analysis phase

---

**Reference:**
- [WORKFLOW_SIMULATION_PART3.md](./WORKFLOW_SIMULATION_PART3.md) - Previous part
- [VISION.md](./VISION.md) - Maturity system requirement (lines 329-350)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Maturity calculation logic
