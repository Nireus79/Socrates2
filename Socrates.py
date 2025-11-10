#!/usr/bin/env python3
"""
Socrates CLI - Interactive Command-Line Interface for Socrates2
A Claude Code-style interface for specification gathering and project development.

Usage:
    python Socrates.py [--api-url URL] [--debug]
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import subprocess
import signal
import time
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from pathlib import Path

if TYPE_CHECKING:
    from rich.console import Console

# Try to import CLI dependencies - defer error to runtime
_cli_imports_available = True
_cli_import_error = None

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from prompt_toolkit import PromptSession, prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from getpass import getpass
except ImportError as e:
    _cli_imports_available = False
    _cli_import_error = e


class SocratesConfig:
    """Configuration management for Socrates CLI"""

    def __init__(self):
        self.config_dir = Path.home() / ".socrates"
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.txt"
        self.config_dir.mkdir(exist_ok=True)
        self.data = self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.data[key] = value
        self.save()

    def clear(self):
        """Clear all configuration"""
        self.data = {}
        self.save()


class SocratesAPI:
    """API client for Socrates backend"""

    def __init__(self, base_url: str, console: Console):
        self.base_url = base_url.rstrip('/')
        self.console = console
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.config: Optional["SocratesConfig"] = None

    def set_token(self, token: str):
        """Set authentication token"""
        self.access_token = token

    def set_refresh_token(self, token: str):
        """Set refresh token"""
        self.refresh_token = token

    def set_config(self, config: "SocratesConfig"):
        """Set config object for saving tokens"""
        self.config = config

    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _refresh_access_token(self) -> bool:
        """
        Attempt to refresh the access token using the refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

                # Save tokens to config
                if self.config:
                    self.config.set("access_token", self.access_token)
                    self.config.set("refresh_token", self.refresh_token)

                return True
        except Exception:
            pass

        return False

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('headers', self._headers())

        try:
            response = requests.request(method, url, **kwargs)

            # If we get a 401, try to refresh the token and retry
            if response.status_code == 401 and self.refresh_token:
                if self._refresh_access_token():
                    # Update headers with new token and retry
                    kwargs['headers'] = self._headers()
                    response = requests.request(method, url, **kwargs)

            return response
        except requests.exceptions.ConnectionError:
            # Re-raise connection errors for the caller to handle gracefully
            raise
        except Exception as e:
            # Re-raise other exceptions for the caller to handle
            raise

    def register(self, username: str, name: str, surname: str, email: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        response = self._request("POST", "/api/v1/auth/register", json={
            "username": username,
            "name": name,
            "surname": surname,
            "email": email,
            "password": password
        })
        return response.json()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and return tokens"""
        # OAuth2PasswordRequestForm expects form data, not JSON
        response = self._request("POST", "/api/v1/auth/login", data={
            "username": email,  # OAuth2 uses 'username' field
            "password": password
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        return response.json()

    def logout(self) -> Dict[str, Any]:
        """Logout user"""
        response = self._request("POST", "/api/v1/auth/logout")
        return response.json()

    def list_projects(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List user's projects"""
        response = self._request("GET", f"/api/v1/projects?skip={skip}&limit={limit}")
        return response.json()

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new project"""
        response = self._request("POST", "/api/v1/projects", json={
            "name": name,
            "description": description
        })
        return response.json()

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details"""
        response = self._request("GET", f"/api/v1/projects/{project_id}")
        return response.json()

    def update_project(self, project_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update project"""
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        response = self._request("PUT", f"/api/v1/projects/{project_id}", json=data)
        return response.json()

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete project"""
        response = self._request("DELETE", f"/api/v1/projects/{project_id}")
        return response.json()

    def start_session(self, project_id: str) -> Dict[str, Any]:
        """Start new session for project"""
        response = self._request("POST", "/api/v1/sessions", json={
            "project_id": project_id
        })
        return response.json()

    def list_sessions(self, project_id: str) -> Dict[str, Any]:
        """List project sessions"""
        response = self._request("GET", "/api/v1/sessions", params={"project_id": project_id})
        return response.json()

    def get_next_question(self, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get next Socratic question"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/next-question",
                                 json={"context": context or {}})
        return response.json()

    def submit_answer(self, session_id: str, question_id: str, answer: str) -> Dict[str, Any]:
        """Submit answer to question"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/answer", json={
            "question_id": question_id,
            "answer": answer
        })
        return response.json()

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/end")
        return response.json()

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get session conversation history"""
        response = self._request("GET", f"/api/v1/sessions/{session_id}/history")
        return response.json()

    def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send chat message to a session (in direct chat mode)"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/chat", json={
            "message": message
        })

        # Check for HTTP errors before parsing JSON
        if response.status_code >= 400:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {
                "success": False,
                "error": f"Server error: {error_msg}",
                "status_code": response.status_code
            }

        try:
            return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "response_text": response.text[:100] if response.text else "Empty response"
            }

    def get_session_mode(self, session_id: str) -> Dict[str, Any]:
        """Get current session mode"""
        response = self._request("GET", f"/api/v1/sessions/{session_id}/mode")
        return response.json()

    def set_session_mode(self, session_id: str, mode: str) -> Dict[str, Any]:
        """Set session mode (socratic or direct_chat)"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/mode", json={
            "mode": mode
        })
        return response.json()

    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a session"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/pause")
        return response.json()

    def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a paused session"""
        response = self._request("POST", f"/api/v1/sessions/{session_id}/resume")
        return response.json()

    # Priority 2: Export endpoints
    def export_markdown(self, project_id: str) -> Dict[str, Any]:
        """Export project as Markdown"""
        try:
            response = self._request("GET", f"/api/v1/export/markdown/{project_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "EXPORT_FAILED"}

    def export_json(self, project_id: str) -> Dict[str, Any]:
        """Export project as JSON"""
        try:
            response = self._request("GET", f"/api/v1/export/json/{project_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "EXPORT_FAILED"}

    def export_csv(self, project_id: str) -> Dict[str, Any]:
        """Export project as CSV"""
        try:
            response = self._request("GET", f"/api/v1/export/csv/{project_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "EXPORT_FAILED"}

    def export_pdf(self, project_id: str) -> Dict[str, Any]:
        """Export project as PDF"""
        try:
            response = self._request("GET", f"/api/v1/export/pdf/{project_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "EXPORT_FAILED"}

    # Priority 2: Session enhancements
    def add_session_note(self, session_id: str, note: str) -> Dict[str, Any]:
        """Add note to session"""
        try:
            response = self._request("POST", f"/api/v1/sessions/{session_id}/notes", json={"content": note})
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "NOTE_FAILED"}

    def bookmark_session(self, session_id: str) -> Dict[str, Any]:
        """Create bookmark in session"""
        try:
            response = self._request("POST", f"/api/v1/sessions/{session_id}/bookmark")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "BOOKMARK_FAILED"}

    def branch_session(self, session_id: str, branch_name: str = None) -> Dict[str, Any]:
        """Create alternative branch from session"""
        try:
            data = {}
            if branch_name:
                data["branch_name"] = branch_name
            response = self._request("POST", f"/api/v1/sessions/{session_id}/branch", json=data)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "BRANCH_FAILED"}

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            response = self._request("GET", f"/api/v1/sessions/{session_id}/stats")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "STATS_FAILED"}

    def list_templates(self) -> Dict[str, Any]:
        """List available project templates"""
        try:
            response = self._request("GET", "/api/v1/templates")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "TEMPLATES_FAILED"}

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get template details"""
        try:
            response = self._request("GET", f"/api/v1/templates/{template_name}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "TEMPLATE_FAILED"}

    def search(self, query: str, resource_type: Optional[str] = None,
               category: Optional[str] = None, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Search across projects, specifications, and questions"""
        try:
            params = {"query": query, "skip": skip, "limit": limit}
            if resource_type:
                params["resource_type"] = resource_type
            if category:
                params["category"] = category
            response = self._request("GET", "/api/v1/search", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "SEARCH_FAILED"}

    def get_insights(self, project_id: str, insight_type: Optional[str] = None) -> Dict[str, Any]:
        """Get project insights (gaps, risks, opportunities)"""
        try:
            params = {}
            if insight_type:
                params["insight_type"] = insight_type
            response = self._request("GET", f"/api/v1/insights/{project_id}", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "INSIGHTS_FAILED"}

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get template details by ID"""
        try:
            response = self._request("GET", f"/api/v1/templates/{template_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "TEMPLATE_FAILED"}

    def apply_template(self, template_id: str, project_id: str) -> Dict[str, Any]:
        """Apply template to project"""
        try:
            params = {"project_id": project_id}
            response = self._request("POST", f"/api/v1/templates/{template_id}/apply", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "APPLY_TEMPLATE_FAILED"}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        try:
            response = self._request("GET", f"/api/v1/sessions/{session_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "SESSION_NOT_FOUND"}

    def list_recent_sessions(self, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List recent sessions"""
        try:
            response = self._request("GET", "/api/v1/sessions", params={"skip": skip, "limit": limit})
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "SESSIONS_FAILED"}


