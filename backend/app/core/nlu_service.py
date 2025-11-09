"""
Natural Language Understanding Service for Socrates2

Provides natural language interpretation for all user-facing components:
- Conversational CLI
- Direct Chat Agent
- Socratic Counselor (for conversational mode)
- Any future conversational interfaces

Features:
- Intent parsing: Converts user text to structured operations
- Conversational responses: Handles non-operational queries
- Context awareness: Uses conversation history for context
- Model flexibility: Supports different Claude models
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from anthropic import Anthropic


@dataclass
class Intent:
    """Structured representation of user intent"""
    is_operation: bool  # True if operation request, False if conversation
    operation: Optional[str] = None  # Operation name (if is_operation=True)
    params: Optional[Dict[str, Any]] = None  # Operation parameters
    explanation: Optional[str] = None  # Brief explanation of action
    response: Optional[str] = None  # Conversational response (if is_operation=False)


class NLUService:
    """
    Natural Language Understanding service for Socrates2.

    Transforms user natural language input into structured operations or
    conversational responses using Claude API.

    Usage:
        nlu = NLUService(claude_client)
        intent = nlu.parse_intent("Create a project called Mobile App")

        if intent.is_operation:
            # Execute operation
            perform_operation(intent.operation, intent.params)
        else:
            # Have conversation
            display_response(intent.response)
    """

    # Available operations that users can request
    AVAILABLE_OPERATIONS = {
        'register_user': {
            'description': 'Create a new user account',
            'params': ['name', 'email', 'password']
        },
        'login_user': {
            'description': 'Log in to existing account',
            'params': ['email', 'password']
        },
        'logout_user': {
            'description': 'Log out from current account',
            'params': []
        },
        'create_project': {
            'description': 'Create a new project',
            'params': ['name', 'description']
        },
        'list_projects': {
            'description': 'List all user projects',
            'params': []
        },
        'start_session': {
            'description': 'Start a new specification gathering session',
            'params': ['project_id']
        },
        'ask_question': {
            'description': 'Ask a question in current session',
            'params': ['question']
        },
        'resolve_conflict': {
            'description': 'Resolve a specification conflict',
            'params': ['conflict_id', 'resolution']
        },
        'view_insights': {
            'description': 'View project insights (gaps, risks, opportunities)',
            'params': ['project_id']
        },
        'export_project': {
            'description': 'Export project in various formats',
            'params': ['project_id', 'format']
        },
        'ask_socratic': {
            'description': 'Ask the Socratic agent a question',
            'params': ['question', 'session_id']
        },
        'toggle_mode': {
            'description': 'Switch between Socratic and Direct Chat mode',
            'params': ['session_id', 'mode']
        },
    }

    def __init__(self, claude_client: Anthropic, logger: Optional[logging.Logger] = None):
        """
        Initialize NLU service.

        Args:
            claude_client: Anthropic client for API calls
            logger: Optional logger instance
        """
        self.client = claude_client
        self.logger = logger or logging.getLogger(__name__)
        self.current_model = "claude-sonnet-4-5-20250929"  # Default model
        self.conversation_history: List[Dict[str, str]] = []

    def set_model(self, model_name: str) -> None:
        """Set the Claude model to use"""
        self.current_model = model_name
        self.logger.debug(f"NLU model switched to: {model_name}")

    def add_to_history(self, role: str, content: str) -> None:
        """Add message to conversation history for context"""
        self.conversation_history.append({"role": role, "content": content})
        # Keep history to last 20 messages to avoid context explosion
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []

    def parse_intent(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Intent:
        """
        Parse user input to determine intent (operation vs conversation).

        Args:
            user_input: User's natural language input
            context: Optional context dict with keys:
                - current_user: User name (for personalization)
                - current_project: Project name
                - current_session: Session ID
                - conversation_context: Additional context

        Returns:
            Intent object with parsed information
        """
        try:
            # Build operations list for prompt
            operations_list = "\n".join([
                f"- {op}: {details['description']}"
                for op, details in self.AVAILABLE_OPERATIONS.items()
            ])

            # Prepare context information
            user_info = "None"
            project_info = "None"
            if context:
                if context.get('current_user'):
                    user_info = context['current_user']
                if context.get('current_project'):
                    project_info = context['current_project']

            prompt = f"""You are Claude, an AI assistant for Socrates specification gathering system.

