# Phase 6: User Learning & Adaptation

**Status:** ⏳ PENDING
**Duration:** 3-4 days
**Goal:** Learn user behavior patterns and adapt question selection dynamically

---

## ⚠️ CRITICAL: Read Before Implementation

**MANDATORY:** Review [CRITICAL_LESSONS_LEARNED.md](CRITICAL_LESSONS_LEARNED.md) before starting Phase 6.

**Critical Checklist for Phase 6:**

### Models (user_behavior_patterns, question_effectiveness, knowledge_base_documents):
- [ ] Inherits from BaseModel? → Include id, created_at, updated_at in migration
- [ ] AVOID column names: metadata, query, session
- [ ] Use pattern_metadata NOT just "metadata" (if storing metadata)
- [ ] Use document_metadata NOT just "metadata" (if storing metadata)

### Migrations (Phase 6 migrations):
- [ ] Add `import os` and `_should_run()` function
- [ ] Check DATABASE_URL contains "socrates_specs"
- [ ] Add check to BOTH upgrade() and downgrade()
- [ ] Verify BaseModel columns if model inherits

### Tests (test_phase_6_user_learning.py):
- [ ] Use `auth_session` NOT `db_auth`
- [ ] Use `specs_session` NOT `db_specs`
- [ ] Use `mock_claude_client` fixture, NOT @patch decorators
- [ ] DO NOT patch instance attributes

### UserLearningAgent:
- [ ] Accept ServiceContainer in __init__
- [ ] Store as self.services (instance attribute)
- [ ] Get database via self.services.get_database_specs()
- [ ] Get Claude client via self.services.get_claude_client()

**Database:** All Phase 6 tables go to `socrates_specs`

---

## 📋 Objectives

1. Create UserLearningAgent
2. Track question effectiveness per user
3. Learn user behavior patterns (communication style, detail level)
4. Implement knowledge base document upload
5. Adapt question selection based on learned patterns
6. Provide user learning insights

---

## 🔗 Dependencies

**From Phase 5:**
- Working Quality Control system
- Question generation pipeline
- Specification extraction

**Provides To Phase 7:**
- User behavior profiles for Direct Chat Mode
- Learned communication preferences
- Question effectiveness data

**From Phase 2:**
- SocraticCounselorAgent for question generation
- ContextAnalyzerAgent for spec extraction

---

## 🌐 API Endpoints

This phase implements user learning and adaptation. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 6:**
- GET /api/v1/learning/user/{id}/profile - Get user learning profile
- GET /api/v1/learning/user/{id}/patterns - Get behavior patterns
- GET /api/v1/learning/user/{id}/effectiveness - Get question effectiveness stats
- POST /api/v1/learning/project/{id}/upload-document - Upload knowledge base document
- GET /api/v1/learning/project/{id}/documents - List knowledge base documents

**Testing Endpoints:**
```bash
# Get user learning profile
curl -X GET http://localhost:8000/api/v1/learning/user/{user_id}/profile \
  -H "Authorization: Bearer <token>"

# Get behavior patterns
curl -X GET http://localhost:8000/api/v1/learning/user/{user_id}/patterns \
  -H "Authorization: Bearer <token>"

# Upload knowledge base document
curl -X POST http://localhost:8000/api/v1/learning/project/{project_id}/upload-document \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@requirements.pdf"
```

---

## 📦 Key Component: UserLearningAgent

