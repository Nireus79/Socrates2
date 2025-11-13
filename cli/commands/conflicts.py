"""Conflict detection and resolution commands.

/conflicts detect - Detect specification conflicts
/conflicts list - List detected conflicts
/conflicts resolve - Resolve a conflict
/conflicts analysis - Analyze conflict patterns
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class ConflictsCommandHandler(CommandHandler):
    """Handler for conflict detection and resolution commands"""

    command_name = "conflicts"
    description = "Conflicts: detect, list, resolve, analysis"
    help_text = """
[bold cyan]Conflict Commands:[/bold cyan]
  [yellow]/conflicts detect[/yellow]       Detect specification conflicts
  [yellow]/conflicts list[/yellow]         List detected conflicts
  [yellow]/conflicts resolve <id>[/yellow] Resolve a conflict
  [yellow]/conflicts analysis[/yellow]     Analyze conflict patterns
"""

    def handle(self, args: List[str]) -> None:
        """Route conflict commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "detect":
            self.detect()
        elif subcommand == "list":
            self.list()
        elif subcommand == "resolve":
            self.resolve(args[1:])
        elif subcommand == "analysis":
            self.analysis()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def detect(self) -> None:
        """Detect specification conflicts"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Analyzing specifications for conflicts...[/cyan]")

        try:
            result = self.api.detect_conflicts(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to detect conflicts")
                return

            conflicts = result.get("data", {}).get("conflicts", [])

            if not conflicts:
                self.print_success("No conflicts detected")
                return

            self.console.print(f"[bold cyan]Found {len(conflicts)} Conflict(s)[/bold cyan]\n")

            for conflict in conflicts:
                conflict_id = conflict.get("id", "N/A")
                conflict_type = conflict.get("type", "Unknown")
                severity = conflict.get("severity", "low")
                specs = conflict.get("affected_specs", [])

                severity_color = {
                    "critical": "red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "green"
                }.get(severity, "white")

                self.console.print(f"[yellow]ID:[/yellow] {conflict_id}")
                self.console.print(f"[yellow]Type:[/yellow] {conflict_type}")
                self.console.print(f"[yellow]Severity:[/yellow] [{severity_color}]{severity}[/{severity_color}]")
                self.console.print(f"[yellow]Affected Specs:[/yellow] {', '.join(specs)}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def list(self) -> None:
        """List detected conflicts"""
        project = self.ensure_project_selected()
        if not project:
            return

        # Get filter
        filter_by = prompts.prompt_choice(
            self.console,
            "Filter by",
            ["all", "unresolved", "critical", "high", "medium", "low"],
            default="unresolved"
        )

        self.console.print("[cyan]Loading conflicts...[/cyan]")

        try:
            result = self.api.list_conflicts(project.get("id"), filter=filter_by)

            if not result.get("success"):
                self.print_error("Failed to load conflicts")
                return

            conflicts = result.get("data", {}).get("conflicts", [])

            if not conflicts:
                self.console.print("[yellow]No conflicts found[/yellow]")
                return

            self.console.print(f"[bold cyan]Conflicts ({filter_by})[/bold cyan]\n")

            for conflict in conflicts:
                conflict_id = conflict.get("id", "N/A")
                title = conflict.get("title", "Unknown")
                severity = conflict.get("severity", "low")
                status = conflict.get("status", "open")

                severity_color = {
                    "critical": "red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "green"
                }.get(severity, "white")

                status_color = "yellow" if status == "open" else "green"

                self.console.print(f"[yellow]{conflict_id}[/yellow] {title}")
                self.console.print(f"  Severity: [{severity_color}]{severity}[/{severity_color}] | Status: [{status_color}]{status}[/{status_color}]\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def resolve(self, args: List[str]) -> None:
        """Resolve a conflict"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /conflicts resolve <conflict_id>[/yellow]")
            return

        conflict_id = args[0]

        try:
            # Get conflict details
            result = self.api.get_conflict(conflict_id)

            if not result.get("success"):
                self.print_error("Conflict not found")
                return

            conflict = result.get("data")

            self.console.print(f"\n[bold cyan]{conflict.get('title')}[/bold cyan]\n")
            self.console.print(f"Description: {conflict.get('description', 'N/A')}\n")

            # Show options
            options = conflict.get("resolution_options", [])
            if options:
                self.console.print("[bold]Resolution Options:[/bold]")
                for i, option in enumerate(options, 1):
                    self.console.print(f"  {i}. {option.get('title', 'Option')}")
                    self.console.print(f"     {option.get('description', '')}\n")

                choice = prompts.prompt_choice(
                    self.console,
                    "Select resolution",
                    [opt.get("title", f"Option {i}") for i, opt in enumerate(options, 1)],
                )

                resolution_index = [opt.get("title", f"Option {i}") for i, opt in enumerate(options, 1)].index(choice)
                selected_option = options[resolution_index]
            else:
                # Manual resolution
                self.console.print("[bold]Enter Resolution[/bold]")
                resolution = prompts.prompt_text(self.console, "Resolution details")
                selected_option = {"title": "manual", "action": resolution}

            # Confirm resolution
            if not prompts.prompt_confirm(
                self.console,
                "Apply this resolution?",
                default=True
            ):
                self.console.print("[yellow]Cancelled[/yellow]")
                return

            # Submit resolution
            resolve_result = self.api.resolve_conflict(
                conflict_id,
                resolution=selected_option.get("action") or selected_option.get("title")
            )

            if resolve_result.get("success"):
                self.print_success("Conflict resolved")
            else:
                error = resolve_result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def analysis(self) -> None:
        """Analyze conflict patterns"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Analyzing conflict patterns...[/cyan]")

        try:
            result = self.api.analyze_conflict_patterns(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to analyze conflicts")
                return

            analysis = result.get("data", {})

            self.console.print("[bold cyan]Conflict Analysis[/bold cyan]\n")

            # Summary
            summary = analysis.get("summary", {})
            self.console.print("[bold]Summary:[/bold]")
            self.console.print(f"  Total conflicts: {summary.get('total', 0)}")
            self.console.print(f"  Unresolved: {summary.get('unresolved', 0)}")
            self.console.print(f"  Resolved: {summary.get('resolved', 0)}")
            self.console.print(f"  Avg resolution time: {summary.get('avg_resolution_time', 'N/A')}h\n")

            # Conflict types
            types = analysis.get("conflict_types", {})
            self.console.print("[bold]Conflict Types:[/bold]")
            for conflict_type, count in types.items():
                self.console.print(f"  {conflict_type}: {count}")
            self.console.print()

            # Most common issues
            issues = analysis.get("common_issues", [])
            if issues:
                self.console.print("[bold]Common Issues:[/bold]")
                for issue in issues[:5]:
                    self.console.print(f"  • {issue}")
                self.console.print()

            # Recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                self.console.print("[bold]Recommendations:[/bold]")
                for rec in recommendations[:5]:
                    self.console.print(f"  • {rec}")

        except Exception as e:
            self.print_error(f"Error: {e}")
