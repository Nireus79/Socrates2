#!/usr/bin/env python3
"""
Socrates CLI - Interactive Command-Line Interface for Socrates2
A Claude Code-style interface for specification gathering and project development.

Usage:
    python Socrates.py [--api-url URL] [--debug]
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Check for required packages
try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("\nPlease install CLI dependencies:")
    print("    pip install -r cli-requirements.txt")
    sys.exit(1)


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

    def set_token(self, token: str):
        """Set authentication token"""
        self.access_token = token

    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('headers', self._headers())

        try:
            response = requests.request(method, url, **kwargs)
            return response
        except requests.exceptions.ConnectionError:
            self.console.print("[red]Error: Cannot connect to Socrates backend[/red]")
            self.console.print(f"[yellow]Make sure the server is running at {self.base_url}[/yellow]")
            raise
        except Exception as e:
            self.console.print(f"[red]Request error: {e}[/red]")
            raise

    def register(self, email: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        response = self._request("POST", "/api/v1/auth/register", json={
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
        response = self._request("POST", f"/api/v1/projects/{project_id}/sessions")
        return response.json()

    def list_sessions(self, project_id: str) -> Dict[str, Any]:
        """List project sessions"""
        response = self._request("GET", f"/api/v1/projects/{project_id}/sessions")
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

    def direct_chat(self, project_id: str, message: str) -> Dict[str, Any]:
        """Send direct chat message (non-Socratic)"""
        response = self._request("POST", f"/api/v1/chat/direct", json={
            "project_id": project_id,
            "message": message
        })
        return response.json()


class SocratesCLI:
    """Main CLI application"""

    def __init__(self, api_url: str, debug: bool = False):
        self.console = Console()
        self.api = SocratesAPI(api_url, self.console)
        self.config = SocratesConfig()
        self.debug = debug
        self.running = True
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_session: Optional[Dict[str, Any]] = None
        self.current_question: Optional[Dict[str, Any]] = None
        self.chat_mode: str = "socratic"  # "socratic" or "direct"

        # Command completer
        self.commands = [
            "/help", "/exit", "/quit",
            "/register", "/login", "/logout", "/whoami",
            "/projects", "/project", "/sessions", "/session",
            "/history", "/clear", "/debug", "/mode", "/chat",
            "/config", "/theme", "/format", "/save"
        ]
        self.completer = WordCompleter(self.commands, ignore_case=True)

        # Prompt session with history
        self.prompt_session = PromptSession(
            history=FileHistory(str(self.config.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer
        )

    def print_banner(self):
        """Print welcome banner"""
        banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]                    [bold white]SOCRATES CLI v1.0[/bold white]                      [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]          [italic]AI-Powered Specification Gathering[/italic]             [bold cyan]║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════════════╝[/bold cyan]

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

[bold yellow]System:[/bold yellow]
  /help                  Show this help message
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

    def cmd_register(self):
        """Handle /register command"""
        self.console.print("\n[bold cyan]Register New Account[/bold cyan]\n")

        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)
        password_confirm = Prompt.ask("Confirm password", password=True)

        if password != password_confirm:
            self.console.print("[red]Passwords do not match![/red]")
            return

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Creating account...", total=None)
                result = self.api.register(email, password)

            # Backend returns user_id on success (no "success" field)
            if result.get("user_id"):
                self.console.print(f"[green]✓ Account created successfully![/green]")
                self.console.print(f"[dim]User ID: {result.get('user_id')}[/dim]")
                self.console.print(f"[dim]Email: {result.get('email')}[/dim]")
                self.console.print("\n[yellow]Please login with /login[/yellow]")
            else:
                self.console.print(f"[red]✗ Registration failed: {result.get('message', 'Unknown error')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def cmd_login(self):
        """Handle /login command"""
        self.console.print("\n[bold cyan]Login[/bold cyan]\n")

        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)

        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Logging in...", total=None)
                result = self.api.login(email, password)

            if result.get("access_token"):
                self.config.set("access_token", result["access_token"])
                self.config.set("user_email", email)
                self.api.set_token(result["access_token"])
                self.console.print(f"[green]✓ Logged in successfully as {email}[/green]")
            else:
                self.console.print(f"[red]✗ Login failed: {result.get('message', 'Invalid credentials')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

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
            name = Prompt.ask("Project name")
            description = Prompt.ask("Description (optional)", default="")

            try:
                result = self.api.create_project(name, description)
                if result.get("success"):
                    project_id = result.get("project_id")
                    self.console.print(f"[green]✓ Project created: {project_id}[/green]")

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
            if len(args) < 2:
                self.console.print("[yellow]Usage: /project select <project_id>[/yellow]")
                return

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
            self.console.print("[yellow]Usage: /session <start|end>[/yellow]")
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
                    self.current_session = result.get("session")
                    session_id = self.current_session["id"]
                    self.console.print(f"[green]✓ Session started: {session_id}[/green]")
                    self.console.print("\n[cyan]Ready to begin Socratic questioning![/cyan]")
                    self.console.print(
                        "[dim]Just type your thoughts and press Enter to continue the conversation.[/dim]\n")

                    # Get first question
                    self.get_next_question()
                else:
                    self.console.print(f"[red]✗ Failed: {result.get('message')}[/red]")
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
                self.current_question = result
                question_text = result.get("question")
                question_id = result.get("question_id")

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
                specs_extracted = result.get("specs_extracted", [])

                if specs_extracted:
                    self.console.print(f"[green]✓ Extracted {len(specs_extracted)} specification(s):[/green]")
                    for spec in specs_extracted:
                        self.console.print(f"  • [cyan]{spec}[/cyan]")
                    self.console.print()

                # Get next question
                self.get_next_question()
            else:
                self.console.print(f"[red]Failed to process answer: {result.get('message')}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def handle_direct_message(self, message: str):
        """Handle direct chat message (non-Socratic)"""
        if not self.ensure_project_selected():
            self.console.print("[yellow]Select a project first with /project select or /project create[/yellow]")
            return

        try:
            # Send direct chat message
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          console=self.console, transient=True) as progress:
                progress.add_task("Thinking...", total=None)
                result = self.api.direct_chat(self.current_project["id"], message)

            if result.get("success"):
                response_text = result.get("response", "")
                self.console.print(f"\n[bold cyan]Socrates:[/bold cyan]")
                self.console.print(Panel(response_text, border_style="cyan", padding=(1, 2)))
                self.console.print()

                # Show any extracted specs
                specs_extracted = result.get("specs_extracted", [])
                if specs_extracted:
                    self.console.print(f"[green]✓ Extracted {len(specs_extracted)} specification(s):[/green]")
                    for spec in specs_extracted:
                        self.console.print(f"  • [cyan]{spec}[/cyan]")
                    self.console.print()
            else:
                self.console.print(f"[red]Failed: {result.get('message', 'Unknown error')}[/red]")
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
            self.console.print("\n[cyan]Goodbye! Keep building great things! 🚀[/cyan]\n")

        elif command == "/clear":
            self.console.clear()
            self.print_banner()

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
            if args:
                mode = args[0].lower()
                if mode in ["socratic", "direct"]:
                    self.chat_mode = mode
                    mode_emoji = "🤔" if mode == "socratic" else "💬"
                    self.console.print(f"[green]✓ Switched to {mode} mode {mode_emoji}[/green]")
                else:
                    self.console.print("[red]Invalid mode. Use: socratic or direct[/red]")
            else:
                # Toggle mode
                self.chat_mode = "direct" if self.chat_mode == "socratic" else "socratic"
                mode_emoji = "🤔" if self.chat_mode == "socratic" else "💬"
                self.console.print(f"[green]✓ Switched to {self.chat_mode} mode {mode_emoji}[/green]")

                if self.chat_mode == "socratic":
                    self.console.print("[dim]Socratic mode: Thoughtful questioning to extract specifications[/dim]")
                else:
                    self.console.print("[dim]Direct mode: Direct conversation with AI assistant[/dim]")

        elif command == "/config":
            self.cmd_config(args)

        elif command == "/theme":
            self.cmd_theme(args)

        elif command == "/format":
            self.cmd_format(args)

        elif command == "/save":
            self.cmd_save(args)

        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("[yellow]Type /help for available commands[/yellow]")

    def run(self):
        """Main CLI loop"""
        self.print_banner()

        # Check if user is logged in
        if self.config.get("access_token"):
            email = self.config.get("user_email", "User")
            self.console.print(f"[green]Welcome back, {email}![/green]\n")
            self.api.set_token(self.config.get("access_token"))
        else:
            self.console.print("[yellow]Please /login or /register to get started[/yellow]\n")

        # Main loop
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


def main():
    """Main entry point"""
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

    args = parser.parse_args()

    cli = SocratesCLI(api_url=args.api_url, debug=args.debug)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
