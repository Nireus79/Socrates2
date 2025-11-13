"""
Authentication command module.

Handles user authentication operations:
- /auth register - Register new account
- /auth login - Login to existing account
- /auth logout - Logout current user
- /auth whoami - Show current user information
"""

from typing import Any, Dict, List
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from cli.base import CommandHandler
from cli.utils import prompts


class AuthCommandHandler(CommandHandler):
    """Handler for authentication commands"""

    command_name = "auth"
    description = "Authentication: register, login, logout, whoami"
    help_text = """
[bold cyan]Authentication Commands:[/bold cyan]

  [yellow]/auth register[/yellow]     Register new account
  [yellow]/auth login[/yellow]        Login to existing account
  [yellow]/auth logout[/yellow]       Logout from current session
  [yellow]/auth whoami[/yellow]       Show current user information

[bold]Examples:[/bold]
  /auth register                       # Start registration workflow
  /auth login                          # Start login workflow
  /auth logout                         # Sign out
  /auth whoami                         # View your profile
"""

    def handle(self, args: List[str]) -> None:
        """Route authentication commands"""
        if not args:
            self.show_help()
            return

        subcommand = args[0].lower()

        if subcommand == "register":
            self.register()
        elif subcommand == "login":
            self.login()
        elif subcommand == "logout":
            self.logout()
        elif subcommand == "whoami":
            self.whoami()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")
            self.show_help()

    def register(self) -> None:
        """User registration workflow"""
        self.console.print("[bold cyan]User Registration[/bold cyan]\n")

        try:
            # Get user information
            username = prompts.prompt_text(
                self.console,
                "Username",
                default="user"
            )

            name = prompts.prompt_text(
                self.console,
                "First name",
                default="User"
            )

            surname = prompts.prompt_text(
                self.console,
                "Last name",
                default="Account"
            )

            email = prompts.prompt_email(self.console, "Email address")

            password = prompts.prompt_text(
                self.console,
                "Password",
                password=True
            )

            password_confirm = prompts.prompt_text(
                self.console,
                "Confirm password",
                password=True
            )

            if password != password_confirm:
                self.print_error("Passwords do not match")
                return

            # Register via API
            self.console.print("[cyan]Registering...[/cyan]")

            result = self.api.register(username, name, surname, email, password)

            if result.get("success"):
                self.print_success("Registration successful!")
                self.console.print(f"[green]Welcome, {name}![/green]")
                self.console.print("[yellow]Now use /auth login to sign in[/yellow]")
            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Registration failed: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Registration cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Registration error: {e}")

    def login(self) -> None:
        """User login workflow"""
        self.console.print("[bold cyan]User Login[/bold cyan]\n")

        try:
            email = prompts.prompt_email(self.console, "Email address")

            password = prompts.prompt_text(
                self.console,
                "Password",
                password=True
            )

            # Attempt login
            self.console.print("[cyan]Logging in...[/cyan]")

            result = self.api.login(email, password)

            if result.get("success"):
                # Save tokens to config
                access_token = result.get("access_token")
                refresh_token = result.get("refresh_token")
                user_data = result.get("user", {})

                if access_token:
                    self.config["access_token"] = access_token
                    self.api.set_token(access_token)

                if refresh_token:
                    self.config["refresh_token"] = refresh_token
                    self.api.set_refresh_token(refresh_token)

                # Save user info
                self.config["user"] = user_data
                self.config["user_email"] = user_data.get("email")
                self.config["user_id"] = str(user_data.get("id", ""))

                user_name = user_data.get("name", "User")
                self.print_success(f"Logged in successfully!")
                self.console.print(f"[green]Welcome back, {user_name}![/green]")

            else:
                error = result.get("error") or result.get("detail") or "Unknown error"
                self.print_error(f"Login failed: {error}")

        except KeyboardInterrupt:
            self.console.print("[yellow]Login cancelled[/yellow]")
        except Exception as e:
            self.print_error(f"Login error: {e}")

    def logout(self) -> None:
        """User logout workflow"""
        # Confirm logout
        if not prompts.prompt_confirm(
            self.console,
            "Are you sure you want to log out?",
            default=False
        ):
            self.console.print("[yellow]Logout cancelled[/yellow]")
            return

        try:
            # Call logout endpoint
            result = self.api.logout()

            # Clear tokens from config regardless of API result
            self.config["access_token"] = None
            self.config["refresh_token"] = None
            self.config["user"] = None
            self.config["user_email"] = None
            self.config["user_id"] = None
            self.config["current_project"] = None
            self.config["current_session"] = None

            self.api.access_token = None
            self.api.refresh_token = None

            self.print_success("Logged out successfully")
            self.console.print("[yellow]Use /auth login to sign in again[/yellow]")

        except Exception as e:
            self.print_error(f"Logout error: {e}")

    def whoami(self) -> None:
        """Show current user information"""
        # Check if authenticated
        if not self.ensure_authenticated():
            return

        user = self.get_current_user()
        if not user:
            self.print_warning("No user information available")
            return

        # Display user info
        from cli.utils.table_formatter import format_key_value_table

        user_data = {
            "ID": user.get("id", "N/A"),
            "Name": user.get("name", "N/A"),
            "Surname": user.get("surname", "N/A"),
            "Email": user.get("email", "N/A"),
            "Username": user.get("username", "N/A"),
            "Role": user.get("role", "user"),
            "Created": user.get("created_at", "N/A"),
            "Status": user.get("status", "active"),
        }

        table = format_key_value_table(user_data, title="Current User")
        self.console.print(table)
