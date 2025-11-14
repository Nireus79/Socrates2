#!/usr/bin/env python3
"""
Socrates CLI - Interactive Command-Line Interface for Socrates
A Claude Code-style interface for specification gathering and project development.

Usage:
    python Socrates.py [--api-url URL] [--debug]
"""

from __future__ import annotations

# Fix encoding for Windows console compatibility
import sys
import io
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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

# Import CLI logger
from cli_logger import get_cli_logger

# Import API extensions
from api_client_extension import SocratesAPIExtension

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

    def get_logging_enabled(self) -> bool:
        """Get CLI logging enabled state"""
        return self.data.get("cli_logging_enabled", False)

    def set_logging_enabled(self, enabled: bool):
        """Set CLI logging enabled state"""
        self.set("cli_logging_enabled", enabled)


class SocratesAPI(SocratesAPIExtension):
    """API client for Socrates backend with 150+ extended methods"""

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

    def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update project"""
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        response = self._request("PUT", f"/api/v1/projects/{project_id}", json=data)
        return response.json()

    def archive_project(self, project_id: str) -> Dict[str, Any]:
        """Archive project (soft delete)"""
        response = self._request("DELETE", f"/api/v1/projects/{project_id}")
        return response.json()

    def restore_project(self, project_id: str) -> Dict[str, Any]:
        """Restore an archived project back to active status"""
        response = self._request("POST", f"/api/v1/projects/{project_id}/restore")
        return response.json()

    def destroy_project(self, project_id: str) -> Dict[str, Any]:
        """Permanently delete an archived project (hard delete)"""
        response = self._request("POST", f"/api/v1/projects/{project_id}/destroy")
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

    def get_sessions(self, project_id: str) -> Dict[str, Any]:
        """Alias for list_sessions - get project sessions"""
        return self.list_sessions(project_id)

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

    def branch_session(self, session_id: str, branch_name: Optional[str] = None) -> Dict[str, Any]:
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
        self.console = Console(legacy_windows=None, force_terminal=None, color_system='auto')
        self.api = SocratesAPI(api_url, self.console)
        self.config = SocratesConfig()
        # Let API know about config so it can save tokens
        self.api.set_config(self.config)

        # Initialize CLI logger
        self.cli_logger = get_cli_logger()
        self.cli_logger.set_enabled(self.config.get_logging_enabled())

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

        # Initialize modular command registry
        try:
            from cli.registry import CommandRegistry
            self.registry = CommandRegistry(self.console, self.api, self._get_config_dict())
            self.registry.load_all_commands()
            registry_commands = list(self.registry.list_commands().keys())
        except Exception as e:
            self.console.print(f"Warning: Could not load command registry: {e}")
            self.registry = None
            registry_commands = []

        # Command completer - combine system commands with registry commands
        self.system_commands = ["/help", "/exit", "/back", "/clear", "/debug"]
        self.commands = self.system_commands + [f"/{cmd}" for cmd in registry_commands] + [
            "/chat",  # Legacy command
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True)

        # Prompt session with history
        self.use_simple_input = False

        try:
            self.prompt_session = PromptSession(
                history=FileHistory(str(self.config.history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer
            )
        except Exception as e:
            # Handle terminal compatibility issues by falling back to basic input()
            if "NoConsoleScreenBufferError" in str(type(e).__name__) or "xterm" in str(e):
                # Print without special characters to avoid encoding issues
                print("[WARN] Terminal compatibility issue detected")
                print("[INFO] Using basic input mode (no auto-completion)\n")
                self.use_simple_input = True
                self.prompt_session = None
            else:
                raise

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (Ctrl+C, SIGTERM)"""
        self.console.print("\nShutting down gracefully...")
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
                self.console.print(f"[OK] Backend server already running at {self.server_url}")
                return
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        # Start the server
        print("Starting backend server...")

        # Find the backend directory
        backend_dir = Path(__file__).parent / "backend"
        if not backend_dir.exists():
            print(f"Error: Backend directory not found at {backend_dir}")
            print("Continuing without auto-started server...")
            return

        try:
            # Create a temporary file for server logs (for debugging)
            import tempfile
            import platform

            server_log_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False)
            server_log_path = server_log_file.name
            server_log_file.close()

            if platform.system() == "Windows":
                # Hide the server process window on Windows
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                preexec_fn = None
            else:
                creationflags = 0
                # Use preexec_fn for graceful shutdown on Unix
                preexec_fn = os.setsid

            with open(server_log_path, 'w') as log_file:
                self.server_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
                    cwd=str(backend_dir),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=creationflags if platform.system() == "Windows" else 0,
                    preexec_fn=preexec_fn if platform.system() != "Windows" else None
                )

            # Wait for server to be ready
            if self._wait_for_server(log_path=server_log_path):
                print(f"[OK] Backend server started on {self.server_url}")
            else:
                print("[ERROR] Server failed to start")
                # Try to read the error from the log file
                try:
                    with open(server_log_path, 'r') as log_file:
                        log_content = log_file.read()
                        if log_content.strip():
                            print("Server startup error:")
                            for line in log_content.split('\n')[-20:]:  # Show last 20 lines
                                if line.strip():
                                    print(f"  {line}")
                except Exception:
                    pass
                print("Continuing without server...\n")
        except Exception as e:
            print(f"Failed to start server: {e}")
            print("Continuing without auto-started server...\n")

    def _wait_for_server(self, timeout: int = 10, log_path: Optional[str] = None) -> bool:
        """Wait for server to be ready"""
        start_time = time.time()
        last_check_time = 0

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.server_url}/api/v1/admin/health", timeout=1)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                pass
            except Exception as e:
                # Log unexpected errors
                if time.time() - last_check_time > 2:  # Don't log too frequently
                    if self.debug:
                        print(f"Health check error: {type(e).__name__}")
                    last_check_time = time.time()

            time.sleep(0.5)

        # Check if process is still running
        if self.server_process:
            if self.server_process.poll() is not None:
                # Process crashed
                print("Server process crashed")
                if log_path:
                    try:
                        with open(log_path, 'r') as f:
                            content = f.read()
                            if content.strip():
                                print("Last log output:")
                                for line in content.split('\n')[-10:]:
                                    if line.strip():
                                        print(f"  {line}")
                    except Exception:
                        pass

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
                    self.console.print(f"Note: {e}")

    def shutdown(self):
        """Gracefully shutdown the application"""
        if self.auto_start_server and self.server_process is not None:
            try:
                self.console.print("Stopping backend server...")
            except Exception:
                print("Stopping backend server...")
            self._stop_server()

    def print_banner(self):
        """Print welcome banner"""
        try:
            # Try to print fancy banner with Rich
            banner = """
╔═════════════════════════════════════════════════════════╗
║       [bold white]                 SOCRATES           [/bold white]              ║
║[italic]     Ουδέν οίδα, ούτε διδάσκω τι, αλλά διαπορώ μόνον[/italic]     ║
╚═════════════════════════════════════════════════════════╝

Type /help for available commands or just start chatting!
"""
            self.console.print(banner)
        except Exception:
            # Fallback to plain text if encoding issues
            print("=" * 55)
            print("           SOCRATES")
            print("     Ουδέν οίδα, ούτε διδάσκω τι, αλλά διαπορώ μόνον")
            print("=" * 55)
            print("\nType /help for available commands or just start chatting!\n")

    def print_help(self):
        """Print help message"""
        help_text = """
Available Commands:

Authentication & Account:
  /register              Register new account
  /login                 Login to existing account
  /logout                Logout from current session
  /whoami                Show current user information
  /account               Manage your account (show, change-password, delete)
  /account show          Show account details
  /account change-password  Change your password
  /account delete        Delete your account (permanent)

Project Management:
  /projects              List all your projects
  /project                Show project menu
  /project create        Create new project
  /project select        Show interactive project list to select from
  /project select <id>   Select project directly by ID
  /project info          Show current project details
  /project manage        Manage project (archive, restore, destroy)

Session Management:
  /sessions              List all sessions for current project
  /session               Show session menu
  /session start         Start new Socratic questioning session
  /session select        Show interactive session list to select from
  /session end           End current session
  /session delete <id>   Delete a session
  /session note          Add note to current session
  /history               Show conversation history

Chat Modes:
  /mode                  Toggle between Socratic and direct chat modes
  /mode socratic         Switch to Socratic questioning mode
  /mode direct           Switch to direct chat mode

Configuration & Export:
  /config                Show/manage configuration settings
  /config set <key> <val> Set configuration value
  /config get <key>      Get configuration value
  /theme [<name>]        Show/change color theme
  /format [<name>]       Show/change output format
  /save [<filename>]     Save session to Markdown file
  /export [format]       Export project (markdown, json, csv, pdf)
  /stats                 Show session statistics

Advanced Features:
  /template              Manage project templates
  /template list         List available templates
  /template info <name>  Show template details
  /search <query>        Search projects, specs, and questions
  /insights              Analyze project gaps, risks, opportunities
  /filter [type] [cat]   Filter specifications by category
  /resume                Resume a paused session
  /wizard                Interactive project setup with templates
  /status                Show current project and session status

System:
  /help                  Show this help message
  /back                  Go back (clear project/session selection)
  /clear                 Clear screen
  /debug                 Toggle debug mode
  /exit                  Exit Socrates CLI (aliases: /quit, /q)

Quick Tips:

Getting Started:
1. /register or /login to create/access your account
2. /project create to start a new project
3. /session start to begin a Socratic session
4. Type your requirements and answer AI questions
5. /save or /export to save your work

Project Discovery:
• /projects - View all projects
• /project select - Interactive project selection
• /status - Show current context

Session Management:
• /sessions - List sessions in current project
• /session start - Create new session
• /mode - Switch between Socratic and direct chat

Chat Modes:

Socratic Mode (default) :
The AI uses Socratic questioning to help you think deeply about your
requirements. It asks thoughtful questions to extract specifications.
Requires an active session (/session start).

Direct Mode :
Chat directly with the AI assistant without structured questioning.
Great for quick questions, clarifications, or general discussion.
No session required.
"""
        self.console.print(Panel(help_text, title="Socrates CLI Help", border_style="cyan"))

    def ensure_authenticated(self) -> bool:
        """Check if user is authenticated"""
        token = self.config.get("access_token")
        if self.debug:
            self.console.print(f"DEBUG: ensure_authenticated() called")
            self.console.print(f"DEBUG: Config data keys: {list(self.config.data.keys())}")
            self.console.print(f"DEBUG: access_token value: {repr(token)}")
        if not token:
            if self.debug:
                self.console.print(f"DEBUG: No access_token in config. Config file: {self.config.config_file}")
            self.console.print("[ERROR] Not authenticated. Use /login or /register first")
            return False
        self.api.set_token(token)
        if self.debug:
            self.console.print(f"DEBUG: Token found in config, user: {self.config.get('user_email')}")
        return True

    def _get_config_dict(self) -> Dict[str, Any]:
        """Get full config as dictionary for command handlers."""
        return {
            "access_token": self.config.get("access_token"),
            "refresh_token": self.config.get("refresh_token"),
            "user": self.config.get("user"),
            "user_email": self.config.get("user_email"),
            "current_project": self.current_project,
            "current_session": self.current_session,
            "current_question": self.current_question,
            "chat_mode": self.chat_mode,
            "debug": self.debug,
        }

    def ensure_project_selected(self) -> bool:
        """Check if project is selected"""
        if not self.current_project:
            self.console.print("No project selected. Use /project select <id> or /project create")
            return False
        return True

    def ensure_session_active(self) -> bool:
        """Check if session is active"""
        if not self.current_session:
            self.console.print("No active session. Use /session start")
            return False
        return True

    def prompt_with_back(self, prompt_text: str, password: bool = False, default: Optional[str] = None) -> Optional[str]:
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
            if self.use_simple_input:
                # Simple mode: use getpass for password input
                from getpass import getpass
                try:
                    user_input = getpass(f"{prompt_text}: ")
                except EOFError:
                    return None
            else:
                try:
                    pwd_session = PromptSession()
                    user_input = pwd_session.prompt(
                        f"{prompt_text}: ",
                        is_password=True
                    )
                except EOFError:
                    return None
        else:
            if self.use_simple_input:
                # Simple mode: use basic input()
                default_text = f" ({default})" if default else ""
                user_input = input(f"{prompt_text}{default_text}: ").strip()
                if not user_input and default:
                    user_input = default
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
            if self.use_simple_input:
                user_input = input(f"{question} (y/n/back): ").strip().lower()
            else:
                user_input = Prompt.ask(question + " (y/n/back)", choices=["y", "n", "back"]).lower()
            if user_input == "back":
                return None
            return user_input == "y"
        except Exception:
            return False

    def getpass(self, prompt_text: str = "Password: ") -> str:
        """
        Get password input securely (masked input).
        """
        return self.prompt_with_password(prompt_text, is_password=True) or ""

    def get_prompt_input(self, prompt_text: str) -> str:
        """
        Get user input, handling both PromptSession and basic input() modes.
        Falls back to basic input() if PromptSession is unavailable.
        """
        if self.use_simple_input:
            return input(prompt_text).strip()
        else:
            try:
                return self.prompt_session.prompt(
                    prompt_text,
                    completer=self.completer
                ).strip()
            except AttributeError:
                # Fallback in case prompt_session is None
                return input(prompt_text).strip()

    def cmd_register(self):
        """Handle /register command"""
        self.console.print("\nRegister New Account\n")
        self.console.print("Tip: Type 'back' at any step to go back\n")

        try:
            data = {}

            # Step 1: Username
            while True:
                username = self.prompt_with_back("Username")
                if username is None:
                    self.console.print("Registration cancelled")
                    return
                if username:
                    data['username'] = username
                    break
                self.console.print("Username is required")

            # Step 2: Name
            while True:
                name = self.prompt_with_back("First name")
                if name is None:
                    # Go back to username
                    self.console.print("Going back...")
                    data.pop('username', None)
                    self.cmd_register()
                    return
                if name:
                    data['name'] = name
                    break
                self.console.print("First name is required")

            # Step 3: Surname
            while True:
                surname = self.prompt_with_back("Last name")
                if surname is None:
                    # Go back to name
                    self.console.print("Going back...")
                    data.pop('name', None)
                    # Restart from Step 2
                    self.cmd_register()
                    return
                if surname:
                    data['surname'] = surname
                    break
                self.console.print("Last name is required")

            # Step 4: Email
            while True:
                email = self.prompt_with_back("Email")
                if email is None:
                    # Go back to surname
                    self.console.print("Going back...")
                    data.pop('surname', None)
                    self.cmd_register()
                    return
                if email:
                    data['email'] = email
                    break
                self.console.print("Email is required")

            # Step 5: Password
            while True:
                password = self.prompt_with_back("Password", password=True)
                if password is None:
                    # Go back to email
                    self.console.print("Going back...")
                    data.pop('email', None)
                    self.cmd_register()
                    return
                if password:
                    data['password'] = password
                    break
                self.console.print("Password is required")

            # Step 6: Confirm password
            while True:
                password_confirm = self.prompt_with_back("Confirm password", password=True)
                if password_confirm is None:
                    # Go back to password
                    self.console.print("Going back...")
                    data.pop('password', None)
                    self.cmd_register()
                    return
                if password_confirm:
                    break
                self.console.print("Please confirm your password")

            if data['password'] != password_confirm:
                self.console.print("Passwords do not match!")
                return

            # Step 7: Review and confirm
            self.console.print("\nReview your information:")
            self.console.print(f"  Username: {data['username']}")
            self.console.print(f"  Name: {data['name']} {data['surname']}")
            self.console.print(f"  Email: {data['email']}")

            proceed = Confirm.ask("\nProceed with registration?")
            if not proceed:
                self.console.print("Registration cancelled")
                return

            try:
                if self.debug:
                    self.console.print(f"DEBUG: Sending registration request for username='{data['username']}'")

                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Creating account...", total=None)
                    result = self.api.register(data['username'], data['name'], data['surname'], data['email'], data['password'])

                if self.debug:
                    if result.get("user_id"):
                        self.console.print(f"DEBUG: Registration successful - user_id={result.get('user_id')}")
                    else:
                        self.console.print(f"DEBUG: Registration failed - response: {result}")

                # Backend returns user_id on success (no "success" field)
                if result.get("user_id"):
                    # Log the registration action
                    self.cli_logger.log_register(data['username'], data['email'])
                    self.console.print(f"\n[OK] Account created successfully!")
                    self.console.print(f"User ID: {result.get('user_id')}")
                    self.console.print(f"Username: {data['username']}")
                    self.console.print(f"Email: {data['email']}")
                    self.console.print("\nPlease login with /login")
                else:
                    self.console.print(f"\n[ERROR] Registration failed: {result.get('message', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                self.console.print(f"\n[ERROR] Cannot connect to Socrates backend")
                self.console.print(f"The server is not running at http://localhost:8000")
                self.console.print(f"Please start the backend server first:")
                self.console.print(f"  cd backend")
                self.console.print(f"  uvicorn app.main:app --reload")
            except Exception as e:
                self.console.print(f"[ERROR] Registration error: {str(e)[:100]}")
        except requests.exceptions.ConnectionError:
            self.console.print(f"\n[ERROR] Cannot connect to Socrates backend")
            self.console.print(f"The server is not running at http://localhost:8000")
            self.console.print(f"Please start the backend server first:")
            self.console.print(f"  cd backend")
            self.console.print(f"  uvicorn app.main:app --reload")
        except Exception as e:
            self.console.print(f"[ERROR] Error: {str(e)[:100]}")

    def cmd_login(self):
        """Handle /login command"""
        self.console.print("\nLogin\n")
        self.console.print("Tip: Type 'back' at any step to go back\n")

        try:
            data = {}

            # Step 1: Username
            while True:
                username = self.prompt_with_back("Username")
                if username is None:
                    self.console.print("Login cancelled")
                    return
                if username:
                    data['username'] = username
                    break
                self.console.print("Username is required")

            # Step 2: Password
            while True:
                password = self.prompt_with_back("Password", password=True)
                if password is None:
                    # Go back to username
                    self.console.print("Going back...")
                    data.pop('username', None)
                    self.cmd_login()
                    return
                if password:
                    data['password'] = password
                    break
                self.console.print("Password is required")

            try:
                if self.debug:
                    self.console.print(f"DEBUG: Sending login request for username='{data['username']}'")

                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Logging in...", total=None)
                    result = self.api.login(data['username'], data['password'])

                if self.debug:
                    if result.get("access_token"):
                        self.console.print(f"DEBUG: Login successful")
                    else:
                        self.console.print(f"DEBUG: Login failed - response: {result}")

                if result.get("access_token"):
                    self.config.set("access_token", result["access_token"])
                    self.config.set("refresh_token", result.get("refresh_token"))
                    self.config.set("user_email", result.get("username"))
                    self.config.set("username", result.get("username"))  # Store username for account mgmt
                    self.config.set("user_id", result.get("user_id"))
                    self.config.set("user_name", result.get("name"))
                    self.api.set_token(result["access_token"])
                    if result.get("refresh_token"):
                        self.api.set_refresh_token(result["refresh_token"])
                    user_display = result.get("name", data['username'])
                    # Log the login action
                    self.cli_logger.log_login(data['username'], result.get("username", ""))
                    if self.debug:
                        self.console.print(f"DEBUG: Token saved to config. Config keys: {list(self.config.data.keys())}")
                        self.console.print(f"DEBUG: Config file: {self.config.config_file}")
                    self.console.print(f"\n[OK] Logged in successfully as {user_display}")
                else:
                    error_detail = result.get('message', result.get('detail', 'Invalid credentials'))
                    self.console.print(f"\n[ERROR] Login failed: {error_detail}")
            except requests.exceptions.ConnectionError:
                self.console.print(f"\n[ERROR] Cannot connect to Socrates backend")
                self.console.print(f"The server is not running at http://localhost:8000")
                self.console.print(f"Please start the backend server first:")
                self.console.print(f"  cd backend")
                self.console.print(f"  uvicorn app.main:app --reload")
            except Exception as e:
                self.console.print(f"[ERROR] Login error: {str(e)[:100]}")

        except requests.exceptions.ConnectionError:
            self.console.print(f"\n[ERROR] Cannot connect to Socrates backend")
            self.console.print(f"The server is not running at http://localhost:8000")
            self.console.print(f"Please start the backend server first:")
            self.console.print(f"  cd backend")
            self.console.print(f"  uvicorn app.main:app --reload")
        except Exception as e:
            self.console.print(f"[ERROR] Error: {str(e)[:100]}")

    def cmd_logout(self):
        """Handle /logout command"""
        if not self.ensure_authenticated():
            return

        try:
            email = self.config.get("user_email", "Unknown")
            self.api.logout()
            # Log the logout action
            self.cli_logger.log_logout(email)
            self.config.clear()
            self.current_project = None
            self.current_session = None
            self.console.print("[OK] Logged out successfully")
        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_whoami(self):
        """Handle /whoami command"""
        if not self.ensure_authenticated():
            return

        email = self.config.get("user_email", "Unknown")
        self.console.print(f"\nLogged in as: {email}")

        if self.current_project:
            self.console.print(
                f"Current project: {self.current_project['name']} ({self.current_project['id']})")

        if self.current_session:
            self.console.print(f"Active session: {self.current_session['id']}")

    def cmd_account(self, args: List[str]):
        """Handle /account command - manage user account"""
        if not self.ensure_authenticated():
            return

        if not args:
            self.console.print("\nAccount Management\n")
            self.console.print("Usage: /account <command>\n")
            self.console.print("Available commands:")
            self.console.print("  show              Show account details")
            self.console.print("  change-password   Change your password")
            self.console.print("  delete            Delete your account (permanent)")
            self.console.print()
            return

        subcommand = args[0].lower()

        if subcommand == "show":
            email = self.config.get("user_email", "Unknown")
            username = self.config.get("username", "Unknown")
            user_id = self.config.get("user_id", "Unknown")

            info = f"""
Account Information

Username: {username}
Email: {email}
User ID: {user_id}
"""
            self.console.print(Panel(info, border_style="cyan"))

        elif subcommand == "change-password":
            self.console.print("\nChange Password\n")
            try:
                current_password = self.getpass("Current password: ")
                if not current_password:
                    self.console.print("Password change cancelled")
                    return

                # Confirm new password twice
                while True:
                    new_password = self.getpass("New password (min 8 characters): ")
                    if not new_password or len(new_password) < 8:
                        self.console.print("Password must be at least 8 characters")
                        continue

                    confirm_password = self.getpass("Confirm new password: ")
                    if new_password == confirm_password:
                        break
                    self.console.print("Passwords do not match. Try again.")

                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Changing password...", total=None)
                    result = self.api.change_password(current_password, new_password)

                if result.get("success"):
                    self.console.print("\n[OK] Password changed successfully!")
                else:
                    error = result.get("error") or result.get("data", {}).get("detail", "Unknown error")
                    self.console.print(f"\n[ERROR] Failed: {error}")

            except KeyboardInterrupt:
                self.console.print("\nPassword change cancelled")
            except Exception as e:
                self.console.print(f"Error: {e}")

        elif subcommand == "delete":
            email = self.config.get("user_email", "Unknown")
            username = self.config.get("username", "Unknown")

            self.console.print("\n[WARNING] DELETE ACCOUNT\n")
            self.console.print("This action is PERMANENT and CANNOT be undone!")
            self.console.print(f"You are about to delete the account: {email}\n")

            # Double confirmation
            confirm1 = Confirm.ask("Are you sure you want to delete your account?", default=False)
            if not confirm1:
                self.console.print("Account deletion cancelled")
                return

            confirm2 = Confirm.ask("Type your username to confirm: ", choices=["yes", "no"], default="no")
            if confirm2 != "yes":
                # Actually, we need password verification
                password = self.getpass("Enter your password to confirm deletion: ")
                if not password:
                    self.console.print("Account deletion cancelled")
                    return

                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Deleting account...", total=None)
                    result = self.api.delete_account(password, username)

                if result.get("success"):
                    self.console.print("\n[OK] Account deleted successfully")
                    self.console.print("You have been logged out. Please close this application.")
                    self.config.clear()
                    self.running = False
                else:
                    error = result.get("error") or result.get("data", {}).get("detail", "Unknown error")
                    self.console.print(f"\n[ERROR] Failed: {error}")
            else:
                self.console.print("Account deletion cancelled")

        else:
            self.console.print(f"Unknown subcommand: {subcommand}")
            self.console.print("Use /account (with no args) to see available commands")

    def cmd_back(self):
        """Handle /back command - go back by clearing selections"""
        had_selection = False

        if self.current_session:
            self.current_session = None
            self.current_question = None
            self.console.print("[OK] Session cleared")
            had_selection = True

        if self.current_project:
            self.current_project = None
            self.console.print("[OK] Project cleared")
            had_selection = True

        if not had_selection:
            self.console.print("No project or session selected to clear")
            self.console.print("Available commands:")
            self.console.print("  /project create  - Create a new project")
            self.console.print("  /projects        - List your projects")
            self.console.print("  /help            - Show all available commands")

    def cmd_projects(self):
        """Handle /projects command"""
        if not self.ensure_authenticated():
            return

        try:
            result = self.api.list_projects()
            # Extract projects from data wrapper
            data = result.get("data", {})
            projects = data.get("projects", []) if isinstance(data, dict) else []

            if not projects:
                self.console.print("\nNo projects yet. Create one with /project create")
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
                # Backend returns: id, name, description, status, phase, maturity_level, created_at
                maturity = project.get("maturity_level", 0)
                maturity_str = f"{maturity}%" if isinstance(maturity, (int, float)) else "0%"
                table.add_row(
                    selected + project["id"][:8],
                    project["name"],
                    project.get("description", "")[:40],
                    project.get("phase", "N/A"),
                    maturity_str,
                    project.get("created_at", "")[:10]
                )

            self.console.print()
            self.console.print(table)
            self.console.print()
        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_project(self, args: List[str]):
        """Handle /project command"""
        if not self.ensure_authenticated():
            return

        if not args:
            # Show interactive menu
            self.console.print("\nProject Management\n")
            self.console.print("What would you like to do?")
            self.console.print("  [1] Create a new project")
            self.console.print("  [2] Select an existing project")
            self.console.print("  [3] View current project info")
            self.console.print("  [4] Manage a project (archive/restore/delete)")
            self.console.print("  [back] Go back\n")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "back"], default="1")

            if choice == "back":
                return
            elif choice == "1":
                self.cmd_project(["create"])
            elif choice == "2":
                self.cmd_project(["select"])
            elif choice == "3":
                self.cmd_project(["info"])
            elif choice == "4":
                self.console.print("Use: /project manage <project_id> or /project manage")
                self.cmd_project(["manage"])
            return

        subcommand = args[0]

        if subcommand == "create":
            self.console.print("\nCreate New Project\n")
            self.console.print("Tip: Type 'back' to cancel\n")

            # Step 1: Project name
            while True:
                name = self.prompt_with_back("Project name")
                if name is None:
                    self.console.print("Project creation cancelled")
                    return
                if name:
                    break
                self.console.print("Project name is required")

            # Step 2: Description (optional)
            description = self.prompt_with_back("Description (optional)", default="")
            if description is None:
                self.console.print("Going back...")
                self.cmd_project(["create"])
                return

            description = description or ""

            try:
                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Creating project...", total=None)
                    result = self.api.create_project(name, description)

                if result.get("success"):
                    project_id = result.get("data", {}).get("project_id")
                    # Log the project creation
                    self.cli_logger.log_project_create(name, project_id)
                    self.console.print(f"\n[OK] Project created: {project_id}")

                    # Auto-select the new project
                    project_result = self.api.get_project(project_id)
                    if project_result.get("success"):
                        self.current_project = project_result.get("data")
                        self.console.print(f"Selected project: {name}")
                else:
                    error_msg = result.get('message') or result.get('detail') or 'Unknown error'
                    self.console.print(f"[ERROR] Failed: {error_msg}")
            except Exception as e:
                self.console.print(f"Error: {e}")

        elif subcommand == "select":
            # Project selection: /project select [number|id]
            try:
                result = self.api.list_projects()

                if not result.get("success"):
                    self.console.print("ERROR: Could not load projects")
                    return

                # Get projects from data wrapper
                data = result.get("data", {})
                projects = data.get("projects", []) if isinstance(data, dict) else []

                if not projects:
                    self.console.print("No projects found. Create one with /project create")
                    return

                # If number/id provided as argument, use it directly
                if len(args) >= 2:
                    choice = args[1]
                else:
                    # Show interactive list
                    self.console.print("\nYour Projects:\n")

                    for i, proj in enumerate(projects, 1):
                        desc = proj.get("description", "")
                        if len(desc) > 40:
                            desc = desc[:37] + "..."
                        status = proj.get("status", "unknown")
                        proj_id = str(proj.get("id", ""))[:8]
                        self.console.print(f"  [{i}] {proj.get('name', 'Unnamed')} ({proj_id}) - {status}")
                        if desc:
                            self.console.print(f"      {desc}")

                    self.console.print()
                    choice = Prompt.ask("Select project by number or enter project ID (or 'back')", default="1")

                    if choice.lower() in ["/back", "back"]:
                        return

                # Parse selection
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(projects):
                        project_id = str(projects[choice_num - 1].get("id"))
                    else:
                        self.console.print("ERROR: Invalid selection")
                        return
                except ValueError:
                    # Not a number, try to match as partial or full UUID
                    project_id = None
                    for proj in projects:
                        if str(proj.get("id")).startswith(choice):
                            project_id = str(proj.get("id"))
                            break
                    if not project_id:
                        project_id = choice

                # Load and select the project
                proj_result = self.api.get_project(project_id)
                if proj_result.get("success"):
                    # Get project data (handle wrapped response)
                    proj_data = proj_result.get("data", {})
                    self.current_project = proj_data
                    self.cli_logger.log_project_select(self.current_project['name'], project_id)
                    self.current_session = None
                    self.console.print(f"\nSelected project: {self.current_project['name']}\n")
                else:
                    self.console.print("ERROR: Project not found")

            except Exception as e:
                self.console.print(f"ERROR: {e}")
                if self.debug:
                    import traceback
                    self.console.print(traceback.format_exc())

        elif subcommand == "info":
            if not self.ensure_project_selected():
                return

            p = self.current_project
            info = f"""
Project Information

Name: {p['name']}
ID: {p['id']}
Description: {p.get('description', 'N/A')}
Phase: {p.get('current_phase', 'N/A')}
Maturity Score: {p.get('maturity_score', 0):.1f}%
Created: {p.get('created_at', 'N/A')}
Updated: {p.get('updated_at', 'N/A')}
"""
            self.console.print(Panel(info, border_style="cyan"))

        elif subcommand == "manage":
            if len(args) < 2:
                self.console.print("Usage: /project manage <number|project_id>")
                return

            project_input = args[1]
            project_id = None

            try:
                # Load all projects
                response = self.api._request("GET", f"/api/v1/projects?skip=0&limit=100")
                if response.status_code != 200:
                    self.console.print("[ERROR] Failed to load projects")
                    return

                result = response.json()
                if not result.get("success"):
                    self.console.print("[ERROR] Failed to load projects")
                    return

                all_projects = result.get("data", {}).get("projects", [])

                # Try to resolve input as number or partial UUID
                try:
                    choice_num = int(project_input)
                    if 1 <= choice_num <= len(all_projects):
                        project_id = str(all_projects[choice_num - 1].get("id"))
                    else:
                        self.console.print(f"[ERROR] Invalid project number")
                        return
                except ValueError:
                    # Try partial or full UUID match
                    for proj in all_projects:
                        if str(proj.get("id")).startswith(project_input):
                            project_id = str(proj.get("id"))
                            break
                    if not project_id:
                        project_id = project_input

                # Get project details
                proj_result = self.api.get_project(project_id)
                if not proj_result.get("success"):
                    self.console.print("[ERROR] Project not found")
                    return

                project = proj_result.get("data")
                status = project.get("status", "unknown")

                # Show project info
                self.console.print(f"\nManage Project")
                self.console.print(f"Name: {project.get('name')}")
                self.console.print(f"Status: {status}")
                self.console.print(f"ID: {project_id}\n")

                # Show context-based actions
                if status == "active":
                    actions = {"1": ("Archive (soft delete)", "archive_project")}
                elif status == "archived":
                    actions = {
                        "1": ("Restore to active", "restore_project"),
                        "2": ("Permanently destroy", "destroy_project")
                    }
                else:
                    self.console.print(f"No actions available for status: {status}")
                    return

                # Show menu
                for key, (label, _) in actions.items():
                    self.console.print(f"  [{key}] {label}")
                self.console.print(f"  [back] Cancel\n")

                choice = Prompt.ask("Choose action", choices=list(actions.keys()) + ["back"], default="back")

                if choice == "back":
                    self.console.print("Cancelled")
                    return

                action_label, action_method = actions[choice]

                # Confirmation
                if action_method == "destroy_project":
                    self.console.print("[red bold][WARNING] WARNING: This will permanently delete the project![/red bold]")
                    self.console.print("This action CANNOT be undone.\n")

                confirm = Prompt.ask(f"[red bold]{action_label} project?[/red bold]" if action_method == "destroy_project" else f"{action_label}?", choices=["y", "n"], default="n")

                if confirm.lower() == "y":
                    api_method = getattr(self.api, action_method)
                    result = api_method(project_id)

                    if result.get("success"):
                        self.console.print(f"[OK] {action_label} successful")
                        if self.current_project and str(self.current_project.get("id")) == str(project_id):
                            self.current_project = None
                            self.current_session = None
                    else:
                        error_msg = result.get('message') or result.get('detail') or 'Unknown error'
                        self.console.print(f"[ERROR] Failed: {error_msg}")
                else:
                    self.console.print("Cancelled")

            except Exception as e:
                self.console.print(f"Error: {e}")


        else:
            self.console.print(f"Unknown subcommand: {subcommand}")

    def cmd_session(self, args: List[str]):
        """Handle /session command"""
        if not self.ensure_authenticated():
            return

        if not args:
            # Show interactive menu
            self.console.print("\nSession Management\n")
            self.console.print("What would you like to do?")
            self.console.print("  [1] Start a new Socratic session")
            self.console.print("  [2] Select an existing session")
            self.console.print("  [3] End current session")
            self.console.print("  [4] List all sessions")
            self.console.print("  [5] Add note to current session")
            self.console.print("  [back] Go back\n")

            if not self.current_project:
                self.console.print("[WARNING] You need to select a project first!")
                self.console.print("Use: /project select\n")
                return

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "back"], default="1")

            if choice == "back":
                return
            elif choice == "1":
                self.cmd_session(["start"])
            elif choice == "2":
                self.cmd_session(["select"])
            elif choice == "3":
                self.cmd_session(["end"])
            elif choice == "4":
                self.cmd_sessions()
            elif choice == "5":
                self.cmd_session(["note"])
            return

        subcommand = args[0]

        if subcommand == "start":
            if not self.ensure_project_selected():
                return

            try:
                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Starting session...", total=None)
                    result = self.api.start_session(self.current_project["id"])

                if result.get("success"):
                    # Extract data from wrapped response
                    data = result.get("data", {})

                    # Handle both response formats: session object or session_id
                    session_data = data.get("session")
                    if not session_data:
                        # Fallback: construct session object from response fields
                        session_data = {
                            "id": data.get("session_id"),
                            "project_id": data.get("project_id"),
                            "status": data.get("status"),
                            "mode": "socratic"
                        }

                    if not session_data or not session_data.get("id"):
                        self.console.print("[ERROR] Error: Invalid session data received")
                        return

                    self.current_session = session_data
                    session_id = self.current_session["id"]
                    # Log the session start
                    self.cli_logger.log_session_start(session_id, "socratic", self.current_project["id"])
                    self.console.print(f"[OK] Session started: {session_id}")
                    self.console.print("\nReady to begin Socratic questioning!")
                    self.console.print(
                        "Just type your thoughts and press Enter to continue the conversation.\n")

                    # Get first question
                    self.get_next_question()
                else:
                    error_msg = result.get('message') or result.get('detail') or 'Unknown error'
                    self.console.print(f"[ERROR] Failed: {error_msg}")
            except Exception as e:
                self.console.print(f"Error: {e}")
                if self.debug:
                    import traceback
                    self.console.print(traceback.format_exc())

        elif subcommand == "select":
            # If no session ID provided, show interactive list
            if len(args) < 2:
                if not self.ensure_project_selected():
                    return

                try:
                    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                                  console=self.console, transient=True) as progress:
                        progress.add_task("Loading sessions...", total=None)
                        result = self.api.list_sessions(self.current_project["id"])

                    # Note: list_sessions returns unwrapped response (not in "data" wrapper like projects)
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

                        self.console.print("\nSessions for project '{}':\n".format(
                            self.current_project.get("name", "Unnamed")))
                        self.console.print(table)
                        self.console.print()

                        # Prompt user to select
                        choice = Prompt.ask(
                            "Select session by number or enter session ID (or 'back')",
                            default="1"
                        )

                        # Check for back command
                        if choice.lower() in ["/back", "back"]:
                            self.console.print("Going back...")
                            return

                        try:
                            choice_num = int(choice)
                            if 1 <= choice_num <= len(sessions):
                                session_id = str(sessions[choice_num - 1].get("id"))
                            else:
                                self.console.print("Invalid selection")
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
                            self.console.print(f"\n[OK] Selected session")
                            self.console.print(f"Status: {self.current_session.get('status')} | Mode: {mode}\n")
                        else:
                            self.console.print(f"[ERROR] Session not found")
                    else:
                        self.console.print("No sessions found. Start one with /session start")
                except Exception as e:
                    self.console.print(f"Error: {e}")
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
                        self.console.print(f"[OK] Selected session")
                        self.console.print(f"Status: {self.current_session.get('status')} | Mode: {mode}")
                    else:
                        self.console.print(f"[ERROR] Session not found")
                except Exception as e:
                    self.console.print(f"Error: {e}")

        elif subcommand == "end":
            if not self.ensure_session_active():
                return

            if Confirm.ask("End current session?"):
                try:
                    session_id = self.current_session["id"]
                    result = self.api.end_session(session_id)
                    if result.get("success"):
                        # Log the session end
                        self.cli_logger.log_session_end(session_id)
                        self.console.print(f"[OK] Session ended")
                        self.console.print(f"Specifications extracted: {result.get('specs_count', 0)}")
                        self.current_session = None
                        self.current_question = None
                    else:
                        self.console.print(f"[ERROR] Failed: {result.get('message')}")
                except Exception as e:
                    self.console.print(f"Error: {e}")

        elif subcommand == "note":
            self.cmd_session_note(args[1:])

        elif subcommand == "bookmark":
            self.cmd_session_bookmark()

        elif subcommand == "branch":
            self.cmd_session_branch(args[1:])

        else:
            self.console.print(f"Unknown subcommand: {subcommand}")

    def cmd_sessions(self):
        """Handle /sessions command"""
        if not self.ensure_authenticated():
            return
        if not self.ensure_project_selected():
            return

        try:
            result = self.api.list_sessions(self.current_project["id"])
            # Note: list_sessions returns unwrapped response (not in "data" wrapper like projects)
            sessions = result.get("sessions", [])

            if not sessions:
                self.console.print("\nNo sessions yet. Start one with /session start")
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
            self.console.print(f"Error: {e}")

    def cmd_history(self):
        """Handle /history command"""
        if not self.ensure_authenticated():
            return
        if not self.ensure_session_active():
            return

        try:
            result = self.api.get_session_history(self.current_session["id"])
            if result.get("success"):
                # Extract from data wrapper
                data = result.get("data", {})
                history = data.get("conversation_history", []) if isinstance(data, dict) else []

                if not history:
                    self.console.print("No conversation history yet")
                    return

                self.console.print("\nConversation History\n")

                for entry in history:
                    timestamp = entry.get("timestamp", "")[:16]

                    if entry.get("question"):
                        self.console.print(f"{timestamp} Socrates:")
                        self.console.print(Panel(entry["question"], border_style="cyan", padding=(0, 2)))

                    if entry.get("answer"):
                        self.console.print(f"{timestamp} You:")
                        self.console.print(Panel(entry["answer"], border_style="green", padding=(0, 2)))

                    self.console.print()
            else:
                self.console.print(f"Failed to load history")
        except Exception as e:
            self.console.print(f"Error: {e}")

    def get_next_question(self):
        """Get next Socratic question"""
        if not self.current_session:
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Generating question...", total=None)
                result = self.api.get_next_question(self.current_session["id"])

            if result.get("success"):
                # Extract from data wrapper
                data = result.get("data", {})
                # Handle both response formats
                question_data = data.get("question") if isinstance(data, dict) else None
                if isinstance(question_data, dict):
                    # If question is an object, extract fields
                    question_text = question_data.get("text") or question_data.get("question")
                    question_id = question_data.get("id") or question_data.get("question_id")
                else:
                    # If question is a string, assume it's the text
                    question_text = data.get("text") or data.get("question") or question_data
                    question_id = data.get("id") or data.get("question_id")

                if not question_text:
                    self.console.print("Error: No question text received")
                    return

                # Store the full question object for later submission
                self.current_question = {
                    "question_id": question_id,
                    "text": question_text,
                    **(data if isinstance(data, dict) else {})  # Include all other fields from data
                }

                self.console.print(f"Socrates:")
                self.console.print(Panel(question_text, border_style="cyan", padding=(1, 2)))
                self.console.print()
            else:
                # Error getting question (result.get('success') is False)
                error_msg = result.get("error") or result.get("detail", "Unknown error")
                self.console.print(f"Failed to get question: {error_msg}")
        except Exception as e:
            self.console.print(f"Error: {e}")
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
            self.console.print("Start a session with /session start to begin Socratic chat")
            return

        if not self.current_question:
            self.console.print("No active question. Getting next question...")
            self.get_next_question()
            return

        try:
            # Log the chat message
            self.cli_logger.log_chat_message(self.current_session["id"], message, "socratic")

            # Submit answer
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
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
                    self.console.print(f"[OK] Extracted {specs_extracted} specification(s)")
                    self.console.print()

                # Get next question
                self.get_next_question()
            else:
                self.console.print(f"Failed to process answer: {result.get('message')}")
        except Exception as e:
            self.console.print(f"Error: {e}")

    def handle_direct_message(self, message: str):
        """Handle direct chat message (non-Socratic)"""
        if not self.ensure_session_active():
            self.console.print("Start a session with /session start to use direct chat")
            return

        try:
            # Log the chat message
            self.cli_logger.log_chat_message(self.current_session["id"], message, "direct")

            # First, ensure session is in direct_chat mode
            if self.chat_mode != "direct_chat":
                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Switching to direct chat mode...", total=None)
                    mode_result = self.api.set_session_mode(
                        self.current_session["id"],
                        "direct_chat"
                    )

                if not mode_result.get("success"):
                    self.console.print(f"Failed to switch modes: {mode_result.get('error', 'Unknown error')}")
                    return

                self.chat_mode = "direct_chat"

            # Send direct chat message
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Thinking...", total=None)
                result = self.api.send_chat_message(self.current_session["id"], message)

            if result.get("success"):
                response_text = result.get("response", "")
                self.console.print(f"\nSocrates:")
                self.console.print(Panel(response_text, border_style="cyan", padding=(1, 2)))
                self.console.print()

                # Show any extracted specs (backend returns count as integer)
                specs_extracted = result.get("specs_extracted", 0)
                if specs_extracted > 0:
                    self.console.print(f"[OK] Extracted {specs_extracted} specification(s)")
                    self.console.print()
            else:
                self.console.print(f"Failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_config(self, args: List[str]):
        """Manage CLI configuration settings"""
        if not args:
            # List all configuration
            self.console.print("\nCurrent Configuration:\n")
            config_data = self.config.data
            if not config_data:
                self.console.print("No custom settings configured")
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
                self.console.print("Usage: /config set <key> <value>")
                return

            key = args[1]
            value = " ".join(args[2:])

            # Basic validation for common keys
            if key == "theme" and value not in ["dark", "light", "colorblind", "monokai"]:
                self.console.print(f"Theme options: dark, light, colorblind, monokai")
                return

            if key == "format" and value not in ["rich", "json", "table", "minimal"]:
                self.console.print(f"Format options: rich, json, table, minimal")
                return

            self.config.set(key, value)
            self.console.print(f"[OK] Set {key} = {value}")

        elif subcommand == "get":
            if len(args) < 2:
                self.console.print("Usage: /config get <key>")
                return

            key = args[1]
            value = self.config.get(key)

            if value is None:
                self.console.print(f"Setting '{key}' not found")
            else:
                self.console.print(f"{key} = {value}")

        elif subcommand == "reset":
            if len(args) > 1 and args[1] == "--all":
                if Confirm.ask("Reset all settings to defaults?"):
                    self.config.clear()
                    self.console.print("[OK] Configuration reset to defaults")
            else:
                self.console.print("Usage: /config reset --all")

        else:
            self.console.print(f"Unknown subcommand: {subcommand}")
            self.console.print("Use: /config [list|set|get|reset]")

    def cmd_logging(self, args: List[str]):
        """Manage centralized logging for CLI and backend"""
        if not args:
            args = ["status"]

        subcommand = args[0].lower()

        if subcommand == "on":
            # Enable both CLI and backend logging
            try:
                # Enable CLI logging
                self.cli_logger.set_enabled(True)
                self.config.set_logging_enabled(True)

                # Enable backend logging
                response = self.api._request(
                    "POST",
                    "/api/v1/admin/logging/action",
                    json={"enabled": True}
                )

                if response.status_code == 200:
                    self.console.print("[OK] CLI logging enabled")
                    self.console.print("[OK] Backend logging enabled")
                else:
                    self.console.print("[WARN] Backend logging might not be enabled")
            except Exception as e:
                self.console.print(f"Error enabling logging: {str(e)}")

        elif subcommand == "off":
            # Disable both CLI and backend logging
            try:
                # Disable CLI logging
                self.cli_logger.set_enabled(False)
                self.config.set_logging_enabled(False)

                # Disable backend logging
                response = self.api._request(
                    "POST",
                    "/api/v1/admin/logging/action",
                    json={"enabled": False}
                )

                if response.status_code == 200:
                    self.console.print("[OK] CLI logging disabled")
                    self.console.print("[OK] Backend logging disabled")
                else:
                    self.console.print("[WARN] Backend logging might not be disabled")
            except Exception as e:
                self.console.print(f"Error disabling logging: {str(e)}")

        elif subcommand == "status":
            # Show logging status
            try:
                cli_enabled = self.cli_logger.is_enabled()
                cli_status = "ENABLED" if cli_enabled else "DISABLED"

                # Get backend status
                response = self.api._request("GET", "/api/v1/admin/logging/action")
                if response.status_code == 200:
                    backend_data = response.json()
                    backend_enabled = backend_data.get("enabled", False)
                    backend_status = "ENABLED" if backend_enabled else "DISABLED"
                else:
                    backend_status = "UNKNOWN"

                self.console.print("\nLogging Status:")
                self.console.print(f"  CLI Logging:     {cli_status}")
                self.console.print(f"  Backend Logging: {backend_status}")
                self.console.print(f"  Log File:        {self.cli_logger.get_log_file_path()}")

                # Show recent logs if enabled
                if cli_enabled:
                    recent = self.cli_logger.get_recent_logs(3)
                    if recent:
                        self.console.print("\nRecent logs:")
                        for line in recent:
                            self.console.print(f"  {line}")
                self.console.print()

            except Exception as e:
                self.console.print(f"Error getting logging status: {str(e)}")

        elif subcommand == "clear":
            # Clear log file
            try:
                if self.cli_logger.clear_logs():
                    self.console.print("[OK] Log file cleared")
                else:
                    self.console.print("Failed to clear log file")
            except Exception as e:
                self.console.print(f"Error clearing logs: {str(e)}")

        else:
            self.console.print("Usage: /logging [on|off|status|clear]")

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
            self.console.print("\nAvailable Themes:\n")
            current = self.config.get("theme", "dark")

            for theme_name, description in themes.items():
                marker = "→ " if theme_name == current else "  "
                self.console.print(f"{marker}{theme_name} - {description}")

            self.console.print(f"\nCurrent theme: {current}")
            self.console.print("Use: /theme <name> to change\n")
            return

        theme_name = args[0].lower()

        if theme_name not in themes:
            self.console.print(f"Unknown theme: {theme_name}")
            self.console.print(f"Available: {', '.join(themes.keys())}")
            return

        self.config.set("theme", theme_name)
        self.console.print(f"[OK] Theme changed to: {theme_name}")
        self.console.print(f"{themes[theme_name]}")

        # Note: Full theme implementation would require reloading console colors
        self.console.print("(Theme will apply on next session)")

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
            self.console.print("\nAvailable Formats:\n")
            current = self.config.get("format", "rich")

            for fmt_name, description in formats.items():
                marker = "→ " if fmt_name == current else "  "
                self.console.print(f"{marker}{fmt_name} - {description}")

            self.console.print(f"\nCurrent format: {current}")
            self.console.print("Use: /format <name> to change\n")
            return

        format_name = args[0].lower()

        if format_name not in formats:
            self.console.print(f"Unknown format: {format_name}")
            self.console.print(f"Available: {', '.join(formats.keys())}")
            return

        self.config.set("format", format_name)
        self.console.print(f"[OK] Format changed to: {format_name}")
        self.console.print(f"{formats[format_name]}")

    def cmd_save(self, args: List[str]):
        """Save current session or project to file"""
        if not self.current_session and not self.current_project:
            self.console.print("No active session or project to save")
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

            self.console.print(f"[OK] Saved to: {output_path}")
            self.console.print(f"File size: {output_path.stat().st_size} bytes")

        except Exception as e:
            self.console.print(f"Error saving file: {e}")
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
            self.console.print("Usage: /export <format> [<project_id>]")
            self.console.print("Formats: markdown, json, csv, pdf")
            return

        format_type = args[0].lower()
        project_id = args[1] if len(args) > 1 else (
            self.current_project["id"] if self.current_project else None
        )

        if not project_id:
            self.console.print("No project selected. Use /project select or specify project_id")
            return

        if format_type not in ["markdown", "json", "csv", "pdf"]:
            self.console.print(f"Unknown format: {format_type}")
            self.console.print("Available: markdown, json, csv, pdf")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
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
                self.console.print(f"[OK] Export successful")
                self.console.print(f"Format: {format_type}")
                self.console.print(f"Filename: {filename}")

                # Display content if available (for text formats)
                if "content" in result and format_type in ["markdown", "json"]:
                    self.console.print("\nPreview:")
                    content_preview = result["content"][:200] + "..." if len(result.get("content", "")) > 200 else result["content"]
                    self.console.print(content_preview)
            else:
                error = result.get("error", "Unknown error")
                self.console.print(f"[ERROR] Export failed: {error}")

        except Exception as e:
            self.console.print(f"Error: {e}")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())

    def cmd_session_note(self, args: List[str]):
        """Add a note to the current session"""
        if not self.ensure_session_active():
            return

        if not args:
            self.console.print("Usage: /session note <your note text>")
            return

        note_text = " ".join(args)

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Adding note...", total=None)
                result = self.api.add_session_note(self.current_session["id"], note_text)

            if result.get("success"):
                self.console.print(f"[OK] Note added")
                self.console.print(f"Note: {note_text}")
            else:
                error = result.get("error", "Failed to add note")
                self.console.print(f"[WARNING] {error}")
                self.console.print("Note saved locally: " + note_text + "")

        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_session_bookmark(self):
        """Create a bookmark at current point in session"""
        if not self.ensure_session_active():
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating bookmark...", total=None)
                result = self.api.bookmark_session(self.current_session["id"])

            if result.get("success"):
                self.console.print(f"[OK] Bookmark created")
                bookmark_id = result.get("bookmark_id", "")
                if bookmark_id:
                    self.console.print(f"ID: {bookmark_id}")
            else:
                self.console.print(f"[WARNING] Bookmark not saved (backend unavailable)")
                self.console.print("[OK] Mark saved locally")

        except Exception as e:
            self.console.print(f"[OK] Mark created at current position")

    def cmd_session_branch(self, args: List[str]):
        """Create an alternative branch from current session"""
        if not self.ensure_session_active():
            return

        branch_name = args[0] if args else None

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating branch...", total=None)
                result = self.api.branch_session(self.current_session["id"], branch_name)

            if result.get("success"):
                self.console.print(f"[OK] Branch created")
                new_session_id = result.get("session_id", "")
                if new_session_id:
                    self.console.print(f"New session ID: {new_session_id}")
                    self.console.print("You can resume this branch with: /session select " + new_session_id + "")
            else:
                self.console.print(f"[WARNING] {result.get('error', 'Could not create branch')}")

        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_stats(self, args: List[str]):
        """Show statistics for session or project"""
        if not args:
            # Show current session stats if active
            if self.current_session:
                try:
                    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                                  console=self.console, transient=True) as progress:
                        progress.add_task("Loading stats...", total=None)
                        result = self.api.get_session_stats(self.current_session["id"])

                    if result.get("success"):
                        self.console.print("\nSession Statistics\n")
                        stats = result.get("stats", {})

                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("Metric", style="bold")
                        table.add_column("Value", justify="right")

                        for key, value in stats.items():
                            table.add_row(str(key).replace("_", " ").title(), str(value))

                        self.console.print(table)
                        self.console.print()
                    else:
                        self.console.print("Stats not available")

                except Exception as e:
                    self.console.print(f"Error loading stats: {e}")
            else:
                self.console.print("No active session. Start a session first with /session start")
            return

        subcommand = args[0].lower()
        if subcommand == "session" and len(args) > 1:
            session_id = args[1]
            # Load specific session stats
            self.console.print(f"Stats for session {session_id}")
        else:
            self.console.print("Usage: /stats [session <session_id>]")

    def cmd_template(self, args: List[str]):
        """Manage project templates"""
        if not args:
            # List available templates
            try:
                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Loading templates...", total=None)
                    result = self.api.list_templates()

                if result.get("success"):
                    templates = result.get("templates", [])
                    self.console.print("\nAvailable Templates\n")

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
                        self.console.print("\nUse: /template info <name> for details\n")
                    else:
                        self.console.print("No templates available")

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
                    self.console.print(f"\n{tmpl.get('name', template_name)}")
                    self.console.print(f"\n{tmpl.get('description', 'No description')}\n")
                else:
                    self.console.print(f"Template not found: {template_name}")
            except Exception:
                self.console.print(f"Template not found: {template_name}")

        else:
            self.console.print("Usage: /template [list|info <name>]")

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

        self.console.print("\nAvailable Templates\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Description")

        for name, desc in templates:
            table.add_row(name, desc)

        self.console.print(table)
        self.console.print("\nUse: /template info <name> for details")
        self.console.print("Use: /project create --template <name> to create from template\n")

    # ==================== PRIORITY 3 COMMANDS ====================

    def cmd_search(self, args: List[str]):
        """Search across projects, specifications, and questions"""
        if not self.ensure_authenticated():
            return

        if not args:
            self.console.print("Usage: /search <query> [resource_type] [category]")
            self.console.print("Resource types: projects, specifications, questions")
            return

        query = args[0]
        resource_type = args[1].lower() if len(args) > 1 else None
        category = args[2].lower() if len(args) > 2 else None

        # Validate resource type
        valid_types = ["projects", "specifications", "questions"]
        if resource_type and resource_type not in valid_types:
            self.console.print(f"Invalid resource type: {resource_type}")
            self.console.print(f"Valid types: {', '.join(valid_types)}")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Searching...", total=None)
                result = self.api.search(query, resource_type=resource_type, category=category)

            if result.get("success"):
                self._display_search_results(result)
            else:
                error = result.get("error", "Search failed")
                self.console.print(f"[ERROR] Search failed: {error}")

        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_status(self, args: List[str]):
        """Display current project and session status"""
        if not self.ensure_authenticated():
            return

        self.console.print()

        # Project Status
        if self.current_project:
            self._display_project_status(self.current_project)
        else:
            self.console.print("No project selected. Use /project select <id> or /project create")

        self.console.print()

        # Session Status
        if self.current_session:
            self._display_session_status(self.current_session)
        else:
            self.console.print("No active session. Use /session start to begin")

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
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Filtering...", total=None)

                # Search for specifications
                if filter_type in ["spec", "specification", "all"]:
                    result = self.api.search("", resource_type="specifications", category=category)
                    if result.get("success"):
                        specs = result.get("results", [])
                        self.console.print(f"\nSpecifications ({len(specs)} found)\n")
                        self._display_filtered_results(specs, is_spec=True)

                # Search for questions
                if filter_type in ["question", "questions", "all"]:
                    result = self.api.search("", resource_type="questions", category=category)
                    if result.get("success"):
                        questions = result.get("results", [])
                        self.console.print(f"\nQuestions ({len(questions)} found)\n")
                        self._display_filtered_results(questions, is_spec=False)

        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_insights(self, args: List[str]):
        """Get insights for project (gaps, risks, opportunities)"""
        if not self.ensure_authenticated():
            return

        project_id = args[0] if args else (
            self.current_project["id"] if self.current_project else None
        )

        if not project_id:
            self.console.print("Usage: /insights [project_id]")
            self.console.print("If no project_id provided, uses currently selected project")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Analyzing project...", total=None)
                result = self.api.get_insights(project_id)

            if result.get("success"):
                self._display_insights(result)
            else:
                error = result.get("error", "Failed to get insights")
                self.console.print(f"[ERROR] {error}")

        except Exception as e:
            self.console.print(f"Error: {e}")

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
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Loading session...", total=None)
                result = self.api.get_session(session_id)

            if result.get("success"):
                session = result.get("session")
                self.current_session = session
                self.console.print(f"[OK] Session resumed: {session_id}")
                self._display_session_status(session)
                self.console.print("\nType your next response to continue the session\n")
            else:
                error = result.get("error", "Session not found")
                self.console.print(f"[ERROR] {error}")
                self.console.print("Use /resume (without args) to see recent sessions")

        except Exception as e:
            self.console.print(f"Error: {e}")

    def cmd_wizard(self, args: List[str]):
        """Interactive project setup wizard"""
        if not self.ensure_authenticated():
            return

        self.console.print("\n✨ Project Setup Wizard\n")
        self.console.print("Let's create a new project with templates!")
        self.console.print("Tip: Type 'back' at any step to go back\n")

        # Step 1: Get project name
        while True:
            project_name = self.prompt_with_back("Project name")
            if project_name is None:
                self.console.print("Wizard cancelled")
                return
            if project_name:
                break
            self.console.print("Project name is required")

        # Step 2: Project description
        project_description = self.prompt_with_back("Project description (optional)", default="")
        if project_description is None:
            self.console.print("Going back...")
            self.cmd_wizard([])
            return

        project_description = project_description or ""

        # Step 2: Select template
        template_id = self._wizard_select_template()
        if not template_id:
            self.console.print("Template selection cancelled")
            return

        # Step 3: Create project
        try:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating project...", total=None)
                create_result = self.api.create_project(project_name, project_description)

            if not create_result.get("success"):
                self.console.print(f"[ERROR] Project creation failed: {create_result.get('error')}")
                return

            project = create_result.get("project")
            project_id = project["id"]
            self.current_project = project

            self.console.print(f"[OK] Project created: {project_name}")

            # Step 4: Apply template
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Applying template...", total=None)
                template_result = self.api.apply_template(template_id, project_id)

            if template_result.get("success"):
                specs_count = template_result.get("specs_created", 0)
                self.console.print(f"[OK] Template applied: {specs_count} specifications created")
                self._display_project_created(project, template_id)
            else:
                self.console.print(f"[WARNING] Template application failed: {template_result.get('error')}")
                self._display_project_created(project, None)

        except Exception as e:
            self.console.print(f"Error: {e}")

    # ==================== PRIORITY 3 HELPERS ====================

    def _display_insights(self, result: Dict[str, Any]):
        """Display project insights"""
        project_name = result.get("project_name", "Unknown")
        insights = result.get("insights", [])
        summary = result.get("summary", {})

        self.console.print(f"\nProject Insights: {project_name}\n")

        if not insights:
            self.console.print("No insights to display\n")
            return

        # Group insights by type
        gaps = [i for i in insights if i.get("type") == "gap"]
        risks = [i for i in insights if i.get("type") == "risk"]
        opportunities = [i for i in insights if i.get("type") == "opportunity"]

        # Display Gaps
        if gaps:
            self.console.print("[WARNING] GAPS")
            for gap in gaps:
                severity = gap.get("severity", "medium")
                severity_icon = "🔴" if severity == "high" else "🟡"
                self.console.print(f"  {severity_icon} {gap.get('title')}")
                self.console.print(f"     {gap.get('description')}")
            self.console.print()

        # Display Risks
        if risks:
            self.console.print("⚡ RISKS")
            for risk in risks:
                self.console.print(f"  🟡 {risk.get('title')}")
                self.console.print(f"     {risk.get('description')}")
            self.console.print()

        # Display Opportunities
        if opportunities:
            self.console.print("✨ OPPORTUNITIES")
            for opp in opportunities:
                self.console.print(f"  🟢 {opp.get('title')}")
                self.console.print(f"     {opp.get('description')}")
            self.console.print()

        # Summary
        self.console.print("Summary")
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

        self.console.print(f"\nSearch Results for: {query}\n")

        if not results:
            self.console.print("No results found\n")
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
        self.console.print(f"\nFound {resource_counts.get('projects', 0)} projects, "
                          f"{resource_counts.get('specifications', 0)} specifications, "
                          f"{resource_counts.get('questions', 0)} questions\n")

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
        self.console.print("📋 Project Status")
        self.console.print(f"  Name: {project.get('name', 'Unknown')}")
        self.console.print(f"  ID: {project.get('id', 'Unknown')[:8]}")
        self.console.print(f"  Phase: {project.get('current_phase', 'phase_1')}")
        self.console.print(f"  Status: {project.get('status', 'active')}")
        self.console.print(f"  Maturity: {project.get('maturity_score', 0):.0f}%")

    def _display_session_status(self, session: Dict[str, Any]):
        """Display session status"""
        self.console.print(" Session Status")
        self.console.print(f"  ID: {session.get('id', 'Unknown')[:8]}")
        self.console.print(f"  Mode: {session.get('mode', 'socratic')}")
        self.console.print(f"  Status: {session.get('status', 'active')}")
        started = session.get('started_at', 'N/A')
        self.console.print(f"  Started: {started}")

    def _display_next_steps(self):
        """Display suggested next steps"""
        self.console.print("💡 Next Steps")

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
        self.console.print(f"\n[OK] Project created successfully!")
        self.console.print(f"Name: {project.get('name', 'Unknown')}")
        self.console.print(f"ID: {project.get('id', 'Unknown')[:8]}")
        if template_id:
            self.console.print(f"Template: {template_id}")
        self.console.print("\nYou can now:")
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

        self.console.print("\nChoose a template:\n")
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
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Loading recent sessions...", total=None)
                result = self.api.list_recent_sessions()

            if result.get("success"):
                sessions = result.get("sessions", [])
                self.console.print(f"\nRecent Sessions\n")

                if not sessions:
                    self.console.print("No recent sessions\n")
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
                self.console.print(f"\nUse: /resume <session_id> to resume\n")
            else:
                self.console.print("Could not load recent sessions\n")

        except Exception as e:
            self.console.print(f"Error loading sessions: {e}\n")

    def handle_command(self, user_input: str):
        """Parse and handle command"""
        parts = user_input.strip().split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        # Handle system commands locally
        if command in ["/help", "/h"]:
            self.print_help()
            return

        elif command in ["/exit", "/quit", "/q"]:
            if self.current_session:
                if Confirm.ask("You have an active session. End it before exiting?"):
                    self.cmd_session(["end"])
            self.running = False
            self.console.print("\n..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..\n")
            # Shutdown is called in run()'s finally block, but set running=False to exit the loop
            return

        elif command == "/clear":
            self.console.clear()
            self.print_banner()
            return

        elif command == "/back":
            self.cmd_back()
            return

        elif command == "/debug":
            self.debug = not self.debug
            self.console.print(f"Debug mode: {'ON' if self.debug else 'OFF'}")
            return

        # Try to route through modular registry first
        # Strip the leading slash to get command name
        command_name = command.lstrip('/')

        if self.registry and self.registry.command_exists(command_name):
            # Update config dict before routing
            self.registry.config = self._get_config_dict()
            if self.registry.route_command(command_name, args):
                # Command was handled successfully
                return

        # Fall back to legacy command methods for backwards compatibility
        if command == "/register":
            self.cmd_register()

        elif command == "/login":
            self.cmd_login()

        elif command == "/logout":
            self.cmd_logout()

        elif command == "/whoami":
            self.cmd_whoami()

        elif command == "/account":
            self.cmd_account(args)

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
                self.console.print("Start a session first with /session start")
                return

            try:
                # Map CLI mode names to backend mode names
                cli_mode_map = {"socratic": "socratic", "direct": "direct_chat"}
                backend_mode_map = {"socratic": "socratic", "direct_chat": "direct"}

                if args:
                    mode = args[0].lower()
                    if mode not in cli_mode_map:
                        self.console.print("Invalid mode. Use: socratic or direct")
                        return

                    backend_mode = cli_mode_map[mode]
                else:
                    # Toggle mode
                    new_backend_mode = "direct_chat" if self.chat_mode == "socratic" else "socratic"
                    mode = backend_mode_map[new_backend_mode]
                    backend_mode = new_backend_mode

                # Switch mode on backend
                with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                              console=self.console, transient=True) as progress:
                    progress.add_task("Switching mode...", total=None)
                    result = self.api.set_session_mode(
                        self.current_session["id"],
                        backend_mode
                    )

                if result.get("success"):
                    self.chat_mode = mode
                    mode_emoji = "" if mode == "socratic" else ""
                    self.console.print(f"[OK] Switched to {mode} mode {mode_emoji}")

                    if mode == "socratic":
                        self.console.print("Socratic mode: Thoughtful questioning to extract specifications")
                    else:
                        self.console.print("Direct mode: Direct conversation with AI assistant")
                else:
                    self.console.print(f"Failed to switch modes: {result.get('error', 'Unknown error')}")
            except Exception as e:
                self.console.print(f"Error: {e}")

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

        elif command == "/logging":
            self.cmd_logging(args)

        else:
            self.console.print(f"Unknown command: {command}")
            self.console.print("Type /help for available commands")

    def run(self):
        """Main CLI loop"""
        # Start backend server
        self._start_server()

        self.print_banner()

        # Check if user is logged in
        if self.config.get("access_token"):
            email = self.config.get("user_email", "User")
            self.console.print(f"Welcome back, {email}!\n")
            self.api.set_token(self.config.get("access_token"))
            # Also set refresh token if available
            refresh_token = self.config.get("refresh_token")
            if refresh_token:
                self.api.set_refresh_token(refresh_token)

            # Restore active project from config
            saved_project = self.config.get("current_project")
            if saved_project:
                self.current_project = saved_project
                self.console.print(f"Restored project: {saved_project.get('name')}")

            # Restore active session from config
            saved_session = self.config.get("current_session")
            if saved_session:
                self.current_session = saved_session
                self.console.print(f"Restored session: {saved_session.get('id', 'unknown')[:8]}...")

            self.console.print()
        else:
            self.console.print("Please /login or /register to get started\n")

        # Main loop
        try:
            while self.running:
                try:
                    # Build prompt
                    prompt_parts = []
                    if self.current_project:
                        prompt_parts.append(f"{self.current_project['name'][:20]}")
                    if self.current_session:
                        prompt_parts.append(f"session")

                    # Add mode indicator
                    mode_emoji = "" if self.chat_mode == "socratic" else ""
                    prompt_parts.append(f"{mode_emoji}")

                    prompt_text = " ".join(prompt_parts) if prompt_parts else f"socrates {mode_emoji}"

                    # Get user input
                    user_input = self.get_prompt_input(f"{prompt_text} > ")

                    if not user_input:
                        continue

                    # Handle command or chat message
                    if user_input.startswith('/'):
                        self.handle_command(user_input)
                    else:
                        self.handle_chat_message(user_input)

                except KeyboardInterrupt:
                    self.console.print("\nUse /exit to quit")
                    continue

                except EOFError:
                    break

                except Exception as e:
                    self.console.print(f"Error: {e}")
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

# cd backend
#   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#   This will start the backend server on http://localhost:8000 with hot-reload enabled (automatically reloads
#   when you save code changes).
#
#   To stop it, press Ctrl+C.