```python
class UserLearningAgent(BaseAgent):
    """Learn user behavior patterns and adapt questions accordingly"""

    def get_capabilities(self):
        return [
            'track_question_effectiveness',
            'learn_behavior_pattern',
            'recommend_next_question',
            'upload_knowledge_document',
            'get_user_profile'
        ]

    def _track_question_effectiveness(self, data):
        """Track how effective a question was for the user

        Args:
            data: {
                'user_id': UUID,
                'question_template_id': str,
                'role': str (PM, BA, UX, etc.),
                'answer_length': int,
                'specs_extracted': int,
                'answer_quality': float (0-1)
            }

        Returns:
            {'success': bool, 'effectiveness_score': float}
        """
        user_id = data['user_id']
        question_template_id = data['question_template_id']
        role = data['role']

        # Query existing effectiveness record
        effectiveness = self.db.query(QuestionEffectiveness).filter_by(
            user_id=user_id,
            question_template_id=question_template_id
        ).first()

        if not effectiveness:
            # Create new effectiveness record
            effectiveness = QuestionEffectiveness(
                user_id=user_id,
                question_template_id=question_template_id,
                role=role,
                times_asked=0,
                times_answered_well=0,
                average_answer_length=0,
                average_spec_extraction_count=0.0,
                effectiveness_score=0.5  # Start neutral
            )
            self.db.add(effectiveness)

        # Update metrics
        effectiveness.times_asked += 1

        # Determine if answered well (extracted specs + good quality)
        answered_well = (
            data['specs_extracted'] > 0 and
            data['answer_quality'] > 0.6
        )
        if answered_well:
            effectiveness.times_answered_well += 1

        # Update averages (exponential moving average)
        alpha = 0.3  # Learning rate
        effectiveness.average_answer_length = int(
            alpha * data['answer_length'] +
            (1 - alpha) * (effectiveness.average_answer_length or 0)
        )
        effectiveness.average_spec_extraction_count = (
            alpha * data['specs_extracted'] +
            (1 - alpha) * effectiveness.average_spec_extraction_count
        )

        # Calculate effectiveness score (0-1)
        effectiveness.effectiveness_score = (
            effectiveness.times_answered_well / effectiveness.times_asked
            if effectiveness.times_asked > 0 else 0.5
        )

        effectiveness.last_asked_at = datetime.now(timezone.utc)
        effectiveness.updated_at = datetime.now(timezone.utc)

        self.db.commit()

        return {
            'success': True,
            'effectiveness_score': effectiveness.effectiveness_score,
            'times_asked': effectiveness.times_asked,
            'times_answered_well': effectiveness.times_answered_well
        }

    def _learn_behavior_pattern(self, data):
        """Learn or update user behavior pattern

        Args:
            data: {
                'user_id': UUID,
                'pattern_type': str (communication_style, detail_level, etc.),
                'pattern_data': dict,
                'confidence': float (0-1),
                'project_id': UUID
            }

        Returns:
            {'success': bool, 'pattern_id': UUID}
        """
        user_id = data['user_id']
        pattern_type = data['pattern_type']

        # Query existing pattern
        pattern = self.db.query(UserBehaviorPattern).filter_by(
            user_id=user_id,
            pattern_type=pattern_type
        ).first()

        if pattern:
            # Update existing pattern
            # Merge new data with existing (increase confidence)
            pattern.pattern_data = self._merge_pattern_data(
                pattern.pattern_data,
                data['pattern_data']
            )
            pattern.confidence = min(
                1.0,
                pattern.confidence + 0.1  # Increase confidence
            )
            pattern.learned_from_projects = list(set(
                pattern.learned_from_projects + [str(data['project_id'])]
            ))
            pattern.updated_at = datetime.now(timezone.utc)
        else:
            # Create new pattern
            pattern = UserBehaviorPattern(
                user_id=user_id,
                pattern_type=pattern_type,
                pattern_data=data['pattern_data'],
                confidence=data['confidence'],
                learned_from_projects=[str(data['project_id'])],
                learned_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(pattern)

        self.db.commit()

        return {
            'success': True,
            'pattern_id': pattern.id,
            'confidence': pattern.confidence
        }

    def _recommend_next_question(self, data):
        """Recommend next question based on user learning

        Args:
            data: {
                'user_id': UUID,
                'project_id': UUID,
                'available_questions': List[dict]
            }

        Returns:
            {
                'success': bool,
                'recommended_question': dict,
                'reason': str
            }
        """
        user_id = data['user_id']
        available_questions = data['available_questions']

        # Load user's question effectiveness data
        effectiveness_records = self.db.query(QuestionEffectiveness).filter_by(
            user_id=user_id
        ).all()

        # Score each available question
        scored_questions = []
        for question in available_questions:
            # Find effectiveness record for this question
            effectiveness = next(
                (e for e in effectiveness_records
                 if e.question_template_id == question['template_id']),
                None
            )

            if effectiveness:
                # Use learned effectiveness score
                score = effectiveness.effectiveness_score
            else:
                # No data yet, use neutral score
                score = 0.5

            scored_questions.append({
                'question': question,
                'score': score
            })

        # Sort by score (highest first)
        scored_questions.sort(key=lambda x: x['score'], reverse=True)

        # Get top recommendation
        if scored_questions:
            recommended = scored_questions[0]
            return {
                'success': True,
                'recommended_question': recommended['question'],
                'effectiveness_score': recommended['score'],
                'reason': (
                    f"This question has {recommended['score']:.0%} effectiveness "
                    f"for you based on past interactions"
                )
            }

        return {
            'success': False,
            'error': 'No available questions'
        }

    def _upload_knowledge_document(self, data):
        """Upload knowledge base document for project

        Args:
            data: {
                'project_id': UUID,
                'user_id': UUID,
                'filename': str,
                'content': str,
                'content_type': str,
                'file_size': int
            }

        Returns:
            {'success': bool, 'document_id': UUID}
        """
        # Create knowledge base document
        document = KnowledgeBaseDocument(
            project_id=data['project_id'],
            user_id=data['user_id'],
            filename=data['filename'],
            file_size=data['file_size'],
            content_type=data['content_type'],
            content=data['content'],
            uploaded_at=datetime.now(timezone.utc)
        )

        self.db.add(document)
        self.db.commit()

        # TODO Phase 9: Generate embedding for semantic search
        # embedding = self.embedding_service.generate(document.content)
        # document.embedding = embedding
        # self.db.commit()

        return {
            'success': True,
            'document_id': document.id,
            'filename': document.filename
        }

    def _get_user_profile(self, data):
        """Get comprehensive user learning profile

        Args:
            data: {'user_id': UUID}

        Returns:
            {
                'success': bool,
                'profile': {
                    'behavior_patterns': List[dict],
                    'question_effectiveness': List[dict],
                    'preferred_roles': List[str],
                    'communication_style': str,
                    'detail_level': str
                }
            }
        """
        user_id = data['user_id']

        # Load behavior patterns
        patterns = self.db.query(UserBehaviorPattern).filter_by(
            user_id=user_id
        ).all()

        # Load question effectiveness
        effectiveness = self.db.query(QuestionEffectiveness).filter_by(
            user_id=user_id
        ).all()

        # Analyze patterns to determine preferences
        communication_style = self._infer_communication_style(patterns)
        detail_level = self._infer_detail_level(patterns)
        preferred_roles = self._infer_preferred_roles(effectiveness)

        return {
            'success': True,
            'profile': {
                'behavior_patterns': [
                    {
                        'type': p.pattern_type,
                        'data': p.pattern_data,
                        'confidence': p.confidence
                    }
                    for p in patterns
                ],
                'question_effectiveness': [
                    {
                        'role': e.role,
                        'effectiveness': e.effectiveness_score,
                        'times_asked': e.times_asked
                    }
                    for e in effectiveness
                ],
                'preferred_roles': preferred_roles,
                'communication_style': communication_style,
                'detail_level': detail_level
            }
        }

    def _infer_communication_style(self, patterns):
        """Infer communication style from patterns"""
        # Find communication_style pattern
        for pattern in patterns:
            if pattern.pattern_type == 'communication_style':
                return pattern.pattern_data.get('style', 'balanced')
        return 'balanced'

    def _infer_detail_level(self, patterns):
        """Infer preferred detail level from patterns"""
        # Find detail_level pattern
        for pattern in patterns:
            if pattern.pattern_type == 'detail_level':
                return pattern.pattern_data.get('level', 'moderate')
        return 'moderate'

    def _infer_preferred_roles(self, effectiveness_records):
        """Infer which roles user responds best to"""
        # Group by role and average effectiveness
        role_scores = {}
        for record in effectiveness_records:
            if record.role not in role_scores:
                role_scores[record.role] = []
            role_scores[record.role].append(record.effectiveness_score)

        # Calculate averages
        role_averages = {
            role: sum(scores) / len(scores)
            for role, scores in role_scores.items()
        }

        # Sort by effectiveness (best first)
        sorted_roles = sorted(
            role_averages.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top 3 roles
        return [role for role, _ in sorted_roles[:3]]

    def _merge_pattern_data(self, existing, new):
        """Merge new pattern data with existing"""
        merged = existing.copy()
        merged.update(new)
        return merged
```

