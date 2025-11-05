# User Workflow Simulation - Part 2: Socratic Questioning & Spec Extraction

**Continued from Part 1:** Project created, first session started in Socratic mode.

---

## 4. First Socratic Question Generation

### System Internal Processing:

**Step 1: AgentOrchestrator routes to SocraticCounselorAgent**
```python
# Automatically triggered after project creation
orchestrator.route_request(
    agent_id='socratic',
    action='generate_question',
    data={
        'project_id': 'proj_001',
        'session_id': 'sess_001',
        'user_id': 'user_001'
    }
)
```

**Step 2: SocraticCounselorAgent prepares question**
```python
# Location: backend/app/agents/socratic_counselor.py
def _generate_question(self, data):
    # 1. Load project context
    project = self.db.query(Project).get(data['project_id'])

    context = {
        'name': project.name,  # "E-commerce Platform"
        'description': project.description,  # "Online marketplace..."
        'phase': project.phase  # "discovery"
    }

    # 2. Load maturity tracking
    maturity = self.db.query(MaturityTracking).filter_by(
        project_id=data['project_id']
    ).all()

    maturity_scores = {m.category: m.score for m in maturity}
    # All at 0% - need to start somewhere

    # 3. Determine which category to ask about
    # Priority order: goals > requirements > tech_stack > ...
    # Choose 'goals' (highest priority, 0% coverage)

    # 4. Load user preferences
    user_rules = self.db.query(UserRules).filter_by(
        user_id=data['user_id']
    ).first()

    preferences = user_rules.rules
    # {'communication_style': 'concise', 'preferred_roles': ['pm', 'backend']}

    # 5. Build prompt for Claude API
    prompt = f"""
You are acting as a Project Manager (PM) for a Socratic questioning session.

Project Context:
- Name: {context['name']}
- Description: {context['description']}
- Phase: {context['phase']}
- Current Maturity: 0%

Maturity Coverage:
- Goals: 0% (URGENT - start here)
- Requirements: 0%
- Tech Stack: 0%
- All other categories: 0%

User Preferences:
- Communication style: {preferences['communication_style']}
- Preferred roles: {preferences['preferred_roles']}

Task:
Generate ONE Socratic question to understand the PRIMARY GOAL of this project.

Requirements:
1. Focus on understanding WHAT problem they're solving
2. Keep it concise (communication style preference)
3. Ask from PM perspective (their preferred role)
4. Don't assume technical knowledge
5. Don't suggest solutions
6. Open-ended question

Format response as:
{{
  "question": "your question here",
  "role": "pm",
  "category": "goals",
  "context_hint": "brief explanation of why this matters"
}}
"""

    # 6. Call Claude API
    response = self.anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    question_data = json.loads(response.content[0].text)

    # Example response:
    question_data = {
        "question": "What is the primary goal you're trying to achieve with this e-commerce platform?",
        "role": "pm",
        "category": "goals",
        "context_hint": "Understanding your main objective helps us prioritize features and design decisions."
    }

    # 7. Quality Control check
    quality_result = self.orchestrator.route_request(
        agent_id='quality',
        action='analyze_question',
        data={'question': question_data['question']}
    )

    # Quality checks performed:
    quality_checks = {
        'solution_bias': False,       # ✓ No suggested solution
        'leading_question': False,    # ✓ Not leading
        'technology_bias': False,     # ✓ No tech assumption
        'assumes_expertise': False,   # ✓ No expertise assumed
        'vagueness': 0.1,            # ✓ Clear question
        'quality_score': 0.92        # ✓ High quality
    }

    # 8. Save question to database
    question_record = ConversationHistory(
        id=uuid4(),
        session_id=data['session_id'],
        type='question',
        content=question_data['question'],
        role=question_data['role'],
        metadata={
            'category': question_data['category'],
            'context_hint': question_data['context_hint'],
            'quality_score': quality_checks['quality_score']
        },
        created_at=datetime.utcnow()
    )

    self.db.add(question_record)
    self.db.commit()

    return {
        'success': True,
        'question_id': str(question_record.id),
        'question': question_data['question'],
        'role': question_data['role'],
        'category': question_data['category'],
        'context_hint': question_data['context_hint']
    }
```

**Step 3: Database State**
```sql
-- Table: conversation_history
INSERT INTO conversation_history (id, session_id, type, content, role, metadata, created_at)
VALUES ('msg_002', 'sess_001', 'question',
        'What is the primary goal you''re trying to achieve with this e-commerce platform?',
        'pm',
        '{"category": "goals", "context_hint": "Understanding your main objective...", "quality_score": 0.92}',
        '2025-11-05 14:36:00');
```

