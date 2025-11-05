# My Understanding: System Internal Workflow

**Purpose:** Demonstrate understanding of HOW Socrates processes user input internally, with concrete examples showing data flow

---

## Internal Workflow 1: Question Generation Process

### Flow Diagram
```
User needs question
       ↓
FastAPI endpoint: POST /api/sessions/{id}/question
       ↓
AgentOrchestrator.route_request(agent_id='socratic', action='generate_question')
       ↓
[Quality Control Check]
  - Is this a major operation? YES
  - Run QualityAnalyzer
       ↓
SocraticCounselorAgent._generate_question()
  - Load project context from database
  - Load user behavior profile
  - Build prompt for Claude
  - Call Claude API
       ↓
Claude API returns question
       ↓
[Quality Control Post-Check]
  - Analyze question for bias
  - Check coverage gaps
  - Generate alternatives if biased
       ↓
Save question to database
       ↓
Return to user
```

---

### Detailed Step-by-Step

#### Step 1: Request Arrives

**FastAPI Endpoint:**
```python
@app.post("/api/sessions/{session_id}/question")
async def get_next_question(session_id: str, user_id: str = Depends(get_current_user)):
    # Route to orchestrator
    result = orchestrator.route_request(
        agent_id='socratic',
        action='generate_question',
        data={
            'session_id': session_id,
            'user_id': user_id
        }
    )
    return result
```

---

#### Step 2: AgentOrchestrator Routes Request

**orchestrator.py:**
```python
def route_request(self, agent_id='socratic', action='generate_question', data={}):
    # 1. Validate agent exists
    if agent_id not in self.agents:
        return {'success': False, 'error': 'Unknown agent'}

    agent = self.agents['socratic']  # SocraticCounselorAgent

    # 2. Validate capability
    capabilities = agent.get_capabilities()
    # Returns: ['generate_question', 'generate_questions_batch', 'evaluate_answer', ...]

    if 'generate_question' not in capabilities:
        return {'success': False, 'error': 'Unsupported action'}

    # 3. Check if major operation (needs quality control)
    is_major = self._is_major_operation('socratic', 'generate_question')
    # Returns: True (question generation is major operation)

    # 4. Apply quality control BEFORE execution
    quality_metadata = {}
    if is_major:
        quality_metadata = self._apply_quality_control('socratic', 'generate_question', data)

        # If blocking, stop here
        if quality_metadata.get('is_blocking'):
            return {
                'success': False,
                'error': 'Blocked by Quality Controller',
                'reason': quality_metadata.get('reason'),
                'suggestions': quality_metadata.get('suggestions')
            }

    # 5. Route to agent
    result = agent.process_request('generate_question', data)

    # 6. Attach quality metadata
    result['quality_metadata'] = quality_metadata

    return result
```

---

#### Step 3: Quality Control Pre-Check

**_apply_quality_control():**
```python
def _apply_quality_control(self, agent_id, action, data):
    session_id = data.get('session_id')
    project_id = self.db.get_project_id_from_session(session_id)

    # 1. Load all questions asked so far
    previous_questions = self.db.questions.get_by_project_id(project_id)

    # 2. Analyze coverage
    session_analysis = self.quality_analyzer.analyze_session(
        session_id=session_id,
        questions=previous_questions
    )
    """
    session_analysis = {
        'diversity_score': 0.6,  # 6 out of 10 categories covered
        'coverage_gaps': ['monitoring', 'disaster_recovery', 'testing', 'security'],
        'bias_patterns': [],
        'quality_score': 0.85
    }
    """

    # 3. Check for blocking issues
    is_blocking = False
    blocking_reason = None

    # Too many gaps?
    if len(session_analysis['coverage_gaps']) > 7:
        is_blocking = True
        blocking_reason = "Too many critical areas uncovered"

    # Low diversity?
    if session_analysis['diversity_score'] < 0.3:
        is_blocking = True
        blocking_reason = "Questions are too narrow, need broader coverage"

    # 4. Generate suggested focus areas
    suggested_focus = session_analysis['coverage_gaps'][:3]  # Top 3 gaps

    return {
        'quality_control_applied': True,
        'session_analysis': session_analysis,
        'is_blocking': is_blocking,
        'blocking_reason': blocking_reason,
        'suggested_focus_areas': suggested_focus
    }
```