---

## 🔄 Integration with SocraticCounselorAgent

**Modified `SocraticCounselorAgent._generate_question()` (Phase 6 Enhancement):**

```python
def _generate_question(self, data):
    project_id = data['project_id']
    user_id = data['user_id']

    # Get available questions based on coverage gaps
    available_questions = self._get_available_questions(project_id)

    # NEW in Phase 6: Get recommendation from UserLearningAgent
    if self.user_learning_agent:
        recommendation = self.orchestrator.route_request(
            'user_learning',
            'recommend_next_question',
            {
                'user_id': user_id,
                'project_id': project_id,
                'available_questions': available_questions
            }
        )

        if recommendation['success']:
            self.logger.info(
                f"Using learned recommendation: {recommendation['reason']}"
            )
            question = recommendation['recommended_question']
        else:
            # Fallback to standard selection
            question = self._select_question_by_coverage(available_questions)
    else:
        # Phase 2-5: Standard selection
        question = self._select_question_by_coverage(available_questions)

    # Generate question via Claude API
    return self._generate_from_template(question)
```

---

## 🔄 Integration with ContextAnalyzerAgent

**Modified `ContextAnalyzerAgent._extract_specifications()` (Phase 6 Enhancement):**

```python
def _extract_specifications(self, data):
    # ... existing extraction logic ...

    specs_extracted = len(extracted_specs)
    answer_length = len(data['answer'])

    # Calculate answer quality based on specs extracted and clarity
    answer_quality = self._calculate_answer_quality(
        data['answer'],
        specs_extracted
    )

    # NEW in Phase 6: Track question effectiveness
    if self.user_learning_agent:
        self.orchestrator.route_request(
            'user_learning',
            'track_question_effectiveness',
            {
                'user_id': data['user_id'],
                'question_template_id': data['question_template_id'],
                'role': data['question_role'],
                'answer_length': answer_length,
                'specs_extracted': specs_extracted,
                'answer_quality': answer_quality
            }
        )

        # Learn behavior pattern from this interaction
        self.orchestrator.route_request(
            'user_learning',
            'learn_behavior_pattern',
            {
                'user_id': data['user_id'],
                'pattern_type': 'communication_style',
                'pattern_data': {
                    'style': self._infer_style_from_answer(data['answer']),
                    'answer_length': answer_length
                },
                'confidence': 0.6,
                'project_id': data['project_id']
            }
        )

    return result
```

