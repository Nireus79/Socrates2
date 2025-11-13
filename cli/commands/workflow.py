"""Workflow management commands.

/workflow list - List available workflows
/workflow info - Show workflow details
/workflow start - Start a workflow
/workflow status - Check workflow status
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class WorkflowCommandHandler(CommandHandler):
    """Handler for workflow management commands"""

    command_name = "workflow"
    description = "Workflows: list, info, start, status"
    help_text = """
[bold cyan]Workflow Commands:[/bold cyan]
  [yellow]/workflow list[/yellow]           List available workflows
  [yellow]/workflow info <name>[/yellow]    Show workflow details
  [yellow]/workflow start <name>[/yellow]   Start workflow
  [yellow]/workflow status <id>[/yellow]    Check workflow status
"""

    def handle(self, args: List[str]) -> None:
        """Route workflow commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "info":
            self.info(args[1:])
        elif subcommand == "start":
            self.start(args[1:])
        elif subcommand == "status":
            self.status(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List available workflows"""
        project = self.ensure_project_selected()
        if not project:
            return

        domain = project.get("domain", "general")
        self.console.print(f"[cyan]Loading {domain} workflows...[/cyan]")

        try:
            result = self.api.list_workflows(domain)

            if not result.get("success"):
                self.print_error("Failed to load workflows")
                return

            workflows = result.get("data", {}).get("workflows", [])

            if not workflows:
                self.console.print(f"[yellow]No workflows available for {domain}[/yellow]")
                return

            self.console.print(f"[bold cyan]Available Workflows for {domain.capitalize()}[/bold cyan]\n")

            for i, wf in enumerate(workflows, 1):
                name = wf.get("name", "Unknown")
                desc = wf.get("description", "")
                steps = wf.get("steps_count", 0)
                duration = wf.get("estimated_duration", "Unknown")

                self.console.print(f"[yellow]{i}.[/yellow] [bold]{name}[/bold]")
                self.console.print(f"   {desc}")
                self.console.print(f"   Steps: {steps} | Est. Time: {duration}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def info(self, args: List[str]) -> None:
        """Show workflow information"""
        if not args:
            self.console.print("[yellow]Usage: /workflow info <workflow_name>[/yellow]")
            return

        workflow_name = " ".join(args)

        try:
            result = self.api.get_workflow(workflow_name)

            if not result.get("success"):
                self.print_error("Workflow not found")
                return

            workflow = result.get("data")

            self.console.print(f"\n[bold cyan]{workflow.get('name')}[/bold cyan]\n")
            self.console.print(f"[bold]Description:[/bold] {workflow.get('description', 'N/A')}")
            self.console.print(f"[bold]Domain:[/bold] {workflow.get('domain', 'N/A')}")
            self.console.print(f"[bold]Estimated Time:[/bold] {workflow.get('estimated_duration', 'N/A')}\n")

            self.console.print("[bold]Steps:[/bold]")
            steps = workflow.get("steps", [])
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", "Step")
                step_desc = step.get("description", "")
                self.console.print(f"  {i}. {step_name}")
                if step_desc:
                    self.console.print(f"     {step_desc}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def start(self, args: List[str]) -> None:
        """Start a workflow"""
        project = self.ensure_project_selected()
        if not project:
            return

        session = self.ensure_session_selected()
        if not session:
            return

        if not args:
            self.console.print("[yellow]Usage: /workflow start <workflow_name>[/yellow]")
            return

        workflow_name = " ".join(args)

        if not prompts.prompt_confirm(
            self.console,
            f"Start workflow '{workflow_name}'?",
            default=True
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            self.console.print("[cyan]Starting workflow...[/cyan]")

            result = self.api.start_workflow(
                session.get("id"),
                workflow_name=workflow_name
            )

            if result.get("success"):
                self.print_success(f"Workflow started: {workflow_name}")
                self.console.print(f"[cyan]Workflow ID: {result.get('workflow_id')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def status(self, args: List[str]) -> None:
        """Check workflow status"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /workflow status <workflow_id>[/yellow]")
            return

        workflow_id = args[0]

        try:
            result = self.api.get_workflow_status(workflow_id)

            if not result.get("success"):
                self.print_error("Workflow not found")
                return

            workflow = result.get("data")

            self.console.print(f"\n[bold cyan]{workflow.get('name')}[/bold cyan]\n")

            from cli.utils.table_formatter import format_key_value_table

            status_color = {
                "pending": "yellow",
                "in-progress": "cyan",
                "completed": "green",
                "failed": "red"
            }.get(workflow.get("status"), "white")

            workflow_data = {
                "ID": workflow.get("id", "N/A"),
                "Name": workflow.get("name", "N/A"),
                "Status": f"[{status_color}]{workflow.get('status', 'N/A')}[/{status_color}]",
                "Progress": f"{workflow.get('progress', 0)}%",
                "Current Step": workflow.get("current_step_name", "N/A"),
                "Started": workflow.get("started_at", "N/A"),
            }

            table = format_key_value_table(workflow_data)
            self.console.print(table)

            # Show step details
            steps = workflow.get("steps", [])
            if steps:
                self.console.print("\n[bold]Steps:[/bold]")
                for step in steps:
                    step_status = "✓" if step.get("completed") else "○"
                    self.console.print(f"  {step_status} {step.get('name', 'Unknown step')}")

        except Exception as e:
            self.print_error(f"Error: {e}")
