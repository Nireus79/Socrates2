# Phase 7: Direct Chat Mode

**Status:** ⏳ PENDING
**Duration:** 2-3 days
**Goal:** Enable free-form chat with automatic specification extraction

---

## 📋 Objectives

1. Add Direct Chat Mode to sessions (toggle between Socratic and Direct Chat)
2. Enable free-form conversation with automatic spec extraction
3. Maintain context awareness during direct chat
4. Allow users to ask clarifying questions without breaking flow
5. Extract specifications from natural conversation
6. Integrate with existing conflict detection and quality control

---

## 🔗 Dependencies

**From Phase 2:**
- Session management (sessions table, mode field)
- ContextAnalyzerAgent for spec extraction

**From Phase 5:**
- Quality Control system (still applies in Direct Chat)

**From Phase 6:**
- User Learning (adapts responses based on user profile)

**Provides To Phase 8:**
- Multi-mode chat foundation for team collaboration
- Context-aware conversation system

---

## 🌐 API Endpoints

This phase implements direct chat mode alongside Socratic mode. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 7:**
- POST /api/v1/sessions/{id}/toggle-mode - Switch between Socratic and Direct Chat
- POST /api/v1/sessions/{id}/message - Send message in Direct Chat mode
- GET /api/v1/sessions/{id}/mode - Get current session mode

**Testing Endpoints:**
```bash
# Toggle to Direct Chat mode
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/toggle-mode \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"mode": "direct_chat"}'

# Send chat message
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to build a web app with Python and React"}'

# Get session mode
curl -X GET http://localhost:8000/api/v1/sessions/{session_id}/mode \
  -H "Authorization: Bearer <token>"
```

---

## 📦 Key Component: DirectChatAgent