### User Feedback:
```
📋 Question 1 (Project Manager)

What is the primary goal you're trying to achieve with this e-commerce platform?

💡 Context: Understanding your main objective helps us prioritize features and design decisions.

Your answer: _
```

---

## 5. User Answers (Vague Answer)

### User Action:
```bash
Your answer: Help artisans sell their products online
```

### System Internal Processing:

**Step 1: Save user's answer**
```python
# Save to database
answer_record = ConversationHistory(
    id=uuid4(),
    session_id='sess_001',
    type='answer',
    content='Help artisans sell their products online',
    role='user',
    metadata={'question_id': 'msg_002'},
    created_at=datetime.utcnow()
)

db.add(answer_record)
db.commit()
```

**Step 2: AgentOrchestrator routes to ContextAnalyzerAgent**
```python
orchestrator.route_request(
    agent_id='context',
    action='extract_specifications',
    data={
        'session_id': 'sess_001',
        'question_id': 'msg_002',
        'answer': 'Help artisans sell their products online'
    }
)
```

**Step 3: ContextAnalyzerAgent extracts specs**
```python
# Location: backend/app/agents/context_analyzer.py
def _extract_specifications(self, data):
    # 1. Load conversation context
    question = self.db.query(ConversationHistory).get(data['question_id'])

    # 2. Build prompt for Claude API
    prompt = f"""
You are analyzing a user's answer to extract structured specifications.

Question: {question.content}
Answer: {data['answer']}

Task: Extract all specifications from this answer.

Output format:
{{
  "specifications": [
    {{
      "category": "goals|requirements|constraints|assumptions|user_segments|tech_stack",
      "key": "descriptive_key",
      "value": "extracted value",
      "confidence": 0.0-1.0
    }}
  ],
  "completeness_score": 0.0-1.0,
  "vagueness_detected": ["list of specific gaps or vague areas"],
  "follow_up_needed": true|false,
  "suggested_follow_ups": ["specific questions to ask"]
}}
"""

    # 3. Call Claude API
    response = self.anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    extracted = json.loads(response.content[0].text)

    # Example extraction:
    extracted = {
        "specifications": [
            {
                "category": "goals",
                "key": "primary_goal",
                "value": "Enable artisans to sell products online",
                "confidence": 0.7
            },
            {
                "category": "user_segments",
                "key": "sellers",
                "value": "Artisans",
                "confidence": 0.6
            },
            {
                "category": "user_segments",
                "key": "buyers",
                "value": "Buyers (implied)",
                "confidence": 0.5
            }
        ],
        "completeness_score": 0.3,  # Low! Answer was vague
        "vagueness_detected": [
            "What kind of artisans? (jewelry, pottery, textiles, etc.)",
            "What scale? (local community, regional, national, international?)",
            "What's their tech experience level?",
            "What products specifically?"
        ],
        "follow_up_needed": true,
        "suggested_follow_ups": [
            "Can you tell me more about the type of artisans you're targeting?",
            "Are you thinking local, national, or international reach?",
            "What's the technical skill level of your target artisans?"
        ]
    }

    # 4. Save specifications to database
    saved_specs = []
    for spec in extracted['specifications']:
        spec_record = Specification(
            id=uuid4(),
            project_id=question.session.project_id,
            category=spec['category'],
            key=spec['key'],
            value=spec['value'],
            source='socratic_question',
            confidence=spec['confidence'],
            created_at=datetime.utcnow()
        )
        self.db.add(spec_record)
        saved_specs.append(spec_record)

    self.db.commit()

    # 5. Check for conflicts (none yet - first specs)
    conflicts = self.orchestrator.route_request(
        agent_id='conflict',
        action='detect_conflicts',
        data={'project_id': question.session.project_id}
    )

    # 6. Update maturity tracking
    # Goals category: 1 spec extracted
    maturity = self.db.query(MaturityTracking).filter_by(
        project_id=question.session.project_id,
        category='goals'
    ).first()

    # Calculate score: 1 spec with confidence 0.7 = 10% coverage
    maturity.score = 10.0
    maturity.last_updated = datetime.utcnow()
    self.db.commit()

    # Overall maturity: (10 + 0 + 0 + ... + 0) / 10 = 1%

    return {
        'success': True,
        'specs_extracted': len(saved_specs),
        'specifications': [
            {'category': s.category, 'key': s.key, 'value': s.value}
            for s in saved_specs
        ],
        'completeness_score': extracted['completeness_score'],
        'vagueness_detected': extracted['vagueness_detected'],
        'follow_up_needed': extracted['follow_up_needed'],
        'maturity_updated': {
            'goals': 10.0,
            'overall': 1.0
        },
        'conflicts': conflicts['conflicts']
    }
```

