"""Notifications and alerts commands.

/notifications list - List notifications
/notifications settings - Manage notification settings
/notifications mark-read - Mark notifications as read
/notifications subscribe - Subscribe to notifications
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class NotificationsCommandHandler(CommandHandler):
    """Handler for notification commands"""

    command_name = "notifications"
    description = "Notifications: list, settings, mark-read, subscribe"
    help_text = """
[bold cyan]Notification Commands:[/bold cyan]
  [yellow]/notifications list[/yellow]        List unread notifications
  [yellow]/notifications settings[/yellow]    Manage notification settings
  [yellow]/notifications mark-read[/yellow]   Mark as read
  [yellow]/notifications subscribe[/yellow]   Subscribe to alerts
"""

    def handle(self, args: List[str]) -> None:
        """Route notification commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "settings":
            self.settings()
        elif subcommand == "mark-read":
            self.mark_read(args[1:])
        elif subcommand == "subscribe":
            self.subscribe(args[1:])
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List notifications"""
        user = self.ensure_authenticated()
        if not user:
            return

        # Get filter type
        filter_type = prompts.prompt_choice(
            self.console,
            "Show notifications",
            ["unread", "all", "today", "this-week"],
            default="unread"
        )

        self.console.print("[cyan]Loading notifications...[/cyan]")

        try:
            result = self.api.list_notifications(user.get("id"), filter=filter_type)

            if not result.get("success"):
                self.print_error("Failed to load notifications")
                return

            notifications = result.get("data", {}).get("notifications", [])

            if not notifications:
                self.console.print("[yellow]No notifications[/yellow]")
                return

            self.console.print("[bold cyan]Notifications[/bold cyan]\n")

            for notif in notifications:
                title = notif.get("title", "Notification")
                message = notif.get("message", "")
                notif_type = notif.get("type", "info")
                created = notif.get("created_at", "N/A")
                read = notif.get("read", False)

                # Style based on type
                type_color = {
                    "error": "red",
                    "warning": "yellow",
                    "success": "green",
                    "info": "cyan"
                }.get(notif_type, "white")

                read_status = " " if read else "●"
                self.console.print(f"{read_status} [{type_color}]{title}[/{type_color}]")
                self.console.print(f"  {message}")
                self.console.print(f"  [dim]{created}[/dim]\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def settings(self) -> None:
        """Manage notification settings"""
        user = self.ensure_authenticated()
        if not user:
            return

        self.console.print("[bold cyan]Notification Settings[/bold cyan]\n")

        try:
            result = self.api.get_notification_settings(user.get("id"))

            if not result.get("success"):
                self.print_error("Failed to load settings")
                return

            settings = result.get("data", {})

            # Display current settings
            email = settings.get("email_notifications", {})
            self.console.print("[bold]Email Notifications:[/bold]")
            self.console.print(f"  Session updates: {'On' if email.get('session_updates') else 'Off'}")
            self.console.print(f"  Team invitations: {'On' if email.get('team_invitations') else 'Off'}")
            self.console.print(f"  Project updates: {'On' if email.get('project_updates') else 'Off'}")
            self.console.print(f"  Code generation: {'On' if email.get('code_generation') else 'Off'}")
            self.console.print(f"  Quality alerts: {'On' if email.get('quality_alerts') else 'Off'}\n")

            push = settings.get("push_notifications", {})
            self.console.print("[bold]Push Notifications:[/bold]")
            self.console.print(f"  Session updates: {'On' if push.get('session_updates') else 'Off'}")
            self.console.print(f"  Team activity: {'On' if push.get('team_activity') else 'Off'}")
            self.console.print(f"  Mentions: {'On' if push.get('mentions') else 'Off'}\n")

            # Ask to modify
            modify = prompts.prompt_confirm(
                self.console,
                "Modify settings?",
                default=False
            )

            if modify:
                self.update_settings(user.get("id"))

        except Exception as e:
            self.print_error(f"Error: {e}")

    def update_settings(self, user_id: str) -> None:
        """Update notification settings"""
        setting_type = prompts.prompt_choice(
            self.console,
            "Notification type",
            ["email", "push"],
            default="email"
        )

        if setting_type == "email":
            notification = prompts.prompt_choice(
                self.console,
                "Email notification",
                ["session_updates", "team_invitations", "project_updates", "code_generation", "quality_alerts"],
                default="session_updates"
            )
        else:
            notification = prompts.prompt_choice(
                self.console,
                "Push notification",
                ["session_updates", "team_activity", "mentions"],
                default="session_updates"
            )

        enabled = prompts.prompt_confirm(
            self.console,
            f"Enable {notification}?",
            default=True
        )

        try:
            result = self.api.update_notification_setting(
                user_id,
                setting_type=setting_type,
                notification=notification,
                enabled=enabled
            )

            if result.get("success"):
                self.print_success("Settings updated")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def mark_read(self, args: List[str]) -> None:
        """Mark notifications as read"""
        user = self.ensure_authenticated()
        if not user:
            return

        if not args:
            # Mark all as read
            mark_all = prompts.prompt_confirm(
                self.console,
                "Mark all notifications as read?",
                default=True
            )

            if not mark_all:
                return

            try:
                result = self.api.mark_all_notifications_read(user.get("id"))

                if result.get("success"):
                    self.print_success("All notifications marked as read")
                else:
                    error = result.get("error") or "Unknown error"
                    self.print_error(f"Failed: {error}")

            except Exception as e:
                self.print_error(f"Error: {e}")
        else:
            # Mark specific notification as read
            notif_id = args[0]

            try:
                result = self.api.mark_notification_read(notif_id)

                if result.get("success"):
                    self.print_success("Notification marked as read")
                else:
                    error = result.get("error") or "Unknown error"
                    self.print_error(f"Failed: {error}")

            except Exception as e:
                self.print_error(f"Error: {e}")

    def subscribe(self, args: List[str]) -> None:
        """Subscribe to notifications"""
        user = self.ensure_authenticated()
        if not user:
            return

        if not args:
            # Interactive subscription
            self.console.print("[bold cyan]Subscribe to Notifications[/bold cyan]\n")

            # Get subscription type
            sub_type = prompts.prompt_choice(
                self.console,
                "Notification type",
                ["project", "team", "general"],
                default="project"
            )

            # Get channel
            channel = prompts.prompt_choice(
                self.console,
                "Delivery channel",
                ["email", "push", "in-app"],
                default="email"
            )

            # Get events
            if sub_type == "project":
                events = prompts.select_multiple_from_list(
                    self.console,
                    "Events",
                    ["session-started", "session-ended", "code-generated", "spec-approved"],
                    "Select events to subscribe to"
                )
            elif sub_type == "team":
                events = prompts.select_multiple_from_list(
                    self.console,
                    "Events",
                    ["member-joined", "member-left", "project-shared", "announcement"],
                    "Select events to subscribe to"
                )
            else:
                events = prompts.select_multiple_from_list(
                    self.console,
                    "Events",
                    ["product-updates", "feature-announcements", "maintenance"],
                    "Select events to subscribe to"
                )
        else:
            sub_type = args[0]
            channel = args[1] if len(args) > 1 else "email"
            events = args[2:] if len(args) > 2 else []

        try:
            result = self.api.subscribe_to_notifications(
                user.get("id"),
                sub_type=sub_type,
                channel=channel,
                events=events
            )

            if result.get("success"):
                self.print_success(f"Subscribed to {sub_type} notifications")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