Current user state:
- Logged in: {user_info != 'None'}
- Current user: {user_info}
- Current project: {project_info}

Available operations:
{operations_list}

User input: "{user_input}"

If the user is requesting one of the available operations, respond with ONLY valid JSON (no markdown, no extra text):
{{
    "is_operation": true,
    "operation": "operation_name",
    "params": {{"param1": "value1", "param2": "value2"}},
    "explanation": "Brief explanation of what will happen"
}}

If it's just conversation or a question, respond with:
{{
    "is_operation": false,
    "response": "Your conversational response here"
}}

IMPORTANT: Return ONLY valid JSON, nothing else."""

            self.logger.debug(f"Calling Claude API to parse intent for: {user_input[:50]}...")

            response = self.client.messages.create(
                model=self.current_model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            self.logger.debug(f"Claude response: {response_text}")

            # Parse JSON response
            data = json.loads(response_text)

            # Create Intent object
            if data.get('is_operation'):
                intent = Intent(
                    is_operation=True,
                    operation=data.get('operation'),
                    params=data.get('params', {}),
                    explanation=data.get('explanation', '')
                )
            else:
                intent = Intent(
                    is_operation=False,
                    response=data.get('response', '')
                )

            return intent

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse Claude response as JSON: {e}")
            # Return conversational intent asking for clarification
            return Intent(
                is_operation=False,
                response="I didn't quite understand that. Could you rephrase your request?"
            )
        except Exception as e:
            self.logger.error(f"Error parsing intent: {e}")
            raise

    def chat(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Have a conversational interaction with Claude.

        Args:
            user_input: User's message
            system_prompt: Optional custom system prompt
            conversation_context: Optional conversation history

        Returns:
            Claude's response text
        """
        if system_prompt is None:
            system_prompt = """You are Socrates, an AI assistant for specification gathering.
You help users create and refine product specifications, identify gaps, resolve conflicts, and generate code.
Be helpful, concise, and guide users toward useful actions.
When appropriate, suggest using specific operations."""

        try:
            # Use provided history or fall back to internal history
            messages = conversation_context or self.conversation_history[-10:]
            messages = list(messages)  # Make a copy
            messages.append({"role": "user", "content": user_input})

            self.logger.debug(f"Calling Claude chat API with {len(messages)} messages")

            response = self.client.messages.create(
                model=self.current_model,
                max_tokens=500,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            raise

    def extract_parameters(
        self,
        user_input: str,
        operation: str,
        required_params: List[str]
    ) -> Dict[str, Any]:
        """
        Extract operation parameters from user input using Claude.

        Args:
            user_input: User's natural language input
            operation: Operation name
            required_params: List of required parameter names

        Returns:
            Dictionary of extracted parameters
        """
        try:
            prompt = f"""Extract parameters from user input for the "{operation}" operation.

Required parameters: {', '.join(required_params)}

User input: "{user_input}"

Respond with ONLY valid JSON:
{{
    "params": {{"param_name": "value", ...}},
    "missing": ["param_name", ...],
    "confidence": 0.95
}}

Be intelligent about extracting values. For example:
- Email format: name@domain.com
- Names: proper capitalization
- Passwords: exact text provided
- Dates: ISO format

If parameters are unclear or missing, list them in "missing"."""

            response = self.client.messages.create(
                model=self.current_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            data = json.loads(response.content[0].text.strip())
            return data.get('params', {})

        except Exception as e:
            self.logger.error(f"Error extracting parameters: {e}")
            return {}


def create_nlu_service(claude_client: Anthropic, logger: Optional[logging.Logger] = None) -> NLUService:
    """Factory function to create NLU service"""
    return NLUService(claude_client, logger)
