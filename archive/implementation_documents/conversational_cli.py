#!/usr/bin/env python3
"""
Conversational CLI for Socrates - Natural Language Interface

Transforms the CLI into an AI-powered conversational interface where users
can describe what they want instead of typing commands. Powered by Claude.

Usage:
    python conversational_cli.py
"""

import json
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

try:
    from anthropic import Anthropic
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
except ImportError as e:
    print(f"Error: Missing required packages for conversational CLI")
    print(f"Install with: pip install anthropic rich")
    sys.exit(1)


class MenuContext:
    """Represents a menu context in the conversation"""

    def __init__(self, name: str, exit_handler=None):
        self.name = name
        self.exit_handler = exit_handler


class ConversationalCLI:
    """
    AI-powered conversational CLI for Socrates.

    Users describe what they want in natural language, and Claude interprets
    their intent to execute actions. Supports slash commands and graceful menu exits.
    """

    # Available models (latest versions)
    AVAILABLE_MODELS = {
        '1': {'name': 'claude-sonnet-4.5-20250929', 'display': 'Claude Sonnet 4.5 (Most capable)'},
        '2': {'name': 'claude-haiku-4.5-20251001', 'display': 'Claude Haiku 4.5 (Fast & affordable)'},
        '3': {'name': 'claude-opus-4-1-20250805', 'display': 'Claude Opus 4 (Most advanced)'},
    }

    # Available operations that can be executed
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
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the conversational CLI.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.console = Console()
        self.client = Anthropic(api_key=api_key)

        # User state
        self.current_user = None
        self.current_project = None
        self.current_session = None
        self.current_model = self.AVAILABLE_MODELS['1']['name']

        # Menu navigation
        self.menu_stack: List[MenuContext] = []

        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []

        # Mock auth token (in production, would be real JWT)
        self.auth_token = None

    def run(self):
        """Start the conversational CLI"""
        self._show_welcome()
        self._main_loop()

    def _show_welcome(self):
        """Display welcome message and instructions"""
        welcome_text = """
# 🎯 Socrates Interactive Mode

Welcome to **Socrates** - AI-powered specification gathering!

You can:
- **Describe what you want** in natural language
- **Use slash commands** like `/help`, `/logout`, `/model`
- **Type `/back`** to exit any menu
- **Mix natural language with commands** seamlessly

Try things like:
- "Register a user named John with email john@x.com and password xyz"
- "Create a project called Mobile App"
- "Start a session for my project"
- "What are the missing specifications?"

Type `/help` for full command list.
Type `/logout` to exit.
        """

        self.console.print(Panel(
            Markdown(welcome_text.strip()),
            title="Welcome to Socrates",
            border_style="green"
        ))

    def _main_loop(self):
        """Main conversation loop"""
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]").strip()

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith('/'):
                    self._handle_slash_command(user_input)
                else:
                    # Interpret natural language
                    self._handle_natural_language(user_input)

            except KeyboardInterrupt:
                self._show_goodbye()
                break
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

    def _handle_slash_command(self, command: str):
        """Handle slash commands"""
        cmd = command.split()[0].lower()

        if cmd == '/help':
            self._show_help()
        elif cmd == '/logout':
            self._handle_logout()
        elif cmd == '/model':
            self._select_model()
        elif cmd == '/back' or cmd == '/cancel':
            self._pop_menu()
        elif cmd == '/whoami':
            self._show_user_info()
        elif cmd == '/quit' or cmd == '/exit':
            self._show_goodbye()
            sys.exit(0)
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("Type [bold]/help[/bold] for available commands")

    def _handle_natural_language(self, user_input: str):
        """Process natural language input using Claude"""
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Get intent from Claude
            intent = self._get_intent_from_claude(user_input)

            if intent and intent.get('operation'):
                # Execute the intended operation
                result = self._execute_intent(intent)

                # Show result to user
                if result.get('success'):
                    self.console.print(f"[green]✓ {result.get('message', 'Operation completed')}[/green]")
                    if result.get('details'):
                        self.console.print(f"[dim]{result['details']}[/dim]")
                else:
                    self.console.print(f"[red]✗ {result.get('error', 'Operation failed')}[/red]")

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": result.get('message', 'Operation completed')
                })
            else:
                # Just have a conversation
                response = self._chat_with_claude(user_input)
                self.console.print(f"\n[bold cyan]Socrates[/bold cyan]: {response}")

                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

        except json.JSONDecodeError:
            self.console.print("[yellow]Could not parse response. Please rephrase.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")

    def _get_intent_from_claude(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Ask Claude to interpret user intent and return structured JSON.

        Returns:
            Dict with 'operation' and 'params' keys, or None if not an operation request
        """
        operations_list = "\n".join([
            f"- {op}: {details['description']}"
            for op, details in self.AVAILABLE_OPERATIONS.items()
        ])

        prompt = f"""
You are Claude, an AI assistant for Socrates specification gathering system.

Current user state:
- Logged in: {self.current_user is not None}
- Current user: {self.current_user or 'None'}
- Current project: {self.current_project or 'None'}
- Current model: {self.current_model}

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

IMPORTANT: Return ONLY valid JSON, nothing else.
"""

        try:
            response = self.client.messages.create(
                model=self.current_model,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text.strip()

            # Try to parse JSON
            data = json.loads(response_text)

            if data.get('is_operation'):
                return {
                    'operation': data.get('operation'),
                    'params': data.get('params', {}),
                    'explanation': data.get('explanation', '')
                }
            else:
                # It's conversation, show response
                if data.get('response'):
                    self.console.print(f"\n[bold cyan]Socrates[/bold cyan]: {data['response']}")
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": data['response']
                    })
                return None

        except json.JSONDecodeError as e:
            self.console.print(f"[yellow]Could not understand. Please rephrase.[/yellow]")
            return None

    def _chat_with_claude(self, user_input: str) -> str:
        """Have a general conversation with Claude"""
        system_prompt = f"""You are Socrates, an AI assistant for specification gathering.
You help users create and refine product specifications, identify gaps, resolve conflicts, and generate code.

Current state:
- User logged in: {self.current_user is not None}
- In project: {self.current_project is not None}
- Using model: {self.current_model}

Be helpful, concise, and guide users toward useful actions.
When appropriate, suggest using specific operations (register, create_project, start_session, etc.)
"""

        try:
            response = self.client.messages.create(
                model=self.current_model,
                max_tokens=500,
                system=system_prompt,
                messages=self.conversation_history[-10:] if self.conversation_history else []
            )

            return response.content[0].text

        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"

    def _execute_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the intended operation.

        In a real implementation, this would call the actual API/agent methods.
        For now, we'll mock the responses.
        """
        operation = intent.get('operation')
        params = intent.get('params', {})

        # Mock operation handlers
        if operation == 'register_user':
            return self._mock_register_user(params)
        elif operation == 'login_user':
            return self._mock_login_user(params)
        elif operation == 'logout_user':
            return self._mock_logout_user()
        elif operation == 'create_project':
            return self._mock_create_project(params)
        elif operation == 'list_projects':
            return self._mock_list_projects()
        elif operation == 'start_session':
            return self._mock_start_session(params)
        elif operation == 'ask_question':
            return self._mock_ask_question(params)
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}

    # Mock operation handlers (in production, call real APIs)
    def _mock_register_user(self, params: Dict) -> Dict[str, Any]:
        """Mock user registration"""
        name = params.get('name', 'User')
        email = params.get('email', '')

        if not email:
            return {'success': False, 'error': 'Email is required'}

        self.current_user = {'name': name, 'email': email}
        return {
            'success': True,
            'message': f'User "{name}" registered successfully',
            'details': f'Email: {email}'
        }

    def _mock_login_user(self, params: Dict) -> Dict[str, Any]:
        """Mock user login"""
        email = params.get('email', '')

        if not email:
            return {'success': False, 'error': 'Email is required'}

        self.current_user = {'name': 'Test User', 'email': email}
        self.auth_token = f"token_{email}"
        return {
            'success': True,
            'message': f'Logged in as {email}',
            'details': 'Ready to start building specifications'
        }

    def _mock_logout_user(self) -> Dict[str, Any]:
        """Mock user logout"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}

        self.current_user = None
        self.auth_token = None
        self.current_project = None
        return {
            'success': True,
            'message': 'Logged out successfully'
        }

    def _mock_create_project(self, params: Dict) -> Dict[str, Any]:
        """Mock project creation"""
        if not self.current_user:
            return {'success': False, 'error': 'Must be logged in to create project'}

        name = params.get('name', 'Untitled')
        description = params.get('description', '')

        self.current_project = {'name': name, 'description': description}
        return {
            'success': True,
            'message': f'Project "{name}" created',
            'details': f'Description: {description or "No description"}'
        }

    def _mock_list_projects(self) -> Dict[str, Any]:
        """Mock listing projects"""
        if not self.current_user:
            return {'success': False, 'error': 'Must be logged in'}

        # Mock data
        projects = [
            {'name': 'Mobile App', 'phase': 'discovery'},
            {'name': 'API Redesign', 'phase': 'specification'}
        ]

        return {
            'success': True,
            'message': f'Found {len(projects)} projects',
            'details': '\n'.join([f"- {p['name']} ({p['phase']})" for p in projects])
        }

    def _mock_start_session(self, params: Dict) -> Dict[str, Any]:
        """Mock session start"""
        if not self.current_user:
            return {'success': False, 'error': 'Must be logged in'}

        self.current_session = {'started_at': datetime.now()}
        return {
            'success': True,
            'message': 'Session started',
            'details': 'Ready to gather specifications. Ask me questions about your project!'
        }

    def _mock_ask_question(self, params: Dict) -> Dict[str, Any]:
        """Mock asking a question"""
        question = params.get('question', '')

        if not question:
            return {'success': False, 'error': 'Question is required'}

        return {
            'success': True,
            'message': 'Question recorded',
            'details': f'Q: {question}\nA: [Response from Socratic agent]'
        }

    def _select_model(self):
        """Let user select which Claude model to use"""
        self.console.print("\n[bold]Select Model:[/bold]")
        for key, model_info in self.AVAILABLE_MODELS.items():
            self.console.print(f"{key}. {model_info['display']}")

        choice = Prompt.ask("Choice").strip()

        if choice in self.AVAILABLE_MODELS:
            self.current_model = self.AVAILABLE_MODELS[choice]['name']
            display_name = self.AVAILABLE_MODELS[choice]['display']
            self.console.print(f"[green]✓ Using {display_name}[/green]")
        else:
            self.console.print("[yellow]Invalid choice. Model unchanged.[/yellow]")

    def _push_menu(self, menu_name: str, exit_handler=None):
        """Enter a menu context"""
        self.menu_stack.append(MenuContext(menu_name, exit_handler))
        self.console.print(f"[dim]Entered: {menu_name}[/dim]")

    def _pop_menu(self):
        """Exit current menu context"""
        if self.menu_stack:
            menu = self.menu_stack.pop()
            if menu.exit_handler:
                menu.exit_handler()
            self.console.print(f"[green]✓ Exited {menu.name}[/green]")
        else:
            self.console.print("[yellow]Not in a menu[/yellow]")

    def _show_help(self):
        """Show help information"""
        help_text = """
