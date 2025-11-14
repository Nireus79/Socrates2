"""
Project management command module.

Handles project-related operations:
- /project create - Create new project (domain-aware, team-ready)
- /project list - List all projects
- /project select - Select project to work with
- /project info - Show current project details
- /project manage - Unified interface for archive/restore/destroy
- /project add-member - Add team member to project
- /project remove-member - Remove team member
- /project member-list - List project members
- /project share - Share project with team
"""

from typing import Any, Dict, List, Optional
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from cli.base import CommandHandler
from cli.utils import prompts, table_formatter, constants


class ProjectCommandHandler(CommandHandler):
    """Handler for project management commands"""

    command_name = "project"
    description = "Project management: create, list, select, manage, archive, restore, destroy"
    help_text = """
[bold cyan]Project Commands:[/bold cyan]

  [yellow]/project create[/yellow]              Create new project (domain-aware)
  [yellow]/project list[/yellow]                List all your projects
  [yellow]/project select <id>[/yellow]         Select project to work with
  [yellow]/project info[/yellow]                Show current project details
  [yellow]/project manage <id>[/yellow]         Unified management (archive/restore/destroy)

[bold cyan]Team & Collaboration:[/bold cyan]

  [yellow]/project add-member <email>[/yellow]      Add team member
  [yellow]/project remove-member <email>[/yellow]   Remove team member
  [yellow]/project member-list[/yellow]             List team members
  [yellow]/project share <team_id>[/yellow]         Share with team

[bold]Examples:[/bold]
  /project create                       # Create new project
  /project list                         # Show all projects
  /project select 1                     # Select first project
  /project manage 1                     # Open management interface
  /project add-member alice@example.com # Add collaborator
"""

    def handle(self, args: List[str]) -> None:
        """Route project commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "create":
            self.create()
        elif subcommand == "list":
            self.list()
        elif subcommand == "select":
            self.select(args[1:])
        elif subcommand == "info":
            self.info()
        elif subcommand == "manage":
            self.manage(args[1:])
        elif subcommand == "add-member":
            self.add_member(args[1:])
        elif subcommand == "remove-member":
            self.remove_member(args[1:])
        elif subcommand == "member-list":
            self.member_list()
        elif subcommand == "share":
            self.share(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.show_help()

    def create(self) -> None:
        """Create new project with domain selection"""
        if not self.ensure_authenticated():
            return

        self.console.print("[bold cyan]Create New Project[/bold cyan]\n")

        try:
            # Step 1: Select domain (for domain-awareness)
            self.console.print("[bold]Step 1: Choose Project Domain[/bold]\n")

            domain_list = []
            for domain_key, domain_info in sorted(constants.DOMAINS.items()):
                domain_list.append({
                    "id": domain_key,
                    "name": f"{domain_info['icon']} {domain_info['name']}",
                    "description": domain_info['description']
                })

            selected_domain = prompts.prompt_for_table_selection(
                self.console,
                domain_list,
                ["name", "description"],
                id_column="id",
                title="Select Domain"
            )

            if not selected_domain:
                self.console.print("[yellow]Project creation cancelled[/yellow]")
                return

            domain = selected_domain["id"]
            self.console.print(f"[green]✓ Selected domain: {selected_domain['name']}[/green]\n")

            # Step 2: Get project details
            self.console.print("[bold]Step 2: Project Details[/bold]\n")

            name = prompts.prompt_text(
                self.console,
                "Project name",
                default="My Project"
            )

            description = prompts.prompt_text(
                self.console,
                "Description (optional)",
                default=""
            )

            # Step 3: Solo or team?
            self.console.print(f"\n[bold]Step 3: Working Arrangement[/bold]\n")

            solo_or_team = prompts.prompt_choice(
                self.console,
                "Solo or team project?",
                ["solo", "team"],
                default="solo"
            )

            team_id = None
            if solo_or_team == "team":
                self.print_info("Team feature requires team selection")
                # For now, note that team setup happens later
                self.print_info("You can add team members after project creation")

            # Create project via API
            self.console.print("\n[cyan]Creating project...[/cyan]")

            result = self.api.create_project(
                name=name,
                description=description,
                domain=domain,
                is_team_project=(solo_or_team == "team")
            )

            if result.get("success"):
                project = result.get("data")
                self.print_success(f"Project created: {name}")
                self.console.print(f"[cyan]Project ID: {project.get('id')}[/cyan]")

                # Auto-select the new project
                self.config["current_project"] = project

            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Failed to create project: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Project creation cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Error: {e}")

    def list(self) -> None:
        """List all projects"""
        if not self.ensure_authenticated():
            return

        self.console.print("[cyan]Loading projects...[/cyan]")

        try:
            result = self.api.get_projects()

            if not result.get("success"):
                error = result.get("error") or "Failed to load projects"
                self.print_error(error)
                return

            projects = result.get("data", {}).get("projects", [])

            if not projects:
                self.console.print("[yellow]No projects yet. Use /project create to start[/yellow]")
                return

            # Format and display projects
            table = table_formatter.format_project_table(projects)
            self.console.print(table)

            self.console.print(f"\n[cyan]Total projects: {len(projects)}[/cyan]")

        except Exception as e:
            self.print_error(f"Error loading projects: {e}")

    def select(self, args: List[str]) -> None:
        """Select a project to work with"""
        if not self.ensure_authenticated():
            return

        self.console.print("[cyan]Loading projects...[/cyan]")

        try:
            result = self.api.list_projects()

            if not result.get("success"):
                self.print_error("Failed to load projects")
                return

            projects = result.get("data", {}).get("projects", [])

            if not projects:
                self.console.print("[yellow]No projects available[/yellow]")
                return

            # If no args provided, show interactive selection
            if not args:
                selected_project = prompts.prompt_for_table_selection(
                    self.console,
                    projects,
                    ["name", "domain", "status"],
                    id_column="id",
                    title="Select Project"
                )

                if not selected_project:
                    self.console.print("Project selection cancelled")
                    return
            else:
                # Try to parse input as number or UUID
                user_input = args[0]

                try:
                    # Try as number
                    num = int(user_input)
                    if 1 <= num <= len(projects):
                        selected_project = projects[num - 1]
                    else:
                        self.print_error(f"Invalid project number (1-{len(projects)})")
                        return
                except ValueError:
                    # Try as partial or full UUID
                    selected_project = None
                    for proj in projects:
                        if str(proj.get("id")).startswith(user_input):
                            selected_project = proj
                            break

                    if not selected_project:
                        self.print_error(f"Project not found: {user_input}")
                        return

            # Select the project
            self.config["current_project"] = selected_project
            self.config["current_session"] = None

            project_name = selected_project.get("name")
            self.print_success(f"Selected project: {project_name}")

            # Show brief info
            domain = selected_project.get("domain", "unknown")
            status = selected_project.get("status", "unknown")
            self.console.print(f"Domain: {domain} | Status: {status}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def info(self) -> None:
        """Show current project information"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Project Information[/bold cyan]\n")

        from cli.utils.table_formatter import format_key_value_table

        project_data = {
            "ID": project.get("id", "N/A"),
            "Name": project.get("name", "Unknown"),
            "Domain": project.get("domain", "N/A"),
            "Status": project.get("status", "unknown"),
            "Type": "Team" if project.get("team_id") else "Solo",
            "Created": project.get("created_at", "N/A"),
            "Updated": project.get("updated_at", "N/A"),
            "Description": project.get("description", "N/A"),
        }

        table = format_key_value_table(project_data)
        self.console.print(table)

    def manage(self, args: List[str]) -> None:
        """Unified project management interface (archive/restore/destroy)"""
        if not self.ensure_authenticated():
            return

        if not args:
            # If no args, use current project
            project = self.ensure_project_selected()
            if not project:
                return
            project_id = str(project.get("id"))
        else:
            project_id = args[0]

        try:
            # Get project details
            result = self.api.get_project(project_id)

            if not result.get("success"):
                self.print_error("Project not found")
                return

            project = result.get("data")
            status = project.get("status", "unknown")

            self.console.print(f"\n[bold cyan]Manage Project[/bold cyan]")
            self.console.print(f"[bold]Name:[/bold] {project.get('name')}")
            self.console.print(f"[bold]Status:[/bold] {status}")
            self.console.print(f"[bold]ID:[/bold] {project_id}\n")

            # Determine available actions based on status
            if status == "active":
                actions = {
                    "1": ("Archive (soft delete - reversible)", "archive_project")
                }
            elif status == "archived":
                actions = {
                    "1": ("Restore to active", "restore_project"),
                    "2": ("Permanently destroy (irreversible)", "destroy_project")
                }
            else:
                self.console.print(f"[yellow]No actions available for status: {status}[/yellow]")
                return

            # Show menu
            for key, (label, _) in actions.items():
                self.console.print(f"  [{key}] {label}")
            self.console.print(f"  [back] Cancel\n")

            choice = Prompt.ask(
                "Choose action",
                choices=list(actions.keys()) + ["back"],
                default="back"
            )

            if choice == "back":
                self.console.print("[yellow]Cancelled[/yellow]")
                return

            action_label, action_method = actions[choice]

            # Confirmation
            if action_method == "destroy_project":
                self.console.print("[red bold]⚠ WARNING: This will permanently delete the project![/red bold]")
                self.console.print("[red]This action CANNOT be undone.[/red]\n")

            confirm = prompts.prompt_confirm(
                self.console,
                f"{action_label}?",
                default=False
            )

            if not confirm:
                self.console.print("[yellow]Cancelled[/yellow]")
                return

            # Execute action
            api_method = getattr(self.api, action_method, None)
            if not api_method:
                self.print_error(f"Unknown action: {action_method}")
                return

            result = api_method(project_id)

            if result.get("success"):
                self.print_success(f"{action_label} successful")

                # Clear project selection if it was the current one
                if self.config.get("current_project", {}).get("id") == project_id:
                    self.config["current_project"] = None
                    self.config["current_session"] = None

            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def add_member(self, args: List[str]) -> None:
        """Add team member to project"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            email = prompts.prompt_email(self.console, "Member email")
        else:
            email = args[0]

        # Get role
        role = prompts.prompt_choice(
            self.console,
            "Member role",
            ["contributor", "reviewer", "viewer"],
            default="contributor"
        )

        try:
            self.console.print("[cyan]Adding member...[/cyan]")

            result = self.api.add_project_member(
                project.get("id"),
                email,
                role
            )

            if result.get("success"):
                self.print_success(f"Added {email} as {role}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def remove_member(self, args: List[str]) -> None:
        """Remove team member from project"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            email = prompts.prompt_email(self.console, "Member email")
        else:
            email = args[0]

        if not prompts.prompt_confirm(
            self.console,
            f"Remove {email}?",
            default=False
        ):
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        try:
            self.console.print("[cyan]Removing member...[/cyan]")

            result = self.api.remove_project_member(
                project.get("id"),
                email
            )

            if result.get("success"):
                self.print_success(f"Removed {email}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def member_list(self) -> None:
        """List project members"""
        project = self.ensure_project_selected()
        if not project:
            return

        try:
            result = self.api.get_project_members(project.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load members")
                return

            members = result.get("data", {}).get("members", [])

            if not members:
                self.console.print("[yellow]No members in this project[/yellow]")
                return

            table = table_formatter.format_member_table(members)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def share(self, args: List[str]) -> None:
        """Share project with team"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /project share <team_id>[/yellow]")
            return

        team_id = args[0]

        try:
            self.console.print("[cyan]Sharing project with team...[/cyan]")

            result = self.api.share_project_with_team(
                project.get("id"),
                team_id
            )

            if result.get("success"):
                self.print_success("Project shared with team")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