```python
class DirectChatAgent(BaseAgent):
    """Handle free-form direct chat with automatic spec extraction"""

    def get_capabilities(self):
        return [
            'process_chat_message',
            'toggle_mode',
            'get_mode',
            'maintain_context'
        ]

    def _process_chat_message(self, data):
        """Process a direct chat message

        Args:
            data: {
                'session_id': UUID,
                'user_id': UUID,
                'message': str,
                'project_id': UUID
            }

        Returns:
            {
                'success': bool,
                'response': str,
                'specs_extracted': int,
                'conflicts_detected': bool,
                'suggested_next_question': str (optional)
            }
        """
        session_id = data['session_id']
        user_id = data['user_id']
        message = data['message']
        project_id = data['project_id']

        # Verify session is in direct_chat mode
        session = self.db.query(Session).get(session_id)
        if session.mode != 'direct_chat':
            return {
                'success': False,
                'error': 'Session not in direct_chat mode'
            }

        # Load conversation context
        context = self._load_conversation_context(session_id)

        # Load project context (existing specs, conflicts, maturity)
        project_context = self._load_project_context(project_id)

        # Build chat prompt with full context
        prompt = self._build_chat_prompt(
            message,
            context,
            project_context
        )

        # Call Claude API for response
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        chat_response = response.content[0].text

        # Save conversation history (both user message and assistant response)
        self._save_conversation_turn(
            session_id,
            user_message=message,
            assistant_message=chat_response
        )

        # Extract specifications from both user message AND response
        # (Response might clarify or refine specs)
        extraction_result = self.orchestrator.route_request(
            'context',
            'extract_specifications',
            {
                'session_id': session_id,
                'conversation_text': f"User: {message}\nAssistant: {chat_response}",
                'user_id': user_id,
                'project_id': project_id
            }
        )

        specs_extracted = extraction_result.get('specs_extracted', 0)
        conflicts_detected = extraction_result.get('conflicts_detected', False)

        # Optionally suggest a clarifying question
        suggested_question = None
        if specs_extracted > 0:
            # Check coverage gaps
            suggested_question = self._suggest_clarifying_question(
                project_id,
                extraction_result.get('specs', [])
            )

        return {
            'success': True,
            'response': chat_response,
            'specs_extracted': specs_extracted,
            'conflicts_detected': conflicts_detected,
            'suggested_next_question': suggested_question,
            'maturity_score': project_context.get('maturity_score', 0)
        }

    def _toggle_mode(self, data):
        """Toggle session mode between socratic and direct_chat

        Args:
            data: {
                'session_id': UUID,
                'mode': str ('socratic' | 'direct_chat')
            }

        Returns:
            {'success': bool, 'new_mode': str}
        """
        session_id = data['session_id']
        new_mode = data['mode']

        if new_mode not in ['socratic', 'direct_chat']:
            return {
                'success': False,
                'error': f"Invalid mode: {new_mode}"
            }

        # Update session mode
        session = self.db.query(Session).get(session_id)
        old_mode = session.mode
        session.mode = new_mode
        session.updated_at = datetime.now(timezone.utc)

        self.db.commit()

        self.logger.info(
            f"Session {session_id} mode changed: {old_mode} → {new_mode}"
        )

        return {
            'success': True,
            'old_mode': old_mode,
            'new_mode': new_mode
        }

    def _get_mode(self, data):
        """Get current session mode

        Args:
            data: {'session_id': UUID}

        Returns:
            {'success': bool, 'mode': str}
        """
        session_id = data['session_id']
        session = self.db.query(Session).get(session_id)

        if not session:
            return {
                'success': False,
                'error': 'Session not found'
            }

        return {
            'success': True,
            'mode': session.mode,
            'session_id': session_id,
            'project_id': session.project_id
        }

    def _build_chat_prompt(self, message, context, project_context):
        """Build comprehensive chat prompt with full context"""
        return f"""You are Socrates, an AI system that helps users build software through conversation.

**YOUR ROLE:**
- Engage in natural, helpful conversation
- Help clarify requirements and specifications
- Provide technical guidance
- Extract and organize project specifications

**PROJECT CONTEXT:**
Project: {project_context['name']}
Description: {project_context['description']}
Current Phase: {project_context['phase']}
Maturity: {project_context['maturity_score']}%

**EXISTING SPECIFICATIONS:**
{self._format_specifications(project_context['specifications'])}

**CONVERSATION HISTORY (last 5 turns):**
{self._format_conversation_history(context['recent_messages'])}

**USER MESSAGE:**
{message}

**YOUR TASK:**
1. Respond naturally and helpfully to the user's message
2. If the message contains requirements or specifications, acknowledge them
3. If something is unclear, ask clarifying questions
4. If you notice missing information, gently probe for details
5. Keep the conversation flowing naturally

**IMPORTANT:**
- Be conversational, not formal
- Don't be repetitive with past conversation
- Build on what was already discussed
- If user asks a direct question, answer it directly
- Don't force structure - follow the user's lead

Respond now:"""

    def _load_conversation_context(self, session_id):
        """Load recent conversation history"""
        recent_messages = self.db.query(ConversationHistory).filter_by(
            session_id=session_id
        ).order_by(ConversationHistory.timestamp.desc()).limit(10).all()

        return {
            'recent_messages': list(reversed([
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp
                }
                for msg in recent_messages
            ]))
        }

    def _load_project_context(self, project_id):
        """Load project context for chat"""
        project = self.db.query(Project).get(project_id)
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        return {
            'name': project.name,
            'description': project.description,
            'phase': project.phase,
            'maturity_score': project.maturity_score,
            'specifications': specs
        }

    def _save_conversation_turn(self, session_id, user_message, assistant_message):
        """Save both user message and assistant response"""
        # Save user message
        user_turn = ConversationHistory(
            session_id=session_id,
            role='user',
            content=user_message,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(user_turn)

        # Save assistant message
        assistant_turn = ConversationHistory(
            session_id=session_id,
            role='assistant',
            content=assistant_message,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(assistant_turn)

        self.db.commit()

    def _suggest_clarifying_question(self, project_id, new_specs):
        """Suggest a clarifying question based on coverage gaps"""
        # Analyze what specifications are still missing
        existing_specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Calculate coverage by category
        coverage = self._calculate_coverage_by_category(existing_specs)

        # Find category with lowest coverage
        lowest_category = min(coverage.items(), key=lambda x: x[1])

        if lowest_category[1] < 0.3:  # Less than 30% coverage
            # Generate suggestion
            return f"I notice we haven't covered much about {lowest_category[0]}. Would you like to discuss that?"

        return None

    def _calculate_coverage_by_category(self, specs):
        """Calculate specification coverage by category"""
        categories = [
            'goals', 'requirements', 'tech_stack', 'users',
            'scalability', 'security', 'deployment', 'testing',
            'timeline', 'constraints'
        ]

        coverage = {}
        for category in categories:
            count = len([s for s in specs if s.category == category])
            # Each category should have ~3-5 specs for good coverage
            coverage[category] = min(1.0, count / 3)

        return coverage

    def _format_specifications(self, specs):
        """Format specifications for context"""
        if not specs:
            return "(No specifications yet)"

        formatted = []
        for spec in specs[:20]:  # Limit to 20 most recent
            formatted.append(
                f"- [{spec.category}] {spec.key}: {spec.value}"
            )

        return "\n".join(formatted)

    def _format_conversation_history(self, messages):
        """Format conversation history for context"""
        if not messages:
            return "(No previous messages)"

        formatted = []
        for msg in messages[-5:]:  # Last 5 messages
            role = msg['role'].capitalize()
            content = msg['content'][:200]  # Truncate long messages
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)
```