---

## 🧪 Critical Tests

```python
def test_track_question_effectiveness():
    """Test tracking question effectiveness"""
    result = user_learning_agent.process_request(
        'track_question_effectiveness',
        {
            'user_id': user.id,
            'question_template_id': 'pm_goals_001',
            'role': 'PM',
            'answer_length': 150,
            'specs_extracted': 3,
            'answer_quality': 0.8
        }
    )
    assert result['success'] == True
    assert result['effectiveness_score'] > 0

def test_learn_behavior_pattern():
    """Test learning user behavior pattern"""
    result = user_learning_agent.process_request(
        'learn_behavior_pattern',
        {
            'user_id': user.id,
            'pattern_type': 'communication_style',
            'pattern_data': {'style': 'technical', 'detail': 'high'},
            'confidence': 0.7,
            'project_id': project.id
        }
    )
    assert result['success'] == True
    assert result['confidence'] >= 0.7

def test_recommend_next_question():
    """Test question recommendation based on learned patterns"""
    # Create effectiveness records (user responds well to PM questions)
    effectiveness = QuestionEffectiveness(
        user_id=user.id,
        question_template_id='pm_goals_001',
        role='PM',
        times_asked=5,
        times_answered_well=5,
        effectiveness_score=1.0
    )
    db.add(effectiveness)
    db.commit()

    result = user_learning_agent.process_request(
        'recommend_next_question',
        {
            'user_id': user.id,
            'project_id': project.id,
            'available_questions': [
                {'template_id': 'pm_goals_001', 'role': 'PM'},
                {'template_id': 'ux_users_001', 'role': 'UX'}
            ]
        }
    )

    assert result['success'] == True
    assert result['recommended_question']['template_id'] == 'pm_goals_001'
    assert result['effectiveness_score'] == 1.0

def test_upload_knowledge_document():
    """Test uploading knowledge base document"""
    result = user_learning_agent.process_request(
        'upload_knowledge_document',
        {
            'project_id': project.id,
            'user_id': user.id,
            'filename': 'requirements.pdf',
            'content': 'Project requirements: ...',
            'content_type': 'application/pdf',
            'file_size': 12345
        }
    )
    assert result['success'] == True
    assert result['document_id'] is not None

def test_get_user_profile():
    """Test getting comprehensive user learning profile"""
    result = user_learning_agent.process_request(
        'get_user_profile',
        {'user_id': user.id}
    )
    assert result['success'] == True
    assert 'profile' in result
    assert 'behavior_patterns' in result['profile']
    assert 'question_effectiveness' in result['profile']
```