---

#### Step 4: SocraticCounselorAgent Processes Request

**agent.process_request() (BaseAgent):**
```python
def process_request(self, action='generate_question', data={}):
    # 1. AUTO-LOAD USER CONTEXT
    user_id = data.get('user_id')
    session_id = data.get('session_id')

    if user_id and self.context_enhancer:
        # Build user context from:
        # - UserBehaviorProfile (learned patterns)
        # - Session preferences
        # - Project preferences
        # - Global instructions
        user_context = self.context_enhancer.build_user_context(
            user_id=user_id,
            session_id=session_id,
            project_id=self._get_project_id(session_id)
        )
        """
        user_context = {
            'behavior_profile': {
                'preferred_communication_style': 'concise',
                'preferred_detail_level': 'standard',
                'learning_speed': 'fast'
            },
            'effective_rules': {
                'communication_style': 'concise',  # Merged with priority
                'max_question_length': 100,
                'avoid_jargon': true
            }
        }
        """
        data['_user_context'] = user_context

    # 2. Route to action method
    method_name = f"_{action}"  # _generate_question
    if hasattr(self, method_name):
        return getattr(self, method_name)(data)

    return {'success': False, 'error': f'Unknown action: {action}'}
```

**agent._generate_question():**
```python
def _generate_question(self, data):
    session_id = data['session_id']
    user_context = data.get('_user_context', {})

    # 1. Load project context
    project_context = self._load_project_context(session_id)
    """
    project_context = {
        'project_id': 'proj_abc123',
        'name': 'E-commerce Platform',
        'description': 'Online store for handmade crafts',
        'phase': 'discovery',
        'maturity_score': 45.0,
        'specifications': [
            {'category': 'goals', 'value': 'Help local artisans...'},
            {'category': 'requirements', 'value': 'Simple product listing...'},
            ...
        ],
        'previous_questions': [
            {'text': 'What is the primary goal...', 'category': 'goals'},
            ...
        ],
        'coverage': {
            'goals': 0.8,
            'requirements': 0.5,
            'tech_stack': 0.2,
            ...
        }
    }
    """

    # 2. Identify coverage gaps (what to ask about)
    coverage_gaps = self._identify_gaps(project_context['coverage'])
    # Returns: ['tech_stack', 'security', 'testing'] (lowest coverage areas)

    next_focus = coverage_gaps[0]  # 'tech_stack'

    # 3. Build prompt for Claude
    prompt = self._build_question_generation_prompt(
        project_context=project_context,
        focus_area=next_focus,
        user_context=user_context
    )
    """
    Prompt example:

    You are a Socratic counselor helping gather requirements for a software project.

    PROJECT CONTEXT:
    - Name: E-commerce Platform
    - Description: Online store for handmade crafts
    - Phase: Discovery (45% maturity)
    - Current specifications:
      * Goals: Help local artisans sell products online
      * Requirements: Simple product listing interface, order management
      * Tech stack: (not yet specified)

    PREVIOUS QUESTIONS ASKED:
    1. What is the primary goal you're trying to achieve?
    2. Who are the primary users of this platform?
    3. What specific features do sellers need?
    ... (15 questions total)

    COVERAGE ANALYSIS:
    - Well covered: goals (80%), user_segments (70%)
    - Needs coverage: tech_stack (20%), security (30%), testing (10%)

    USER PREFERENCES:
    - Communication style: concise
    - Detail level: standard
    - Avoid jargon: true

    TASK:
    Generate the next question focusing on: tech_stack

    REQUIREMENTS:
    1. Ask about ONE specific aspect of tech_stack (e.g., backend framework, database, frontend)
    2. Keep question concise (max 100 words)
    3. Avoid assuming solutions (don't say "should we use Django")
    4. Don't use technical jargon
    5. Make it open-ended to encourage detailed answer

    Return JSON:
    {
      "text": "the question text",
      "category": "tech_stack",
      "sub_category": "backend_framework",
      "context": "brief explanation of why this matters"
    }
    """

    # 4. Call Claude API
    response = self.claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # 5. Parse response
    question_data = json.loads(response.content[0].text)
    """
    question_data = {
      "text": "What programming language and framework would you prefer for building the backend API?",
      "category": "tech_stack",
      "sub_category": "backend_framework",
      "context": "The backend framework choice affects development speed, scalability, and team hiring."
    }
    """

    # 6. Quality check on generated question
    quality_analysis = self.quality_analyzer.analyze_question(question_data)
    """
    quality_analysis = {
        'bias_score': 0.0,  # No bias detected
        'quality_score': 0.95,
        'bias_explanation': None,
        'suggested_alternatives': []
    }
    """

    # 7. If biased, regenerate or use alternative
    if quality_analysis['bias_score'] > 0.5:
        self.logger.warning(f"Generated question has high bias: {quality_analysis['bias_score']}")
        # Use suggested alternative or regenerate
        if quality_analysis['suggested_alternatives']:
            question_data['text'] = quality_analysis['suggested_alternatives'][0]

    # 8. Save question to database
    question = self.db.questions.create(
        project_id=project_context['project_id'],
        session_id=session_id,
        text=question_data['text'],
        category=question_data['category'],
        sub_category=question_data.get('sub_category'),
        context=question_data.get('context'),
        quality_score=quality_analysis['quality_score'],
        asked_at=datetime.utcnow()
    )

    # 9. Return to user
    return {
        'success': True,
        'question_id': question.id,
        'text': question.text,
        'category': question.category,
        'context': question.context,
        'quality_metadata': {
            'quality_score': quality_analysis['quality_score'],
            'bias_score': quality_analysis['bias_score']
        }
    }
```

