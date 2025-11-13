"""Specification management commands.

/specification list - List project specifications
/specification create - Create new specification
/specification info - Show specification details
/specification approve - Approve specification
/specification implement - Mark as implemented
/specification delete - Delete specification
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class SpecificationCommandHandler(CommandHandler):
    """Handler for specification management commands"""

    command_name = "specification"
    description = "Specifications: list, create, approve, implement, delete"
    help_text = """
[bold cyan]Specification Commands:[/bold cyan]
  [yellow]/specification list[/yellow]              List project specs
  [yellow]/specification create[/yellow]            Create new spec
  [yellow]/specification info <id>[/yellow]         Show spec details
  [yellow]/specification approve <id>[/yellow]      Approve spec
  [yellow]/specification implement <id>[/yellow]    Mark implemented
  [yellow]/specification delete <id>[/yellow]       Delete spec
"""

    def handle(self, args: List[str]) -> None:
        """Route specification commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "create":
            self.create()
        elif subcommand == "info":
            self.info(args[1:])
        elif subcommand == "approve":
            self.approve(args[1:])
        elif subcommand == "implement":
            self.implement(args[1:])
        elif subcommand == "delete":
            self.delete(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List project specifications"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading specifications...[/cyan]")

        try:
            result = self.api.list_specifications(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load specifications")
                return

            specs = result.get("data", {}).get("specifications", [])

            if not specs:
                self.console.print("[yellow]No specifications yet[/yellow]")
                self.console.print("[yellow]Use /specification create to add one[/yellow]")
                return

            table = table_formatter.format_specification_table(specs)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def create(self) -> None:
        """Create new specification"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Create New Specification[/bold cyan]\n")

        try:
            title = prompts.prompt_text(self.console, "Specification title")
            spec_type = prompts.prompt_choice(
                self.console,
                "Type",
                ["feature", "bug", "enhancement", "documentation"],
                default="feature"
            )
            description = prompts.prompt_text(
                self.console,
                "Description (optional)",
                default=""
            )

            self.console.print("[cyan]Creating specification...[/cyan]")

            result = self.api.create_specification(
                project.get("id"),
                title=title,
                spec_type=spec_type,
                description=description
            )

            if result.get("success"):
                self.print_success(f"Specification created: {title}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Creation cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def info(self, args: List[str]) -> None:
        """Show specification information"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /specification info <spec_id>[/yellow]")
            return

        spec_id = args[0]

        try:
            result = self.api.get_specification(spec_id)

            if not result.get("success"):
                self.print_error("Specification not found")
                return

            spec = result.get("data")

            self.console.print(f"\n[bold cyan]{spec.get('title')}[/bold cyan]\n")

            from cli.utils.table_formatter import format_key_value_table

            spec_data = {
                "ID": spec.get("id", "N/A"),
                "Type": spec.get("type", "N/A"),
                "Status": spec.get("status", "draft"),
                "Created": spec.get("created_at", "N/A"),
                "Updated": spec.get("updated_at", "N/A"),
                "Description": spec.get("description", "N/A"),
            }

            table = format_key_value_table(spec_data)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def approve(self, args: List[str]) -> None:
        """Approve specification"""
        if not args:
            self.console.print("[yellow]Usage: /specification approve <spec_id>[/yellow]")
            return

        spec_id = args[0]

        if not prompts.prompt_confirm(
            self.console,
            "Approve specification?",
            default=True
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            result = self.api.approve_specification(spec_id)

            if result.get("success"):
                self.print_success("Specification approved")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def implement(self, args: List[str]) -> None:
        """Mark specification as implemented"""
        if not args:
            self.console.print("[yellow]Usage: /specification implement <spec_id>[/yellow]")
            return

        spec_id = args[0]

        try:
            result = self.api.implement_specification(spec_id)

            if result.get("success"):
                self.print_success("Specification marked as implemented")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def delete(self, args: List[str]) -> None:
        """Delete specification"""
        if not args:
            self.console.print("[yellow]Usage: /specification delete <spec_id>[/yellow]")
            return

        spec_id = args[0]

        if not prompts.prompt_confirm(
            self.console,
            "Delete specification?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            result = self.api.delete_specification(spec_id)

            if result.get("success"):
                self.print_success("Specification deleted")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