---

## 🗄️ Database Tables Used

**From DATABASE_SCHEMA_COMPLETE.md (Phase 5 tables):**

### socrates_specs Database

**user_behavior_patterns:**
- Stores learned behavior patterns per user
- Fields: pattern_type, pattern_data (JSONB), confidence, learned_from_projects

**question_effectiveness:**
- Tracks effectiveness of each question template per user
- Fields: question_template_id, role, times_asked, times_answered_well, effectiveness_score

**knowledge_base_documents:**
- Stores uploaded documents per project
- Fields: filename, content, content_type, embedding (for Phase 9 semantic search)

---

## ✅ Verification

- [ ] UserLearningAgent created
- [ ] Question effectiveness tracking works
- [ ] Behavior pattern learning works
- [ ] Question recommendation works (prefers high-effectiveness questions)
- [ ] Knowledge document upload works
- [ ] User profile retrieval works
- [ ] Integration with SocraticCounselorAgent works
- [ ] Integration with ContextAnalyzerAgent works
- [ ] Tests pass: `pytest tests/test_phase_6_user_learning.py`

---

## 📊 Success Metrics

**Phase 6 succeeds when:**
1. System learns user preferences over time
2. Question recommendations improve effectiveness (measured)
3. User profile accurately reflects communication style
4. Knowledge documents are stored and retrievable
5. Integration with existing agents works seamlessly

**Example Success Case:**
- User answers 10 PM questions well (effectiveness = 90%)
- User answers 10 UX questions poorly (effectiveness = 30%)
- Next question recommendation: PM question (90% effectiveness)
- Result: Better user experience, more specs extracted

---

**Previous:** [PHASE_5.md](PHASE_5.md)
**Next:** [PHASE_7.md](PHASE_7.md) - Direct Chat Mode
