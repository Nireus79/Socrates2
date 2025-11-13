"""
Base CommandHandler class for all CLI commands.

Every command module implements a subclass of CommandHandler to define:
- Command name and description
- Help text
- Command handling logic
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel


class CommandHandler(ABC):
    """
    Abstract base class for all CLI command handlers.

    Each command (auth, projects, sessions, etc.) extends this class
    to provide command-specific implementation.

    Attributes:
        command_name: Name of the command (e.g., 'project', 'team')
        description: Brief description shown in help
        help_text: Detailed help text for the command
    """

    # Subclasses MUST set these
    command_name: str = None
    description: str = None
    help_text: str = None

    def __init__(
        self,
        console: Console,
        api_client: Any,
        config: Dict[str, Any]
    ):
        """
        Initialize command handler.

        Args:
            console: Rich console for output
            api_client: API client instance (Socrates.APIClient)
            config: Configuration dictionary (shared state)
        """
        self.console = console
        self.api = api_client
        self.config = config

    @abstractmethod
    def handle(self, args: List[str]) -> None:
        """
        Main command handler. Parse arguments and execute command.

        Args:
            args: Command arguments (excluding the command name itself)

        Example:
            If user types: /project create
            handle() receives: ["create"]

            If user types: /project manage 123
            handle() receives: ["manage", "123"]
        """
        pass

    def show_help(self) -> None:
        """Display help for this command."""
        if self.help_text:
            self.console.print(Panel(
                self.help_text,
                title=f"[bold]{self.command_name}[/bold] Help",
                border_style="cyan"
            ))
        else:
            self.console.print(f"[yellow]No help available for /{self.command_name}[/yellow]")

    def ensure_authenticated(self) -> bool:
        """
        Check if user is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        token = self.config.get("access_token")
        if not token:
            self.console.print("[red]✗ Not authenticated. Use /login or /register first[/red]")
            return False
        return True

    def ensure_project_selected(self) -> Optional[Dict[str, Any]]:
        """
        Check if a project is currently selected.

        Returns:
            Project dict if selected, None otherwise
        """
        project = self.config.get("current_project")
        if not project:
            self.console.print("[red]✗ No project selected. Use /project select first[/red]")
            return None
        return project

    def ensure_team_context(self) -> Optional[Dict[str, Any]]:
        """
        Check if team context is available.

        Returns:
            Team dict if available, None otherwise
        """
        team = self.config.get("current_team")
        if not team:
            self.console.print("[red]✗ No team context. This command requires team context[/red]")
            return None
        return team

    def get_current_domain(self) -> Optional[str]:
        """
        Get domain of current project.

        Returns:
            Domain name (e.g., 'business', 'design', 'programming') or None
        """
        project = self.config.get("current_project")
        if not project:
            return None
        return project.get("domain")

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user.

        Returns:
            User dict or None if not authenticated
        """
        return self.config.get("user")

    def print_error(self, message: str) -> None:
        """Print error message with consistent formatting."""
        self.console.print(f"[red]✗ {message}[/red]")

    def print_success(self, message: str) -> None:
        """Print success message with consistent formatting."""
        self.console.print(f"[green]✓ {message}[/green]")

    def print_warning(self, message: str) -> None:
        """Print warning message with consistent formatting."""
        self.console.print(f"[yellow]⚠ {message}[/yellow]")

    def print_info(self, message: str) -> None:
        """Print info message with consistent formatting."""
        self.console.print(f"[cyan]ℹ {message}[/cyan]")