**Step 4: Database State**
```sql
-- Table: conversation_history
INSERT INTO conversation_history (id, session_id, type, content, role, metadata, created_at)
VALUES ('msg_003', 'sess_001', 'answer',
        'Help artisans sell their products online',
        'user',
        '{"question_id": "msg_002"}',
        '2025-11-05 14:37:00');

-- Table: specifications (3 specs extracted)
INSERT INTO specifications (id, project_id, category, key, value, source, confidence, created_at)
VALUES
  ('spec_001', 'proj_001', 'goals', 'primary_goal',
   'Enable artisans to sell products online', 'socratic_question', 0.7, '2025-11-05 14:37:00'),
  ('spec_002', 'proj_001', 'user_segments', 'sellers',
   'Artisans', 'socratic_question', 0.6, '2025-11-05 14:37:00'),
  ('spec_003', 'proj_001', 'user_segments', 'buyers',
   'Buyers (implied)', 'socratic_question', 0.5, '2025-11-05 14:37:00');

-- Table: maturity_tracking (updated)
UPDATE maturity_tracking
SET score = 10.0, last_updated = '2025-11-05 14:37:00'
WHERE project_id = 'proj_001' AND category = 'goals';
```

### User Feedback:
```
✅ Answer recorded and analyzed.

Specifications extracted:
  • Goal: Enable artisans to sell products online
  • User segments: Artisans (sellers), Buyers

Maturity updated: 0% → 1%
  • Goals: 0% → 10% (+10%)

⚠️ Vagueness detected (completeness: 30%)

Your answer was somewhat vague. I detected these gaps:
  • What kind of artisans? (jewelry, pottery, textiles, etc.)
  • What scale? (local community, regional, national, international?)
  • What's their tech experience level?
  • What products specifically?

I'll ask a follow-up question to clarify these areas.

Generating follow-up...
```

---

## 6. Follow-up Question (Addressing Vagueness)

### System Internal Processing:

**Step 1: SocraticCounselorAgent generates targeted follow-up**
```python
def _generate_question(self, data):
    # Context includes previous answer and detected vagueness

    prompt = f"""
Previous question: {previous_question}
User answer: {previous_answer}
Vagueness detected: {vagueness_list}

Generate a follow-up question that addresses the vagueness.
Be specific. Ask about the gaps we identified.
"""

    # Claude generates:
    question = "Let's get more specific. What kind of artisans are you targeting, and are you thinking local community, nationwide, or international reach?"
```

### User Feedback:
```
📋 Question 2 (Project Manager)

Let's get more specific. What kind of artisans are you targeting, and are you thinking
local community, nationwide, or international reach?

💡 Context: This will help us determine the scale and complexity of the platform.

Your answer: _
```

---

## 7. User Answers (Detailed Answer)

### User Action:
```bash
Your answer: We're targeting local artisans in our city who make handmade jewelry,
pottery, and textiles. We want to start local but eventually expand to the whole country.
Most of these artisans are not tech-savvy, many are older, so the platform needs to be
extremely simple for them to use.
```

### System Internal Processing:

**Step 1: ContextAnalyzerAgent extracts specs**
```python
# Much better extraction from detailed answer:
extracted = {
    "specifications": [
        {
            "category": "goals",
            "key": "market_scope_start",
            "value": "Start with local artisans in our city",
            "confidence": 0.9
        },
        {
            "category": "goals",
            "key": "market_scope_expansion",
            "value": "Expand to national (whole country)",
            "confidence": 0.85
        },
        {
            "category": "goals",
            "key": "product_categories",
            "value": "Handmade jewelry, pottery, textiles",
            "confidence": 0.95
        },
        {
            "category": "user_segments",
            "key": "sellers_detail",
            "value": "Local artisans (not tech-savvy, older demographic)",
            "confidence": 0.9
        },
        {
            "category": "constraints",
            "key": "ux_simplicity",
            "value": "Extremely simple interface required",
            "confidence": 0.95
        },
        {
            "category": "constraints",
            "key": "tech_literacy",
            "value": "Low tech literacy target users",
            "confidence": 0.9
        },
        {
            "category": "requirements",
            "key": "ease_of_use",
            "value": "Platform must be easy to use for non-tech-savvy users",
            "confidence": 0.9
        }
    ],
    "completeness_score": 0.85,  # Much better!
    "vagueness_detected": [],
    "follow_up_needed": false
}
```

