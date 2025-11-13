"""Project insights and analysis commands.

/insights overview - Project overview and status
/insights gaps - Identify specification gaps
/insights risks - Risk analysis
/insights recommendations - Get recommendations
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class InsightsCommandHandler(CommandHandler):
    """Handler for project insights commands"""

    command_name = "insights"
    description = "Insights: overview, gaps, risks, recommendations"
    help_text = """
[bold cyan]Insights Commands:[/bold cyan]
  [yellow]/insights overview[/yellow]        Project overview and status
  [yellow]/insights gaps[/yellow]            Identify specification gaps
  [yellow]/insights risks[/yellow]           Risk analysis
  [yellow]/insights recommendations[/yellow] Get recommendations
"""

    def handle(self, args: List[str]) -> None:
        """Route insights commands"""
        if not args:
            self.overview()
            return

        subcommand = args[0].lower()

        if subcommand == "overview":
            self.overview()
        elif subcommand == "gaps":
            self.gaps()
        elif subcommand == "risks":
            self.risks()
        elif subcommand == "recommendations":
            self.recommendations()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def overview(self) -> None:
        """Show project overview and status"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Analyzing project...[/cyan]")

        try:
            result = self.api.get_project_insights(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load insights")
                return

            insights = result.get("data", {})

            self.console.print(f"\n[bold cyan]Project Insights: {project.get('name')}[/bold cyan]\n")

            # Status
            status = insights.get("status", {})
            self.console.print("[bold]Project Status:[/bold]")
            self.console.print(f"  Phase: {status.get('current_phase', 'N/A')}")
            self.console.print(f"  Maturity: {status.get('maturity_score', 0)}/100")
            self.console.print(f"  Completion: {status.get('completion_percentage', 0)}%\n")

            # Summary stats
            summary = insights.get("summary", {})
            self.console.print("[bold]Summary:[/bold]")
            self.console.print(f"  Total Specifications: {summary.get('total_specs', 0)}")
            self.console.print(f"  Implemented: {summary.get('implemented', 0)}")
            self.console.print(f"  In Progress: {summary.get('in_progress', 0)}")
            self.console.print(f"  Pending: {summary.get('pending', 0)}\n")

            # Team info
            team = insights.get("team", {})
            self.console.print("[bold]Team:[/bold]")
            self.console.print(f"  Members: {team.get('member_count', 0)}")
            self.console.print(f"  Active (7d): {team.get('active_7d', 0)}")
            self.console.print(f"  Sessions: {team.get('total_sessions', 0)}\n")

            # Timeline
            timeline = insights.get("timeline", {})
            self.console.print("[bold]Timeline:[/bold]")
            self.console.print(f"  Started: {timeline.get('start_date', 'N/A')}")
            self.console.print(f"  Est. End: {timeline.get('estimated_end', 'N/A')}")
            self.console.print(f"  Duration: {timeline.get('duration_days', 0)} days\n")

            # Key metrics
            metrics = insights.get("key_metrics", {})
            self.console.print("[bold]Key Metrics:[/bold]")
            self.console.print(f"  Avg. Session Length: {metrics.get('avg_session_length', 0)} min")
            self.console.print(f"  Questions Answered: {metrics.get('questions_answered', 0)}")
            self.console.print(f"  Code Generated: {metrics.get('code_lines_generated', 0)} lines")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def gaps(self) -> None:
        """Identify specification gaps"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Analyzing specification gaps...[/cyan]")

        try:
            result = self.api.analyze_specification_gaps(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to analyze gaps")
                return

            analysis = result.get("data", {})

            self.console.print("[bold cyan]Specification Gap Analysis[/bold cyan]\n")

            # Identified gaps
            gaps = analysis.get("gaps", [])
            if gaps:
                self.console.print("[bold]Identified Gaps:[/bold]")
                for gap in gaps:
                    area = gap.get("area", "N/A")
                    severity = gap.get("severity", "low")
                    description = gap.get("description", "")

                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "green"
                    }.get(severity, "white")

                    self.console.print(f"  [yellow]•[/yellow] {area} [{severity_color}]{severity}[/{severity_color}]")
                    if description:
                        self.console.print(f"    {description}")
                self.console.print()

            # Coverage metrics
            coverage = analysis.get("coverage", {})
            self.console.print("[bold]Coverage:[/bold]")
            self.console.print(f"  Requirements covered: {coverage.get('requirements_covered', 0)}%")
            self.console.print(f"  API endpoints: {coverage.get('api_endpoints', 0)}%")
            self.console.print(f"  Database schema: {coverage.get('database_schema', 0)}%")
            self.console.print(f"  Error handling: {coverage.get('error_handling', 0)}%\n")

            # Recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                self.console.print("[bold]Recommendations:[/bold]")
                for rec in recommendations[:5]:
                    self.console.print(f"  • {rec}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def risks(self) -> None:
        """Risk analysis"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Analyzing project risks...[/cyan]")

        try:
            result = self.api.analyze_project_risks(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to analyze risks")
                return

            analysis = result.get("data", {})

            self.console.print("[bold cyan]Risk Analysis[/bold cyan]\n")

            # Overall risk score
            risk_score = analysis.get("risk_score", 0)
            risk_level = analysis.get("risk_level", "low")

            risk_color = {
                "critical": "red",
                "high": "red",
                "medium": "yellow",
                "low": "green"
            }.get(risk_level, "white")

            self.console.print(f"[bold]Overall Risk Level:[/bold] [{risk_color}]{risk_level}[/{risk_color}] ({risk_score}/100)\n")

            # Identified risks
            risks = analysis.get("risks", [])
            if risks:
                self.console.print("[bold]Identified Risks:[/bold]")
                for risk in risks:
                    risk_name = risk.get("name", "Unknown")
                    probability = risk.get("probability", "medium")
                    impact = risk.get("impact", "medium")
                    mitigation = risk.get("mitigation", "")

                    self.console.print(f"  [yellow]•[/yellow] {risk_name}")
                    self.console.print(f"    Probability: {probability} | Impact: {impact}")
                    if mitigation:
                        self.console.print(f"    Mitigation: {mitigation}")
                self.console.print()

            # Timeline risks
            timeline_risks = analysis.get("timeline_risks", {})
            self.console.print("[bold]Timeline Risks:[/bold]")
            self.console.print(f"  Probability of delay: {timeline_risks.get('delay_probability', 0)}%")
            self.console.print(f"  Days at risk: {timeline_risks.get('days_at_risk', 0)}\n")

            # Resource risks
            resource_risks = analysis.get("resource_risks", {})
            self.console.print("[bold]Resource Risks:[/bold]")
            self.console.print(f"  Team capacity risk: {resource_risks.get('capacity_risk', 'low')}")
            self.console.print(f"  Knowledge gaps: {resource_risks.get('knowledge_gaps', 0)}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def recommendations(self) -> None:
        """Get recommendations"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Generating recommendations...[/cyan]")

        try:
            result = self.api.get_project_recommendations(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to generate recommendations")
                return

            recommendations = result.get("data", {}).get("recommendations", [])

            if not recommendations:
                self.console.print("[yellow]No recommendations at this time[/yellow]")
                return

            self.console.print("[bold cyan]Project Recommendations[/bold cyan]\n")

            # Group by category
            by_category = {}
            for rec in recommendations:
                category = rec.get("category", "general")
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(rec)

            for category, items in by_category.items():
                self.console.print(f"[bold]{category.upper()}:[/bold]")
                for item in items:
                    priority = item.get("priority", "medium")
                    title = item.get("title", "Recommendation")
                    description = item.get("description", "")
                    impact = item.get("expected_impact", "medium")

                    priority_color = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "green"
                    }.get(priority, "white")

                    self.console.print(f"  [{priority_color}]{priority.upper()}[/{priority_color}] {title}")
                    if description:
                        self.console.print(f"    {description}")
                    self.console.print(f"    Expected Impact: {impact}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")
