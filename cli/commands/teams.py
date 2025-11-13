"""
Team management command module.

Handles team-related operations (team-first design):
- /team create - Create new team
- /team list - List all teams you belong to
- /team info - Show team details
- /team invite - Invite user to team
- /team member-list - List team members
- /team member-add - Add member to team
- /team member-remove - Remove member from team
- /team member-role - Change member role
"""

from typing import Any, Dict, List
from rich.prompt import Prompt

from cli.base import CommandHandler
from cli.utils import prompts, table_formatter, constants


class TeamCommandHandler(CommandHandler):
    """Handler for team management commands"""

    command_name = "team"
    description = "Team management: create, invite, list, member management"
    help_text = """
[bold cyan]Team Commands:[/bold cyan]

  [yellow]/team create <name>[/yellow]            Create new team
  [yellow]/team list[/yellow]                     List all your teams
  [yellow]/team info <team_id>[/yellow]           Show team details
  [yellow]/team invite <email> <team_id>[/yellow] Invite person to team
  [yellow]/team member-list <team_id>[/yellow]    List team members
  [yellow]/team member-add <email> <team_id>[/yellow] Add member
  [yellow]/team member-remove <email> <team_id>[/yellow] Remove member
  [yellow]/team member-role <email> <team_id> <role>[/yellow] Change role

[bold]Examples:[/bold]
  /team create "Product Team"           # Create team
  /team list                            # Show your teams
  /team invite alice@example.com team_id  # Invite member
  /team member-list team_id             # Show members
"""

    def handle(self, args: List[str]) -> None:
        """Route team commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "create":
            self.create(args[1:])
        elif subcommand == "list":
            self.list()
        elif subcommand == "info":
            self.info(args[1:])
        elif subcommand == "invite":
            self.invite(args[1:])
        elif subcommand == "member-list":
            self.member_list(args[1:])
        elif subcommand == "member-add":
            self.member_add(args[1:])
        elif subcommand == "member-remove":
            self.member_remove(args[1:])
        elif subcommand == "member-role":
            self.member_role(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.show_help()

    def create(self, args: List[str]) -> None:
        """Create new team"""
        if not self.ensure_authenticated():
            return

        self.console.print("[bold cyan]Create New Team[/bold cyan]\n")

        try:
            # Get team name
            if args:
                name = " ".join(args)
            else:
                name = prompts.prompt_text(
                    self.console,
                    "Team name",
                    default="My Team"
                )

            description = prompts.prompt_text(
                self.console,
                "Description (optional)",
                default=""
            )

            # Create team via API
            self.console.print("\n[cyan]Creating team...[/cyan]")

            result = self.api.create_team(
                name=name,
                description=description
            )

            if result.get("success"):
                team = result.get("data")
                team_id = team.get("id")
                self.print_success(f"Team created: {name}")
                self.console.print(f"[cyan]Team ID: {team_id}[/cyan]")
                self.console.print(f"[yellow]Use /team invite to add members[/yellow]")

                # Set as current team
                self.config["current_team"] = team

            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Failed to create team: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Team creation cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def list(self) -> None:
        """List all teams user belongs to"""
        if not self.ensure_authenticated():
            return

        self.console.print("[cyan]Loading teams...[/cyan]")

        try:
            result = self.api.get_teams()

            if not result.get("success"):
                error = result.get("error") or "Failed to load teams"
                self.print_error(error)
                return

            teams = result.get("data", {}).get("teams", [])

            if not teams:
                self.console.print("[yellow]You are not part of any teams yet[/yellow]")
                self.console.print("[yellow]Use /team create to start one[/yellow]")
                return

            # Format and display teams
            table = table_formatter.format_team_table(teams)
            self.console.print(table)

            self.console.print(f"\n[cyan]Total teams: {len(teams)}[/cyan]")

        except Exception as e:
            self.print_error(f"Error loading teams: {e}")

    def info(self, args: List[str]) -> None:
        """Show team information"""
        if not self.ensure_authenticated():
            return

        if not args:
            team = self.ensure_team_context()
            if not team:
                self.console.print("[yellow]Usage: /team info <team_id> or select a team first[/yellow]")
                return
            team_id = team.get("id")
        else:
            team_id = args[0]

        try:
            result = self.api.get_team(team_id)

            if not result.get("success"):
                self.print_error("Team not found")
                return

            team = result.get("data")

            self.console.print(f"[bold cyan]Team Information[/bold cyan]\n")

            from cli.utils.table_formatter import format_key_value_table

            team_data = {
                "ID": team.get("id", "N/A"),
                "Name": team.get("name", "Unknown"),
                "Description": team.get("description", "N/A"),
                "Created": team.get("created_at", "N/A"),
                "Members": team.get("member_count", 0),
                "Projects": team.get("project_count", 0),
                "Your Role": team.get("your_role", "member"),
            }

            table = format_key_value_table(team_data)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def invite(self, args: List[str]) -> None:
        """Invite user to team"""
        if not self.ensure_authenticated():
            return

        team = self.ensure_team_context()
        if not team:
            if len(args) < 2:
                self.console.print("[yellow]Usage: /team invite <email> <team_id>[/yellow]")
                return
            email = args[0]
            team_id = args[1]
        else:
            if not args:
                email = prompts.prompt_email(self.console, "Invite email")
            else:
                email = args[0]
            team_id = team.get("id")

        try:
            self.console.print("[cyan]Sending invitation...[/cyan]")

            result = self.api.invite_team_member(team_id, email)

            if result.get("success"):
                self.print_success(f"Invitation sent to {email}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def member_list(self, args: List[str]) -> None:
        """List team members"""
        if not self.ensure_authenticated():
            return

        team = self.ensure_team_context()
        if not team:
            if not args:
                self.console.print("[yellow]Usage: /team member-list <team_id>[/yellow]")
                return
            team_id = args[0]
        else:
            team_id = team.get("id")

        try:
            result = self.api.get_team_members(team_id)

            if not result.get("success"):
                self.print_error("Failed to load members")
                return

            members = result.get("data", {}).get("members", [])

            if not members:
                self.console.print("[yellow]No members in this team[/yellow]")
                return

            table = table_formatter.format_member_table(members)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def member_add(self, args: List[str]) -> None:
        """Add member to team"""
        if not self.ensure_authenticated():
            return

        team = self.ensure_team_context()
        if not team:
            if len(args) < 2:
                self.console.print("[yellow]Usage: /team member-add <email> <team_id>[/yellow]")
                return
            email = args[0]
            team_id = args[1]
        else:
            if not args:
                email = prompts.prompt_email(self.console, "Member email")
            else:
                email = args[0]
            team_id = team.get("id")

        # Get role
        role = prompts.prompt_choice(
            self.console,
            "Member role",
            ["member", "reviewer", "viewer"],
            default="member"
        )

        try:
            self.console.print("[cyan]Adding member...[/cyan]")

            result = self.api.add_team_member(team_id, email, role)

            if result.get("success"):
                self.print_success(f"Added {email} as {role}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def member_remove(self, args: List[str]) -> None:
        """Remove member from team"""
        if not self.ensure_authenticated():
            return

        team = self.ensure_team_context()
        if not team:
            if len(args) < 2:
                self.console.print("[yellow]Usage: /team member-remove <email> <team_id>[/yellow]")
                return
            email = args[0]
            team_id = args[1]
        else:
            if not args:
                email = prompts.prompt_email(self.console, "Member email")
            else:
                email = args[0]
            team_id = team.get("id")

        if not prompts.prompt_confirm(
            self.console,
            f"Remove {email} from team?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            self.console.print("[cyan]Removing member...[/cyan]")

            result = self.api.remove_team_member(team_id, email)

            if result.get("success"):
                self.print_success(f"Removed {email}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def member_role(self, args: List[str]) -> None:
        """Change member's role in team"""
        if not self.ensure_authenticated():
            return

        team = self.ensure_team_context()
        if not team:
            if len(args) < 3:
                self.console.print(
                    "[yellow]Usage: /team member-role <email> <team_id> <role>[/yellow]"
                )
                return
            email = args[0]
            team_id = args[1]
            role = args[2]
        else:
            if len(args) < 2:
                email = prompts.prompt_email(self.console, "Member email")
                role = prompts.prompt_choice(
                    self.console,
                    "New role",
                    ["member", "reviewer", "viewer"],
                    default="member"
                )
            else:
                email = args[0]
                role = args[1] if len(args) > 1 else "member"

            team_id = team.get("id")

        try:
            self.console.print("[cyan]Updating member role...[/cyan]")

            result = self.api.update_team_member_role(team_id, email, role)

            if result.get("success"):
                self.print_success(f"Updated {email} role to {role}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