**Step 2: Save all specifications**
```sql
-- 7 new specs (spec_004 through spec_010)
INSERT INTO specifications (...)
VALUES
  ('spec_004', 'proj_001', 'goals', 'market_scope_start', 'Start with local artisans...', ...),
  ('spec_005', 'proj_001', 'goals', 'market_scope_expansion', 'Expand to national...', ...),
  ('spec_006', 'proj_001', 'goals', 'product_categories', 'Handmade jewelry, pottery, textiles', ...),
  ('spec_007', 'proj_001', 'user_segments', 'sellers_detail', 'Local artisans (not tech-savvy...)', ...),
  ('spec_008', 'proj_001', 'constraints', 'ux_simplicity', 'Extremely simple interface...', ...),
  ('spec_009', 'proj_001', 'constraints', 'tech_literacy', 'Low tech literacy...', ...),
  ('spec_010', 'proj_001', 'requirements', 'ease_of_use', 'Platform must be easy to use...', ...);
```

**Step 3: Update maturity**
```python
# Goals: 4 specs → 40% (was 10%)
# User segments: 2 specs → 20% (was 0%)
# Constraints: 2 specs → 20% (was 0%)
# Requirements: 1 spec → 10% (was 0%)

# Overall: (40 + 10 + 20 + 20 + 0 + 0 + 0 + 0 + 0 + 0) / 10 = 9%
```

### User Feedback:
```
✅ Excellent! Much more detailed answer.

Specifications extracted (7 new specs):
  • Goals: Start local, expand nationally
  • Product categories: Handmade jewelry, pottery, textiles
  • User segments: Local artisans (not tech-savvy, older demographic)
  • Constraints: Extremely simple interface, low tech literacy
  • Requirements: Easy to use for non-tech-savvy users

Maturity updated: 1% → 9%
  • Goals: 10% → 40% (+30%)
  • User segments: 0% → 20% (+20%)
  • Constraints: 0% → 20% (+20%)
  • Requirements: 0% → 10% (+10%)

✓ No vagueness detected (completeness: 85%)
✓ No conflicts detected

Generating next question (focus: Requirements)...
```

---

## Summary of Part 2

### What Happened:
1. ✅ First Socratic question generated (PM role, goals category)
2. ✅ User answered (vague) → System detected vagueness
3. ✅ Specifications extracted (3 specs, low confidence)
4. ✅ Follow-up question generated (addressed gaps)
5. ✅ User answered (detailed) → Much better extraction
6. ✅ Specifications extracted (7 more specs, high confidence)
7. ✅ Maturity updated (0% → 9%)
8. ✅ Quality control checked questions (no bias detected)

### Database State After Part 2:

**socrates_specs additions:**
- 10 specification records (spec_001 through spec_010)
- 4 conversation_history records (2 questions, 2 answers)
- maturity_tracking updated (4 categories now have coverage)

### Key Features Demonstrated:
- ✅ **Vagueness detection** - System identified gaps in first answer
- ✅ **Adaptive questioning** - Follow-up addressed specific gaps
- ✅ **Completeness scoring** - 30% vs 85% completeness
- ✅ **Quality control** - Questions checked for bias before showing
- ✅ **Dynamic maturity** - Updates after each answer
- ✅ **Multiple categories** - Extracted from one answer (goals, segments, constraints, requirements)

### Agents Used:
1. **SocraticCounselorAgent** - Question generation
2. **ContextAnalyzerAgent** - Spec extraction
3. **QualityControlAgent** - Question quality checking
4. **ConflictDetectorAgent** - Conflict checking (none found yet)
5. **MaturityService** - Score calculation

### Next: Part 3
- User toggles to Direct Chat mode
- User adds tech stack specs
- CONFLICT DETECTED (SQLite incompatibility)
- Conflict resolution workflow

---

**Reference:**
- [WORKFLOW_SIMULATION_PART1.md](./WORKFLOW_SIMULATION_PART1.md) - Previous part
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Agent architecture
- [VISION.md](./VISION.md) - Vagueness detection requirement