---

## 🔄 Integration with Session Management

**Enhanced Session Model (sessions table):**

```python
# sessions table already has 'mode' field (Phase 1)
# VALUES: 'socratic' | 'direct_chat'

# Default mode: 'socratic'
# Can toggle during session without losing context
```

**API Route for Mode Toggle:**

```python
@router.post("/sessions/{session_id}/toggle-mode")
async def toggle_session_mode(
    session_id: UUID,
    mode_data: ToggleModeRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Toggle session mode between Socratic and Direct Chat"""
    result = orchestrator.route_request(
        'direct_chat',
        'toggle_mode',
        {
            'session_id': session_id,
            'mode': mode_data.mode
        }
    )
    return result

@router.post("/sessions/{session_id}/message")
async def send_chat_message(
    session_id: UUID,
    message_data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Send a message in Direct Chat mode"""
    result = orchestrator.route_request(
        'direct_chat',
        'process_chat_message',
        {
            'session_id': session_id,
            'user_id': current_user.id,
            'message': message_data.message,
            'project_id': message_data.project_id
        }
    )
    return result
```

---

## 🧪 Critical Tests

```python
def test_toggle_mode():
    """Test toggling between Socratic and Direct Chat modes"""
    # Start in Socratic mode
    session = Session(
        project_id=project.id,
        user_id=user.id,
        mode='socratic',
        status='active'
    )
    db.add(session)
    db.commit()

    # Toggle to Direct Chat
    result = direct_chat_agent.process_request(
        'toggle_mode',
        {'session_id': session.id, 'mode': 'direct_chat'}
    )
    assert result['success'] == True
    assert result['new_mode'] == 'direct_chat'

    # Verify database updated
    db.refresh(session)
    assert session.mode == 'direct_chat'

def test_process_chat_message():
    """Test processing a direct chat message"""
    session = Session(
        project_id=project.id,
        user_id=user.id,
        mode='direct_chat',
        status='active'
    )
    db.add(session)
    db.commit()

    result = direct_chat_agent.process_request(
        'process_chat_message',
        {
            'session_id': session.id,
            'user_id': user.id,
            'message': 'I want to build a REST API with FastAPI',
            'project_id': project.id
        }
    )

    assert result['success'] == True
    assert 'response' in result
    assert len(result['response']) > 0
    # Should extract specs from message
    assert result['specs_extracted'] >= 0

def test_conversation_context_maintained():
    """Test that conversation context is maintained across messages"""
    session = Session(
        project_id=project.id,
        user_id=user.id,
        mode='direct_chat',
        status='active'
    )
    db.add(session)
    db.commit()

    # Send first message
    result1 = direct_chat_agent.process_request(
        'process_chat_message',
        {
            'session_id': session.id,
            'user_id': user.id,
            'message': 'I want to use Python',
            'project_id': project.id
        }
    )

    # Send follow-up message (should reference previous)
    result2 = direct_chat_agent.process_request(
        'process_chat_message',
        {
            'session_id': session.id,
            'user_id': user.id,
            'message': 'What web framework would you recommend?',
            'project_id': project.id
        }
    )

    assert result2['success'] == True
    # Response should be contextually aware (mention Python)
    assert 'python' in result2['response'].lower() or \
           'fastapi' in result2['response'].lower() or \
           'django' in result2['response'].lower()

def test_spec_extraction_from_chat():
    """Test that specs are extracted from natural conversation"""
    session = Session(
        project_id=project.id,
        user_id=user.id,
        mode='direct_chat',
        status='active'
    )
    db.add(session)
    db.commit()

    result = direct_chat_agent.process_request(
        'process_chat_message',
        {
            'session_id': session.id,
            'user_id': user.id,
            'message': '''I need a web application where users can register, login,
                         and manage their profiles. It should use PostgreSQL for
                         the database and be deployed on AWS.''',
            'project_id': project.id
        }
    )

    assert result['success'] == True
    assert result['specs_extracted'] >= 3  # Should extract multiple specs
    # Verify specs were actually saved
    specs = db.query(Specification).filter_by(project_id=project.id).all()
    assert len(specs) >= 3

def test_conflict_detection_in_direct_chat():
    """Test that conflict detection still works in direct chat mode"""
    # Create existing spec
    existing_spec = Specification(
        project_id=project.id,
        category='tech_stack',
        key='database',
        value='MySQL',
        source='socratic_question'
    )
    db.add(existing_spec)
    db.commit()

    session = Session(
        project_id=project.id,
        user_id=user.id,
        mode='direct_chat',
        status='active'
    )
    db.add(session)
    db.commit()

    # Send conflicting message
    result = direct_chat_agent.process_request(
        'process_chat_message',
        {
            'session_id': session.id,
            'user_id': user.id,
            'message': 'Actually, I want to use PostgreSQL instead',
            'project_id': project.id
        }
    )

    assert result['success'] == True
    assert result['conflicts_detected'] == True
```