---

## Internal Workflow 2: Answer Processing and Spec Extraction

### Flow Diagram
```
User submits answer
       ↓
FastAPI endpoint: POST /api/sessions/{id}/answer
       ↓
AgentOrchestrator routes to multiple agents:
  1. ContextAnalyzerAgent (extract specs)
  2. ConflictDetectorAgent (check conflicts)
       ↓
ContextAnalyzerAgent._extract_specifications()
  - Call Claude API to extract structured data
  - Parse JSON response
  - Assign confidence scores
       ↓
ConflictDetectorAgent._detect_conflicts()
  - For each extracted spec:
    * Query existing specs in database
    * Compare values
    * Detect contradictions
       ↓
If conflicts found:
  - Create conflict records
  - STOP and ask user to resolve
       ↓
If no conflicts:
  - Save specs to database
  - Update maturity score
  - Generate next question
       ↓
Return to user
```

---

### Detailed Step-by-Step

#### Step 1: Request Arrives

**FastAPI Endpoint:**
```python
@app.post("/api/sessions/{session_id}/answer")
async def submit_answer(
    session_id: str,
    question_id: str,
    answer: str,
    user_id: str = Depends(get_current_user)
):
    # Orchestrate multi-agent workflow
    result = orchestrator.coordinate_workflow([
        {
            'agent_id': 'context',
            'action': 'extract_specifications',
            'data': {
                'session_id': session_id,
                'question_id': question_id,
                'answer': answer,
                'user_id': user_id
            }
        },
        # Conflict detection happens in extract_specifications automatically
    ])

    return result
```

---

#### Step 2: ContextAnalyzerAgent Extracts Specs

