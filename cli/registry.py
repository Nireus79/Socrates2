"""
CommandRegistry: Auto-discovers and loads all CLI command handlers.

The registry scans the cli/commands/ directory for CommandHandler subclasses,
instantiates them, and provides a central routing mechanism for all commands.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from importlib import import_module
from rich.console import Console
from rich.table import Table

from cli.base import CommandHandler

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Registry for discovering, loading, and routing CLI commands.

    On initialization, automatically scans cli/commands/ directory and loads
    all CommandHandler subclasses. Commands can then be routed by name.

    Example:
        registry = CommandRegistry(console, api_client, config)
        registry.load_all_commands()
        registry.route_command("project", ["create"])
        registry.list_commands()
    """

    def __init__(
        self,
        console: Console,
        api_client: Any,
        config: Dict[str, Any]
    ):
        """
        Initialize registry.

        Args:
            console: Rich console for output
            api_client: API client instance
            config: Shared configuration state
        """
        self.console = console
        self.api_client = api_client
        self.config = config
        self.commands: Dict[str, CommandHandler] = {}
        self.failed_modules: List[str] = []

    def load_all_commands(self) -> None:
        """
        Auto-discover and load all commands from cli/commands/ directory.

        Scans for .py files, imports them, finds CommandHandler subclasses,
        instantiates them, and registers by command_name.

        Handles errors gracefully - if a module fails to load, continues
        with others and logs the failure.
        """
        commands_dir = Path(__file__).parent / "commands"

        if not commands_dir.exists():
            self.console.print(f"[red]✗ Commands directory not found: {commands_dir}[/red]")
            return

        logger.info(f"Loading commands from {commands_dir}")

        for module_file in sorted(commands_dir.glob("*.py")):
            # Skip private modules and __init__
            if module_file.name.startswith("_"):
                continue

            module_name = module_file.stem

            try:
                # Import the module
                module = import_module(f"cli.commands.{module_name}")

                # Find all CommandHandler subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # Check if it's a CommandHandler subclass (but not the base class)
                    if (isinstance(attr, type) and
                        issubclass(attr, CommandHandler) and
                        attr is not CommandHandler):

                        try:
                            # Instantiate the handler
                            handler = attr(self.console, self.api_client, self.config)

                            # Validate that it has required attributes
                            if not handler.command_name:
                                logger.warning(
                                    f"Skipping {attr.__name__} in {module_name}: "
                                    "command_name not set"
                                )
                                continue

                            # Register by command name
                            self.commands[handler.command_name] = handler

                            logger.info(
                                f"Loaded command: /{handler.command_name} "
                                f"({attr.__name__} from {module_name})"
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to instantiate {attr.__name__} "
                                f"from {module_name}: {e}"
                            )

            except ImportError as e:
                logger.warning(f"Failed to import {module_name}: {e}")
                self.failed_modules.append(module_name)
            except Exception as e:
                logger.error(f"Unexpected error loading {module_name}: {e}")
                self.failed_modules.append(module_name)

        logger.info(f"Command registry loaded {len(self.commands)} commands")

    def route_command(self, command: str, args: List[str]) -> bool:
        """
        Route a command to the appropriate handler.

        Args:
            command: Command name (e.g., 'project', 'session')
            args: Command arguments

        Returns:
            True if command was found and handled, False otherwise
        """
        if command in self.commands:
            try:
                self.commands[command].handle(args)
                return True
            except Exception as e:
                self.console.print(f"[red]✗ Error executing command: {e}[/red]")
                logger.error(f"Error routing command '{command}': {e}", exc_info=True)
                return False
        return False

    def command_exists(self, command: str) -> bool:
        """
        Check if a command is registered.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        return command in self.commands

    def list_commands(self) -> Dict[str, str]:
        """
        Get all registered commands with descriptions.

        Returns:
            Dict mapping command names to descriptions
        """
        return {
            name: handler.description or "No description"
            for name, handler in sorted(self.commands.items())
        }

    def get_command(self, command: str) -> Optional[CommandHandler]:
        """
        Get a specific command handler.

        Args:
            command: Command name

        Returns:
            CommandHandler instance or None if not found
        """
        return self.commands.get(command)

    def show_commands_table(self) -> None:
        """Display all commands in a formatted table."""
        if not self.commands:
            self.console.print("[yellow]No commands loaded[/yellow]")
            return

        table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        for name in sorted(self.commands.keys()):
            handler = self.commands[name]
            description = handler.description or "No description"
            # Truncate long descriptions
            if len(description) > 60:
                description = description[:57] + "..."
            table.add_row(f"/{name}", description)

        self.console.print(table)

    def show_command_help(self, command: str) -> None:
        """
        Display help for a specific command.

        Args:
            command: Command name
        """
        if command not in self.commands:
            self.console.print(f"[red]✗ Unknown command: /{command}[/red]")
            self.console.print("[yellow]Use /help to see available commands[/yellow]")
            return

        self.commands[command].show_help()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded commands.

        Returns:
            Dict with stats like total commands, failed modules, etc.
        """
        return {
            "total_commands": len(self.commands),
            "command_names": sorted(self.commands.keys()),
            "failed_modules": self.failed_modules,
            "total_failed": len(self.failed_modules)
        }
