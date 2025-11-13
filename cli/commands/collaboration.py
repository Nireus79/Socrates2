"""
Collaboration command module.

Handles team collaboration features:
- /collaboration status - Show active collaborators
- /collaboration activity - Show recent activity
- /collaboration members - Show team members on project
"""

from typing import Any, Dict, List

from cli.base import CommandHandler
from cli.utils import table_formatter


class CollaborationCommandHandler(CommandHandler):
    """Handler for team collaboration commands"""

    command_name = "collaboration"
    description = "Team collaboration: status, activity, members"
    help_text = """
[bold cyan]Collaboration Commands:[/bold cyan]

  [yellow]/collaboration status[/yellow]      Show active collaborators
  [yellow]/collaboration activity[/yellow]    Show recent activity
  [yellow]/collaboration members[/yellow]     Show team members on project

[bold]Examples:[/bold]
  /collaboration status                  # Who's working now?
  /collaboration activity                # Recent changes
  /collaboration members                 # Show team members
"""

    def handle(self, args: List[str]) -> None:
        """Route collaboration commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "status":
            self.status()
        elif subcommand == "activity":
            self.activity()
        elif subcommand == "members":
            self.members()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.show_help()

    def status(self) -> None:
        """Show active collaborators on current project"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading collaboration status...[/cyan]")

        try:
            result = self.api.get_collaboration_status(project.get("id"))

            if not result.get("success"):
                error = result.get("error") or "Failed to load status"
                self.print_error(error)
                return

            data = result.get("data", {})

            self.console.print(f"\n[bold cyan]Active Collaborators[/bold cyan]\n")

            # Show current user
            current_user = self.get_current_user()
            if current_user:
                self.console.print(f"[green]●[/green] {current_user.get('name', 'You')} (You)")

            # Show other active members
            active_members = data.get("active_members", [])
            if not active_members:
                self.console.print("[dim]No other collaborators online[/dim]")
            else:
                for member in active_members:
                    name = member.get("name", "Unknown")
                    role = member.get("role", "member")
                    last_activity = member.get("last_activity", "Recently")
                    self.console.print(f"[yellow]●[/yellow] {name} ({role}) - {last_activity}")

            # Show project info
            self.console.print(f"\n[bold]Project: {project.get('name')}[/bold]")
            project_type = "Team" if project.get("team_id") else "Solo"
            self.console.print(f"[dim]Type: {project_type}[/dim]")

            # Show session info if active
            session = self.config.get("current_session")
            if session:
                session_contributors = data.get("session_contributors", [])
                if session_contributors:
                    self.console.print(f"\n[bold]Active Session Contributors:[/bold]")
                    for contributor in session_contributors:
                        name = contributor.get("name", "Unknown")
                        answers = contributor.get("answer_count", 0)
                        self.console.print(f"  [cyan]•[/cyan] {name} ({answers} answers)")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def activity(self) -> None:
        """Show recent collaboration activity"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading activity...[/cyan]")

        try:
            result = self.api.get_collaboration_activity(project.get("id"))

            if not result.get("success"):
                error = result.get("error") or "Failed to load activity"
                self.print_error(error)
                return

            activities = result.get("data", {}).get("activities", [])

            if not activities:
                self.console.print("[yellow]No recent activity[/yellow]")
                return

            # Format and display activity
            table = table_formatter.format_activity_table(activities)
            self.console.print(table)

            self.console.print(f"\n[cyan]Total activities: {len(activities)}[/cyan]")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def members(self) -> None:
        """Show team members on current project"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[cyan]Loading team members...[/cyan]")

        try:
            result = self.api.get_project_members(project.get("id"))

            if not result.get("success"):
                error = result.get("error") or "Failed to load members"
                self.print_error(error)
                return

            members = result.get("data", {}).get("members", [])

            if not members:
                self.console.print("[yellow]No members in this project[/yellow]")
                self.console.print("[yellow]Use /project add-member to invite someone[/yellow]")
                return

            # Format and display members
            table = table_formatter.format_member_table(members)
            self.console.print(table)

            self.console.print(f"\n[cyan]Total members: {len(members)}[/cyan]")

            # Show roles info
            self.console.print(f"\n[dim]Roles:[/dim]")
            self.console.print("[dim]  Owner: Full control[/dim]")
            self.console.print("[dim]  Contributor: Can edit[/dim]")
            self.console.print("[dim]  Reviewer: Can comment[/dim]")
            self.console.print("[dim]  Viewer: Read-only[/dim]")

        except Exception as e:
            self.print_error(f"Error: {e}")