**agent._extract_specifications():**
```python
def _extract_specifications(self, data):
    answer = data['answer']
    question_id = data['question_id']
    session_id = data['session_id']

    # 1. Load question context
    question = self.db.questions.get_by_id(question_id)
    project_id = self.db.get_project_id_from_session(session_id)

    # 2. Load existing specifications (for context)
    existing_specs = self.db.specifications.get_by_project_id(project_id)

    # 3. Build extraction prompt
    prompt = self._build_extraction_prompt(question, answer, existing_specs)
    """
    Prompt example:

    Extract structured specifications from the user's answer.

    QUESTION ASKED:
    "What programming language and framework would you prefer for building the backend API?"

    USER ANSWER:
    "I'd like to use Python with FastAPI. We already have Python expertise on the team, and FastAPI is modern and fast."

    EXISTING SPECIFICATIONS:
    - Goals: Help local artisans sell products online
    - Requirements: Simple product listing, order management
    - User segments: Local artisans (sellers), buyers

    TASK:
    Extract ALL specifications mentioned in the answer. Return JSON array:
    [
      {
        "category": "tech_stack",
        "sub_category": "backend_language",
        "key": "primary_language",
        "value": "Python",
        "confidence": 0.95,
        "reasoning": "Explicitly stated"
      },
      {
        "category": "tech_stack",
        "sub_category": "backend_framework",
        "key": "api_framework",
        "value": "FastAPI",
        "confidence": 0.95,
        "reasoning": "Explicitly stated"
      },
      {
        "category": "constraints",
        "sub_category": "team_expertise",
        "key": "team_language_experience",
        "value": "Python expertise",
        "confidence": 0.9,
        "reasoning": "Mentioned as reason for choice"
      },
      {
        "category": "requirements",
        "sub_category": "performance",
        "key": "api_performance",
        "value": "Fast API responses",
        "confidence": 0.7,
        "reasoning": "Implied by 'FastAPI is fast'"
      }
    ]

    IMPORTANT:
    - Include EVERY piece of information, even implied ones
    - Assign confidence (0.0-1.0) based on how explicit it is
    - Provide reasoning for each extraction
    """

    # 4. Call Claude API
    response = self.claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # 5. Parse response
    extracted_specs = json.loads(response.content[0].text)
    """
    extracted_specs = [
      {
        "category": "tech_stack",
        "sub_category": "backend_language",
        "key": "primary_language",
        "value": "Python",
        "confidence": 0.95,
        "reasoning": "Explicitly stated"
      },
      {
        "category": "tech_stack",
        "sub_category": "backend_framework",
        "key": "api_framework",
        "value": "FastAPI",
        "confidence": 0.95,
        "reasoning": "Explicitly stated"
      },
      ...
    ]
    """

    # 6. CONFLICT DETECTION (Real-Time)
    conflicts = self._detect_conflicts_realtime(extracted_specs, existing_specs, project_id)

    # 7. If conflicts found, STOP and ask user
    if conflicts:
        # Save conflicts to database
        for conflict in conflicts:
            self.db.conflicts.create(
                project_id=project_id,
                conflict_type=conflict['type'],
                old_spec_id=conflict['old_spec']['id'],
                new_spec_value=conflict['new_spec']['value'],
                detected_at=datetime.utcnow(),
                resolution='PENDING'
            )

        # Return conflicts to user (blocks saving)
        return {
            'success': False,
            'conflicts_detected': True,
            'conflicts': conflicts,
            'specs_extracted': extracted_specs,  # Not saved yet
            'message': 'Conflicts detected. Please resolve before proceeding.'
        }

    # 8. No conflicts → Save specs
    saved_specs = []
    for spec in extracted_specs:
        saved_spec = self.db.specifications.create(
            project_id=project_id,
            category=spec['category'],
            sub_category=spec.get('sub_category'),
            key=spec['key'],
            value=spec['value'],
            source='socratic_question',
            source_id=question_id,
            confidence=spec['confidence'],
            reasoning=spec.get('reasoning'),
            created_at=datetime.utcnow()
        )
        saved_specs.append(saved_spec)

    # 9. Update maturity score
    new_maturity = self._recalculate_maturity(project_id)

    # 10. Save answer to message history
    self.db.messages.create(
        session_id=session_id,
        question_id=question_id,
        role='user',
        content=answer,
        specs_extracted=len(saved_specs),
        created_at=datetime.utcnow()
    )

    # 11. Return success
    return {
        'success': True,
        'specs_extracted': len(saved_specs),
        'specifications': [
            {'category': s.category, 'key': s.key, 'value': s.value}
            for s in saved_specs
        ],
        'maturity_score': new_maturity,
        'conflicts_detected': False
    }
```

---

#### Step 3: Real-Time Conflict Detection

