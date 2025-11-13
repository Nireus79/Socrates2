"""Template management commands.

/template list - List available templates
/template info - Show template details
/template apply - Apply template to project
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts


class TemplateCommandHandler(CommandHandler):
    """Handler for template management commands"""

    command_name = "template"
    description = "Templates: list, info, apply"
    help_text = """
[bold cyan]Template Commands:[/bold cyan]
  [yellow]/template list[/yellow]           List available templates
  [yellow]/template info <name>[/yellow]    Show template details
  [yellow]/template apply <name>[/yellow]   Apply template to current project
"""

    def handle(self, args: List[str]) -> None:
        """Route template commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "info":
            self.info(args[1:])
        elif subcommand == "apply":
            self.apply(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List available templates"""
        self.console.print("[cyan]Loading templates...[/cyan]")

        try:
            result = self.api.get_templates()

            if not result.get("success"):
                self.print_error("Failed to load templates")
                return

            templates = result.get("data", {}).get("templates", [])

            if not templates:
                self.console.print("[yellow]No templates available[/yellow]")
                return

            self.console.print("[bold cyan]Available Templates[/bold cyan]\n")

            for i, template in enumerate(templates, 1):
                name = template.get("name")
                desc = template.get("description", "")
                domain = template.get("domain", "general")

                self.console.print(f"[yellow]{i}.[/yellow] [bold]{name}[/bold]")
                self.console.print(f"   Domain: {domain}")
                self.console.print(f"   {desc}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def info(self, args: List[str]) -> None:
        """Show template information"""
        if not args:
            self.console.print("[yellow]Usage: /template info <template_name>[/yellow]")
            return

        template_name = " ".join(args)

        try:
            result = self.api.get_template(template_name)

            if not result.get("success"):
                self.print_error("Template not found")
                return

            template = result.get("data")

            self.console.print(f"\n[bold cyan]{template.get('name')}[/bold cyan]\n")
            self.console.print(f"[bold]Domain:[/bold] {template.get('domain', 'general')}")
            self.console.print(f"[bold]Description:[/bold] {template.get('description', 'N/A')}\n")

            self.console.print("[bold]Includes:[/bold]")
            for item in template.get("includes", []):
                self.console.print(f"  • {item}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def apply(self, args: List[str]) -> None:
        """Apply template to current project"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /template apply <template_name>[/yellow]")
            return

        template_name = " ".join(args)

        if not prompts.prompt_confirm(
            self.console,
            f"Apply template '{template_name}' to project?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            self.console.print("[cyan]Applying template...[/cyan]")

            result = self.api.apply_template(project.get("id"), template_name)

            if result.get("success"):
                self.print_success(f"Template applied: {template_name}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
