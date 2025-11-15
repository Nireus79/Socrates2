"""
Natural Language Intent Parser for Socrates CLI.

Converts user natural language input to CLI commands using:
1. Pattern matching (fast, no API calls)
2. Claude-based parsing (flexible, uses LLM)
"""

import re
from typing import Any, Dict, List, Optional


class IntentParser:
    """
    Natural Language Intent Parser - converts user input to CLI commands.

    Two-level approach:
    1. Pattern matching for common phrases (fast, no API calls)
    2. Claude-based parsing for complex requests (flexible, uses LLM)
    """

    def __init__(self, api: Optional["SocratesAPI"] = None, console: Optional["Console"] = None):
        """Initialize the intent parser"""
        self.api = api
        self.console = console

        # Pattern-based intent mappings
        # Format: (pattern_regex, command_template, param_extractor)
        self.patterns = [
            # Project creation
            (r'(?:create|make|new)\s+(?:project|proj)\s+(?:called|named)?\s*["\']?(\w+)["\']?',
             lambda m: ("/project create", [m.group(1)])),

            # Project selection/opening
            (r'(?:open|select|choose|go to)\s+(?:project|proj)\s+["\']?(\w+)["\']?',
             lambda m: ("/project select", [m.group(1)])),

            # Session management
            (r'(?:start|begin|create)\s+(?:session|chat)',
             lambda m: ("/session start", [])),

            (r'(?:end|stop|close)\s+(?:session|chat)',
             lambda m: ("/session end", [])),

            # Mode switching
            (r'(?:switch|change|go to)\s+(?:socratic|direct)\s+(?:mode|chat)?',
             lambda m: ("/mode " + m.group(1) if m.lastindex else "/mode", [])),

            # LLM model selection (with explicit "model/llm" keyword)
            (r'(?:use|switch\s+to|select)\s+(?:model|llm)\s+(.+?)(?:\s*$|\s+)',
             lambda m: ("_parse_model_selection", [m.group(1).strip()])),

            # List operations
            (r'(?:list|show|view)\s+(?:projects|sessions|models)',
             lambda m: ("_get_list_command", [m.group(0)])),

            # Export/Save operations
            (r'(?:save|export)\s+(?:as\s+)?(?:markdown|json|csv|pdf)',
             lambda m: ("_get_export_command", [m.group(0)])),

            # Document management
            (r'(?:upload|add|import)\s+(?:document|doc|file)\s+(.+)',
             lambda m: ("/doc upload", [m.group(1)])),

            (r'(?:list|show|view)\s+(?:documents|docs)',
             lambda m: ("/doc list", [])),

            (r'(?:search|find)\s+(?:in\s+)?(?:documents|docs)\s+(?:for\s+)?(.+)',
             lambda m: ("/doc search", [m.group(1)])),

            # GitHub integration
            (r'(?:import|fetch|download)\s+(?:from\s+)?github\s+(.+)',
             lambda m: ("/fetch github", [m.group(1)])),

            (r'(?:connect|setup)\s+github',
             lambda m: ("/fetch github connect", [])),

            # Code generation
            (r'(?:generate|create)(?:\s+\w+)?\s+(?:code|software|app|application|project)',
             lambda m: ("/code generate", [])),

            (r'(?:list|show|view)\s+(?:code\s+)?generations?',
             lambda m: ("/code list", [])),

            (r'(?:check|show)\s+(?:(?:my|me|the|your|you|our|us)\s+)*(?:(?:code|generation)\s+)?status(?:\s+for\s+)?(.+)?',
             lambda m: ("_code_status", [m.group(1).strip()] if m.lastindex and m.group(1) else [])),

            (r'(?:download|get)\s+(?:my\s+)?(?:the\s+)?(?:generated\s+)?code(?:\s+for\s+)?(.+)?',
             lambda m: ("_code_download", [m.group(1).strip()] if m.lastindex and m.group(1) else [])),

            (r'(?:preview|show|view)\s+(?:(?:my|the|generated|code|preview)\s+)*(?:for\s+)?(\S+)?',
             lambda m: ("_code_preview", [m.group(1).strip()] if m.lastindex and m.group(1) else [])),

            # Help - only at start of input
            (r'^help(?:\s+(.+))?$',
             lambda m: ("/help " + m.group(1).strip() if m.lastindex and m.group(1) else "/help", [])),
        ]

    def parse(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parse user input and return command details or None.

        Returns:
            {
                'intent': str,
                'command': str,
                'args': List[str],
                'confidence': float (0.0-1.0),
                'requires_confirmation': bool
            }
        """
        user_input = user_input.strip().lower()

        # Skip if it's already a command
        if user_input.startswith('/'):
            return None

        # Level 1: Try pattern matching
        result = self._try_pattern_matching(user_input)
        if result:
            return result

        # Level 2: Try Claude-based parsing for complex requests
        if self.api and self.console:
            result = self._try_claude_parsing(user_input)
            if result:
                return result

        return None

    def _try_pattern_matching(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Try to match against known patterns"""
        for pattern, handler in self.patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                try:
                    result = handler(match)
                    if isinstance(result, tuple):
                        command, args = result

                        # Handle special cases
                        if command == "_parse_model_selection":
                            return self._parse_model_selection(args[0])
                        elif command == "_get_list_command":
                            return self._get_list_command(args[0])
                        elif command == "_get_export_command":
                            return self._get_export_command(args[0])
                        elif command == "_code_status":
                            return self._parse_code_status(args)
                        elif command == "_code_download":
                            return self._parse_code_download(args)
                        elif command == "_code_preview":
                            return self._parse_code_preview(args)

                        return {
                            'intent': 'command',
                            'command': command,
                            'args': args,
                            'confidence': 0.95,
                            'requires_confirmation': False
                        }
                except Exception as e:
                    if self.console:
                        self.console.print(f"[DEBUG] Pattern matching error: {e}")
                    continue

        return None

    def _parse_model_selection(self, model_spec: str) -> Dict[str, Any]:
        """Parse model selection like 'gpt-4' or 'anthropic claude-3.5-sonnet'"""
        parts = model_spec.strip().split()

        if len(parts) == 1:
            # Just model name, try to guess provider
            model_name = parts[0]
            provider = self._guess_provider(model_name)
        else:
            provider = parts[0]
            model_name = " ".join(parts[1:])

        return {
            'intent': 'select_model',
            'command': '/llm select',
            'args': [provider, model_name],
            'confidence': 0.9,
            'requires_confirmation': True
        }

    def _get_list_command(self, text: str) -> Dict[str, Any]:
        """Map list requests to appropriate commands"""
        if 'project' in text.lower():
            command = '/projects'
        elif 'session' in text.lower():
            command = '/sessions'
        elif 'model' in text.lower() or 'llm' in text.lower():
            command = '/llm list'
        else:
            command = '/help'

        return {
            'intent': 'list',
            'command': command,
            'args': [],
            'confidence': 0.9,
            'requires_confirmation': False
        }

    def _get_export_command(self, text: str) -> Dict[str, Any]:
        """Map export requests to appropriate commands"""
        format_map = {
            'markdown': 'markdown',
            'json': 'json',
            'csv': 'csv',
            'pdf': 'pdf'
        }

        format_type = 'markdown'  # default
        for fmt in format_map:
            if fmt in text.lower():
                format_type = format_map[fmt]
                break

        return {
            'intent': 'export',
            'command': '/export',
            'args': [format_type],
            'confidence': 0.9,
            'requires_confirmation': False
        }

    def _guess_provider(self, model_name: str) -> str:
        """Guess LLM provider from model name"""
        model_lower = model_name.lower()

        if 'claude' in model_lower or 'anthropic' in model_lower:
            return 'anthropic'
        elif 'gpt' in model_lower or 'openai' in model_lower:
            return 'openai'
        elif 'gemini' in model_lower or 'google' in model_lower:
            return 'google'
        else:
            return 'anthropic'  # default

    def _parse_code_status(self, args: List[str]) -> Dict[str, Any]:
        """Parse code status request"""
        if args and args[0]:
            gen_id = args[0].strip()
        else:
            gen_id = None

        return {
            'intent': 'code_status',
            'command': '/code status',
            'args': [gen_id] if gen_id else [],
            'confidence': 0.85 if gen_id else 0.7,
            'requires_confirmation': False
        }

    def _parse_code_download(self, args: List[str]) -> Dict[str, Any]:
        """Parse code download request"""
        if args and args[0]:
            gen_id = args[0].strip()
        else:
            gen_id = None

        return {
            'intent': 'code_download',
            'command': '/code download',
            'args': [gen_id] if gen_id else [],
            'confidence': 0.85 if gen_id else 0.7,
            'requires_confirmation': False
        }

    def _parse_code_preview(self, args: List[str]) -> Dict[str, Any]:
        """Parse code preview request"""
        if args and args[0]:
            gen_id = args[0].strip()
        else:
            gen_id = None

        return {
            'intent': 'code_preview',
            'command': '/code preview',
            'args': [gen_id] if gen_id else [],
            'confidence': 0.85 if gen_id else 0.7,
            'requires_confirmation': False
        }

    def _try_claude_parsing(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Use Claude to parse complex natural language requests.
        This is a fallback for requests that don't match patterns.
        """
        try:
            # Prepare prompt for Claude
            prompt = f"""Parse this user request into a Socrates CLI command.

User request: "{user_input}"

Available commands:
- /project create <name> - Create new project
- /project select <name> - Select existing project
- /session start - Start Socratic session
- /session end - End session
- /mode socratic/direct - Switch chat modes
- /llm list - List models
- /llm select <provider> <model> - Select LLM
- /save [filename] - Save session
- /export [format] - Export project
- /help - Show help

If the request matches a command, respond with JSON only:
{{"command": "/command arg1 arg2", "confidence": 0.9, "requires_confirmation": false}}

If no clear command match, respond: {{"command": null}}

Do not include markdown formatting or explanations."""

            # Call Claude via API
            response = self.api._request(
                "POST",
                "/api/v1/llm/parse-intent",
                json={"prompt": prompt}
            )

            if response.status_code == 200:
                result = response.json()
                parsed = result.get("parsed", {})

                if parsed.get("command"):
                    # Parse the command response
                    command_str = parsed["command"].strip()
                    parts = command_str.split(None, 1)

                    return {
                        'intent': 'claude_parsed',
                        'command': parts[0],
                        'args': parts[1:] if len(parts) > 1 else [],
                        'confidence': parsed.get("confidence", 0.7),
                        'requires_confirmation': parsed.get("requires_confirmation", True)
                    }
        except Exception as e:
            if self.console:
                self.console.print(f"[DEBUG] Claude parsing error: {e}")

        return None