**_detect_conflicts_realtime():**
```python
def _detect_conflicts_realtime(self, new_specs, existing_specs, project_id):
    conflicts = []

    for new_spec in new_specs:
        # Find related existing specs (same category + key)
        related_existing = [
            existing for existing in existing_specs
            if existing.category == new_spec['category']
            and existing.key == new_spec['key']
        ]

        for existing in related_existing:
            # Compare values
            conflict = self._compare_specs(existing, new_spec)

            if conflict:
                conflicts.append({
                    'type': conflict['type'],
                    'old_spec': {
                        'id': existing.id,
                        'category': existing.category,
                        'key': existing.key,
                        'value': existing.value,
                        'source': existing.source,
                        'created_at': existing.created_at.isoformat()
                    },
                    'new_spec': {
                        'category': new_spec['category'],
                        'key': new_spec['key'],
                        'value': new_spec['value'],
                        'confidence': new_spec['confidence']
                    },
                    'explanation': conflict['explanation'],
                    'severity': conflict['severity']
                })

    return conflicts

def _compare_specs(self, existing, new_spec):
    """Detect if two specs conflict"""

    # Exact match → No conflict
    if existing.value.lower().strip() == new_spec['value'].lower().strip():
        return None

    # Use Claude to determine if it's a conflict or clarification
    prompt = f"""
    Existing specification:
    - Category: {existing.category}
    - Key: {existing.key}
    - Value: {existing.value}

    New specification:
    - Category: {new_spec['category']}
    - Key: {new_spec['key']}
    - Value: {new_spec['value']}

    Are these in conflict, or is the new spec a clarification/addition?

    Return JSON:
    {{
      "is_conflict": true/false,
      "conflict_type": "TECHNOLOGY" | "REQUIREMENTS" | "TIMELINE" | "RESOURCES" | "CLARIFICATION",
      "explanation": "brief explanation",
      "severity": "high" | "medium" | "low"
    }}

    Examples:
    - Existing: "PostgreSQL", New: "MySQL" → CONFLICT (technology)
    - Existing: "Web app", New: "Web app with mobile responsive design" → CLARIFICATION (not conflict)
    - Existing: "5 developers", New: "3 developers" → CONFLICT (resources)
    """

    response = self.claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    analysis = json.loads(response.content[0].text)

    if analysis['is_conflict'] and analysis['conflict_type'] != 'CLARIFICATION':
        return {
            'type': analysis['conflict_type'],
            'explanation': analysis['explanation'],
            'severity': analysis['severity']
        }

    return None  # No conflict
```

---

## Internal Workflow 3: Maturity Calculation

**_recalculate_maturity():**
```python
def _recalculate_maturity(self, project_id):
    """Calculate project maturity based on spec coverage"""

    # 10 required categories
    required_categories = {
        'goals': 10,
        'requirements': 15,
        'tech_stack': 12,
        'scalability': 8,
        'security': 10,
        'performance': 8,
        'testing': 8,
        'monitoring': 6,
        'data_retention': 5,
        'disaster_recovery': 8
    }

    total_weight = sum(required_categories.values())  # 90

    # Load all specifications
    specs = self.db.specifications.get_by_project_id(project_id)

    # Group by category
    specs_by_category = {}
    for spec in specs:
        if spec.category not in specs_by_category:
            specs_by_category[spec.category] = []
        specs_by_category[spec.category].append(spec)

    # Calculate coverage per category
    category_scores = {}
    for category, max_points in required_categories.items():
        specs_in_category = specs_by_category.get(category, [])

        # Base score: number of specs (capped at max_points)
        base_score = min(len(specs_in_category), max_points)

        # Adjust by average confidence
        if specs_in_category:
            avg_confidence = sum(s.confidence for s in specs_in_category) / len(specs_in_category)
            adjusted_score = base_score * avg_confidence
        else:
            adjusted_score = 0

        category_scores[category] = adjusted_score

    # Total maturity = sum of category scores / total weight * 100
    total_score = sum(category_scores.values())
    maturity_percentage = (total_score / total_weight) * 100

    # Update project
    self.db.projects.update(
        project_id=project_id,
        maturity_score=maturity_percentage,
        category_coverage=json.dumps(category_scores)
    )

    # Check phase transition
    self._check_phase_transition(project_id, maturity_percentage)

    return maturity_percentage

def _check_phase_transition(self, project_id, maturity):
    project = self.db.projects.get_by_id(project_id)

    # Discovery → Analysis (60%)
    if project.phase == 'discovery' and maturity >= 60.0:
        # Emit event
        self.events.emit('phase_transition_eligible', {
            'project_id': project_id,
            'from_phase': 'discovery',
            'to_phase': 'analysis',
            'maturity': maturity
        })

    # Analysis → Design (80%)
    if project.phase == 'analysis' and maturity >= 80.0:
        self.events.emit('phase_transition_eligible', {
            'project_id': project_id,
            'from_phase': 'analysis',
            'to_phase': 'design',
            'maturity': maturity
        })

    # Design → Implementation (100%)
    if project.phase == 'design' and maturity >= 100.0:
        self.events.emit('phase_transition_eligible', {
            'project_id': project_id,
            'from_phase': 'design',
            'to_phase': 'implementation',
            'maturity': maturity
        })
```

