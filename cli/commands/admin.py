"""Admin and system commands.

/admin health - Check system health
/admin stats - Show system statistics
/admin users - Manage users
/admin config - System configuration
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import table_formatter


class AdminCommandHandler(CommandHandler):
    """Handler for admin and system commands"""

    command_name = "admin"
    description = "Admin: health, stats, users, config"
    help_text = """
[bold cyan]Admin Commands:[/bold cyan]
  [yellow]/admin health[/yellow]      Check system health
  [yellow]/admin stats[/yellow]       Show system statistics
  [yellow]/admin users[/yellow]       Manage users
  [yellow]/admin config[/yellow]      System configuration
"""

    def handle(self, args: List[str]) -> None:
        """Route admin commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "health":
            self.health()
        elif subcommand == "stats":
            self.stats()
        elif subcommand == "users":
            self.users(args[1:])
        elif subcommand == "config":
            self.config(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def health(self) -> None:
        """Check system health"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[cyan]Checking system health...[/cyan]")

        try:
            result = self.api.get_system_health()

            if not result.get("success"):
                self.print_error("Failed to check system health")
                return

            health = result.get("data", {})

            self.console.print("[bold cyan]System Health Status[/bold cyan]\n")

            # Database status
            db_status = health.get("database", {})
            db_color = "green" if db_status.get("healthy") else "red"
            self.console.print(f"[bold]Database:[/bold] [{db_color}]{db_status.get('status', 'unknown')}[/{db_color}]")
            self.console.print(f"  Response time: {db_status.get('response_time', 'N/A')}ms\n")

            # API status
            api_status = health.get("api", {})
            api_color = "green" if api_status.get("healthy") else "red"
            self.console.print(f"[bold]API:[/bold] [{api_color}]{api_status.get('status', 'unknown')}[/{api_color}]")
            self.console.print(f"  Uptime: {api_status.get('uptime', 'N/A')}\n")

            # LLM status
            llm_status = health.get("llm", {})
            llm_color = "green" if llm_status.get("healthy") else "yellow"
            self.console.print(f"[bold]LLM Service:[/bold] [{llm_color}]{llm_status.get('status', 'unknown')}[/{llm_color}]")
            self.console.print(f"  Latency: {llm_status.get('latency', 'N/A')}ms\n")

            # Storage status
            storage_status = health.get("storage", {})
            storage_color = "green" if storage_status.get("healthy") else "yellow"
            self.console.print(f"[bold]Storage:[/bold] [{storage_color}]{storage_status.get('status', 'unknown')}[/{storage_color}]")
            self.console.print(f"  Available: {storage_status.get('available', 'N/A')}GB\n")

            # Overall status
            overall = health.get("overall_status", "unknown")
            overall_color = "green" if overall == "healthy" else "yellow" if overall == "degraded" else "red"
            self.console.print(f"[bold]Overall:[/bold] [{overall_color}]{overall}[/{overall_color}]")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def stats(self) -> None:
        """Show system statistics"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[cyan]Loading system statistics...[/cyan]")

        try:
            result = self.api.get_system_stats()

            if not result.get("success"):
                self.print_error("Failed to load statistics")
                return

            stats = result.get("data", {})

            self.console.print("[bold cyan]System Statistics[/bold cyan]\n")

            # User stats
            user_stats = stats.get("users", {})
            self.console.print("[bold]Users:[/bold]")
            self.console.print(f"  Total: {user_stats.get('total', 0)}")
            self.console.print(f"  Active (30d): {user_stats.get('active_30d', 0)}")
            self.console.print(f"  New (7d): {user_stats.get('new_7d', 0)}\n")

            # Project stats
            project_stats = stats.get("projects", {})
            self.console.print("[bold]Projects:[/bold]")
            self.console.print(f"  Total: {project_stats.get('total', 0)}")
            self.console.print(f"  Active: {project_stats.get('active', 0)}")
            self.console.print(f"  Archived: {project_stats.get('archived', 0)}\n")

            # Session stats
            session_stats = stats.get("sessions", {})
            self.console.print("[bold]Sessions:[/bold]")
            self.console.print(f"  Total: {session_stats.get('total', 0)}")
            self.console.print(f"  Active: {session_stats.get('active', 0)}")
            self.console.print(f"  Avg duration: {session_stats.get('avg_duration', 'N/A')}min\n")

            # API usage
            api_stats = stats.get("api", {})
            self.console.print("[bold]API Usage:[/bold]")
            self.console.print(f"  Requests (24h): {api_stats.get('requests_24h', 0)}")
            self.console.print(f"  Avg response: {api_stats.get('avg_response_time', 0)}ms")
            self.console.print(f"  Error rate: {api_stats.get('error_rate', 0)}%\n")

            # Storage stats
            storage_stats = stats.get("storage", {})
            self.console.print("[bold]Storage:[/bold]")
            self.console.print(f"  Used: {storage_stats.get('used', 'N/A')}GB")
            self.console.print(f"  Total: {storage_stats.get('total', 'N/A')}GB")
            self.console.print(f"  Utilization: {storage_stats.get('utilization', 'N/A')}%")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def users(self, args: List[str]) -> None:
        """Manage users"""
        user = self.ensure_authenticated()
        if not user:
            return

        if not args:
            self.list_users()
        else:
            subcommand = args[0].lower()
            if subcommand == "list":
                self.list_users()
            elif subcommand == "info":
                self.user_info(args[1:])
            elif subcommand == "role":
                self.change_user_role(args[1:])
            elif subcommand == "disable":
                self.disable_user(args[1:])
            elif subcommand == "enable":
                self.enable_user(args[1:])
            else:
                self.print_error(f"Unknown subcommand: {subcommand}")

    def list_users(self) -> None:
        """List all users"""
        self.console.print("[cyan]Loading users...[/cyan]")

        try:
            result = self.api.list_all_users()

            if not result.get("success"):
                self.print_error("Failed to load users")
                return

            users = result.get("data", {}).get("users", [])

            if not users:
                self.console.print("[yellow]No users found[/yellow]")
                return

            self.console.print("[bold cyan]Users[/bold cyan]\n")

            for user in users:
                email = user.get("email", "N/A")
                role = user.get("role", "user")
                status = user.get("status", "active")
                created = user.get("created_at", "N/A")

                status_color = "green" if status == "active" else "red"
                self.console.print(f"[yellow]• {email}[/yellow] [{status_color}]{status}[/{status_color}]")
                self.console.print(f"  Role: {role} | Created: {created}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def user_info(self, args: List[str]) -> None:
        """Show user information"""
        if not args:
            self.console.print("[yellow]Usage: /admin users info <email>[/yellow]")
            return

        email = args[0]

        try:
            result = self.api.get_user_info(email)

            if not result.get("success"):
                self.print_error("User not found")
                return

            user = result.get("data")

            from cli.utils.table_formatter import format_key_value_table

            user_data = {
                "Email": user.get("email", "N/A"),
                "Role": user.get("role", "N/A"),
                "Status": user.get("status", "N/A"),
                "Created": user.get("created_at", "N/A"),
                "Last Login": user.get("last_login", "N/A"),
                "Projects": user.get("project_count", 0),
                "Teams": user.get("team_count", 0),
            }

            table = format_key_value_table(user_data)
            self.console.print(table)

        except Exception as e:
            self.print_error(f"Error: {e}")

    def change_user_role(self, args: List[str]) -> None:
        """Change user role"""
        if len(args) < 2:
            self.console.print("[yellow]Usage: /admin users role <email> <role>[/yellow]")
            return

        email = args[0]
        new_role = args[1]

        try:
            result = self.api.change_user_role(email, new_role)

            if result.get("success"):
                self.print_success(f"User role changed: {email} → {new_role}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def disable_user(self, args: List[str]) -> None:
        """Disable user account"""
        if not args:
            self.console.print("[yellow]Usage: /admin users disable <email>[/yellow]")
            return

        email = args[0]

        try:
            result = self.api.disable_user(email)

            if result.get("success"):
                self.print_success(f"User disabled: {email}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def enable_user(self, args: List[str]) -> None:
        """Enable user account"""
        if not args:
            self.console.print("[yellow]Usage: /admin users enable <email>[/yellow]")
            return

        email = args[0]

        try:
            result = self.api.enable_user(email)

            if result.get("success"):
                self.print_success(f"User enabled: {email}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def config(self, args: List[str]) -> None:
        """System configuration"""
        user = self.ensure_authenticated()
        if not user:
            return

        if not args:
            self.show_config()
        else:
            subcommand = args[0].lower()
            if subcommand == "show":
                self.show_config()
            elif subcommand == "set":
                self.set_config(args[1:])
            else:
                self.print_error(f"Unknown subcommand: {subcommand}")

    def show_config(self) -> None:
        """Show system configuration"""
        self.console.print("[cyan]Loading configuration...[/cyan]")

        try:
            result = self.api.get_system_config()

            if not result.get("success"):
                self.print_error("Failed to load configuration")
                return

            config = result.get("data", {})

            self.console.print("[bold cyan]System Configuration[/bold cyan]\n")

            # Display config sections
            for section, values in config.items():
                self.console.print(f"[bold]{section.upper()}:[/bold]")
                if isinstance(values, dict):
                    for key, value in values.items():
                        self.console.print(f"  {key}: {value}")
                else:
                    self.console.print(f"  {values}")
                self.console.print()

        except Exception as e:
            self.print_error(f"Error: {e}")

    def set_config(self, args: List[str]) -> None:
        """Set configuration value"""
        if len(args) < 2:
            self.console.print("[yellow]Usage: /admin config set <key> <value>[/yellow]")
            return

        key = args[0]
        value = " ".join(args[1:])

        try:
            result = self.api.set_system_config(key, value)

            if result.get("success"):
                self.print_success(f"Configuration updated: {key}")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