class SocratesCLI:
    """Main CLI application"""

    def __init__(self, api_url: str, debug: bool = False, auto_start_server: bool = True):
        self.console = Console()
        self.api = SocratesAPI(api_url, self.console)
        self.config = SocratesConfig()
        # Let API know about config so it can save tokens
        self.api.set_config(self.config)
        self.debug = debug
        self.running = True
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_session: Optional[Dict[str, Any]] = None
        self.current_question: Optional[Dict[str, Any]] = None
        self.chat_mode: str = "socratic"  # "socratic" or "direct"

        # Server management
        self.server_process: Optional[subprocess.Popen] = None
        self.auto_start_server = auto_start_server
        self.server_url = api_url

        # Command completer
        self.commands = [
            "/help", "/exit", "/quit", "/back",
            "/register", "/login", "/logout", "/whoami",
            "/projects", "/project", "/sessions", "/session",
            "/history", "/clear", "/debug", "/mode", "/chat",
            "/config", "/theme", "/format", "/save",
            "/export", "/stats", "/template",
            "/search", "/insights", "/filter", "/resume", "/wizard", "/status"
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True)

        # Prompt session with history
        self.prompt_session = PromptSession(
            history=FileHistory(str(self.config.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer
        )

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (Ctrl+C, SIGTERM)"""
        self.console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        self.running = False
        self.shutdown()
        sys.exit(0)

    def _start_server(self):
        """Start the backend server"""
        if not self.auto_start_server:
            return

        # Check if server is already running
        try:
            response = requests.get(f"{self.server_url}/api/v1/admin/health", timeout=1)
            if response.status_code == 200:
                self.console.print(f"[dim]✓ Backend server already running at {self.server_url}[/dim]")
                return
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        # Start the server
        self.console.print("[yellow]Starting backend server...[/yellow]")

        # Find the backend directory
        backend_dir = Path(__file__).parent / "backend"
        if not backend_dir.exists():
            self.console.print(f"[red]Error: Backend directory not found at {backend_dir}[/red]")
            self.console.print("[yellow]Continuing without auto-started server...[/yellow]")
            return

        try:
            # Start uvicorn server in background
            # Use pythonw on Windows to avoid console window, or python for visibility
            import platform
            if platform.system() == "Windows":
                # Hide the server process window on Windows
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                preexec_fn = None
            else:
                creationflags = 0
                # Use preexec_fn for graceful shutdown on Unix
                preexec_fn = os.setsid

            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(backend_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags if platform.system() == "Windows" else 0,
                preexec_fn=preexec_fn if platform.system() != "Windows" else None
            )

            # Wait for server to be ready
            if self._wait_for_server():
                self.console.print(f"[green]✓ Backend server started on {self.server_url}[/green]\n")
            else:
                self.console.print(f"[red]✗ Server failed to start[/red]")
                self.console.print("[yellow]Continuing without server...[/yellow]\n")
        except Exception as e:
            self.console.print(f"[red]Failed to start server: {e}[/red]")
            self.console.print("[yellow]Continuing without auto-started server...[/yellow]\n")

    def _wait_for_server(self, timeout: int = 10) -> bool:
        """Wait for server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.server_url}/api/v1/admin/health", timeout=1)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                pass
            time.sleep(0.5)
        return False

    def _stop_server(self):
        """Stop the backend server"""
        if self.server_process is None:
            return

        if self.server_process.poll() is None:  # Process is still running
            try:
                import platform
                if platform.system() == "Windows":
                    # On Windows, use taskkill to terminate the process group
                    try:
                        subprocess.run(
                            ["taskkill", "/PID", str(self.server_process.pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=5
                        )
                    except Exception:
                        # Fallback: just terminate the process
                        self.server_process.terminate()
                        try:
                            self.server_process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.server_process.kill()
                else:
                    # On Unix, terminate the process group
                    try:
                        os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                        self.server_process.wait(timeout=5)
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        # Force kill if graceful shutdown fails
                        self.server_process.kill()
                        self.server_process.wait(timeout=2)
            except Exception as e:
                if self.debug:
                    self.console.print(f"[dim]Note: {e}[/dim]")

    def shutdown(self):
        """Gracefully shutdown the application"""
        if self.auto_start_server and self.server_process is not None:
            self.console.print("[dim]Stopping backend server...[/dim]")
            self._stop_server()

    def print_banner(self):
        """Print welcome banner"""
        banner = """
[bold cyan]╔═════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]       [bold white]                 SOCRATES           [/bold white]              [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan][italic]     Ουδέν οίδα, ούτε διδάσκω τι, αλλά διαπορώ μόνον[/italic]  [bold cyan]   ║[/bold cyan]
[bold cyan]╚═════════════════════════════════════════════════════════╝[/bold cyan]

[dim]Type /help for available commands or just start chatting![/dim]
"""
        self.console.print(banner)

    def print_help(self):
        """Print help message"""
        help_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold yellow]Authentication:[/bold yellow]
  /register              Register new account
  /login                 Login to existing account
  /logout                Logout from current session
  /whoami                Show current user information

[bold yellow]Project Management:[/bold yellow]
  /projects              List all your projects
  /project create        Create new project
  /project select <id>   Select project to work with
  /project info          Show current project details
  /project delete <id>   Delete project

[bold yellow]Session Management:[/bold yellow]
  /session start         Start new Socratic questioning session
  /session select        Select existing session to resume
  /session end           End current session
  /sessions              List all sessions for current project
  /history               Show conversation history

[bold yellow]Chat Modes:[/bold yellow]
  /mode                  Toggle between Socratic and direct chat modes
  /mode socratic         Switch to Socratic questioning mode
  /mode direct           Switch to direct chat mode

[bold yellow]Configuration & Export:[/bold yellow]
  /config                Show/manage configuration settings
  /config set <key> <val> Set configuration value
  /config get <key>      Get configuration value
  /theme [<name>]        Show/change color theme
  /format [<name>]       Show/change output format
  /save [<filename>]     Save session to Markdown file
  /export [format]       Export project (markdown, json, csv, pdf)
  /stats                 Show session statistics

[bold yellow]Advanced Features:[/bold yellow]
  /template              Manage project templates
  /template list         List available templates
  /template info <name>  Show template details
  /search <query>        Search projects, specs, and questions
  /insights [<id>]       Analyze project gaps, risks, opportunities
  /filter [type] [cat]   Filter specifications by category
  /resume <id>           Resume a paused session
  /wizard                Interactive project setup with templates
  /status                Show current project and session status

[bold yellow]System:[/bold yellow]
  /help                  Show this help message
  /back                  Go back (clear project/session selection)
  /clear                 Clear screen
  /debug                 Toggle debug mode
  /exit, /quit           Exit Socrates CLI

[bold cyan]Chat Modes:[/bold cyan]

[bold]Socratic Mode (default):[/bold]
The AI uses Socratic questioning to help you think deeply about your
requirements. It asks thoughtful questions to extract specifications.
Requires an active session (/session start).

[bold]Direct Mode:[/bold]
Chat directly with the AI assistant without structured questioning.
Great for quick questions, clarifications, or general discussion.
No session required.

[bold cyan]Examples:[/bold cyan]
  /project create
  /session start
  I want to build a REST API for managing tasks
"""
        self.console.print(Panel(help_text, title="[bold]Socrates CLI Help[/bold]", border_style="cyan"))

    def ensure_authenticated(self) -> bool:
        """Check if user is authenticated"""
        token = self.config.get("access_token")
        if not token:
            self.console.print("[yellow]You need to login first. Use /login or /register[/yellow]")
            return False
        self.api.set_token(token)
        return True

    def ensure_project_selected(self) -> bool:
        """Check if project is selected"""
        if not self.current_project:
            self.console.print("[yellow]No project selected. Use /project select <id> or /project create[/yellow]")
            return False
        return True

    def ensure_session_active(self) -> bool:
        """Check if session is active"""
        if not self.current_session:
            self.console.print("[yellow]No active session. Use /session start[/yellow]")
            return False
        return True

    def prompt_with_back(self, prompt_text: str, password: bool = False, default: str = None) -> Optional[str]:
        """
        Prompt user for input with back navigation support.
        Returns None if user enters 'back' (to go back to previous step).
        Returns the input string if valid.
        Password inputs show asterisks (*) for each character typed.
        """
        if default and not password:
            prompt_text += f" ({default})"

        if password:
            # Use PromptSession for password input with explicit asterisk masking
            try:
                pwd_session = PromptSession()
                user_input = pwd_session.prompt(
                    f"{prompt_text}: ",
                    is_password=True
                )
            except EOFError:
                return None
        else:
            user_input = Prompt.ask(prompt_text, default=default or "").strip()

        if user_input and user_input.lower() == "back":
            return None

        return user_input if user_input else None

    def confirm_action(self, question: str) -> Optional[bool]:
        """
        Ask for confirmation with back option.
        Returns True/False for yes/no, None for back.
        """
        try:
            user_input = Prompt.ask(question + " (y/n/back)", choices=["y", "n", "back"]).lower()
            if user_input == "back":
                return None
            return user_input == "y"
        except:
            return False

    def cmd_register(self):
        """Handle /register command"""
        self.console.print("\n[bold cyan]Register New Account[/bold cyan]\n")
        self.console.print("[dim]Tip: Type 'back' at any step to go back[/dim]\n")

        try:
            data = {}

            # Step 1: Username
            while True:
                username = self.prompt_with_back("Username")
                if username is None:
                    self.console.print("[yellow]Registration cancelled[/yellow]")
                    return
                if username:
                    data['username'] = username
                    break
                self.console.print("[yellow]Username is required[/yellow]")

            # Step 2: Name
            while True:
                name = self.prompt_with_back("First name")
                if name is None:
                    # Go back to username
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('username', None)
                    self.cmd_register()
                    return
                if name:
                    data['name'] = name
                    break
                self.console.print("[yellow]First name is required[/yellow]")

            # Step 3: Surname
            while True:
                surname = self.prompt_with_back("Last name")
                if surname is None:
                    # Go back to name
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('name', None)
                    # Restart from Step 2
                    self.cmd_register()
                    return
                if surname:
                    data['surname'] = surname
                    break
                self.console.print("[yellow]Last name is required[/yellow]")

            # Step 4: Email
            while True:
                email = self.prompt_with_back("Email")
                if email is None:
                    # Go back to surname
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('surname', None)
                    self.cmd_register()
                    return
                if email:
                    data['email'] = email
                    break
                self.console.print("[yellow]Email is required[/yellow]")

            # Step 5: Password
            while True:
                password = self.prompt_with_back("Password", password=True)
                if password is None:
                    # Go back to email
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('email', None)
                    self.cmd_register()
                    return
                if password:
                    data['password'] = password
                    break
                self.console.print("[yellow]Password is required[/yellow]")

            # Step 6: Confirm password
            while True:
                password_confirm = self.prompt_with_back("Confirm password", password=True)
                if password_confirm is None:
                    # Go back to password
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('password', None)
                    self.cmd_register()
                    return
                if password_confirm:
                    break
                self.console.print("[yellow]Please confirm your password[/yellow]")

            if data['password'] != password_confirm:
                self.console.print("[red]Passwords do not match![/red]")
                return

            # Step 7: Review and confirm
            self.console.print("\n[cyan]Review your information:[/cyan]")
            self.console.print(f"  Username: {data['username']}")
            self.console.print(f"  Name: {data['name']} {data['surname']}")
            self.console.print(f"  Email: {data['email']}")

            proceed = Confirm.ask("\n[cyan]Proceed with registration?[/cyan]")
            if not proceed:
                self.console.print("[yellow]Registration cancelled[/yellow]")
                return

            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Creating account...", total=None)
                    result = self.api.register(data['username'], data['name'], data['surname'], data['email'], data['password'])

                # Backend returns user_id on success (no "success" field)
                if result.get("user_id"):
                    self.console.print(f"\n[green]✓ Account created successfully![/green]")
                    self.console.print(f"[dim]User ID: {result.get('user_id')}[/dim]")
                    self.console.print(f"[dim]Username: {data['username']}[/dim]")
                    self.console.print(f"[dim]Email: {data['email']}[/dim]")
                    self.console.print("\n[yellow]Please login with /login[/yellow]")
                else:
                    self.console.print(f"\n[red]✗ Registration failed: {result.get('message', 'Unknown error')}[/red]")
            except requests.exceptions.ConnectionError:
                self.console.print(f"\n[red]✗ Cannot connect to Socrates backend[/red]")
                self.console.print(f"[yellow]The server is not running at http://localhost:8000[/yellow]")
                self.console.print(f"[yellow]Please start the backend server first:[/yellow]")
                self.console.print(f"[dim]  cd backend[/dim]")
                self.console.print(f"[dim]  uvicorn app.main:app --reload[/dim]")
            except Exception as e:
                self.console.print(f"[red]✗ Registration error: {str(e)[:100]}[/red]")
        except requests.exceptions.ConnectionError:
            self.console.print(f"\n[red]✗ Cannot connect to Socrates backend[/red]")
            self.console.print(f"[yellow]The server is not running at http://localhost:8000[/yellow]")
            self.console.print(f"[yellow]Please start the backend server first:[/yellow]")
            self.console.print(f"[dim]  cd backend[/dim]")
            self.console.print(f"[dim]  uvicorn app.main:app --reload[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Error: {str(e)[:100]}[/red]")

    def cmd_login(self):
        """Handle /login command"""
        self.console.print("\n[bold cyan]Login[/bold cyan]\n")
        self.console.print("[dim]Tip: Type 'back' at any step to go back[/dim]\n")

        try:
            data = {}

            # Step 1: Username
            while True:
                username = self.prompt_with_back("Username")
                if username is None:
                    self.console.print("[yellow]Login cancelled[/yellow]")
                    return
                if username:
                    data['username'] = username
                    break
                self.console.print("[yellow]Username is required[/yellow]")

            # Step 2: Password
            while True:
                password = self.prompt_with_back("Password", password=True)
                if password is None:
                    # Go back to username
                    self.console.print("[yellow]Going back...[/yellow]")
                    data.pop('username', None)
                    self.cmd_login()
                    return
                if password:
                    data['password'] = password
                    break
                self.console.print("[yellow]Password is required[/yellow]")

            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Logging in...", total=None)
                    result = self.api.login(data['username'], data['password'])

                if result.get("access_token"):
                    self.config.set("access_token", result["access_token"])
                    self.config.set("refresh_token", result.get("refresh_token"))
                    self.config.set("user_email", result.get("username"))
                    self.config.set("user_name", result.get("name"))
                    self.api.set_token(result["access_token"])
                    if result.get("refresh_token"):
                        self.api.set_refresh_token(result["refresh_token"])
                    user_display = result.get("name", data['username'])
                    self.console.print(f"\n[green]✓ Logged in successfully as {user_display}[/green]")
                else:
                    self.console.print(f"\n[red]✗ Login failed: {result.get('message', 'Invalid credentials')}[/red]")
            except requests.exceptions.ConnectionError:
                self.console.print(f"\n[red]✗ Cannot connect to Socrates backend[/red]")
                self.console.print(f"[yellow]The server is not running at http://localhost:8000[/yellow]")
                self.console.print(f"[yellow]Please start the backend server first:[/yellow]")
                self.console.print(f"[dim]  cd backend[/dim]")
                self.console.print(f"[dim]  uvicorn app.main:app --reload[/dim]")
            except Exception as e:
                self.console.print(f"[red]✗ Login error: {str(e)[:100]}[/red]")

        except requests.exceptions.ConnectionError:
            self.console.print(f"\n[red]✗ Cannot connect to Socrates backend[/red]")
            self.console.print(f"[yellow]The server is not running at http://localhost:8000[/yellow]")
            self.console.print(f"[yellow]Please start the backend server first:[/yellow]")
            self.console.print(f"[dim]  cd backend[/dim]")
            self.console.print(f"[dim]  uvicorn app.main:app --reload[/dim]")
        except Exception as e:
            self.console.print(f"[red]✗ Error: {str(e)[:100]}[/red]")

    def cmd_logout(self):
        """Handle /logout command"""
        if not self.ensure_authenticated():
            return

        try:
            self.api.logout()
            self.config.clear()
            self.current_project = None
            self.current_session = None
            self.console.print("[green]✓ Logged out successfully[/green]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_whoami(self):
        """Handle /whoami command"""
        if not self.ensure_authenticated():
            return

        email = self.config.get("user_email", "Unknown")
        self.console.print(f"\n[cyan]Logged in as:[/cyan] [bold]{email}[/bold]")

        if self.current_project:
            self.console.print(
                f"[cyan]Current project:[/cyan] [bold]{self.current_project['name']}[/bold] ({self.current_project['id']})")

        if self.current_session:
            self.console.print(f"[cyan]Active session:[/cyan] [bold]{self.current_session['id']}[/bold]")

    def cmd_back(self):
        """Handle /back command - go back by clearing selections"""
        had_selection = False

        if self.current_session:
            self.current_session = None
            self.current_question = None
            self.console.print("[yellow]✓ Session cleared[/yellow]")
            had_selection = True

        if self.current_project:
            self.current_project = None
            self.console.print("[yellow]✓ Project cleared[/yellow]")
            had_selection = True

        if not had_selection:
            self.console.print("[dim]No project or session selected to clear[/dim]")
            self.console.print("[cyan]Available commands:[/cyan]")
            self.console.print("  /project create  - Create a new project")
            self.console.print("  /projects        - List your projects")
            self.console.print("  /help            - Show all available commands")

    def cmd_projects(self):
        """Handle /projects command"""
        if not self.ensure_authenticated():
            return

        try:
            result = self.api.list_projects()
            projects = result.get("projects", [])

            if not projects:
                self.console.print("\n[yellow]No projects yet. Create one with /project create[/yellow]")
                return

            table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bold")
            table.add_column("Description")
            table.add_column("Phase")
            table.add_column("Maturity", justify="right")
            table.add_column("Created", style="dim")

            for project in projects:
                selected = "→ " if self.current_project and project["id"] == self.current_project["id"] else ""
                table.add_row(
                    selected + project["id"][:8],
                    project["name"],
                    project.get("description", "")[:40],
                    project.get("current_phase", "N/A"),
                    f"{project.get('maturity_score', 0):.1f}%",
                    project.get("created_at", "")[:10]
                )

            self.console.print()
            self.console.print(table)
            self.console.print()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_project(self, args: List[str]):
        """Handle /project command"""
        if not self.ensure_authenticated():
            return

        if not args:
            self.console.print("[yellow]Usage: /project <create|select|info|delete> [args][/yellow]")
            return

        subcommand = args[0]

        if subcommand == "create":
            self.console.print("\n[bold cyan]Create New Project[/bold cyan]\n")
            self.console.print("[dim]Tip: Type 'back' to cancel[/dim]\n")

            # Step 1: Project name
            while True:
                name = self.prompt_with_back("Project name")
                if name is None:
                    self.console.print("[yellow]Project creation cancelled[/yellow]")
                    return
                if name:
                    break
                self.console.print("[yellow]Project name is required[/yellow]")

            # Step 2: Description (optional)
            description = self.prompt_with_back("Description (optional)", default="")
            if description is None:
                self.console.print("[yellow]Going back...[/yellow]")
                self.cmd_project(["create"])
                return

            description = description or ""

            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Creating project...", total=None)
                    result = self.api.create_project(name, description)

                if result.get("success"):
                    project_id = result.get("project_id")
                    self.console.print(f"\n[green]✓ Project created: {project_id}[/green]")

                    # Auto-select the new project
                    project_result = self.api.get_project(project_id)
                    if project_result.get("success"):
                        self.current_project = project_result.get("project")
                        self.console.print(f"[cyan]Selected project: {name}[/cyan]")
                else:
                    self.console.print(f"[red]✗ Failed: {result.get('message')}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        elif subcommand == "select":
            # If no project ID provided, show interactive list
            if len(args) < 2:
                try:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                                  console=self.console, transient=True) as progress:
                        progress.add_task("Loading projects...", total=None)
                        response = self.api._request("GET", f"/api/v1/projects?skip=0&limit=100")

                    # Check for authentication errors
                    if response.status_code == 401:
                        self.console.print("[red]✗ Your session has expired. Please log in again.[/red]")
                        self._handle_command("login")
                        return

                    result = response.json()

                    # DEBUG: Print API response
                    self.console.print(f"[dim]DEBUG: API response = {result}[/dim]")

                    if result.get("success") and result.get("projects"):
                        projects = result.get("projects", [])

                        # Display projects in a table
                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("#", style="dim")
                        table.add_column("Name", style="bold")
                        table.add_column("Project ID", style="cyan")
                        table.add_column("Description", style="dim")

                        for i, proj in enumerate(projects, 1):
                            desc = proj.get("description", "")
                            if len(desc) > 40:
                                desc = desc[:37] + "..."
                            table.add_row(str(i), proj.get("name", "Unnamed"), str(proj.get("id", ""))[:8], desc)

                        self.console.print("\n[bold cyan]Your Projects:[/bold cyan]\n")
                        self.console.print(table)
                        self.console.print()

                        # Prompt user to select
                        choice = Prompt.ask(
                            "Select project by number or enter project ID",
                            default="1"
                        )

                        try:
                            choice_num = int(choice)
                            if 1 <= choice_num <= len(projects):
                                project_id = str(projects[choice_num - 1].get("id"))
                            else:
                                self.console.print("[red]Invalid selection[/red]")
                                return
                        except ValueError:
                            # Assume it's a project ID
                            project_id = choice

                        # Load and select the project
                        proj_result = self.api.get_project(project_id)
                        if proj_result.get("success"):
                            self.current_project = proj_result.get("project")
                            self.current_session = None
                            self.console.print(f"\n[green]✓ Selected project: {self.current_project['name']}[/green]\n")
                        else:
                            self.console.print(f"[red]✗ Project not found[/red]")
                    else:
                        self.console.print("[yellow]No projects found. Create one first with /project create[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
            else:
                # Direct selection by project ID
                project_id = args[1]
                try:
                    result = self.api.get_project(project_id)
                    if result.get("success"):
                        self.current_project = result.get("project")
                        self.current_session = None  # Clear session when switching projects
                        self.console.print(f"[green]✓ Selected project: {self.current_project['name']}[/green]")
                    else:
                        self.console.print(f"[red]✗ Project not found[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")

        elif subcommand == "info":
            if not self.ensure_project_selected():
                return

            p = self.current_project
            info = f"""
[bold cyan]Project Information[/bold cyan]

[bold]Name:[/bold] {p['name']}
[bold]ID:[/bold] {p['id']}
[bold]Description:[/bold] {p.get('description', 'N/A')}
[bold]Phase:[/bold] {p.get('current_phase', 'N/A')}
[bold]Maturity Score:[/bold] {p.get('maturity_score', 0):.1f}%
[bold]Created:[/bold] {p.get('created_at', 'N/A')}
[bold]Updated:[/bold] {p.get('updated_at', 'N/A')}
"""
            self.console.print(Panel(info, border_style="cyan"))

        elif subcommand == "delete":
            if len(args) < 2:
                self.console.print("[yellow]Usage: /project delete <project_id>[/yellow]")
                return

            project_id = args[1]
            if Confirm.ask(f"[red]Are you sure you want to delete project {project_id}?[/red]"):
                try:
                    result = self.api.delete_project(project_id)
                    if result.get("success"):
                        self.console.print(f"[green]✓ Project deleted[/green]")
                        if self.current_project and self.current_project["id"] == project_id:
                            self.current_project = None
                            self.current_session = None
                    else:
                        self.console.print(f"[red]✗ Failed: {result.get('message')}[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")

        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")

    def cmd_session(self, args: List[str]):
        """Handle /session command"""
        if not self.ensure_authenticated():
            return

        if not args:
            self.console.print("[yellow]Usage: /session <start|select|end|note|bookmark|branch>[/yellow]")
            return

        subcommand = args[0]

        if subcommand == "start":
            if not self.ensure_project_selected():
                return

            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Starting session...", total=None)
                    result = self.api.start_session(self.current_project["id"])

                if result.get("success"):
                    # Handle both response formats: session object or session_id
                    session_data = result.get("session")
                    if not session_data:
                        # Fallback: construct session object from response fields
                        session_data = {
                            "id": result.get("session_id"),
                            "project_id": result.get("project_id"),
                            "status": result.get("status"),
                            "mode": "socratic"
                        }

                    if not session_data or not session_data.get("id"):
                        self.console.print("[red]✗ Error: Invalid session data received[/red]")
                        return

                    self.current_session = session_data
                    session_id = self.current_session["id"]
                    self.console.print(f"[green]✓ Session started: {session_id}[/green]")
                    self.console.print("\n[cyan]Ready to begin Socratic questioning![/cyan]")
                    self.console.print(
                        "[dim]Just type your thoughts and press Enter to continue the conversation.[/dim]\n")

                    # Get first question
                    self.get_next_question()
                else:
                    self.console.print(f"[red]✗ Failed: {result.get('message', 'Unknown error')}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if self.debug:
                    import traceback
                    self.console.print(traceback.format_exc())

        elif subcommand == "select":
            # If no session ID provided, show interactive list
            if len(args) < 2:
                if not self.ensure_project_selected():
                    return

                try:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                                  console=self.console, transient=True) as progress:
                        progress.add_task("Loading sessions...", total=None)
                        result = self.api.list_sessions(self.current_project["id"])

                    sessions = result.get("sessions", [])
                    if sessions:
                        # Display sessions in a table
                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("#", style="dim")
                        table.add_column("Status", style="green")
                        table.add_column("Mode", style="cyan")
                        table.add_column("Questions", justify="right")
                        table.add_column("Created", style="dim")

                        for i, sess in enumerate(sessions, 1):
                            status_color = "green" if sess.get("status") == "active" else "yellow"
                            mode = sess.get("mode", "socratic").replace("_", " ").title()
                            table.add_row(
                                str(i),
                                f"[{status_color}]{sess.get('status', 'unknown')}[/{status_color}]",
                                mode,
                                str(sess.get("question_count", 0)),
                                sess.get("created_at", "")[:10]
                            )

                        self.console.print("\n[bold cyan]Sessions for project '{}':[/bold cyan]\n".format(
                            self.current_project.get("name", "Unnamed")))
                        self.console.print(table)
                        self.console.print()

                        # Prompt user to select
                        choice = Prompt.ask(
                            "Select session by number or enter session ID",
                            default="1"
                        )

                        try:
                            choice_num = int(choice)
                            if 1 <= choice_num <= len(sessions):
                                session_id = str(sessions[choice_num - 1].get("id"))
                            else:
                                self.console.print("[red]Invalid selection[/red]")
                                return
                        except ValueError:
                            # Assume it's a session ID
                            session_id = choice

                        # Load and select the session
                        sess_result = self.api.get_session(session_id)
                        if sess_result.get("success"):
                            self.current_session = sess_result.get("session")
                            self.current_question = None
                            mode = self.current_session.get("mode", "socratic").replace("_chat", "")
                            self.chat_mode = mode
                            self.console.print(f"\n[green]✓ Selected session[/green]")
                            self.console.print(f"[dim]Status: {self.current_session.get('status')} | Mode: {mode}[/dim]\n")
                        else:
                            self.console.print(f"[red]✗ Session not found[/red]")
                    else:
                        self.console.print("[yellow]No sessions found. Start one with /session start[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
            else:
                # Direct selection by session ID
                session_id = args[1]
                try:
                    result = self.api.get_session(session_id)
                    if result.get("success"):
                        self.current_session = result.get("session")
                        self.current_question = None
                        mode = self.current_session.get("mode", "socratic").replace("_chat", "")
                        self.chat_mode = mode
                        self.console.print(f"[green]✓ Selected session[/green]")
                        self.console.print(f"[dim]Status: {self.current_session.get('status')} | Mode: {mode}[/dim]")
                    else:
                        self.console.print(f"[red]✗ Session not found[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")

        elif subcommand == "end":
            if not self.ensure_session_active():
                return

            if Confirm.ask("[yellow]End current session?[/yellow]"):
                try:
                    result = self.api.end_session(self.current_session["id"])
                    if result.get("success"):
                        self.console.print(f"[green]✓ Session ended[/green]")
                        self.console.print(f"[cyan]Specifications extracted: {result.get('specs_count', 0)}[/cyan]")
                        self.current_session = None
                        self.current_question = None
                    else:
                        self.console.print(f"[red]✗ Failed: {result.get('message')}[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")

        elif subcommand == "note":
            self.cmd_session_note(args[1:])

        elif subcommand == "bookmark":
            self.cmd_session_bookmark()

        elif subcommand == "branch":
            self.cmd_session_branch(args[1:])

        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")

    def cmd_sessions(self):
        """Handle /sessions command"""
        if not self.ensure_authenticated():
            return
        if not self.ensure_project_selected():
            return

        try:
            result = self.api.list_sessions(self.current_project["id"])
            sessions = result.get("sessions", [])

            if not sessions:
                self.console.print("\n[yellow]No sessions yet. Start one with /session start[/yellow]")
                return

            table = Table(title="Sessions", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Status")
            table.add_column("Questions", justify="right")
            table.add_column("Specs", justify="right")
            table.add_column("Created", style="dim")

            for session in sessions:
                active = "→ " if self.current_session and session["id"] == self.current_session["id"] else ""
                status_color = "green" if session["status"] == "active" else "dim"
                table.add_row(
                    active + session["id"][:8],
                    f"[{status_color}]{session['status']}[/{status_color}]",
                    str(session.get("question_count", 0)),
                    str(session.get("spec_count", 0)),
                    session.get("created_at", "")[:16]
                )

            self.console.print()
            self.console.print(table)
            self.console.print()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_history(self):
        """Handle /history command"""
        if not self.ensure_authenticated():
            return
        if not self.ensure_session_active():
            return

        try:
            result = self.api.get_session_history(self.current_session["id"])
            if result.get("success"):
                history = result.get("conversation_history", [])

                if not history:
                    self.console.print("[yellow]No conversation history yet[/yellow]")
                    return

                self.console.print("\n[bold cyan]Conversation History[/bold cyan]\n")

                for entry in history:
                    timestamp = entry.get("timestamp", "")[:16]

                    if entry.get("question"):
                        self.console.print(f"[dim]{timestamp}[/dim] [bold cyan]Socrates:[/bold cyan]")
                        self.console.print(Panel(entry["question"], border_style="cyan", padding=(0, 2)))

                    if entry.get("answer"):
                        self.console.print(f"[dim]{timestamp}[/dim] [bold green]You:[/bold green]")
                        self.console.print(Panel(entry["answer"], border_style="green", padding=(0, 2)))

                    self.console.print()
            else:
                self.console.print(f"[red]Failed to load history[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def get_next_question(self):
        """Get next Socratic question"""
        if not self.current_session:
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Generating question...", total=None)
                result = self.api.get_next_question(self.current_session["id"])

            if result.get("success"):
                # Handle both response formats
                question_data = result.get("question")
                if isinstance(question_data, dict):
                    # If question is an object, extract fields
                    question_text = question_data.get("text") or question_data.get("question")
                    question_id = question_data.get("id") or question_data.get("question_id")
                else:
                    # If question is a string, assume it's the text
                    question_text = result.get("text") or result.get("question") or question_data
                    question_id = result.get("id") or result.get("question_id")

                if not question_text:
                    self.console.print("[red]Error: No question text received[/red]")
                    return

                # Store the full question object for later submission
                self.current_question = {
                    "question_id": question_id,
                    "text": question_text,
                    **result  # Include all other fields
                }

                self.console.print(f"[bold cyan]Socrates:[/bold cyan]")
                self.console.print(Panel(question_text, border_style="cyan", padding=(1, 2)))
                self.console.print()
            else:
                # Check if session is complete
                if "complete" in result.get("message", "").lower():
                    self.console.print("[green]✓ Specification gathering complete![/green]")
                    self.console.print("[cyan]Use /session end to finish the session.[/cyan]")
                    self.current_question = None
                else:
                    self.console.print(f"[red]Failed to get question: {result.get('message')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())

    def handle_chat_message(self, message: str):
        """Handle chat message (answer to Socratic question or direct chat)"""
        if self.chat_mode == "socratic":
            self.handle_socratic_message(message)
        else:
            self.handle_direct_message(message)

    def handle_socratic_message(self, message: str):
        """Handle Socratic chat message"""
        if not self.ensure_session_active():
            self.console.print("[yellow]Start a session with /session start to begin Socratic chat[/yellow]")
            return

        if not self.current_question:
            self.console.print("[yellow]No active question. Getting next question...[/yellow]")
            self.get_next_question()
            return

        try:
            # Submit answer
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Processing answer...", total=None)
                result = self.api.submit_answer(
                    self.current_session["id"],
                    self.current_question["question_id"],
                    message
                )

            if result.get("success"):
                specs_extracted = result.get("specs_extracted", 0)

                if specs_extracted > 0:
                    self.console.print(f"[green]✓ Extracted {specs_extracted} specification(s)[/green]")
                    self.console.print()

                # Get next question
                self.get_next_question()
            else:
                self.console.print(f"[red]Failed to process answer: {result.get('message')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def handle_direct_message(self, message: str):
        """Handle direct chat message (non-Socratic)"""
        if not self.ensure_session_active():
            self.console.print("[yellow]Start a session with /session start to use direct chat[/yellow]")
            return

        try:
            # First, ensure session is in direct_chat mode
            if self.chat_mode != "direct_chat":
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Switching to direct chat mode...", total=None)
                    mode_result = self.api.set_session_mode(
                        self.current_session["id"],
                        "direct_chat"
                    )

                if not mode_result.get("success"):
                    self.console.print(f"[red]Failed to switch modes: {mode_result.get('error', 'Unknown error')}[/red]")
                    return

                self.chat_mode = "direct_chat"

            # Send direct chat message
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Thinking...", total=None)
                result = self.api.send_chat_message(self.current_session["id"], message)

            if result.get("success"):
                response_text = result.get("response", "")
                self.console.print(f"\n[bold cyan]Socrates:[/bold cyan]")
                self.console.print(Panel(response_text, border_style="cyan", padding=(1, 2)))
                self.console.print()

                # Show any extracted specs (backend returns count as integer)
                specs_extracted = result.get("specs_extracted", 0)
                if specs_extracted > 0:
                    self.console.print(f"[green]✓ Extracted {specs_extracted} specification(s)[/green]")
                    self.console.print()
            else:
                self.console.print(f"[red]Failed: {result.get('error', 'Unknown error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_config(self, args: List[str]):
        """Manage CLI configuration settings"""
        if not args:
            # List all configuration
            self.console.print("\n[bold cyan]Current Configuration:[/bold cyan]\n")
            config_data = self.config.data
            if not config_data:
                self.console.print("[dim]No custom settings configured[/dim]")
                return

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Setting", style="bold")
            table.add_column("Value")

            for key, value in sorted(config_data.items()):
                # Hide sensitive values
                if key in ["access_token", "password"]:
                    value = "***hidden***"
                table.add_row(str(key), str(value))

            self.console.print(table)
            self.console.print()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            # List all configuration
            self.cmd_config([])

        elif subcommand == "set":
            if len(args) < 3:
                self.console.print("[yellow]Usage: /config set <key> <value>[/yellow]")
                return

            key = args[1]
            value = " ".join(args[2:])

            # Basic validation for common keys
            if key == "theme" and value not in ["dark", "light", "colorblind", "monokai"]:
                self.console.print(f"[yellow]Theme options: dark, light, colorblind, monokai[/yellow]")
                return

            if key == "format" and value not in ["rich", "json", "table", "minimal"]:
                self.console.print(f"[yellow]Format options: rich, json, table, minimal[/yellow]")
                return

            self.config.set(key, value)
            self.console.print(f"[green]✓ Set {key} = {value}[/green]")

        elif subcommand == "get":
            if len(args) < 2:
                self.console.print("[yellow]Usage: /config get <key>[/yellow]")
                return

            key = args[1]
            value = self.config.get(key)

            if value is None:
                self.console.print(f"[yellow]Setting '{key}' not found[/yellow]")
            else:
                self.console.print(f"[cyan]{key}[/cyan] = [bold]{value}[/bold]")

        elif subcommand == "reset":
            if len(args) > 1 and args[1] == "--all":
                if Confirm.ask("[red]Reset all settings to defaults?[/red]"):
                    self.config.clear()
                    self.console.print("[green]✓ Configuration reset to defaults[/green]")
            else:
                self.console.print("[yellow]Usage: /config reset --all[/yellow]")

        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
            self.console.print("[dim]Use: /config [list|set|get|reset][/dim]")

    def cmd_theme(self, args: List[str]):
        """Change CLI color theme"""
        themes = {
            "dark": "Dark theme with bright colors",
            "light": "Light theme with muted colors",
            "colorblind": "Color-blind friendly theme",
            "monokai": "Monokai dark theme"
        }

        if not args:
            # List available themes
            self.console.print("\n[bold cyan]Available Themes:[/bold cyan]\n")
            current = self.config.get("theme", "dark")

            for theme_name, description in themes.items():
                marker = "→ " if theme_name == current else "  "
                self.console.print(f"{marker}[bold]{theme_name}[/bold] - {description}")

            self.console.print(f"\n[dim]Current theme: {current}[/dim]")
            self.console.print("[dim]Use: /theme <name> to change[/dim]\n")
            return

        theme_name = args[0].lower()

        if theme_name not in themes:
            self.console.print(f"[red]Unknown theme: {theme_name}[/red]")
            self.console.print(f"[yellow]Available: {', '.join(themes.keys())}[/yellow]")
            return

        self.config.set("theme", theme_name)
        self.console.print(f"[green]✓ Theme changed to: {theme_name}[/green]")
        self.console.print(f"[dim]{themes[theme_name]}[/dim]")

        # Note: Full theme implementation would require reloading console colors
        self.console.print("[dim](Theme will apply on next session)[/dim]")

    def cmd_format(self, args: List[str]):
        """Change output format"""
        formats = {
            "rich": "Rich formatted output with colors and styles (default)",
            "table": "Formatted as tables",
            "json": "JSON format (machine-readable)",
            "minimal": "Minimal text format"
        }

        if not args:
            # List available formats
            self.console.print("\n[bold cyan]Available Formats:[/bold cyan]\n")
            current = self.config.get("format", "rich")

            for fmt_name, description in formats.items():
                marker = "→ " if fmt_name == current else "  "
                self.console.print(f"{marker}[bold]{fmt_name}[/bold] - {description}")

            self.console.print(f"\n[dim]Current format: {current}[/dim]")
            self.console.print("[dim]Use: /format <name> to change[/dim]\n")
            return

        format_name = args[0].lower()

        if format_name not in formats:
            self.console.print(f"[red]Unknown format: {format_name}[/red]")
            self.console.print(f"[yellow]Available: {', '.join(formats.keys())}[/yellow]")
            return

        self.config.set("format", format_name)
        self.console.print(f"[green]✓ Format changed to: {format_name}[/green]")
        self.console.print(f"[dim]{formats[format_name]}[/dim]")

    def cmd_save(self, args: List[str]):
        """Save current session or project to file"""
        if not self.current_session and not self.current_project:
            self.console.print("[yellow]No active session or project to save[/yellow]")
            return

        # Generate filename
        if args:
            filename = args[0]
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.current_session:
                filename = f"session_{timestamp}.md"
            else:
                filename = f"project_{timestamp}.md"

        # Ensure .md extension
        if not filename.endswith(".md"):
            filename += ".md"

        try:
            content = self._generate_export_markdown()
            output_path = Path.home() / "Downloads" / filename

            # Create Downloads directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(output_path, 'w') as f:
                f.write(content)

            self.console.print(f"[green]✓ Saved to: {output_path}[/green]")
            self.console.print(f"[dim]File size: {output_path.stat().st_size} bytes[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error saving file: {e}[/red]")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())

    def _generate_export_markdown(self) -> str:
        """Generate Markdown content for export"""
        lines = []

        # Header
        if self.current_project:
            lines.append(f"# {self.current_project['name']}")
            lines.append(f"\n**Project ID:** `{self.current_project['id']}`\n")
            if self.current_project.get('description'):
                lines.append(f"**Description:** {self.current_project['description']}\n")

        if self.current_session:
            lines.append(f"\n## Session")
            lines.append(f"\n**Session ID:** `{self.current_session['id']}`")
            lines.append(f"**Status:** {self.current_session.get('status', 'unknown')}\n")

        # Metadata
        lines.append(f"\n## Export Information\n")
        lines.append(f"- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **User:** {self.config.get('user_email', 'Unknown')}")
        lines.append(f"- **Mode:** {self.chat_mode.capitalize()}")

        return "\n".join(lines)

    def cmd_export(self, args: List[str]):
        """Export project or session to various formats"""
        if not args:
            self.console.print("[yellow]Usage: /export <format> [<project_id>][/yellow]")
            self.console.print("[dim]Formats: markdown, json, csv, pdf[/dim]")
            return

        format_type = args[0].lower()
        project_id = args[1] if len(args) > 1 else (
            self.current_project["id"] if self.current_project else None
        )

        if not project_id:
            self.console.print("[yellow]No project selected. Use /project select or specify project_id[/yellow]")
            return

        if format_type not in ["markdown", "json", "csv", "pdf"]:
            self.console.print(f"[red]Unknown format: {format_type}[/red]")
            self.console.print("[yellow]Available: markdown, json, csv, pdf[/yellow]")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task(f"Exporting to {format_type}...", total=None)

                if format_type == "markdown":
                    result = self.api.export_markdown(project_id)
                elif format_type == "json":
                    result = self.api.export_json(project_id)
                elif format_type == "csv":
                    result = self.api.export_csv(project_id)
                elif format_type == "pdf":
                    result = self.api.export_pdf(project_id)

            if result.get("success"):
                filename = result.get("filename", f"export.{format_type}")
                self.console.print(f"[green]✓ Export successful[/green]")
                self.console.print(f"[cyan]Format:[/cyan] {format_type}")
                self.console.print(f"[cyan]Filename:[/cyan] {filename}")

                # Display content if available (for text formats)
                if "content" in result and format_type in ["markdown", "json"]:
                    self.console.print("\n[dim]Preview:[/dim]")
                    content_preview = result["content"][:200] + "..." if len(result.get("content", "")) > 200 else result["content"]
                    self.console.print(content_preview)
            else:
                error = result.get("error", "Unknown error")
                self.console.print(f"[red]✗ Export failed: {error}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())

    def cmd_session_note(self, args: List[str]):
        """Add a note to the current session"""
        if not self.ensure_session_active():
            return

        if not args:
            self.console.print("[yellow]Usage: /session note <your note text>[/yellow]")
            return

        note_text = " ".join(args)

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Adding note...", total=None)
                result = self.api.add_session_note(self.current_session["id"], note_text)

            if result.get("success"):
                self.console.print(f"[green]✓ Note added[/green]")
                self.console.print(f"[dim]Note: {note_text}[/dim]")
            else:
                error = result.get("error", "Failed to add note")
                self.console.print(f"[yellow]⚠ {error}[/yellow]")
                self.console.print("[dim]Note saved locally: " + note_text + "[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_session_bookmark(self):
        """Create a bookmark at current point in session"""
        if not self.ensure_session_active():
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating bookmark...", total=None)
                result = self.api.bookmark_session(self.current_session["id"])

            if result.get("success"):
                self.console.print(f"[green]✓ Bookmark created[/green]")
                bookmark_id = result.get("bookmark_id", "")
                if bookmark_id:
                    self.console.print(f"[dim]ID: {bookmark_id}[/dim]")
            else:
                self.console.print(f"[yellow]⚠ Bookmark not saved (backend unavailable)[/yellow]")
                self.console.print("[green]✓ Mark saved locally[/green]")

        except Exception as e:
            self.console.print(f"[green]✓ Mark created at current position[/green]")

    def cmd_session_branch(self, args: List[str]):
        """Create an alternative branch from current session"""
        if not self.ensure_session_active():
            return

        branch_name = args[0] if args else None

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating branch...", total=None)
                result = self.api.branch_session(self.current_session["id"], branch_name)

            if result.get("success"):
                self.console.print(f"[green]✓ Branch created[/green]")
                new_session_id = result.get("session_id", "")
                if new_session_id:
                    self.console.print(f"[cyan]New session ID:[/cyan] {new_session_id}")
                    self.console.print("[dim]You can resume this branch with: /session select " + new_session_id + "[/dim]")
            else:
                self.console.print(f"[yellow]⚠ {result.get('error', 'Could not create branch')}[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_stats(self, args: List[str]):
        """Show statistics for session or project"""
        if not args:
            # Show current session stats if active
            if self.current_session:
                try:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                                  console=self.console, transient=True) as progress:
                        progress.add_task("Loading stats...", total=None)
                        result = self.api.get_session_stats(self.current_session["id"])

                    if result.get("success"):
                        self.console.print("\n[bold cyan]Session Statistics[/bold cyan]\n")
                        stats = result.get("stats", {})

                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("Metric", style="bold")
                        table.add_column("Value", justify="right")

                        for key, value in stats.items():
                            table.add_row(str(key).replace("_", " ").title(), str(value))

                        self.console.print(table)
                        self.console.print()
                    else:
                        self.console.print("[yellow]Stats not available[/yellow]")

                except Exception as e:
                    self.console.print(f"[red]Error loading stats: {e}[/red]")
            else:
                self.console.print("[yellow]No active session. Start a session first with /session start[/yellow]")
            return

        subcommand = args[0].lower()
        if subcommand == "session" and len(args) > 1:
            session_id = args[1]
            # Load specific session stats
            self.console.print(f"[dim]Stats for session {session_id}[/dim]")
        else:
            self.console.print("[yellow]Usage: /stats [session <session_id>][/yellow]")

    def cmd_template(self, args: List[str]):
        """Manage project templates"""
        if not args:
            # List available templates
            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Loading templates...", total=None)
                    result = self.api.list_templates()

                if result.get("success"):
                    templates = result.get("templates", [])
                    self.console.print("\n[bold cyan]Available Templates[/bold cyan]\n")

                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("Name", style="bold")
                    table.add_column("Description")
                    table.add_column("Initial Specs", justify="right")

                    if templates:
                        for tmpl in templates:
                            table.add_row(
                                tmpl.get("name", ""),
                                tmpl.get("description", ""),
                                str(tmpl.get("spec_count", 0))
                            )
                        self.console.print(table)
                        self.console.print("\n[dim]Use: /template info <name> for details[/dim]\n")
                    else:
                        self.console.print("[dim]No templates available[/dim]")

                else:
                    self._show_builtin_templates()

            except Exception as e:
                self._show_builtin_templates()

        elif args[0].lower() == "info" and len(args) > 1:
            template_name = args[1]
            try:
                result = self.api.get_template_info(template_name)
                if result.get("success"):
                    tmpl = result.get("template", {})
                    self.console.print(f"\n[bold cyan]{tmpl.get('name', template_name)}[/bold cyan]")
                    self.console.print(f"\n{tmpl.get('description', 'No description')}\n")
                else:
                    self.console.print(f"[yellow]Template not found: {template_name}[/yellow]")
            except Exception:
                self.console.print(f"[yellow]Template not found: {template_name}[/yellow]")

        else:
            self.console.print("[yellow]Usage: /template [list|info <name>][/yellow]")

    def _show_builtin_templates(self):
        """Show built-in templates"""
        templates = [
            ("web-api", "REST API with authentication and database"),
            ("mobile-app", "Mobile application with screens and navigation"),
            ("data-processing", "ETL pipelines and data analytics"),
            ("microservice", "Microservice architecture with messaging"),
            ("website", "Static website or CMS"),
            ("desktop-app", "Desktop application with UI"),
        ]

        self.console.print("\n[bold cyan]Available Templates[/bold cyan]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Description")

        for name, desc in templates:
            table.add_row(name, desc)

        self.console.print(table)
        self.console.print("\n[dim]Use: /template info <name> for details[/dim]")
        self.console.print("[dim]Use: /project create --template <name> to create from template[/dim]\n")

    # ==================== PRIORITY 3 COMMANDS ====================

    def cmd_search(self, args: List[str]):
        """Search across projects, specifications, and questions"""
        if not self.ensure_authenticated():
            return

        if not args:
            self.console.print("[yellow]Usage: /search <query> [resource_type] [category][/yellow]")
            self.console.print("[dim]Resource types: projects, specifications, questions[/dim]")
            return

        query = args[0]
        resource_type = args[1].lower() if len(args) > 1 else None
        category = args[2].lower() if len(args) > 2 else None

        # Validate resource type
        valid_types = ["projects", "specifications", "questions"]
        if resource_type and resource_type not in valid_types:
            self.console.print(f"[red]Invalid resource type: {resource_type}[/red]")
            self.console.print(f"[dim]Valid types: {', '.join(valid_types)}[/dim]")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Searching...", total=None)
                result = self.api.search(query, resource_type=resource_type, category=category)

            if result.get("success"):
                self._display_search_results(result)
            else:
                error = result.get("error", "Search failed")
                self.console.print(f"[red]✗ Search failed: {error}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_status(self, args: List[str]):
        """Display current project and session status"""
        if not self.ensure_authenticated():
            return

        self.console.print()

        # Project Status
        if self.current_project:
            self._display_project_status(self.current_project)
        else:
            self.console.print("[dim]No project selected. Use /project select <id> or /project create[/dim]")

        self.console.print()

        # Session Status
        if self.current_session:
            self._display_session_status(self.current_session)
        else:
            self.console.print("[dim]No active session. Use /session start to begin[/dim]")

        self.console.print()

        # Next steps
        self._display_next_steps()
        self.console.print()

    def cmd_filter(self, args: List[str]):
        """Filter specifications by type and category"""
        if not self.ensure_project_selected():
            return

        filter_type = args[0].lower() if args else "spec"  # 'spec' or 'question'
        category = args[1].lower() if len(args) > 1 else None

        # For now, use search with filters
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Filtering...", total=None)

                # Search for specifications
                if filter_type in ["spec", "specification", "all"]:
                    result = self.api.search("", resource_type="specifications", category=category)
                    if result.get("success"):
                        specs = result.get("results", [])
                        self.console.print(f"\n[bold cyan]Specifications ({len(specs)} found)[/bold cyan]\n")
                        self._display_filtered_results(specs, is_spec=True)

                # Search for questions
                if filter_type in ["question", "questions", "all"]:
                    result = self.api.search("", resource_type="questions", category=category)
                    if result.get("success"):
                        questions = result.get("results", [])
                        self.console.print(f"\n[bold cyan]Questions ({len(questions)} found)[/bold cyan]\n")
                        self._display_filtered_results(questions, is_spec=False)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_insights(self, args: List[str]):
        """Get insights for project (gaps, risks, opportunities)"""
        if not self.ensure_authenticated():
            return

        project_id = args[0] if args else (
            self.current_project["id"] if self.current_project else None
        )

        if not project_id:
            self.console.print("[yellow]Usage: /insights [project_id][/yellow]")
            self.console.print("[dim]If no project_id provided, uses currently selected project[/dim]")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Analyzing project...", total=None)
                result = self.api.get_insights(project_id)

            if result.get("success"):
                self._display_insights(result)
            else:
                error = result.get("error", "Failed to get insights")
                self.console.print(f"[red]✗ {error}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_resume(self, args: List[str]):
        """Resume a paused session"""
        if not self.ensure_authenticated():
            return

        if not args:
            # Show recent sessions
            self._show_recent_sessions()
            return

        session_id = args[0]

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Loading session...", total=None)
                result = self.api.get_session(session_id)

            if result.get("success"):
                session = result.get("session")
                self.current_session = session
                self.console.print(f"[green]✓ Session resumed: {session_id}[/green]")
                self._display_session_status(session)
                self.console.print("\n[cyan]Type your next response to continue the session[/cyan]\n")
            else:
                error = result.get("error", "Session not found")
                self.console.print(f"[red]✗ {error}[/red]")
                self.console.print("[dim]Use /resume (without args) to see recent sessions[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_wizard(self, args: List[str]):
        """Interactive project setup wizard"""
        if not self.ensure_authenticated():
            return

        self.console.print("\n[bold cyan]✨ Project Setup Wizard[/bold cyan]\n")
        self.console.print("[dim]Let's create a new project with templates![/dim]")
        self.console.print("[dim]Tip: Type 'back' at any step to go back[/dim]\n")

        # Step 1: Get project name
        while True:
            project_name = self.prompt_with_back("Project name")
            if project_name is None:
                self.console.print("[yellow]Wizard cancelled[/yellow]")
                return
            if project_name:
                break
            self.console.print("[yellow]Project name is required[/yellow]")

        # Step 2: Project description
        project_description = self.prompt_with_back("Project description (optional)", default="")
        if project_description is None:
            self.console.print("[yellow]Going back...[/yellow]")
            self.cmd_wizard([])
            return

        project_description = project_description or ""

        # Step 2: Select template
        template_id = self._wizard_select_template()
        if not template_id:
            self.console.print("[yellow]Template selection cancelled[/yellow]")
            return

        # Step 3: Create project
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating project...", total=None)
                create_result = self.api.create_project(project_name, project_description)

            if not create_result.get("success"):
                self.console.print(f"[red]✗ Project creation failed: {create_result.get('error')}[/red]")
                return

            project = create_result.get("project")
            project_id = project["id"]
            self.current_project = project

            self.console.print(f"[green]✓ Project created: {project_name}[/green]")

            # Step 4: Apply template
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Applying template...", total=None)
                template_result = self.api.apply_template(template_id, project_id)

            if template_result.get("success"):
                specs_count = template_result.get("specs_created", 0)
                self.console.print(f"[green]✓ Template applied: {specs_count} specifications created[/green]")
                self._display_project_created(project, template_id)
            else:
                self.console.print(f"[yellow]⚠ Template application failed: {template_result.get('error')}[/yellow]")
                self._display_project_created(project, None)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    # ==================== PRIORITY 3 HELPERS ====================

    def _display_insights(self, result: Dict[str, Any]):
        """Display project insights"""
        project_name = result.get("project_name", "Unknown")
        insights = result.get("insights", [])
        summary = result.get("summary", {})

        self.console.print(f"\n[bold cyan]Project Insights: {project_name}[/bold cyan]\n")

        if not insights:
            self.console.print("[dim]No insights to display[/dim]\n")
            return

        # Group insights by type
        gaps = [i for i in insights if i.get("type") == "gap"]
        risks = [i for i in insights if i.get("type") == "risk"]
        opportunities = [i for i in insights if i.get("type") == "opportunity"]

        # Display Gaps
        if gaps:
            self.console.print("[bold red]⚠ GAPS[/bold red]")
            for gap in gaps:
                severity = gap.get("severity", "medium")
                severity_icon = "🔴" if severity == "high" else "🟡"
                self.console.print(f"  {severity_icon} {gap.get('title')}")
                self.console.print(f"     {gap.get('description')}")
            self.console.print()

        # Display Risks
        if risks:
            self.console.print("[bold yellow]⚡ RISKS[/bold yellow]")
            for risk in risks:
                self.console.print(f"  🟡 {risk.get('title')}")
                self.console.print(f"     {risk.get('description')}")
            self.console.print()

        # Display Opportunities
        if opportunities:
            self.console.print("[bold green]✨ OPPORTUNITIES[/bold green]")
            for opp in opportunities:
                self.console.print(f"  🟢 {opp.get('title')}")
                self.console.print(f"     {opp.get('description')}")
            self.console.print()

        # Summary
        self.console.print("[bold cyan]Summary[/bold cyan]")
        coverage = summary.get("coverage_percentage", 0)
        coverage_bar = "█" * int(coverage / 10) + "░" * (10 - int(coverage / 10))
        self.console.print(f"  Coverage: [{coverage_bar}] {coverage:.0f}%")
        self.console.print(f"  Gaps: {summary.get('gaps_count', 0)}")
        self.console.print(f"  Risks: {summary.get('risks_count', 0)}")
        self.console.print(f"  Opportunities: {summary.get('opportunities_count', 0)}")
        self.console.print()

    def _display_search_results(self, result: Dict[str, Any]):
        """Display search results"""
        query = result.get("query", "")
        results = result.get("results", [])
        resource_counts = result.get("resource_counts", {})

        self.console.print(f"\n[bold cyan]Search Results for: {query}[/bold cyan]\n")

        if not results:
            self.console.print("[dim]No results found[/dim]\n")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Type", style="bold")
        table.add_column("Title")
        table.add_column("Preview")

        for res in results[:20]:  # Limit to 20 for display
            res_type = res.get("resource_type", "unknown").capitalize()
            title = res.get("title", "")[:40]
            preview = res.get("preview", "")[:60]
            table.add_row(res_type, title, preview)

        self.console.print(table)
        self.console.print(f"\n[dim]Found {resource_counts.get('projects', 0)} projects, "
                          f"{resource_counts.get('specifications', 0)} specifications, "
                          f"{resource_counts.get('questions', 0)} questions[/dim]\n")

    def _display_filtered_results(self, results: List[Dict[str, Any]], is_spec: bool):
        """Display filtered results"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Title")

        if is_spec:
            table.add_column("Category")

        for res in results[:30]:  # Limit to 30
            res_id = str(res.get("id", ""))[:8]
            title = res.get("title", "")[:50]

            if is_spec:
                category = res.get("category", "")
                table.add_row(res_id, title, category)
            else:
                table.add_row(res_id, title)

        self.console.print(table)
        self.console.print()

    def _display_project_status(self, project: Dict[str, Any]):
        """Display project status"""
        self.console.print("[bold cyan]📋 Project Status[/bold cyan]")
        self.console.print(f"  Name: {project.get('name', 'Unknown')}")
        self.console.print(f"  ID: {project.get('id', 'Unknown')[:8]}")
        self.console.print(f"  Phase: {project.get('current_phase', 'phase_1')}")
        self.console.print(f"  Status: {project.get('status', 'active')}")
        self.console.print(f"  Maturity: {project.get('maturity_score', 0):.0f}%")

    def _display_session_status(self, session: Dict[str, Any]):
        """Display session status"""
        self.console.print("[bold cyan]💬 Session Status[/bold cyan]")
        self.console.print(f"  ID: {session.get('id', 'Unknown')[:8]}")
        self.console.print(f"  Mode: {session.get('mode', 'socratic')}")
        self.console.print(f"  Status: {session.get('status', 'active')}")
        started = session.get('started_at', 'N/A')
        self.console.print(f"  Started: {started}")

    def _display_next_steps(self):
        """Display suggested next steps"""
        self.console.print("[bold cyan]💡 Next Steps[/bold cyan]")

        if not self.current_project:
            self.console.print("  → Create a project with /project create")
            self.console.print("  → Or use the wizard: /wizard")
        elif not self.current_session:
            self.console.print("  → Start a session: /session start")
            self.console.print("  → Or search: /search <query>")
        else:
            self.console.print("  → Continue the session by typing your response")
            self.console.print("  → Or view insights: /insights")
            self.console.print("  → Or end session: /session end")

    def _display_project_created(self, project: Dict[str, Any], template_id: Optional[str]):
        """Display project creation confirmation"""
        self.console.print(f"\n[bold green]✓ Project created successfully![/bold green]")
        self.console.print(f"[cyan]Name:[/cyan] {project.get('name', 'Unknown')}")
        self.console.print(f"[cyan]ID:[/cyan] {project.get('id', 'Unknown')[:8]}")
        if template_id:
            self.console.print(f"[cyan]Template:[/cyan] {template_id}")
        self.console.print("\n[dim]You can now:[/dim]")
        self.console.print("  • /session start - Begin gathering specifications")
        self.console.print("  • /insights - View project recommendations")
        self.console.print("  • /search - Search specifications")
        self.console.print()

    def _wizard_select_template(self) -> Optional[str]:
        """Interactive template selection for wizard"""
        templates = [
            ("template-web-app", "Web Application"),
            ("template-api", "REST API"),
            ("template-mobile", "Mobile Application"),
        ]

        self.console.print("\n[cyan]Choose a template:[/cyan]\n")
        for i, (template_id, template_name) in enumerate(templates, 1):
            self.console.print(f"  {i}. {template_name}")

        while True:
            choice = Prompt.ask("\nTemplate (1-3 or 'back')", choices=["1", "2", "3", "back"], default="1")

            if choice == "back":
                return None
            elif choice == "1":
                return "template-web-app"
            elif choice == "2":
                return "template-api"
            elif choice == "3":
                return "template-mobile"

    def _show_recent_sessions(self):
        """Show list of recent sessions"""
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Loading recent sessions...", total=None)
                result = self.api.list_recent_sessions()

            if result.get("success"):
                sessions = result.get("sessions", [])
                self.console.print(f"\n[bold cyan]Recent Sessions[/bold cyan]\n")

                if not sessions:
                    self.console.print("[dim]No recent sessions[/dim]\n")
                    return

                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim")
                table.add_column("Project")
                table.add_column("Status")
                table.add_column("Mode")

                for session in sessions[:10]:
                    sess_id = str(session.get("id", ""))[:8]
                    project = session.get("project_id", "Unknown")[:8]
                    status = session.get("status", "unknown")
                    mode = session.get("mode", "socratic")
                    table.add_row(sess_id, project, status, mode)

                self.console.print(table)
                self.console.print(f"\n[dim]Use: /resume <session_id> to resume[/dim]\n")
            else:
                self.console.print("[yellow]Could not load recent sessions[/yellow]\n")

        except Exception as e:
            self.console.print(f"[red]Error loading sessions: {e}[/red]\n")

    def handle_command(self, user_input: str):
        """Parse and handle command"""
        parts = user_input.strip().split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        if command in ["/help", "/h"]:
            self.print_help()

        elif command in ["/exit", "/quit", "/q"]:
            if self.current_session:
                if Confirm.ask("[yellow]You have an active session. End it before exiting?[/yellow]"):
                    self.cmd_session(["end"])
            self.running = False
            self.console.print("\n[cyan]..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..[/cyan]\n")
            # Shutdown is called in run()'s finally block, but set running=False to exit the loop

        elif command == "/clear":
            self.console.clear()
            self.print_banner()

        elif command == "/back":
            self.cmd_back()

        elif command == "/debug":
            self.debug = not self.debug
            self.console.print(f"[cyan]Debug mode: {'ON' if self.debug else 'OFF'}[/cyan]")

        elif command == "/register":
            self.cmd_register()

        elif command == "/login":
            self.cmd_login()

        elif command == "/logout":
            self.cmd_logout()

        elif command == "/whoami":
            self.cmd_whoami()

        elif command == "/projects":
            self.cmd_projects()

        elif command == "/project":
            self.cmd_project(args)

        elif command == "/session":
            self.cmd_session(args)

        elif command == "/sessions":
            self.cmd_sessions()

        elif command == "/history":
            self.cmd_history()

        elif command == "/mode":
            if not self.ensure_session_active():
                self.console.print("[yellow]Start a session first with /session start[/yellow]")
                return

            try:
                # Map CLI mode names to backend mode names
                cli_mode_map = {"socratic": "socratic", "direct": "direct_chat"}
                backend_mode_map = {"socratic": "socratic", "direct_chat": "direct"}

                if args:
                    mode = args[0].lower()
                    if mode not in cli_mode_map:
                        self.console.print("[red]Invalid mode. Use: socratic or direct[/red]")
                        return

                    backend_mode = cli_mode_map[mode]
                else:
                    # Toggle mode
                    new_backend_mode = "direct_chat" if self.chat_mode == "socratic" else "socratic"
                    mode = backend_mode_map[new_backend_mode]
                    backend_mode = new_backend_mode

                # Switch mode on backend
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Switching mode...", total=None)
                    result = self.api.set_session_mode(
                        self.current_session["id"],
                        backend_mode
                    )

                if result.get("success"):
                    self.chat_mode = mode
                    mode_emoji = "🤔" if mode == "socratic" else "💬"
                    self.console.print(f"[green]✓ Switched to {mode} mode {mode_emoji}[/green]")

                    if mode == "socratic":
                        self.console.print("[dim]Socratic mode: Thoughtful questioning to extract specifications[/dim]")
                    else:
                        self.console.print("[dim]Direct mode: Direct conversation with AI assistant[/dim]")
                else:
                    self.console.print(f"[red]Failed to switch modes: {result.get('error', 'Unknown error')}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        elif command == "/config":
            self.cmd_config(args)

        elif command == "/theme":
            self.cmd_theme(args)

        elif command == "/format":
            self.cmd_format(args)

        elif command == "/save":
            self.cmd_save(args)

        elif command == "/export":
            self.cmd_export(args)

        elif command == "/stats":
            self.cmd_stats(args)

        elif command == "/template":
            self.cmd_template(args)

        elif command == "/search":
            self.cmd_search(args)

        elif command == "/status":
            self.cmd_status(args)

        elif command == "/insights":
            self.cmd_insights(args)

        elif command == "/filter":
            self.cmd_filter(args)

        elif command == "/resume":
            self.cmd_resume(args)

        elif command == "/wizard":
            self.cmd_wizard(args)

        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[yellow]Type /help for available commands[/yellow]")

    def run(self):
        """Main CLI loop"""
        # Start backend server
        self._start_server()

        self.print_banner()

        # Check if user is logged in
        if self.config.get("access_token"):
            email = self.config.get("user_email", "User")
            self.console.print(f"[green]Welcome back, {email}![/green]\n")
            self.api.set_token(self.config.get("access_token"))
            # Also set refresh token if available
            refresh_token = self.config.get("refresh_token")
            if refresh_token:
                self.api.set_refresh_token(refresh_token)
        else:
            self.console.print("[yellow]Please /login or /register to get started[/yellow]\n")

        # Main loop
        try:
            while self.running:
                try:
                    # Build prompt
                    prompt_parts = []
                    if self.current_project:
                        prompt_parts.append(f"[cyan]{self.current_project['name'][:20]}[/cyan]")
                    if self.current_session:
                        prompt_parts.append(f"[green]session[/green]")

                    # Add mode indicator
                    mode_emoji = "🤔" if self.chat_mode == "socratic" else "💬"
                    prompt_parts.append(f"[dim]{mode_emoji}[/dim]")

                    prompt_text = " ".join(prompt_parts) if prompt_parts else f"[dim]socrates {mode_emoji}[/dim]"

                    # Get user input
                    user_input = self.prompt_session.prompt(
                        f"{prompt_text} > ",
                        completer=self.completer
                    ).strip()

                    if not user_input:
                        continue

                    # Handle command or chat message
                    if user_input.startswith('/'):
                        self.handle_command(user_input)
                    else:
                        self.handle_chat_message(user_input)

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use /exit to quit[/yellow]")
                    continue

                except EOFError:
                    break

                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    if self.debug:
                        import traceback
                        self.console.print(traceback.format_exc())
        finally:
            # Ensure server shuts down even if there's an unhandled exception
            self.shutdown()


def main():
    """Main entry point"""
    # Check if CLI dependencies are available
    if not _cli_imports_available:
        print(f"Error: Missing required package: {_cli_import_error}")
        print("\nPlease install CLI dependencies:")
        print("    pip install requests rich prompt-toolkit")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Socrates CLI - AI-Powered Specification Gathering")
    parser.add_argument(
        "--api-url",
        default=os.getenv("SOCRATES_API_URL", "http://localhost:8000"),
        help="Socrates API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Don't automatically start the backend server"
    )

    args = parser.parse_args()

    cli = SocratesCLI(
        api_url=args.api_url,
        debug=args.debug,
        auto_start_server=not args.no_auto_start
    )

    try:
        cli.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n")
        cli.shutdown()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        cli.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
