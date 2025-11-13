"""Project export commands.

/export list - List available export formats
/export generate - Generate export
/export download - Download exported project
/export schedule - Schedule recurring exports
"""

from typing import List
from cli.base import CommandHandler
from cli.utils import prompts, table_formatter


class ExportCommandHandler(CommandHandler):
    """Handler for project export commands"""

    command_name = "export"
    description = "Export: list, generate, download, schedule"
    help_text = """
[bold cyan]Export Commands:[/bold cyan]
  [yellow]/export list[/yellow]              List available export formats
  [yellow]/export generate <format>[/yellow] Generate export
  [yellow]/export download <id>[/yellow]     Download exported project
  [yellow]/export schedule[/yellow]          Schedule recurring export
"""

    def handle(self, args: List[str]) -> None:
        """Route export commands"""
        if not args:
            self.list()
            return

        subcommand = args[0].lower()

        if subcommand == "list":
            self.list()
        elif subcommand == "generate":
            self.generate(args[1:])
        elif subcommand == "download":
            self.download(args[1:])
        elif subcommand == "schedule":
            self.schedule()
        else:
            self.print_error(f"Unknown subcommand: {subcommand}")

    def list(self) -> None:
        """List available export formats"""
        project = self.ensure_project_selected()
        if not project:
            return

        domain = project.get("domain", "general")
        self.console.print(f"[cyan]Loading export formats for {domain}...[/cyan]")

        try:
            result = self.api.list_export_formats(domain)

            if not result.get("success"):
                self.print_error("Failed to load export formats")
                return

            formats = result.get("data", {}).get("formats", [])

            if not formats:
                self.console.print("[yellow]No export formats available[/yellow]")
                return

            self.console.print("[bold cyan]Available Export Formats[/bold cyan]\n")

            for fmt in formats:
                name = fmt.get("name", "Unknown")
                description = fmt.get("description", "")
                file_type = fmt.get("file_type", "N/A")
                size_estimate = fmt.get("size_estimate", "Unknown")

                self.console.print(f"[yellow]• {name}[/yellow]")
                self.console.print(f"  {description}")
                self.console.print(f"  Type: {file_type} | Est. Size: {size_estimate}\n")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def generate(self, args: List[str]) -> None:
        """Generate project export"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            # Show list and let user select
            result = self.api.list_export_formats(project.get("domain", "general"))
            if result.get("success"):
                formats = [f.get("name") for f in result.get("data", {}).get("formats", [])]
                if formats:
                    export_format = prompts.prompt_choice(
                        self.console,
                        "Export format",
                        formats,
                        default=formats[0]
                    )
                else:
                    self.print_error("No export formats available")
                    return
            else:
                self.print_error("Failed to load export formats")
                return
        else:
            export_format = args[0]

        # Get include options
        include_options = ["specifications", "code", "documentation", "tests", "generated-files"]
        includes = prompts.select_multiple_from_list(
            self.console,
            "Include in export",
            include_options,
            "Select items to include"
        )

        # Get optional settings
        include_history = prompts.prompt_confirm(
            self.console,
            "Include conversation history?",
            default=False
        )

        include_metadata = prompts.prompt_confirm(
            self.console,
            "Include metadata?",
            default=True
        )

        try:
            self.console.print("[cyan]Generating export...[/cyan]")

            result = self.api.generate_export(
                project.get("id"),
                export_format=export_format,
                includes=includes,
                include_history=include_history,
                include_metadata=include_metadata
            )

            if result.get("success"):
                self.print_success(f"Export generated: {export_format}")
                self.console.print(f"[cyan]Export ID: {result.get('export_id')}[/cyan]")
                self.console.print(f"[cyan]File size: {result.get('file_size')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def download(self, args: List[str]) -> None:
        """Download exported project"""
        project = self.ensure_project_selected()
        if not project:
            return

        if not args:
            self.console.print("[yellow]Usage: /export download <export_id>[/yellow]")
            return

        export_id = args[0]

        try:
            self.console.print("[cyan]Preparing download...[/cyan]")

            result = self.api.download_export(export_id)

            if result.get("success"):
                self.print_success("Export downloaded successfully")
                self.console.print(f"[cyan]Filename: {result.get('filename')}[/cyan]")
                self.console.print(f"[cyan]Location: {result.get('location')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")

    def schedule(self) -> None:
        """Schedule recurring export"""
        project = self.ensure_project_selected()
        if not project:
            return

        self.console.print("[bold cyan]Schedule Recurring Export[/bold cyan]\n")

        try:
            # Get format
            result = self.api.list_export_formats(project.get("domain", "general"))
            if result.get("success"):
                formats = [f.get("name") for f in result.get("data", {}).get("formats", [])]
                if formats:
                    export_format = prompts.prompt_choice(
                        self.console,
                        "Export format",
                        formats,
                        default=formats[0]
                    )
                else:
                    self.print_error("No export formats available")
                    return
            else:
                self.print_error("Failed to load export formats")
                return

            # Get frequency
            frequency = prompts.prompt_choice(
                self.console,
                "Export frequency",
                ["daily", "weekly", "monthly"],
                default="weekly"
            )

            # Get day/time if applicable
            if frequency == "weekly":
                day = prompts.prompt_choice(
                    self.console,
                    "Day of week",
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    default="Friday"
                )
            elif frequency == "monthly":
                day = prompts.prompt_choice(
                    self.console,
                    "Day of month",
                    [str(i) for i in range(1, 29)],
                    default="1"
                )

            time = prompts.prompt_text(self.console, "Time (HH:MM, e.g. 14:30)", default="09:00")

            # Get email
            email = prompts.prompt_confirm(
                self.console,
                "Email export when ready?",
                default=False
            )

            if not prompts.prompt_confirm(
                self.console,
                f"Schedule {frequency} {export_format} exports?",
                default=True
            ):
                self.console.print("[yellow]Cancelled[/yellow]")
                return

            self.console.print("[cyan]Scheduling export...[/cyan]")

            result = self.api.schedule_export(
                project.get("id"),
                export_format=export_format,
                frequency=frequency,
                time=time,
                email_on_complete=email
            )

            if result.get("success"):
                self.print_success("Export scheduled successfully")
                self.console.print(f"[cyan]Schedule ID: {result.get('schedule_id')}[/cyan]")
            else:
                error = result.get("error") or "Unknown error"
                self.print_error(f"Failed: {error}")

        except Exception as e:
            self.print_error(f"Error: {e}")
