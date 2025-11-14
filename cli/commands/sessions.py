"""
Session management command module.

Handles session-related operations (domain-aware, Socratic questioning):
- /session start - Start new Socratic session
- /session select - Select existing session to resume
- /session list - List all sessions
- /session end - End current session
- /session info - Show session details
"""

from typing import Any, Dict, List
from rich.prompt import Prompt

from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class SessionCommandHandler(CommandHandler):
    """Handler for session management commands"""

    command_name = "session"
    description = "Session management: start, select, end, manage"
    help_text = """
[bold cyan]Session Commands:[/bold cyan]

  [yellow]/session start[/yellow]       Start new Socratic session
  [yellow]/session list[/yellow]       List all project sessions
  [yellow]/session select <id>[/yellow] Select session to resume
  [yellow]/session end[/yellow]        End current session
  [yellow]/session info[/yellow]       Show session details

[bold cyan]Session Features:[/bold cyan]
  Socratic Mode: AI asks thoughtful questions to extract specifications
  Direct Mode: Direct conversation with AI assistant
  Multi-Domain: Sessions adapt to project domain

[bold]Examples:[/bold]
  /session start                       # Start new session
  /session list                        # Show all sessions
  /session select 1                    # Resume first session
  /session end                         # End current session
"""

    def handle(self, args: List[str]) -> None:
        """Route session commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "start":
            self.start()
        elif subcommand == "list":
            self.list()
        elif subcommand == "select":
            self.select(args[1:])
        elif subcommand == "end":
            self.end()
        elif subcommand == "info":
            self.info()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.show_help()

    def start(self) -> None:
        """Start new Socratic session"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Start New Session[/bold cyan]\n")

        try:
            # Determine domain from project
            domain = self.get_current_domain()
            self.console.print(f"[dim]Project domain: {domain}[/dim]\n")

            # Ask for session mode
            mode = prompts.prompt_choice(
                self.console,
                "Session mode",
                ["socratic", "direct"],
                default="socratic"
            )

            # Optional: Get initial topic
            topic = prompts.prompt_text(
                self.console,
                "Initial topic or question (optional)",
                default=""
            )

            # Create session via API
            self.console.print("Starting session...")

            result = self.api.start_session(
                project_id=project.get("id")
            )

            if result.get("success"):
                session = result.get("data")
                if not isinstance(session, dict):
                    session = {}

                # Store mode preference for this session
                session["mode"] = mode
                session["domain"] = domain

                self.config["current_session"] = session
                session_id = session.get("session_id") or session.get("id")

                self.print_success("Session started!")
                self.console.print(f"Session ID: {session_id}")
                self.console.print(f"\nMode: {mode}")

                if mode == "socratic":
                    self.console.print("Socratic mode: I will ask thoughtful questions")
                else:
                    self.console.print("Direct mode: Ask me anything")

                self.console.print(f"\nType your message or /session end to finish")

            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Failed to start session: {error}")

        except KeyboardInterrupt:
            self.console.print("Session creation cancelled")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def list(self) -> None:
        """List all sessions for current project"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading sessions...[/cyan]")

        try:
            result = self.api.get_sessions(project.get("id"))

            if not result.get("success"):
                error = result.get("error") or "Failed to load sessions"
                self.print_error(error)
                return

            sessions = result.get("data", {}).get("sessions", [])

            if not sessions:
                self.console.print("[yellow]No sessions yet[/yellow]")
                self.console.print("[yellow]Use /session start to create one[/yellow]")
                return

            # Format and display sessions
            table = table_formatter.format_session_table(sessions)
            self.console.print(table)

            self.console.print(f"\n[cyan]Total sessions: {len(sessions)}[/cyan]")

        except Exception as e:
            self.print_error(f"Error loading sessions: {e}")

    def select(self, args: List[str]) -> None:
        """Select a session to resume"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /session select <number|session_id>[/yellow]")
            return

        self.console.print("[cyan]Loading sessions...[/cyan]")

        try:
            result = self.api.get_sessions(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load sessions")
                return

            sessions = result.get("data", {}).get("sessions", [])

            if not sessions:
                self.console.print("[yellow]No sessions available[/yellow]")
                return

            # Try to parse input as number or UUID
            user_input = args[0]

            try:
                # Try as number
                num = int(user_input)
                if 1 <= num <= len(sessions):
                    selected_session = sessions[num - 1]
                else:
                    self.print_error(f"Invalid session number (1-{len(sessions)})")
                    return
            except ValueError:
                # Try as partial or full UUID
                selected_session = None
                for sess in sessions:
                    if str(sess.get("id")).startswith(user_input):
                        selected_session = sess
                        break

                if not selected_session:
                    self.print_error(f"Session not found: {user_input}")
                    return

            # Select the session
            self.config["current_session"] = selected_session
            session_id = selected_session.get("id")
            mode = selected_session.get("mode", "socratic")

            self.print_success(f"Selected session")

            mode_emoji = "🤔" if mode == "socratic" else "💬"
            self.console.print(f"[dim]Mode: {mode} {mode_emoji}[/dim]")
            self.console.print(f"[dim]Messages: {selected_session.get('message_count', 0)}[/dim]")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def end(self) -> None:
        """End current session"""
        session = self.config.get("current_session")
        if not session:
            self.print_warning("No active session")
            return

        if not prompts.prompt_confirm(
            self.console,
            "End session?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            self.console.print("[cyan]Ending session...[/cyan]")

            result = self.api.end_session(session.get("id"))

            if result.get("success"):
                self.config["current_session"] = None
                self.print_success("Session ended")

                # Show summary if available
                summary = result.get("data", {})
                if summary:
                    self.console.print(f"\n[dim]Messages: {summary.get('message_count', 0)}[/dim]")
                    self.console.print(f"[dim]Duration: {summary.get('duration', 'N/A')}[/dim]")

            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def info(self) -> None:
        """Show current session information"""
        session = self.config.get("current_session")
        if not session:
            self.print_warning("No active session")
            return

        self.console.print("[bold cyan]Session Information[/bold cyan]\n")

        from cli.utils.table_formatter import format_key_value_table

        session_data = {
            "ID": session.get("id", "N/A"),
            "Status": session.get("status", "unknown"),
            "Mode": session.get("mode", "socratic"),
            "Messages": session.get("message_count", 0),
            "Created": session.get("created_at", "N/A"),
            "Updated": session.get("updated_at", "N/A"),
        }

        table = format_key_value_table(session_data)
        self.console.print(table)