---

## Internal Workflow 4: Quality Control Path Optimization

**When:** Before code generation, architecture decisions, major operations

**How It Works:**

```python
# In AgentOrchestrator._apply_quality_control()
def _apply_quality_control(self, agent_id='code', action='generate_code', data={}):
    project_id = data['project_id']

    # 1. Assess readiness
    assessment = self.quality_analyzer.analyze_readiness(project_id)
    """
    assessment = {
        'is_ready': False,
        'gaps': [
            {'category': 'testing', 'severity': 'high', 'missing': 'No testing strategy'},
            {'category': 'monitoring', 'severity': 'medium', 'missing': 'No monitoring specified'},
            {'category': 'disaster_recovery', 'severity': 'high', 'missing': 'No backup plan'}
        ],
        'maturity_score': 85.0,
        'required_maturity': 100.0
    }
    """

    # 2. Generate all possible paths
    paths = self.path_optimizer.compare_paths(
        goal='generate_code',
        project_id=project_id
    )
    """
    paths = [
        {
            'id': 'fill_gaps_then_generate',
            'steps': [
                {'agent': 'socratic', 'action': 'ask_gap_questions', 'tokens': 800},
                {'agent': 'code', 'action': 'generate_code', 'tokens': 5000}
            ],
            'direct_cost': 5800,
            'rework_cost': 0,
            'total_cost': 5800,
            'risk_level': 'LOW'
        },
        {
            'id': 'generate_now',
            'steps': [
                {'agent': 'code', 'action': 'generate_code', 'tokens': 5000}
            ],
            'direct_cost': 5000,
            'rework_cost': 3000,  # Estimated rework due to missing specs
            'total_cost': 8000,
            'risk_level': 'HIGH'
        }
    ]
    """

    # 3. Determine if blocking
    is_blocking = (
        not assessment['is_ready'] and
        any(gap['severity'] == 'high' for gap in assessment['gaps'])
    )

    # 4. Return quality metadata
    return {
        'quality_control_applied': True,
        'assessment': assessment,
        'available_paths': paths,
        'recommended_path': paths[0],  # Lowest total cost
        'is_blocking': is_blocking,
        'blocking_reason': 'High-severity gaps detected' if is_blocking else None
    }
```

**Path Optimizer Internals:**

```python
# path_optimizer.py
def compare_paths(self, goal='generate_code', project_id):
    # Generate all paths
    all_paths = self._generate_all_paths(goal)

    # Cost each path
    for path in all_paths:
        # Direct cost = sum of step tokens
        path['direct_cost'] = sum(step['tokens'] for step in path['steps'])

        # Rework cost = estimated additional work due to gaps
        path['rework_cost'] = self._estimate_rework_cost(path, project_id)

        # Total cost
        path['total_cost'] = path['direct_cost'] + path['rework_cost']

    # Sort by total cost (lowest first)
    return sorted(all_paths, key=lambda p: p['total_cost'])

def _estimate_rework_cost(self, path, project_id):
    """Estimate rework cost if path skips requirements"""

    # Load current maturity
    project = self.db.projects.get_by_id(project_id)
    maturity = project.maturity_score

    # If path includes gap-filling, rework = 0
    if any(step['action'] == 'ask_gap_questions' for step in path['steps']):
        return 0

    # If path skips gap-filling, estimate rework
    missing_percentage = 100 - maturity

    # Rework cost = 30 tokens per 1% missing (empirical)
    rework_cost = missing_percentage * 30

    return rework_cost
```

---

## Internal Workflow 5: User Learning and Adaptation

**When:** After each session completes

**Process:**

