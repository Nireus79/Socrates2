"""Analytics and insights commands.

/analytics dashboard - Show analytics dashboard
/analytics project - Project-specific analytics
/analytics user - User activity analytics
/analytics export - Export analytics data
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class AnalyticsCommandHandler(CommandHandler):
    """Handler for analytics and tracking commands"""

    command_name = "analytics"
    description = "Analytics: dashboard, project, user, export"
    help_text = """
[bold cyan]Analytics Commands:[/bold cyan]
  [yellow]/analytics dashboard[/yellow]      Show analytics dashboard
  [yellow]/analytics project[/yellow]        Project-specific analytics
  [yellow]/analytics user[/yellow]          User activity analytics
  [yellow]/analytics export <format>[/yellow] Export analytics data
"""

    def handle(self, args: List[str]) -> None:
        """Route analytics commands"""
        if not args:
            self.dashboard()
            return

        subcommand = args[0].lower()

        if subcommand == "dashboard":
            self.dashboard()
        elif subcommand == "project":
            self.project()
        elif subcommand == "user":
            self.user()
        elif subcommand == "export":
            self.export(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def dashboard(self) -> None:
        """Show analytics dashboard"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[cyan]Loading analytics dashboard...[/cyan]")

        try:
            result = self.api.get_analytics_dashboard(user.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load analytics")
                return

            data = result.get("data", {})

            self.console.print("[bold cyan]Analytics Dashboard[/bold cyan]\n")

            # Session metrics
            sessions = data.get("sessions", {})
            self.console.print("[bold]Sessions:[/bold]")
            self.console.print(f"  Total: {sessions.get('total', 0)}")
            self.console.print(f"  This month: {sessions.get('this_month', 0)}")
            self.console.print(f"  Avg duration: {sessions.get('avg_duration', 0)} min\n")

            # Question metrics
            questions = data.get("questions", {})
            self.console.print("[bold]Questions:[/bold]")
            self.console.print(f"  Answered: {questions.get('answered', 0)}")
            self.console.print(f"  Pending: {questions.get('pending', 0)}")
            self.console.print(f"  Completion rate: {questions.get('completion_rate', 0)}%\n")

            # Code metrics
            code = data.get("code", {})
            self.console.print("[bold]Code Generation:[/bold]")
            self.console.print(f"  Total generated: {code.get('total_generated', 0)}")
            self.console.print(f"  Languages: {code.get('languages_used', 0)}")
            self.console.print(f"  Lines of code: {code.get('lines_of_code', 0)}\n")

            # Time metrics
            time_spent = data.get("time_spent", {})
            self.console.print("[bold]Time Spent:[/bold]")
            self.console.print(f"  This week: {time_spent.get('this_week', 0)} hours")
            self.console.print(f"  This month: {time_spent.get('this_month', 0)} hours")
            self.console.print(f"  Total: {time_spent.get('total', 0)} hours\n")

            # Top projects
            projects = data.get("top_projects", [])
            if projects:
                self.console.print("[bold]Top Projects:[/bold]")
                for proj in projects[:5]:
                    name = proj.get("name", "Unknown")
                    sessions_count = proj.get("sessions", 0)
                    self.console.print(f"  • {name} ({sessions_count} sessions)")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def project(self) -> None:
        """Show project-specific analytics"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading project analytics...[/cyan]")

        try:
            result = self.api.get_project_analytics(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load project analytics")
                return

            data = result.get("data", {})

            self.console.print(f"[bold cyan]Analytics: {project.get('name')}[/bold cyan]\n")

            # Project overview
            overview = data.get("overview", {})
            self.console.print("[bold]Overview:[/bold]")
            self.console.print(f"  Domain: {overview.get('domain', 'N/A')}")
            self.console.print(f"  Created: {overview.get('created_at', 'N/A')}")
            self.console.print(f"  Last activity: {overview.get('last_activity', 'N/A')}\n")

            # Session analytics
            sessions = data.get("sessions", {})
            self.console.print("[bold]Sessions:[/bold]")
            self.console.print(f"  Total: {sessions.get('total', 0)}")
            self.console.print(f"  Avg duration: {sessions.get('avg_duration', 0)} min")
            self.console.print(f"  Socratic: {sessions.get('socratic', 0)}")
            self.console.print(f"  Direct: {sessions.get('direct', 0)}\n")

            # Question analytics
            questions = data.get("questions", {})
            self.console.print("[bold]Questions:[/bold]")
            self.console.print(f"  Total asked: {questions.get('total', 0)}")
            self.console.print(f"  Answered: {questions.get('answered', 0)}")
            self.console.print(f"  Custom: {questions.get('custom', 0)}\n")

            # Team analytics
            team = data.get("team", {})
            if team:
                self.console.print("[bold]Team:[/bold]")
                self.console.print(f"  Members: {team.get('members', 0)}")
                self.console.print(f"  Active: {team.get('active', 0)}")
                self.console.print(f"  Last week: {team.get('last_week_active', 0)}\n")

            # Maturity
            maturity = data.get("maturity", {})
            self.console.print("[bold]Maturity Score:[/bold]")
            self.console.print(f"  Overall: {maturity.get('overall', 0)}%")
            self.console.print(f"  Completeness: {maturity.get('completeness', 0)}%")
            self.console.print(f"  Quality: {maturity.get('quality', 0)}%")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def user(self) -> None:
        """Show user activity analytics"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[cyan]Loading user analytics...[/cyan]")

        try:
            result = self.api.get_user_analytics(user.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load user analytics")
                return

            data = result.get("data", {})

            self.console.print(f"[bold cyan]Analytics: {user.get('email')}[/bold cyan]\n")

            # Activity summary
            activity = data.get("activity", {})
            self.console.print("[bold]Activity:[/bold]")
            self.console.print(f"  Last login: {activity.get('last_login', 'N/A')}")
            self.console.print(f"  Login streak: {activity.get('login_streak', 0)} days")
            self.console.print(f"  Total logins: {activity.get('total_logins', 0)}\n")

            # Usage patterns
            usage = data.get("usage", {})
            self.console.print("[bold]Usage:[/bold]")
            self.console.print(f"  Projects created: {usage.get('projects_created', 0)}")
            self.console.print(f"  Sessions held: {usage.get('sessions_held', 0)}")
            self.console.print(f"  Questions answered: {usage.get('questions_answered', 0)}\n")

            # Time zones and patterns
            patterns = data.get("patterns", {})
            self.console.print("[bold]Patterns:[/bold]")
            self.console.print(f"  Most active day: {patterns.get('most_active_day', 'N/A')}")
            self.console.print(f"  Most active hour: {patterns.get('most_active_hour', 'N/A')}")
            self.console.print(f"  Avg session length: {patterns.get('avg_session_length', 0)} min\n")

            # Preferences
            prefs = data.get("preferences", {})
            self.console.print("[bold]Preferences:[/bold]")
            self.console.print(f"  Favorite domain: {prefs.get('favorite_domain', 'N/A')}")
            self.console.print(f"  Favorite mode: {prefs.get('favorite_mode', 'N/A')}")
            self.console.print(f"  Preferred language: {prefs.get('preferred_language', 'N/A')}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def export(self, args: List[str]) -> None:
        """Export analytics data"""
        user = self.ensure_authenticated()
        if not user:
            return

        if not args:
            export_format = prompts.prompt_choice(
                self.console,
                "Export format",
                ["csv", "json", "pdf", "excel"],
                default="csv"
            )
        else:
            export_format = args[0]

        # Get scope
        scope = prompts.prompt_choice(
            self.console,
            "Export scope",
            ["user", "project", "team"],
            default="user"
        )

        # Get date range
        period = prompts.prompt_choice(
            self.console,
            "Time period",
            ["7d", "30d", "90d", "1y", "all"],
            default="30d"
        )

        # Get fields to include
        fields = prompts.select_multiple_from_list(
            self.console,
            "Data to include",
            ["sessions", "questions", "code", "team-activity", "time-spent"],
            "Select fields to export"
        )

        try:
            self.console.print("[cyan]Generating export...[/cyan]")

            result = self.api.export_analytics(
                scope=scope,
                format=export_format,
                period=period,
                fields=fields
            )

            if result.get("success"):
                self.print_success(f"Analytics exported ({export_format})")
                self.console.print(f"[cyan]File: {result.get('filename')}[/cyan]")
                self.console.print(f"[cyan]Size: {result.get('file_size')}[/cyan]")
                self.console.print(f"[cyan]Location: {result.get('location')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