---

## ✅ Verification

- [ ] DirectChatAgent created
- [ ] Mode toggle works (Socratic ↔ Direct Chat)
- [ ] Chat messages processed with context awareness
- [ ] Conversation history maintained
- [ ] Specifications extracted from natural conversation
- [ ] Conflict detection works in direct chat
- [ ] Quality control still applies
- [ ] Suggested clarifying questions provided when appropriate
- [ ] Tests pass: `pytest tests/test_phase_7_direct_chat.py`

---

## 📊 Success Metrics

**Phase 7 succeeds when:**
1. Users can seamlessly switch between Socratic and Direct Chat modes
2. Direct chat maintains full context awareness
3. Specifications are extracted accurately from natural conversation
4. Conflict detection works identically in both modes
5. Users can have natural conversations without losing structure

**Example Success Case:**
- User starts in Socratic mode (structured questions)
- Switches to Direct Chat: "I want to discuss the tech stack"
- Has natural conversation about technologies
- System extracts: frontend=React, backend=FastAPI, database=PostgreSQL
- User switches back to Socratic mode seamlessly
- All specifications retained, maturity calculated correctly

---

## 🔄 Workflow Comparison

### Socratic Mode (Phase 2):
```
System: "What is the primary goal of your project?"
User: "Build a task management app"
System: "Who are the main users?"
User: "Project managers and team members"
```
**Structured, guided, question-answer format**

### Direct Chat Mode (Phase 7):
```
User: "I want to build a task management app"
System: "Great! A task management app can be very useful.
        Can you tell me more about your vision?"
User: "Users should be able to create projects, assign tasks,
       and track progress"
System: "That sounds like a comprehensive system. Are you thinking
        of a web application or mobile app?"
```
**Natural, conversational, user-driven format**

**Both modes:** Extract specs, detect conflicts, calculate maturity identically

---

**Previous:** [PHASE_6.md](PHASE_6.md)
**Next:** [PHASE_8.md](PHASE_8.md) - Team Collaboration
