"""Quality assurance and metrics commands.

/quality check - Run quality checks
/quality metrics - Show quality metrics
/quality gates - Quality gates configuration
/quality report - Generate quality report
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class QualityCommandHandler(CommandHandler):
    """Handler for quality assurance commands"""

    command_name = "quality"
    description = "Quality: check, metrics, gates, report"
    help_text = """
[bold cyan]Quality Commands:[/bold cyan]
  [yellow]/quality check[/yellow]         Run quality checks
  [yellow]/quality metrics[/yellow]       Show quality metrics
  [yellow]/quality gates[/yellow]        Quality gates config
  [yellow]/quality report[/yellow]       Generate quality report
"""

    def handle(self, args: List[str]) -> None:
        """Route quality commands"""
        if not args:
            self.check()
            return

        subcommand = args[0].lower()

        if subcommand == "check":
            self.check()
        elif subcommand == "metrics":
            self.metrics()
        elif subcommand == "gates":
            self.gates(args[1:])
        elif subcommand == "report":
            self.report()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def check(self) -> None:
        """Run quality checks"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Running quality checks...[/cyan]")

        try:
            result = self.api.run_quality_checks(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to run quality checks")
                return

            checks = result.get("data", {}).get("checks", [])

            if not checks:
                self.console.print("[yellow]No quality checks available[/yellow]")
                return

            self.console.print("[bold cyan]Quality Checks Results[/bold cyan]\n")

            passed = 0
            failed = 0
            warnings = 0

            for check in checks:
                check_name = check.get("name", "Unknown")
                status = check.get("status", "pending")
                message = check.get("message", "")

                if status == "passed":
                    self.console.print(f"[green]✓[/green] {check_name}")
                    passed += 1
                elif status == "failed":
                    self.console.print(f"[red]✗[/red] {check_name}")
                    if message:
                        self.console.print(f"  [red]{message}[/red]")
                    failed += 1
                elif status == "warning":
                    self.console.print(f"[yellow]⚠[/yellow] {check_name}")
                    if message:
                        self.console.print(f"  [yellow]{message}[/yellow]")
                    warnings += 1

            self.console.print(f"\n[bold]Summary:[/bold]")
            self.console.print(f"  [green]Passed:[/green] {passed}")
            self.console.print(f"  [yellow]Warnings:[/yellow] {warnings}")
            self.console.print(f"  [red]Failed:[/red] {failed}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def metrics(self) -> None:
        """Show quality metrics"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading quality metrics...[/cyan]")

        try:
            result = self.api.get_quality_metrics(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load metrics")
                return

            metrics = result.get("data", {})

            self.console.print(f"[bold cyan]Quality Metrics: {project.get('name')}[/bold cyan]\n")

            # Code quality
            code = metrics.get("code_quality", {})
            self.console.print("[bold]Code Quality:[/bold]")
            self.console.print(f"  Maintainability: {code.get('maintainability', 0)}/100")
            self.console.print(f"  Test Coverage: {code.get('test_coverage', 0)}%")
            self.console.print(f"  Complexity: {code.get('avg_complexity', 0)}")
            self.console.print(f"  Documentation: {code.get('documentation', 0)}%\n")

            # Specification quality
            spec = metrics.get("specification_quality", {})
            self.console.print("[bold]Specification Quality:[/bold]")
            self.console.print(f"  Completeness: {spec.get('completeness', 0)}%")
            self.console.print(f"  Clarity: {spec.get('clarity', 0)}/10")
            self.console.print(f"  Detail Level: {spec.get('detail_level', 0)}/10\n")

            # Architecture quality
            arch = metrics.get("architecture_quality", {})
            self.console.print("[bold]Architecture Quality:[/bold]")
            self.console.print(f"  Modularity: {arch.get('modularity', 0)}/10")
            self.console.print(f"  Scalability: {arch.get('scalability', 0)}/10")
            self.console.print(f"  Security: {arch.get('security', 0)}/10\n")

            # Process quality
            process = metrics.get("process_quality", {})
            self.console.print("[bold]Process Quality:[/bold]")
            self.console.print(f"  Documentation: {process.get('documentation', 0)}%")
            self.console.print(f"  Testing: {process.get('testing', 0)}%")
            self.console.print(f"  Deployment: {process.get('deployment', 0)}%\n")

            # Overall score
            overall = metrics.get("overall_score", 0)
            self.console.print(f"[bold]Overall Quality Score: {overall}/100[/bold]")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def gates(self, args: List[str]) -> None:
        """Manage quality gates"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.show_gates()
        else:
            subcommand = args[0].lower()
            if subcommand == "show":
                self.show_gates()
            elif subcommand == "set":
                self.set_gate(args[1:])
            elif subcommand == "enable":
                self.enable_gate(args[1:])
            elif subcommand == "disable":
                self.disable_gate(args[1:])
            else:
                self.print_error(f"Unknown subcommand: {subcommand}")

    def show_gates(self) -> None:
        """Show quality gates configuration"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading quality gates...[/cyan]")

        try:
            result = self.api.get_quality_gates(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load gates")
                return

            gates = result.get("data", {}).get("gates", [])

            self.console.print("[bold cyan]Quality Gates[/bold cyan]\n")

            for gate in gates:
                name = gate.get("name", "Unknown")
                metric = gate.get("metric", "N/A")
                threshold = gate.get("threshold", "N/A")
                enabled = gate.get("enabled", False)

                status = "[green]✓[/green]" if enabled else "[red]✗[/red]"
                self.console.print(f"{status} {name}")
                self.console.print(f"  Metric: {metric} | Threshold: {threshold}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def set_gate(self, args: List[str]) -> None:
        """Set quality gate threshold"""
        project = self.ensure_project_selected()
        if not project:
            return

        if len(args) < 2:
            self.console.print("[yellow]Usage: /quality gates set <gate_name> <threshold>[/yellow]")
            return

        gate_name = args[0]
        threshold = args[1]

        try:
            result = self.api.set_quality_gate(project.get("id"), gate_name, threshold)

            if result.get("success"):
                self.print_success(f"Quality gate updated: {gate_name}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def enable_gate(self, args: List[str]) -> None:
        """Enable quality gate"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /quality gates enable <gate_name>[/yellow]")
            return

        gate_name = args[0]

        try:
            result = self.api.enable_quality_gate(project.get("id"), gate_name)

            if result.get("success"):
                self.print_success(f"Quality gate enabled: {gate_name}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def disable_gate(self, args: List[str]) -> None:
        """Disable quality gate"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /quality gates disable <gate_name>[/yellow]")
            return

        gate_name = args[0]

        try:
            result = self.api.disable_quality_gate(project.get("id"), gate_name)

            if result.get("success"):
                self.print_success(f"Quality gate disabled: {gate_name}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def report(self) -> None:
        """Generate quality report"""
        project = self.ensure_project_selected()
        if not project:
            return

        # Get output format
        output_format = prompts.prompt_choice(
            self.console,
            "Report format",
            ["pdf", "html", "markdown", "json"],
            default="pdf"
        )

        # Get report type
        report_type = prompts.prompt_choice(
            self.console,
            "Report type",
            ["summary", "detailed", "executive"],
            default="detailed"
        )

        try:
            self.console.print("[cyan]Generating quality report...[/cyan]")

            result = self.api.generate_quality_report(
                project.get("id"),
                format=output_format,
                report_type=report_type
            )

            if result.get("success"):
                self.print_success("Quality report generated")
                self.console.print(f"[cyan]File: {result.get('filename')}[/cyan]")
                self.console.print(f"[cyan]Location: {result.get('location')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
