"""
DirectChatAgent - Handles free-form direct chat with automatic spec extraction.

This agent enables natural conversation mode alongside Socratic questioning:
1. Process chat messages with full context awareness
2. Toggle between socratic and direct_chat modes
3. Extract specifications from natural conversation
4. Maintain conversation context and project state
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from ..models import Session, ConversationHistory, Specification, Project
from .base import BaseAgent


class DirectChatAgent(BaseAgent):
    """
    Direct Chat Agent - enables free-form conversation with automatic spec extraction.

    Capabilities:
    - process_chat_message: Handle direct chat messages with context awareness
    - toggle_mode: Switch session between socratic and direct_chat modes
    - get_mode: Get current session mode
    - maintain_context: Load and maintain conversation context
    """

    def __init__(self, agent_id: str, name: str, services=None):
        """Initialize Direct Chat Agent"""
        super().__init__(agent_id, name, services)
        self.logger = logging.getLogger(__name__)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            'process_chat_message',
            'toggle_mode',
            'get_mode',
            'maintain_context'
        ]

    def _process_chat_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a direct chat message with full context awareness.

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
                'suggested_next_question': str (optional),
                'maturity_score': int
            }
        """
        session_id = data['session_id']
        user_id = data['user_id']
        message = data['message']
        project_id = data.get('project_id')  # Optional, will be loaded from session
        specs_session = self.services.get_database_specs()

        # Verify session exists and get project_id from it
        session = specs_session.query(Session).get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}

        # Get project_id from session if not provided
        if not project_id:
            project_id = session.project_id

        if session.mode != 'direct_chat':
            return {
                'success': False,
                'error': f'Session is in {session.mode} mode, not direct_chat mode'
            }

        # Load conversation context (recent messages)
        context = self._load_conversation_context(session_id)

        # Load project context (specs, maturity, etc.)
        project_context = self._load_project_context(project_id)

        # Build chat prompt with full context
        prompt = self._build_chat_prompt(message, context, project_context)

        # Call Claude API for response
        claude_client = self.services.get_claude_client()
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            chat_response = response.content[0].text
        except Exception as e:
            self.logger.error(f"Claude API error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to get response from Claude: {str(e)}'
            }

        # Save conversation history (both user message and assistant response)
        self._save_conversation_turn(session_id, message, chat_response)

        # Extract specifications from conversation
        from ..agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()

        extraction_result = orchestrator.route_request(
            'context',
            'extract_specifications',
            {
                'session_id': session_id,
                'conversation_text': f"User: {message}\nAssistant: {chat_response}",
                'user_id': user_id,
                'project_id': project_id
            }
        )

        specs_extracted = extraction_result.get('specs_extracted', 0) if extraction_result.get('success') else 0
        conflicts_detected = extraction_result.get('conflicts_detected', False) if extraction_result.get('success') else False

        # Optionally suggest a clarifying question
        suggested_question = None
        if specs_extracted > 0:
            suggested_question = self._suggest_clarifying_question(
                project_id,
                extraction_result.get('specs', [])
            )

        # Get updated maturity score
        project = specs_session.query(Project).get(project_id)
        maturity_score = project.maturity_score if project else 0

        return {
            'success': True,
            'response': chat_response,
            'specs_extracted': specs_extracted,
            'conflicts_detected': conflicts_detected,
            'suggested_next_question': suggested_question,
            'maturity_score': maturity_score
        }

    def _toggle_mode(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Toggle session mode between socratic and direct_chat.

        Args:
            data: {
                'session_id': UUID,
                'mode': str ('socratic' | 'direct_chat')
            }

        Returns:
            {'success': bool, 'old_mode': str, 'new_mode': str}
        """
        session_id = data['session_id']
        new_mode = data['mode']
        specs_session = self.services.get_database_specs()

        if new_mode not in ['socratic', 'direct_chat']:
            return {
                'success': False,
                'error': f"Invalid mode: {new_mode}. Must be 'socratic' or 'direct_chat'"
            }

        # Update session mode
        session = specs_session.query(Session).get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}

        old_mode = session.mode
        session.mode = new_mode
        session.updated_at = datetime.now(timezone.utc)

        specs_session.commit()

        self.logger.info(
            f"Session {session_id} mode changed: {old_mode} → {new_mode}"
        )

        return {
            'success': True,
            'old_mode': old_mode,
            'new_mode': new_mode
        }

    def _get_mode(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current session mode.

        Args:
            data: {'session_id': UUID}

        Returns:
            {'success': bool, 'mode': str, 'session_id': UUID, 'project_id': UUID}
        """
        session_id = data['session_id']
        specs_session = self.services.get_database_specs()

        session = specs_session.query(Session).get(session_id)

        if not session:
            return {
                'success': False,
                'error': 'Session not found'
            }

        return {
            'success': True,
            'mode': session.mode,
            'session_id': str(session.id),
            'project_id': str(session.project_id)
        }

    def _maintain_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load and return conversation context for a session.

        Args:
            data: {'session_id': UUID}

        Returns:
            {
                'success': bool,
                'recent_messages': List[dict],
                'message_count': int
            }
        """
        session_id = data['session_id']
        context = self._load_conversation_context(session_id)

        return {
            'success': True,
            'recent_messages': context['recent_messages'],
            'message_count': context['message_count']
        }

    def _load_conversation_context(self, session_id) -> Dict[str, Any]:
        """Load recent conversation history for context"""
        specs_session = self.services.get_database_specs()

        # Get last 5 conversation turns
        messages = specs_session.query(ConversationHistory).filter_by(
            session_id=session_id
        ).order_by(ConversationHistory.timestamp.desc()).limit(10).all()

        # Reverse to chronological order
        messages = list(reversed(messages))

        recent_messages = [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]

        return {
            'recent_messages': recent_messages,
            'message_count': len(messages)
        }

    def _load_project_context(self, project_id) -> Dict[str, Any]:
        """Load project context including specs and maturity"""
        specs_session = self.services.get_database_specs()

        project = specs_session.query(Project).get(project_id)
        if not project:
            return {}

        # Get current specifications
        specs = specs_session.query(Specification).filter_by(
            project_id=project_id,
            is_current=True
        ).all()

        # Group specs by category
        specs_by_category = {}
        for spec in specs:
            if spec.category not in specs_by_category:
                specs_by_category[spec.category] = []
            specs_by_category[spec.category].append(spec.content)

        return {
            'name': project.name,
            'description': project.description,
            'phase': project.current_phase,
            'maturity_score': project.maturity_score,
            'specifications': specs_by_category
        }

    def _build_chat_prompt(self, message: str, context: Dict, project_context: Dict) -> str:
        """Build comprehensive chat prompt with full context"""
        specs_text = self._format_specifications(project_context.get('specifications', {}))
        history_text = self._format_conversation_history(context.get('recent_messages', []))

        return f"""You are Socrates, an AI system that helps users build software through conversation.

**YOUR ROLE:**
- Engage in natural, helpful conversation
- Help clarify requirements and specifications
- Provide technical guidance when asked
- Ask clarifying questions when details are unclear
- Extract and remember important project specifications

**PROJECT CONTEXT:**
Project: {project_context.get('name', 'Unknown')}
Description: {project_context.get('description', 'No description')}
Current Phase: {project_context.get('phase', 'discovery')}
Maturity: {project_context.get('maturity_score', 0)}%

**EXISTING SPECIFICATIONS:**
{specs_text}

**CONVERSATION HISTORY (recent):**
{history_text}

**USER MESSAGE:**
{message}

**INSTRUCTIONS:**
- Respond naturally and helpfully to the user's message
- Reference existing specifications when relevant
- Ask clarifying questions if the user's request is ambiguous
- Provide specific technical guidance when appropriate
- Keep responses concise but informative (2-4 paragraphs max)
"""

    def _format_specifications(self, specs_by_category: Dict[str, List[str]]) -> str:
        """Format specifications for prompt"""
        if not specs_by_category:
            return "(No specifications defined yet)"

        lines = []
        for category, specs in specs_by_category.items():
            lines.append(f"\n{category.upper()}:")
            for spec in specs:
                lines.append(f"  - {spec}")

        return "\n".join(lines)

    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """Format conversation history for prompt"""
        if not messages:
            return "(No conversation history)"

        lines = []
        for msg in messages[-5:]:  # Last 5 messages
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:200]  # Truncate long messages
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _save_conversation_turn(self, session_id, user_message: str, assistant_message: str):
        """Save both user message and assistant response to conversation history"""
        specs_session = self.services.get_database_specs()

        # Save user message
        user_msg = ConversationHistory(
            session_id=session_id,
            role='user',
            content=user_message,
            timestamp=datetime.now(timezone.utc)
        )
        specs_session.add(user_msg)

        # Save assistant response
        assistant_msg = ConversationHistory(
            session_id=session_id,
            role='assistant',
            content=assistant_message,
            timestamp=datetime.now(timezone.utc)
        )
        specs_session.add(assistant_msg)

        specs_session.commit()

    def _suggest_clarifying_question(self, project_id, specs: List) -> str:
        """Suggest a clarifying question based on coverage gaps"""
        specs_session = self.services.get_database_specs()

        # Get all current specs
        all_specs = specs_session.query(Specification).filter_by(
            project_id=project_id,
            is_current=True
        ).all()

        # Count specs per category
        categories = {}
        for spec in all_specs:
            categories[spec.category] = categories.get(spec.category, 0) + 1

        # Find categories with < 3 specs
        sparse_categories = [cat for cat, count in categories.items() if count < 3]

        if sparse_categories:
            cat = sparse_categories[0]
            return f"Could you tell me more about your {cat} requirements?"

        return "Is there anything else you'd like to specify?"