## Commands

- `/model` - Choose which Claude model to use
- `/whoami` - Show current user info
- `/help` - Show this help
- `/back` or `/cancel` - Exit current menu
- `/logout` - Log out
- `/quit` or `/exit` - Exit Socrates

## Natural Language Examples

- "Register a user named John with email john@x.com and password xyz"
- "Log me in with my email"
- "Create a new project called Mobile App"
- "List all my projects"
- "Start a session"
- "What specifications are missing?"
- "Generate code for my project"

## Tips

- You can describe what you want in natural language
- Mix slash commands and natural language
- Type `/back` to exit any menu
- Type `/logout` to exit your account
        """

        self.console.print(Panel(
            Markdown(help_text.strip()),
            title="Help",
            border_style="blue"
        ))

    def _show_user_info(self):
        """Show current user information"""
        if self.current_user:
            info = f"""
**Email:** {self.current_user.get('email')}
**Name:** {self.current_user.get('name')}
**Current Project:** {self.current_project.get('name') if self.current_project else 'None'}
**Current Model:** {self.current_model}
            """
            self.console.print(Panel(
                Markdown(info.strip()),
                title="User Info",
                border_style="cyan"
            ))
        else:
            self.console.print("[yellow]Not logged in[/yellow]")

    def _handle_logout(self):
        """Handle logout"""
        result = self._execute_intent({'operation': 'logout_user', 'params': {}})
        if result['success']:
            self.console.print(f"[green]✓ {result['message']}[/green]")
        else:
            self.console.print(f"[red]✗ {result['error']}[/red]")

    def _show_goodbye(self):
        """Show goodbye message"""
        goodbye_text = "Thanks for using Socrates! Goodbye! 👋"
        self.console.print(f"\n[bold green]{goodbye_text}[/bold green]")


def main():
    """Main entry point"""
    cli = ConversationalCLI()
    cli.run()


if __name__ == "__main__":
    main()