```python
# Event listener in BehaviorAnalyzerService
@on_event('session_completed')
def analyze_session(event_data):
    session_id = event_data['session_id']
    user_id = event_data['user_id']

    # 1. Load session messages
    messages = self.db.messages.get_by_session_id(session_id)
    session = self.db.sessions.get_by_id(session_id)

    # 2. Analyze communication style
    comm_style = self._analyze_communication_style(messages, user_id)
    """
    comm_style = {
        'style_characteristics': ['concise', 'code_focused'],
        'average_message_length': 65,
        'question_frequency': 0.15,
        'code_usage_frequency': 0.35
    }
    """

    # 3. Extract decision patterns
    decision_patterns = self._extract_decision_patterns(messages)
    """
    decision_patterns = {
        'decision_making_style': 'data_driven',
        'evidence': 'User asks for comparisons, pros/cons before deciding'
    }
    """

    # 4. Identify pain points
    pain_points = self._identify_pain_points(messages)
    """
    pain_points = {
        'async_debugging': {'frequency': 3, 'severity': 'high'},
        'database_migration': {'frequency': 2, 'severity': 'medium'}
    }
    """

    # 5. Identify strengths
    strengths = self._identify_strengths(messages)
    """
    strengths = {
        'database_design': {'confidence': 0.9, 'evidence': 'Detailed schema discussions'},
        'api_design': {'confidence': 0.85, 'evidence': 'Clear REST principles'}
    }
    """

    # 6. Load existing behavior profile
    profile = self.db.user_behavior_profiles.get_by_user_id(user_id)

    # 7. Update profile (incremental learning)
    if profile:
        # Merge new insights with existing (weighted average)
        profile.preferred_communication_style = self._merge_style(
            old=profile.preferred_communication_style,
            new=comm_style['style_characteristics'][0],
            weight=0.2  # 20% new, 80% old
        )

        # Update pain points (accumulate)
        existing_pain_points = json.loads(profile.pain_points or '{}')
        for topic, data in pain_points.items():
            if topic in existing_pain_points:
                existing_pain_points[topic]['frequency'] += data['frequency']
            else:
                existing_pain_points[topic] = data
        profile.pain_points = json.dumps(existing_pain_points)

        # Update confidence (more sessions = higher confidence)
        profile.total_sessions += 1
        profile.profile_confidence = min(1.0, profile.total_sessions * 0.05)

        self.db.user_behavior_profiles.update(profile)

    else:
        # Create new profile
        profile = self.db.user_behavior_profiles.create(
            user_id=user_id,
            preferred_communication_style=comm_style['style_characteristics'][0],
            pain_points=json.dumps(pain_points),
            strengths=json.dumps(strengths),
            total_sessions=1,
            profile_confidence=0.05
        )

    # 8. Emit event
    self.events.emit('user_profile_updated', {
        'user_id': user_id,
        'profile_confidence': profile.profile_confidence
    })
```

**How It's Applied in Next Request:**

```python
# In BaseAgent.process_request()
user_context = self.context_enhancer.build_user_context(user_id)
"""
user_context = {
    'behavior_profile': {
        'preferred_communication_style': 'concise',
        'preferred_detail_level': 'standard',
        'pain_points': {
            'async_debugging': {'frequency': 3, 'severity': 'high'}
        },
        'strengths': {
            'database_design': {'confidence': 0.9}
        }
    },
    'effective_rules': {
        'communication_style': 'concise',
        'avoid_long_explanations': true,
        'focus_on_pain_points': ['async_debugging'],
        'leverage_strengths': ['database_design']
    }
}
"""

# Agent uses this to adapt behavior
if 'async_debugging' in user_context['effective_rules'].get('focus_on_pain_points', []):
    # Proactively help with async debugging
    prompt += "\nNote: User struggles with async debugging. Provide extra guidance in this area."

if 'database_design' in user_context['effective_rules'].get('leverage_strengths', []):
    # User is strong in databases, can skip basics
    prompt += "\nUser has strong database design skills. Skip basic explanations."
```

---

## Summary: Key Internal Workflows

1. **Question Generation:** Load context → Build prompt → Call Claude → Quality check → Save → Return
2. **Spec Extraction:** Parse answer → Extract structured data → Detect conflicts → Save or block → Update maturity
3. **Conflict Detection:** For each new spec → Query existing → Compare → Use Claude to determine if conflict → Return conflicts
4. **Quality Control:** Analyze coverage → Generate all paths → Calculate costs → Block if risky → Recommend best path
5. **User Learning:** Analyze session → Extract patterns → Update behavior profile → Apply in next request

---

**Next:** Read MY_UNDERSTANDING_FEATURES.md for feature-by-feature breakdown
